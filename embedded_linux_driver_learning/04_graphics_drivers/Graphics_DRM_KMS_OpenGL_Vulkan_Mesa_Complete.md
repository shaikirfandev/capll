# Graphics Driver Development — DRM/KMS, OpenGL, Vulkan, Mesa

## Level 1: Graphics Stack Overview

```
User Space Application
        │
        │  OpenGL / Vulkan API calls
        ▼
   Mesa (libGL / libvulkan)           ← User space GPU driver
        │
        │  DRM/GEM ioctls
        ▼
  DRM Subsystem (kernel)              ← /dev/dri/card0
        │
        │  Hardware register access
        ▼
   GPU Hardware (Intel/AMD/ARM Mali)
```

### Key Concepts
- **DRM** = Direct Rendering Manager — kernel subsystem for GPU
- **KMS** = Kernel Mode Setting — controls display output (resolution, connector)
- **GEM** = Graphics Execution Manager — GPU memory management
- **TTM** = Translation Table Manager — VRAM allocator (older GPUs)
- **Mesa** = Open source OpenGL/Vulkan user space driver stack
- **libdrm** = User space library wrapping DRM ioctls

---

## Level 2: DRM/KMS — Kernel Mode Setting

### 2.1 KMS Architecture

```
Display Pipeline:

CRTC ──→ Encoder ──→ Connector ──→ Monitor
 ↑
Plane(s)
 ↑
Framebuffer (GEM object)

Objects:
- drm_crtc      : Controller (pixel clock, scanout)
- drm_encoder   : Signal conversion (CRTC → Connector protocol)
- drm_connector : Physical port (HDMI, DP, LVDS, DSI)
- drm_plane     : Scanout engine (primary, cursor, overlay)
- drm_framebuffer: GEM buffer + format info
```

### 2.2 Minimal DRM Driver Skeleton

```c
#include <drm/drm_drv.h>
#include <drm/drm_device.h>
#include <drm/drm_gem.h>
#include <drm/drm_crtc_helper.h>
#include <drm/drm_atomic_helper.h>
#include <drm/drm_connector.h>
#include <drm/drm_encoder.h>
#include <drm/drm_probe_helper.h>

struct my_gpu {
    struct drm_device   drm;
    void __iomem        *regs;
    struct drm_crtc     crtc;
    struct drm_encoder  encoder;
    struct drm_connector connector;
    struct drm_plane    primary_plane;
};

/* CRTC helpers */
static void my_crtc_enable(struct drm_crtc *crtc,
                            struct drm_atomic_state *state)
{
    struct my_gpu *gpu = container_of(crtc, struct my_gpu, crtc);
    /* Enable scanout hardware */
    writel(CRTC_ENABLE, gpu->regs + CRTC_CTRL);
}

static void my_crtc_disable(struct drm_crtc *crtc,
                             struct drm_atomic_state *state)
{
    struct my_gpu *gpu = container_of(crtc, struct my_gpu, crtc);
    writel(0, gpu->regs + CRTC_CTRL);
}

static const struct drm_crtc_helper_funcs my_crtc_helper_funcs = {
    .atomic_enable  = my_crtc_enable,
    .atomic_disable = my_crtc_disable,
    .atomic_flush   = my_crtc_atomic_flush,
};

static const struct drm_crtc_funcs my_crtc_funcs = {
    .reset              = drm_atomic_helper_crtc_reset,
    .destroy            = drm_crtc_cleanup,
    .set_config         = drm_atomic_helper_set_config,
    .page_flip          = drm_atomic_helper_page_flip,
    .atomic_duplicate_state = drm_atomic_helper_crtc_duplicate_state,
    .atomic_destroy_state   = drm_atomic_helper_crtc_destroy_state,
};

/* Connector — detects attached display */
static int my_connector_get_modes(struct drm_connector *connector)
{
    /* Add supported modes to connector->probed_modes */
    return drm_add_modes_noedid(connector, 1920, 1080);
}

static const struct drm_connector_helper_funcs my_conn_helper = {
    .get_modes = my_connector_get_modes,
};

static const struct drm_connector_funcs my_conn_funcs = {
    .reset                  = drm_atomic_helper_connector_reset,
    .detect                 = my_connector_detect,
    .fill_modes             = drm_helper_probe_single_connector_modes,
    .destroy                = drm_connector_cleanup,
    .atomic_duplicate_state = drm_atomic_helper_connector_duplicate_state,
    .atomic_destroy_state   = drm_atomic_helper_connector_destroy_state,
};

/* Driver description */
static const struct drm_driver my_drm_driver = {
    .driver_features = DRIVER_MODESET | DRIVER_GEM | DRIVER_ATOMIC,
    .name            = "my_gpu",
    .desc            = "My GPU Driver",
    .date            = "20240101",
    .major           = 1,
    .minor           = 0,
    .gem_create_object = my_gem_create_object,
    .prime_handle_to_fd = drm_gem_prime_handle_to_fd,
    .prime_fd_to_handle = drm_gem_prime_fd_to_handle,
    .gem_prime_import_sg_table = my_gem_prime_import_sg_table,
    .fops            = &my_drm_fops,
};

static int my_gpu_probe(struct platform_device *pdev)
{
    struct my_gpu *gpu;
    int ret;

    gpu = devm_drm_dev_alloc(&pdev->dev, &my_drm_driver,
                              struct my_gpu, drm);
    if (IS_ERR(gpu))
        return PTR_ERR(gpu);

    gpu->regs = devm_platform_ioremap_resource(pdev, 0);
    if (IS_ERR(gpu->regs))
        return PTR_ERR(gpu->regs);

    /* Initialize mode config */
    ret = drmm_mode_config_init(&gpu->drm);
    if (ret)
        return ret;

    gpu->drm.mode_config.max_width  = 4096;
    gpu->drm.mode_config.max_height = 4096;
    gpu->drm.mode_config.funcs      = &my_mode_config_funcs;

    /* Setup display pipeline */
    ret = my_setup_pipeline(gpu);
    if (ret)
        return ret;

    drm_mode_config_reset(&gpu->drm);

    ret = drm_dev_register(&gpu->drm, 0);
    if (ret)
        return ret;

    drm_fbdev_generic_setup(&gpu->drm, 32);
    return 0;
}
```

### 2.3 GEM Memory Management

```c
#include <drm/drm_gem.h>
#include <drm/drm_gem_shmem_helper.h>

/* Simple GEM with shmem backing (CPU-accessible) */
struct my_gem_object {
    struct drm_gem_shmem_object base;
    /* GPU-specific fields */
    dma_addr_t gpu_addr;
    u32        gpu_mmu_flags;
};

/* GPU buffer allocation */
static struct drm_gem_object *
my_gem_create_object(struct drm_device *dev, size_t size)
{
    struct my_gem_object *obj;

    obj = kzalloc(sizeof(*obj), GFP_KERNEL);
    if (!obj)
        return ERR_PTR(-ENOMEM);

    /* Map into GPU MMU */
    obj->gpu_addr = my_gpu_map_buffer(dev, obj);

    return &obj->base.base;
}

/* User space creates buffer: drmIoctl(fd, DRM_IOCTL_MODE_CREATE_DUMB, &args) */
/* User space maps buffer: mmap(NULL, size, PROT_READ|PROT_WRITE, MAP_SHARED, fd, offset) */
```

### 2.4 Atomic Modesetting

```c
/*
 * Modern KMS uses atomic commits:
 * - All changes (CRTC, plane, connector) applied atomically
 * - Supports asynchronous page flips
 * - Supports TEST_ONLY (validate without applying)
 */

/* User space (libdrm) atomic commit: */
drmModeAtomicReqPtr req = drmModeAtomicAlloc();
drmModeAtomicAddProperty(req, crtc_id, active_prop, 1);
drmModeAtomicAddProperty(req, plane_id, fb_id_prop, fb_id);
drmModeAtomicAddProperty(req, plane_id, crtc_id_prop, crtc_id);
drmModeAtomicCommit(fd, req, DRM_MODE_ATOMIC_ALLOW_MODESET, NULL);
drmModeAtomicFree(req);

/* Kernel-side atomic check */
static int my_atomic_check(struct drm_device *dev,
                            struct drm_atomic_state *state)
{
    return drm_atomic_helper_check(dev, state);
}

static int my_atomic_commit(struct drm_device *dev,
                             struct drm_atomic_state *state,
                             bool nonblock)
{
    return drm_atomic_helper_commit(dev, state, nonblock);
}
```

---

## Level 3: Mesa (User Space Driver)

### 3.1 Mesa Architecture

```
Application → libGL (mesa) → State Tracker (Gallium3D) → winsys → DRM
                           ↓
                     Driver: radeonsi, iris, lima, panfrost, etc.
                           ↓
                     LLVM / NIR → GPU ISA code generation
```

### 3.2 Mesa Gallium Driver Interface

```c
/* A Gallium driver implements struct pipe_screen and struct pipe_context */

/* screen: device-level operations */
struct pipe_screen *my_screen_create(int fd)
{
    struct my_screen *screen = CALLOC_STRUCT(my_screen);

    screen->base.get_param       = my_get_param;
    screen->base.get_shader_param = my_get_shader_param;
    screen->base.resource_create = my_resource_create;
    screen->base.context_create  = my_context_create;
    screen->base.flush_frontbuffer = my_flush_frontbuffer;

    return &screen->base;
}

/* context: per-context GPU operations */
static void my_draw_vbo(struct pipe_context *ctx,
                         const struct pipe_draw_info *info,
                         unsigned drawid_offset,
                         const struct pipe_draw_indirect_info *indirect,
                         const struct pipe_draw_start_count_bias *draws,
                         unsigned num_draws)
{
    /* Emit GPU commands for this draw call */
    my_emit_draw_packet(ctx, info, draws);
}
```

### 3.3 NIR (New IR) — Mesa's IR for shaders

```
GLSL/SPIR-V → NIR → lowering passes → backend (LLVM/custom) → GPU ISA

# NIR is a tree-based IR for GPU shader compilation
# Key concept: each driver implements "lowering" passes

# Example NIR optimization in Mesa source (src/compiler/nir/):
nir_opt_constant_folding(shader);
nir_opt_algebraic(shader);
nir_lower_vars_to_ssa(shader);
nir_lower_io(shader, nir_var_shader_in | nir_var_shader_out, ...);
```

---

## Level 4: Vulkan Driver Development

### 4.1 Vulkan Driver Stack

```
App → libvulkan (loader) → ICD (driver, e.g., radv, anv, tu, pvr)
                         ↓
                  VkDevice, VkQueue, VkCommandBuffer
                         ↓
                  DRM/KMS (modesetting) + DRM (rendering)
```

### 4.2 Key Vulkan Driver Concepts

```c
/* VkDevice creation triggers driver initialization */
VkResult my_CreateDevice(VkPhysicalDevice physicalDevice,
                          const VkDeviceCreateInfo *pCreateInfo,
                          const VkAllocationCallbacks *pAllocator,
                          VkDevice *pDevice)
{
    struct my_device *device = vk_zalloc(...);
    /* Initialize command submission engine */
    /* Setup descriptor set management */
    /* Initialize GPU memory allocator */
    return VK_SUCCESS;
}

/* Command buffer recording */
VkResult my_BeginCommandBuffer(VkCommandBuffer commandBuffer,
                                const VkCommandBufferBeginInfo *pBeginInfo)
{
    /* Reset CS (command stream) */
    cs_reset(&cmd_buf->cs);
    return VK_SUCCESS;
}

void my_CmdDraw(VkCommandBuffer commandBuffer,
                uint32_t vertexCount, uint32_t instanceCount,
                uint32_t firstVertex, uint32_t firstInstance)
{
    /* Emit draw call into command stream */
    my_emit_draw(&cmd_buf->cs, vertexCount, instanceCount);
}
```

### 4.3 SPIR-V to GPU ISA Flow

```
SPIR-V bytecode (from app)
    ↓ vk_pipeline_cache_create / spirv_to_nir()
NIR (Mesa IR)
    ↓ nir_opt_*() passes
Optimized NIR
    ↓ my_nir_to_isa() — driver-specific backend
GPU ISA binary
    ↓ Upload to VRAM
GPU executes
```

---

## Level 5: OpenGL Driver Concepts

### 5.1 OpenGL State Machine in Gallium

```c
/* OpenGL is a state machine — driver tracks state */
struct my_context {
    /* Bound objects */
    struct my_buffer *vertex_buffer;
    struct my_texture *bound_textures[32];
    struct my_shader *current_vs, *current_fs;

    /* Rasterizer state */
    struct pipe_rasterizer_state rast_state;

    /* Blend state */
    struct pipe_blend_state blend_state;

    /* Depth/stencil */
    struct pipe_depth_stencil_alpha_state dsa_state;
};

/* glDrawArrays → pipe_context::draw_vbo → GPU command */
```

---

## Debugging Graphics Drivers

```bash
# Enable DRM debug output
echo 0xFF > /sys/module/drm/parameters/debug

# Check KMS objects
drmModeGetResources()   → lists CRTCs, encoders, connectors
modetest -a             → display all KMS objects

# Mesa debug env vars
MESA_DEBUG=1            # Enable Mesa debug output
LIBGL_DEBUG=verbose     # OpenGL debug
RADV_DEBUG=startup      # Radeon Vulkan debug
ANV_DEBUG=startup       # Intel Vulkan debug

# GPU performance
intel_gpu_top           # Intel GPU usage
radeontop               # AMD GPU usage
perf stat -e gpu/*      # GPU perf counters

# Trace DRM ioctls
strace -e ioctl ./my_app 2>&1 | grep DRM

# DRI/KMS info
drm_info                # Display DRM device info
kmsprint                # Display KMS pipeline
```

---

## Interview Questions

1. Explain the difference between DRM and KMS.
2. What is a CRTC? What is a Plane? How do they relate?
3. What is atomic modesetting and why is it better than legacy KMS?
4. What is GEM? What is TTM? When is each used?
5. Explain the Mesa Gallium3D architecture.
6. What is NIR? Why does Mesa use an intermediate representation?
7. How does Vulkan differ from OpenGL in the driver model?
8. What is a dma-buf? How is it used for zero-copy buffer sharing?
9. Explain vsync and page flipping in KMS.
10. What is the role of `drm_atomic_helper` in a DRM driver?
