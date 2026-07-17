# Display Driver Development — X11, Wayland, Weston, Display Pipeline

## Level 1: Display Stack Overview

```
Traditional (X11):
App → Xlib/XCB → X Server (Xorg) → DDX (Device Dependent X) → DRM/KMS

Modern (Wayland):
App (Wayland client) → Wayland protocol → Compositor (Weston/Mutter/KWin)
                                                  │
                                                  ▼ DRM/KMS atomic commit
                                               GPU/Display hardware

Embedded:
App → DRM/KMS directly (no compositor) — kiosk mode
```

---

## Level 2: X11 / Xorg Display Driver (DDX)

### 2.1 X.Org Driver Architecture

```
Xorg Server
├── DIX (Device Independent X)  — protocol handling, input dispatch
└── DDX (Device Dependent X)   — driver interface

DDX driver (modesrc/modesetting or legacy):
├── xf86-video-modesetting  ← modern: uses KMS, works with any DRM driver
└── xf86-video-intel        ← legacy Intel-specific (deprecated)
```

### 2.2 Modesetting DDX (Modern Approach)

```bash
# Check Xorg driver being used
grep -i "driver\|module" /var/log/Xorg.0.log

# Force modesetting driver in /etc/X11/xorg.conf:
Section "Device"
    Identifier "GPU"
    Driver     "modesetting"
    Option     "AccelMethod" "glamor"   # glamor = GPU-accelerated 2D via OpenGL
EndSection

# GLAMOR = GL-based 2D acceleration using existing 3D driver
# This is how modern X11 works: modesetting + glamor + mesa
```

### 2.3 X11 Windowing Concepts

```c
/* X11 uses client-server model:
 * - X Server manages display hardware
 * - Clients send drawing commands
 * - Shared memory (MIT-SHM) or DRI3 for efficient rendering
 */

/* DRI3 (Direct Rendering Infrastructure 3) flow:
 * 1. Client creates GEM buffer (Mesa/libdrm)
 * 2. Client renders into buffer (OpenGL)
 * 3. Client sends buffer FD to X Server via DRI3Present
 * 4. X Server composites and displays via KMS
 */

/* Pixmap (server-side drawable) vs Window (hierarchical container) */
Display *dpy = XOpenDisplay(NULL);
Window win = XCreateSimpleWindow(dpy, root, 0, 0, 800, 600, ...);
GC gc = XCreateGC(dpy, win, 0, NULL);
XDrawLine(dpy, win, gc, 0, 0, 100, 100);
XFlush(dpy);
```

---

## Level 3: Wayland Protocol

### 3.1 Wayland Architecture

```
Wayland Client (wl_surface, wl_buffer, wl_seat)
        │
        │ Unix domain socket: /run/user/1000/wayland-0
        ▼
Wayland Compositor (Weston, Mutter, sway, KWin)
        │
        ├── Input handling (wl_seat: keyboard, pointer, touch)
        ├── Surface management (wl_surface, xdg_surface)
        └── Direct output via DRM/KMS atomic commit
```

### 3.2 Wayland Protocol Objects

```c
/* Core Wayland objects */
struct wl_display    /* connection to compositor */
struct wl_registry   /* global object registry */
struct wl_compositor /* creates surfaces */
struct wl_surface    /* framebuffer object */
struct wl_shell_surface /* window decorations (deprecated) */
struct xdg_surface   /* modern window management (xdg-shell) */
struct wl_buffer     /* pixel data (GEM/dma-buf backed) */
struct wl_seat       /* input device group */
struct wl_output     /* display output */
```

### 3.3 Minimal Wayland Client

```c
#include <wayland-client.h>
#include <xdg-shell-client-protocol.h>
#include <sys/mman.h>

struct client_state {
    struct wl_display    *display;
    struct wl_registry   *registry;
    struct wl_compositor *compositor;
    struct xdg_wm_base   *xdg_wm_base;
    struct wl_shm        *shm;
    struct wl_surface    *surface;
    struct xdg_surface   *xdg_surface;
    struct xdg_toplevel  *xdg_toplevel;
    struct wl_buffer     *buffer;
    int width, height;
};

/* Create shared memory buffer */
static struct wl_buffer *create_buffer(struct client_state *state)
{
    int stride = state->width * 4;   /* XRGB8888 */
    int size   = stride * state->height;

    /* Create anonymous shared memory */
    int fd = memfd_create("wayland-shm", 0);
    ftruncate(fd, size);

    void *data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);

    /* Draw something (checkerboard) */
    uint32_t *pixels = data;
    for (int y = 0; y < state->height; y++) {
        for (int x = 0; x < state->width; x++) {
            pixels[y * state->width + x] =
                ((x + y) % 2) ? 0xFFFF0000 : 0xFF00FF00;
        }
    }

    struct wl_shm_pool *pool = wl_shm_create_pool(state->shm, fd, size);
    struct wl_buffer *buf = wl_shm_pool_create_buffer(pool, 0,
        state->width, state->height, stride, WL_SHM_FORMAT_XRGB8888);
    wl_shm_pool_destroy(pool);
    munmap(data, size);
    close(fd);

    return buf;
}

/* Frame callback — re-render on each vsync */
static void frame_callback(void *data, struct wl_callback *cb, uint32_t time)
{
    struct client_state *state = data;
    wl_callback_destroy(cb);

    /* Re-render */
    state->buffer = create_buffer(state);
    wl_surface_attach(state->surface, state->buffer, 0, 0);
    wl_surface_damage(state->surface, 0, 0, state->width, state->height);

    /* Request next frame */
    struct wl_callback *next_cb = wl_surface_frame(state->surface);
    wl_callback_add_listener(next_cb, &frame_listener, state);

    wl_surface_commit(state->surface);
}

int main(void)
{
    struct client_state state = {
        .width  = 800,
        .height = 600,
    };

    state.display  = wl_display_connect(NULL);
    state.registry = wl_display_get_registry(state.display);
    wl_registry_add_listener(state.registry, &registry_listener, &state);
    wl_display_roundtrip(state.display);   /* bind globals */

    state.surface     = wl_compositor_create_surface(state.compositor);
    state.xdg_surface = xdg_wm_base_get_xdg_surface(state.xdg_wm_base,
                                                       state.surface);
    state.xdg_toplevel = xdg_surface_get_toplevel(state.xdg_surface);
    xdg_toplevel_set_title(state.xdg_toplevel, "My Wayland App");

    state.buffer = create_buffer(&state);
    wl_surface_attach(state.surface, state.buffer, 0, 0);
    wl_surface_commit(state.surface);

    while (wl_display_dispatch(state.display) != -1)
        ;   /* event loop */

    return 0;
}
```

---

## Level 4: Weston (Reference Wayland Compositor)

### 4.1 Weston Architecture

```
weston (compositor process)
├── Backend: DRM, Wayland (nested), fbdev, RDP, headless
│     └── DRM backend → KMS atomic commit → display hardware
├── Renderer: GL (EGL/GLES2), Pixman (software)
│     └── Composites surfaces into scanout buffer
├── Input: libinput → wl_seat
└── Shell: desktop-shell, kiosk-shell, fullscreen-shell
```

### 4.2 Weston DRM Backend

```c
/* Weston DRM backend uses KMS atomic for output */

/* Output = CRTC + plane */
struct drm_output {
    struct weston_output  base;
    uint32_t              crtc_id;
    uint32_t              connector_id;
    struct drm_plane     *primary_plane;
};

/* Repaint cycle */
static int drm_output_repaint(struct weston_output *output,
                               pixman_region32_t *damage)
{
    struct drm_output *drm_output = to_drm_output(output);
    struct drm_backend *b = to_drm_backend(output->compositor->backend);

    /* Render surfaces to scanout buffer */
    gl_renderer->repaint_output(output, damage);

    /* Atomic commit */
    drmModeAtomicReqPtr req = drmModeAtomicAlloc();
    add_plane_properties(req, drm_output);
    drmModeAtomicCommit(b->drm.fd, req,
        DRM_MODE_ATOMIC_NONBLOCK | DRM_MODE_PAGE_FLIP_EVENT, output);
    drmModeAtomicFree(req);
    return 0;
}
```

### 4.3 Weston Configuration

```ini
# /etc/xdg/weston/weston.ini

[core]
backend=drm-backend.so
shell=desktop-shell.so
idle-time=300

[output]
name=HDMI-A-1
mode=1920x1080@60
transform=normal

[output]
name=eDP-1
mode=1920x1200@60
transform=normal

[shell]
background-image=/usr/share/backgrounds/bg.jpg
background-type=scale-crop

[keyboard]
keymap_rules=evdev
keymap_layout=us

# Kiosk mode (embedded/automotive)
[core]
shell=kiosk-shell.so
```

### 4.4 Custom Weston Plugin (libweston)

```c
/* Custom compositor plugin using libweston */
#include <libweston/libweston.h>

static void
my_compositor_create_surface(struct wl_listener *listener, void *data)
{
    struct weston_surface *surface = data;

    /* Hook into surface creation */
    surface->committed = my_surface_committed;
    surface->committed_private = my_data;
}

struct weston_compositor *
my_compositor_create(struct wl_display *display)
{
    struct weston_compositor *comp = weston_compositor_create(display, NULL);
    struct weston_drm_backend_config config = {
        .base = { .struct_version = WESTON_DRM_BACKEND_CONFIG_VERSION },
        .connector = 0,    /* auto-detect */
        .tty = 1,
    };

    weston_compositor_load_backend(comp, WESTON_BACKEND_DRM,
                                   &config.base);

    /* Listen for surface creation */
    my_data.surface_create_listener.notify = my_compositor_create_surface;
    wl_signal_add(&comp->create_surface_signal,
                  &my_data.surface_create_listener);

    return comp;
}
```

---

## Level 5: Display Driver (Kernel) — DSI, LVDS, HDMI

### 5.1 DSI (Display Serial Interface) Driver

```c
#include <drm/drm_mipi_dsi.h>
#include <video/mipi_display.h>

struct my_panel {
    struct drm_panel     panel;
    struct mipi_dsi_device *dsi;
    struct gpio_desc     *reset_gpio;
    struct regulator     *supply;
};

static int my_panel_enable(struct drm_panel *panel)
{
    struct my_panel *p = container_of(panel, struct my_panel, panel);

    regulator_enable(p->supply);
    usleep_range(10000, 11000);

    gpiod_set_value_cansleep(p->reset_gpio, 0);
    usleep_range(10000, 11000);
    gpiod_set_value_cansleep(p->reset_gpio, 1);
    usleep_range(10000, 11000);

    return 0;
}

static int my_panel_prepare(struct drm_panel *panel)
{
    struct my_panel *p = container_of(panel, struct my_panel, panel);

    /* Send DSI init commands */
    mipi_dsi_dcs_exit_sleep_mode(p->dsi);
    usleep_range(120000, 121000);

    mipi_dsi_dcs_set_display_on(p->dsi);
    usleep_range(20000, 21000);

    /* Custom vendor-specific init */
    static const u8 init_cmds[] = { 0xB0, 0x01 };
    mipi_dsi_dcs_write_buffer(p->dsi, init_cmds, sizeof(init_cmds));

    return 0;
}

static const struct drm_panel_funcs my_panel_funcs = {
    .prepare = my_panel_prepare,
    .enable  = my_panel_enable,
    .disable = my_panel_disable,
    .unprepare = my_panel_unprepare,
    .get_modes = my_panel_get_modes,
};

static int my_panel_probe(struct mipi_dsi_device *dsi)
{
    struct my_panel *p;
    int ret;

    p = devm_kzalloc(&dsi->dev, sizeof(*p), GFP_KERNEL);
    if (!p)
        return -ENOMEM;

    p->dsi = dsi;
    dsi->mode_flags = MIPI_DSI_MODE_VIDEO | MIPI_DSI_MODE_VIDEO_BURST;
    dsi->format     = MIPI_DSI_FMT_RGB888;
    dsi->lanes      = 4;

    p->supply = devm_regulator_get(&dsi->dev, "power");
    p->reset_gpio = devm_gpiod_get(&dsi->dev, "reset", GPIOD_OUT_HIGH);

    drm_panel_init(&p->panel, &dsi->dev, &my_panel_funcs,
                   DRM_MODE_CONNECTOR_DSI);
    mipi_dsi_set_drvdata(dsi, p);

    ret = drm_panel_add(&p->panel);
    if (ret)
        return ret;

    return mipi_dsi_attach(dsi);
}
```

---

## Debugging Display Drivers

```bash
# List all KMS objects
modetest -a
drm_info

# Force a specific mode
xrandr --output HDMI-1 --mode 1920x1080 --rate 60

# Wayland specific
WAYLAND_DEBUG=1 weston              # protocol trace
weston-debug screenshot             # capture display

# DRM debug
echo 0xFF > /sys/module/drm/parameters/debug
dmesg | grep "drm\|DRM"

# Display EDID
edid-decode /sys/class/drm/card0-HDMI-A-1/edid
get-edid | parse-edid

# Test display pipeline with kmstest
modetest -s <connector_id>:<mode>

# Panel driver debug
cat /sys/class/backlight/*/actual_brightness
echo 100 > /sys/class/backlight/*/brightness
```

---

## Interview Questions

1. What is the difference between X11 and Wayland architecturally?
2. What is XDG shell in Wayland?
3. Explain the Weston repaint cycle.
4. What is glamor in X11?
5. How does DRI3 enable efficient rendering under X11?
6. What is a DSI panel driver and how does it attach to the DRM pipeline?
7. Explain `wl_surface_commit` — what happens at the compositor level?
8. What is a KMS plane and how is it used for hardware composition?
9. What is the role of EGL in a Wayland compositor?
10. How does screen rotation work in a DRM/KMS driver?
