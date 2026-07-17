# Multimedia & Video Driver Development — V4L2, GStreamer, VAAPI, VDPAU

## Level 1: Multimedia Stack Overview

```
Application (ffmpeg, VLC, Chrome)
        │
        │ GStreamer pipeline / libva / libvdpau
        ▼
   Middleware Layer
   ┌──────────┬──────────┬──────────┐
   │ GStreamer│  libva   │ libvdpau │
   │(pipeline)│ (VAAPI)  │ (VDPAU)  │
   └────┬─────┴─────┬────┴────┬─────┘
        │            │         │
        ▼            ▼         ▼
   V4L2 kernel    i965-va   vdpau-va
   subsystem      driver    (Mesa)
        │
        ▼
   Video capture/output driver
   (uvcvideo, vivid, cedrus, etc.)
```

---

## Level 2: V4L2 (Video for Linux 2)

### 2.1 V4L2 Concepts

| Concept | Description |
|---------|-------------|
| `v4l2_device` | Top-level device (binds sub-devices) |
| `video_device` | `/dev/videoN` node |
| `v4l2_subdev` | Sub-device (sensor, ISP, bridge) |
| `vb2_queue` | Video buffer queue (videobuf2) |
| `v4l2_ctrl` | Control (brightness, contrast, gain) |

### 2.2 V4L2 Capture Driver (Full Example)

```c
#include <linux/videodev2.h>
#include <media/v4l2-device.h>
#include <media/v4l2-dev.h>
#include <media/v4l2-ioctl.h>
#include <media/videobuf2-v4l2.h>
#include <media/videobuf2-dma-contig.h>

struct my_cam {
    struct v4l2_device   v4l2_dev;
    struct video_device  vdev;
    struct vb2_queue     queue;
    struct v4l2_format   fmt;
    spinlock_t           qlock;
    struct list_head     buf_list;
    bool                 streaming;
};

struct my_buffer {
    struct vb2_v4l2_buffer vbuf;
    struct list_head        list;
    dma_addr_t              dma_addr;
};

/* ======================== VB2 Operations ======================== */

static int my_queue_setup(struct vb2_queue *vq,
                           unsigned int *nbuffers, unsigned int *nplanes,
                           unsigned int sizes[], struct device *alloc_devs[])
{
    struct my_cam *cam = vb2_get_drv_priv(vq);
    unsigned int size = cam->fmt.fmt.pix.sizeimage;

    if (*nplanes)
        return sizes[0] < size ? -EINVAL : 0;

    *nplanes = 1;
    sizes[0] = size;
    return 0;
}

static void my_buf_queue(struct vb2_buffer *vb)
{
    struct my_cam *cam = vb2_get_drv_priv(vb->vb2_queue);
    struct vb2_v4l2_buffer *vbuf = to_vb2_v4l2_buffer(vb);
    struct my_buffer *buf = container_of(vbuf, struct my_buffer, vbuf);
    unsigned long flags;

    spin_lock_irqsave(&cam->qlock, flags);
    list_add_tail(&buf->list, &cam->buf_list);
    spin_unlock_irqrestore(&cam->qlock, flags);
}

static int my_start_streaming(struct vb2_queue *vq, unsigned int count)
{
    struct my_cam *cam = vb2_get_drv_priv(vq);
    cam->streaming = true;
    /* Enable hardware DMA, IRQ */
    my_hw_start(cam);
    return 0;
}

static void my_stop_streaming(struct vb2_queue *vq)
{
    struct my_cam *cam = vb2_get_drv_priv(vq);
    struct my_buffer *buf, *tmp;
    unsigned long flags;

    my_hw_stop(cam);
    cam->streaming = false;

    /* Return all queued buffers */
    spin_lock_irqsave(&cam->qlock, flags);
    list_for_each_entry_safe(buf, tmp, &cam->buf_list, list) {
        list_del(&buf->list);
        vb2_buffer_done(&buf->vbuf.vb2_buf, VB2_BUF_STATE_ERROR);
    }
    spin_unlock_irqrestore(&cam->qlock, flags);
}

static const struct vb2_ops my_vb2_ops = {
    .queue_setup     = my_queue_setup,
    .buf_queue       = my_buf_queue,
    .start_streaming = my_start_streaming,
    .stop_streaming  = my_stop_streaming,
    .wait_prepare    = vb2_ops_wait_prepare,
    .wait_finish     = vb2_ops_wait_finish,
};

/* ======================== IRQ: Frame completion ======================== */

static irqreturn_t my_frame_irq(int irq, void *data)
{
    struct my_cam *cam = data;
    struct my_buffer *buf;
    unsigned long flags;

    spin_lock_irqsave(&cam->qlock, flags);
    if (list_empty(&cam->buf_list)) {
        spin_unlock_irqrestore(&cam->qlock, flags);
        return IRQ_HANDLED;
    }

    buf = list_first_entry(&cam->buf_list, struct my_buffer, list);
    list_del(&buf->list);
    spin_unlock_irqrestore(&cam->qlock, flags);

    /* Fill timestamp */
    buf->vbuf.vb2_buf.timestamp = ktime_get_ns();
    buf->vbuf.sequence = cam->sequence++;
    buf->vbuf.field = V4L2_FIELD_NONE;

    vb2_buffer_done(&buf->vbuf.vb2_buf, VB2_BUF_STATE_DONE);
    return IRQ_HANDLED;
}

/* ======================== V4L2 ioctls ======================== */

static int my_querycap(struct file *file, void *priv,
                        struct v4l2_capability *cap)
{
    strscpy(cap->driver, "my_camera", sizeof(cap->driver));
    strscpy(cap->card,   "My Camera", sizeof(cap->card));
    cap->device_caps = V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_STREAMING;
    cap->capabilities = cap->device_caps | V4L2_CAP_DEVICE_CAPS;
    return 0;
}

static int my_enum_fmt(struct file *file, void *priv,
                        struct v4l2_fmtdesc *f)
{
    static const u32 formats[] = {
        V4L2_PIX_FMT_YUYV,
        V4L2_PIX_FMT_NV12,
        V4L2_PIX_FMT_RGB24,
    };

    if (f->index >= ARRAY_SIZE(formats))
        return -EINVAL;

    f->pixelformat = formats[f->index];
    return 0;
}

static int my_g_fmt(struct file *file, void *priv, struct v4l2_format *f)
{
    struct my_cam *cam = video_drvdata(file);
    f->fmt.pix = cam->fmt.fmt.pix;
    return 0;
}

static int my_s_fmt(struct file *file, void *priv, struct v4l2_format *f)
{
    struct my_cam *cam = video_drvdata(file);
    if (vb2_is_busy(&cam->queue))
        return -EBUSY;
    /* Validate and apply format */
    cam->fmt = *f;
    return 0;
}

static const struct v4l2_ioctl_ops my_ioctl_ops = {
    .vidioc_querycap         = my_querycap,
    .vidioc_enum_fmt_vid_cap = my_enum_fmt,
    .vidioc_g_fmt_vid_cap    = my_g_fmt,
    .vidioc_s_fmt_vid_cap    = my_s_fmt,
    .vidioc_try_fmt_vid_cap  = my_try_fmt,
    .vidioc_reqbufs          = vb2_ioctl_reqbufs,
    .vidioc_querybuf         = vb2_ioctl_querybuf,
    .vidioc_qbuf             = vb2_ioctl_qbuf,
    .vidioc_dqbuf            = vb2_ioctl_dqbuf,
    .vidioc_streamon         = vb2_ioctl_streamon,
    .vidioc_streamoff        = vb2_ioctl_streamoff,
};

/* ======================== Probe ======================== */

static int my_cam_probe(struct platform_device *pdev)
{
    struct my_cam *cam;
    int ret;

    cam = devm_kzalloc(&pdev->dev, sizeof(*cam), GFP_KERNEL);
    if (!cam)
        return -ENOMEM;

    spin_lock_init(&cam->qlock);
    INIT_LIST_HEAD(&cam->buf_list);

    ret = v4l2_device_register(&pdev->dev, &cam->v4l2_dev);
    if (ret)
        return ret;

    /* Setup VB2 queue */
    cam->queue.type            = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    cam->queue.io_modes        = VB2_MMAP | VB2_DMABUF;
    cam->queue.drv_priv        = cam;
    cam->queue.buf_struct_size = sizeof(struct my_buffer);
    cam->queue.ops             = &my_vb2_ops;
    cam->queue.mem_ops         = &vb2_dma_contig_memops;
    cam->queue.timestamp_flags = V4L2_BUF_FLAG_TIMESTAMP_MONOTONIC;
    cam->queue.lock            = &cam->vdev.lock;

    ret = vb2_queue_init(&cam->queue);
    if (ret)
        goto err_v4l2;

    /* Setup video_device */
    strscpy(cam->vdev.name, "my_camera", sizeof(cam->vdev.name));
    cam->vdev.release   = video_device_release_empty;
    cam->vdev.fops      = &my_fops;
    cam->vdev.ioctl_ops = &my_ioctl_ops;
    cam->vdev.v4l2_dev  = &cam->v4l2_dev;
    cam->vdev.queue     = &cam->queue;
    cam->vdev.device_caps = V4L2_CAP_VIDEO_CAPTURE | V4L2_CAP_STREAMING;
    video_set_drvdata(&cam->vdev, cam);

    ret = video_register_device(&cam->vdev, VFL_TYPE_VIDEO, -1);
    if (ret)
        goto err_v4l2;

    dev_info(&pdev->dev, "Registered as /dev/video%d\n", cam->vdev.num);
    return 0;

err_v4l2:
    v4l2_device_unregister(&cam->v4l2_dev);
    return ret;
}
```

---

## Level 3: GStreamer Pipeline Architecture

### 3.1 GStreamer Concepts

```
Source → Filter → Filter → Sink
(camera)  (decode)  (scale)  (display)

GStreamer elements communicate through pads:
  src pad ──caps negotiation──> sink pad
  
Buffers flow downstream; events/queries flow both ways.
```

### 3.2 GStreamer Pipeline Examples

```bash
# Basic camera capture → display
gst-launch-1.0 v4l2src device=/dev/video0 \
    ! video/x-raw,width=1920,height=1080,framerate=30/1 \
    ! autovideosink

# Hardware decode (H.264) with VAAPI
gst-launch-1.0 filesrc location=video.mp4 \
    ! qtdemux \
    ! h264parse \
    ! vaapih264dec \
    ! vaapipostproc \
    ! autovideosink

# Encode camera to H.264 file
gst-launch-1.0 v4l2src device=/dev/video0 \
    ! video/x-raw,width=1920,height=1080 \
    ! vaapih264enc \
    ! mp4mux \
    ! filesink location=output.mp4

# V4L2 M2M (memory-to-memory) hardware encode
gst-launch-1.0 filesrc location=input.yuv \
    ! rawvideoparse width=1920 height=1080 format=nv12 \
    ! v4l2h264enc \
    ! filesink location=output.h264
```

### 3.3 Writing a GStreamer Plugin (V4L2 M2M)

```c
/* GStreamer plugin that wraps V4L2 M2M encoder */
#include <gst/gst.h>
#include <gst/video/video.h>

typedef struct _GstMyEncoder GstMyEncoder;
struct _GstMyEncoder {
    GstElement   element;
    GstPad      *sinkpad, *srcpad;
    int          fd;        /* V4L2 device fd */
    int          width, height;
};

/* Process incoming buffer */
static GstFlowReturn
gst_my_encoder_chain(GstPad *pad, GstObject *parent, GstBuffer *buf)
{
    GstMyEncoder *enc = GST_MY_ENCODER(parent);
    GstMapInfo map;
    struct v4l2_buffer v4l2_buf = {0};

    gst_buffer_map(buf, &map, GST_MAP_READ);

    /* Queue input buffer to V4L2 */
    v4l2_buf.type   = V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE;
    v4l2_buf.memory = V4L2_MEMORY_DMABUF;
    /* ... setup planes ... */
    ioctl(enc->fd, VIDIOC_QBUF, &v4l2_buf);

    gst_buffer_unmap(buf, &map);
    gst_buffer_unref(buf);

    /* Dequeue encoded output */
    struct v4l2_buffer out_buf = {0};
    out_buf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;
    out_buf.memory = V4L2_MEMORY_MMAP;
    ioctl(enc->fd, VIDIOC_DQBUF, &out_buf);

    GstBuffer *out = gst_buffer_new_wrapped_full(0,
        enc->output_bufs[out_buf.index].addr,
        out_buf.m.planes[0].length,
        0, out_buf.m.planes[0].bytesused,
        NULL, NULL);

    return gst_pad_push(enc->srcpad, out);
}
```

---

## Level 4: VAAPI (Video Acceleration API)

### 4.1 VAAPI Architecture

```
Application (ffmpeg, VLC)
    │ libva API calls
    ▼
libva (VA-API)
    │ loads backend driver
    ▼
Backend driver (intel-media-driver / mesa-va-gallium)
    │ DRM ioctls (execbuf, gem_create)
    ▼
i915/amdgpu kernel driver
    │
    ▼
GPU video decode/encode engine
```

### 4.2 VAAPI Usage (libva)

```c
#include <va/va.h>
#include <va/va_drm.h>

int fd = open("/dev/dri/renderD128", O_RDWR);
VADisplay dpy = vaGetDisplayDRM(fd);

int major, minor;
vaInitialize(dpy, &major, &minor);

/* Create decode context */
VAConfigID config;
VAConfigAttrib attrib = {VAConfigAttribRTFormat, VA_RT_FORMAT_YUV420};
vaCreateConfig(dpy, VAProfileH264High, VAEntrypointVLD, &attrib, 1, &config);

VAContextID context;
vaCreateContext(dpy, config, 1920, 1080, VA_PROGRESSIVE,
                surfaces, num_surfaces, &context);

/* Create surface for decoded output */
VASurfaceID surface;
vaCreateSurfaces(dpy, VA_RT_FORMAT_YUV420, 1920, 1080, &surface, 1, NULL, 0);

/* Begin picture */
vaBeginPicture(dpy, context, surface);
vaRenderPicture(dpy, context, &buf_id, 1);   /* send slice data */
vaEndPicture(dpy, context);

/* Sync and get data */
vaSyncSurface(dpy, surface);
```

---

## Level 5: VDPAU (Video Decode and Presentation API for Unix)

```
VDPAU (mainly NVIDIA + AMD via Mesa)

App → libvdpau → VDPAU driver (mesa-vdpau / nvidia)
                        │
                        ▼ (Mesa path)
              Gallium VDPAU state tracker
                        │
                        ▼
              r600g / radeonsi / nouveau driver
                        │
                        ▼
                     Kernel DRM
```

```c
#include <vdpau/vdpau.h>
#include <vdpau/vdpau_x11.h>

VdpDevice device;
VdpGetProcAddress *vdp_get_proc_address;
vdp_device_create_x11(display, screen, &device, &vdp_get_proc_address);

/* Get function pointers */
VdpDecoderCreate *vdp_decoder_create;
vdp_get_proc_address(device, VDP_FUNC_ID_DECODER_CREATE,
                     (void**)&vdp_decoder_create);

VdpDecoder decoder;
vdp_decoder_create(device, VDP_DECODER_PROFILE_H264_HIGH,
                   1920, 1080, 16, &decoder);
```

---

## Debugging Multimedia Drivers

```bash
# V4L2 tools
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext
v4l2-ctl -d /dev/video0 --list-ctrls
v4l2-ctl -d /dev/video0 --stream-mmap=3 --stream-to=frame.yuv

# Test V4L2 driver with vivid (virtual V4L2 device)
sudo modprobe vivid
v4l2-ctl -d /dev/video0 --set-fmt-video=width=640,height=480,pixelformat=YUYV

# GStreamer debug
GST_DEBUG=3 gst-launch-1.0 ...          # level 1-9
GST_DEBUG=vaapi*:6 gst-launch-1.0 ...  # VAAPI specific

# VAAPI debug
LIBVA_MESSAGING_LEVEL=2 vainfo
LIBVA_DRIVER_NAME=iHD vainfo          # Force Intel media driver

# V4L2 codec/M2M test
v4l2-compliance -d /dev/video0        # compliance test suite
```

---

## Interview Questions

1. What is V4L2 and what is VB2 (videobuf2)?
2. Explain the V4L2 M2M (memory-to-memory) device concept.
3. What is the difference between `V4L2_MEMORY_MMAP`, `V4L2_MEMORY_USERPTR`, and `V4L2_MEMORY_DMABUF`?
4. How does a camera sensor connect to the SoC ISP pipeline using V4L2 sub-devices?
5. What is GStreamer's element-pad-buffer model?
6. Explain the VAAPI decode pipeline.
7. What is the role of `dma-buf` in zero-copy video pipelines?
8. How does hardware video decode work at the kernel level?
9. What is a V4L2 media controller and when is it used?
10. Explain `VIDIOC_STREAMON` / `VIDIOC_STREAMOFF` buffer flow.

---

---

# Real-World Project: Zero-Copy ADAS Dashcam Recording System

## Project Overview

A production-grade embedded dashcam that captures 1080p@30fps from an OV5640 camera over MIPI-CSI2, encodes to H.264 in hardware using a V4L2 M2M encoder (e.g. i.MX8M VPU or Cedrus on Allwinner), and writes segmented MP4 files to eMMC — all without a single CPU memcpy in the critical path.

**Hardware target:** NXP i.MX8M Plus EVK (or any SoC with V4L2 camera + V4L2 M2M encoder)

```
OV5640 sensor (MIPI-CSI2)
       │
       ▼  (Kernel: ov5640 subdev + imx8-mipi-csi2 bridge)
  ISP / CSI receiver
       │  /dev/video0   (V4L2 capture, NV12 frames, dma-buf)
       ▼
  [dma-buf fd export]──────────────────────────────────────────┐
       │                                                        │
       │  /dev/video1   (V4L2 M2M encoder, H.264 bitstream)    │
       ▼                                                        │
  VPU H.264 encoder  ←── imported dma-buf (zero-copy) ←───────┘
       │  H.264 NAL units
       ▼
  MP4 muxer (user-space, libmp4v2)
       │
       ▼
  /data/dashcam/YYYY-MM-DD_HH-MM-SS.mp4   (60-second segments)
```

**Technologies used in this project:**
- V4L2 subdev (sensor driver)
- V4L2 capture driver (ISP/CSI)
- V4L2 M2M encoder driver (VPU)
- dma-buf zero-copy between capture and encoder
- VAAPI encode path (fallback on x86 dev machine)
- GStreamer pipeline (production variant)
- systemd service + watchdog
- Yocto recipe

---

## Project Structure

```
dashcam/
├── kernel/
│   ├── ov5640_dashcam.c          # sensor subdev driver
│   └── Makefile
├── src/
│   ├── capture.c                 # V4L2 capture + dma-buf export
│   ├── capture.h
│   ├── encoder.c                 # V4L2 M2M encoder (dma-buf import)
│   ├── encoder.h
│   ├── muxer.c                   # MP4 segmenter
│   ├── muxer.h
│   ├── pipeline.c                # ties capture → encoder → muxer
│   ├── watchdog.c                # hardware watchdog refresh
│   └── main.c
├── gst/
│   └── dashcam_gst.c             # GStreamer variant (production fallback)
├── systemd/
│   └── dashcam.service
├── yocto/
│   └── dashcam_1.0.bb
└── Makefile
```

---

## 1. Kernel: OV5640 Sensor Subdev Driver

### `kernel/ov5640_dashcam.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * OV5640 MIPI-CSI2 sensor driver (dashcam variant)
 * Supports 1080p30 NV12 output for ADAS recording.
 *
 * This is a simplified production driver. In a real product you would
 * use the upstream ov5640.c with your board-specific DTS overlay.
 */

#include <linux/module.h>
#include <linux/i2c.h>
#include <linux/regmap.h>
#include <linux/gpio/consumer.h>
#include <linux/clk.h>
#include <linux/delay.h>
#include <media/v4l2-subdev.h>
#include <media/v4l2-ctrls.h>

#define OV5640_REG_SYS_RESET        0x3008
#define OV5640_REG_CHIP_ID_H        0x300A
#define OV5640_REG_CHIP_ID_L        0x300B
#define OV5640_CHIP_ID              0x5640
#define OV5640_1080P_LANES          2
#define OV5640_1080P_MBPS           672

struct ov5640_mode {
    u32 width, height;
    u32 fps;
    u32 pixel_rate;
    u32 link_freq;
};

static const struct ov5640_mode ov5640_1080p30 = {
    .width      = 1920,
    .height     = 1080,
    .fps        = 30,
    .pixel_rate = 168000000,
    .link_freq  = 336000000,
};

struct ov5640 {
    struct i2c_client       *client;
    struct regmap           *regmap;
    struct v4l2_subdev       sd;
    struct media_pad         pad;
    struct v4l2_ctrl_handler ctrl_handler;
    struct clk              *xclk;          /* 24 MHz XCLK */
    struct gpio_desc        *reset_gpio;
    struct gpio_desc        *pwdn_gpio;
    const struct ov5640_mode *cur_mode;
    bool                     streaming;
};

static inline struct ov5640 *sd_to_ov5640(struct v4l2_subdev *sd)
{
    return container_of(sd, struct ov5640, sd);
}

/* ------------------------------------------------------------------ */
/*  Power up / down                                                     */
/* ------------------------------------------------------------------ */

static int ov5640_power_on(struct ov5640 *sensor)
{
    int ret;

    ret = clk_prepare_enable(sensor->xclk);
    if (ret)
        return ret;

    /* De-assert power-down first, then reset */
    gpiod_set_value_cansleep(sensor->pwdn_gpio, 0);
    usleep_range(1000, 2000);

    gpiod_set_value_cansleep(sensor->reset_gpio, 1);
    usleep_range(5000, 10000);
    gpiod_set_value_cansleep(sensor->reset_gpio, 0);
    usleep_range(20000, 25000);  /* wait for sensor init */

    return 0;
}

static void ov5640_power_off(struct ov5640 *sensor)
{
    gpiod_set_value_cansleep(sensor->reset_gpio, 1);
    gpiod_set_value_cansleep(sensor->pwdn_gpio, 1);
    clk_disable_unprepare(sensor->xclk);
}

/* ------------------------------------------------------------------ */
/*  Chip ID verify                                                      */
/* ------------------------------------------------------------------ */

static int ov5640_check_chip_id(struct ov5640 *sensor)
{
    u32 hi, lo;
    int ret;

    ret  = regmap_read(sensor->regmap, OV5640_REG_CHIP_ID_H, &hi);
    ret |= regmap_read(sensor->regmap, OV5640_REG_CHIP_ID_L, &lo);
    if (ret)
        return ret;

    if (((hi << 8) | lo) != OV5640_CHIP_ID) {
        dev_err(&sensor->client->dev,
                "unexpected chip id 0x%04x\n", (hi << 8) | lo);
        return -ENODEV;
    }
    return 0;
}

/* ------------------------------------------------------------------ */
/*  Subdev video ops                                                    */
/* ------------------------------------------------------------------ */

static int ov5640_s_stream(struct v4l2_subdev *sd, int enable)
{
    struct ov5640 *sensor = sd_to_ov5640(sd);
    int ret = 0;

    if (enable == sensor->streaming)
        return 0;

    if (enable) {
        /* Write 1080p30 register table (abbreviated) */
        ret = regmap_write(sensor->regmap, OV5640_REG_SYS_RESET, 0x02);
        if (ret)
            return ret;
        /* ... full reg table would be here ... */
    } else {
        regmap_write(sensor->regmap, OV5640_REG_SYS_RESET, 0x42); /* standby */
    }

    sensor->streaming = enable;
    return ret;
}

static int ov5640_enum_mbus_code(struct v4l2_subdev *sd,
                                  struct v4l2_subdev_state *state,
                                  struct v4l2_subdev_mbus_code_enum *code)
{
    if (code->index != 0)
        return -EINVAL;
    code->code = MEDIA_BUS_FMT_UYVY8_2X8;  /* MIPI YUV422 → ISP converts to NV12 */
    return 0;
}

static int ov5640_get_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *state,
                           struct v4l2_subdev_format *fmt)
{
    fmt->format.code   = MEDIA_BUS_FMT_UYVY8_2X8;
    fmt->format.width  = 1920;
    fmt->format.height = 1080;
    fmt->format.field  = V4L2_FIELD_NONE;
    return 0;
}

static const struct v4l2_subdev_video_ops ov5640_video_ops = {
    .s_stream = ov5640_s_stream,
};

static const struct v4l2_subdev_pad_ops ov5640_pad_ops = {
    .enum_mbus_code = ov5640_enum_mbus_code,
    .get_fmt        = ov5640_get_fmt,
    .set_fmt        = ov5640_get_fmt,   /* simplified: always 1080p */
};

static const struct v4l2_subdev_ops ov5640_subdev_ops = {
    .video = &ov5640_video_ops,
    .pad   = &ov5640_pad_ops,
};

/* ------------------------------------------------------------------ */
/*  i2c probe / remove                                                  */
/* ------------------------------------------------------------------ */

static const struct regmap_config ov5640_regmap_config = {
    .reg_bits   = 16,
    .val_bits   = 8,
    .max_register = 0xFFFF,
};

static int ov5640_probe(struct i2c_client *client)
{
    struct device *dev = &client->dev;
    struct ov5640 *sensor;
    int ret;

    sensor = devm_kzalloc(dev, sizeof(*sensor), GFP_KERNEL);
    if (!sensor)
        return -ENOMEM;

    sensor->client = client;

    sensor->xclk = devm_clk_get(dev, "xclk");
    if (IS_ERR(sensor->xclk))
        return dev_err_probe(dev, PTR_ERR(sensor->xclk), "no xclk\n");

    if (clk_get_rate(sensor->xclk) != 24000000)
        return dev_err_probe(dev, -EINVAL, "xclk must be 24 MHz\n");

    sensor->reset_gpio = devm_gpiod_get(dev, "reset", GPIOD_OUT_HIGH);
    if (IS_ERR(sensor->reset_gpio))
        return dev_err_probe(dev, PTR_ERR(sensor->reset_gpio), "no reset gpio\n");

    sensor->pwdn_gpio = devm_gpiod_get(dev, "powerdown", GPIOD_OUT_HIGH);
    if (IS_ERR(sensor->pwdn_gpio))
        return dev_err_probe(dev, PTR_ERR(sensor->pwdn_gpio), "no pwdn gpio\n");

    sensor->regmap = devm_regmap_init_i2c(client, &ov5640_regmap_config);
    if (IS_ERR(sensor->regmap))
        return PTR_ERR(sensor->regmap);

    ret = ov5640_power_on(sensor);
    if (ret)
        return ret;

    ret = ov5640_check_chip_id(sensor);
    if (ret)
        goto err_power_off;

    v4l2_i2c_subdev_init(&sensor->sd, client, &ov5640_subdev_ops);
    sensor->sd.flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
    sensor->pad.flags = MEDIA_PAD_FL_SOURCE;

    ret = media_entity_pads_init(&sensor->sd.entity, 1, &sensor->pad);
    if (ret)
        goto err_power_off;

    ret = v4l2_async_register_subdev(&sensor->sd);
    if (ret)
        goto err_media;

    dev_info(dev, "OV5640 1080p30 sensor ready\n");
    return 0;

err_media:
    media_entity_cleanup(&sensor->sd.entity);
err_power_off:
    ov5640_power_off(sensor);
    return ret;
}

static void ov5640_remove(struct i2c_client *client)
{
    struct ov5640 *sensor = i2c_get_clientdata(client);

    v4l2_async_unregister_subdev(&sensor->sd);
    media_entity_cleanup(&sensor->sd.entity);
    ov5640_power_off(sensor);
}

static const struct of_device_id ov5640_of_ids[] = {
    { .compatible = "ovti,ov5640" },
    {}
};
MODULE_DEVICE_TABLE(of, ov5640_of_ids);

static struct i2c_driver ov5640_driver = {
    .driver = {
        .name  = "ov5640-dashcam",
        .of_match_table = ov5640_of_ids,
    },
    .probe  = ov5640_probe,
    .remove = ov5640_remove,
};
module_i2c_driver(ov5640_driver);

MODULE_AUTHOR("Dashcam Team");
MODULE_DESCRIPTION("OV5640 MIPI-CSI2 sensor for dashcam");
MODULE_LICENSE("GPL v2");
```

---

## 2. User-Space: V4L2 Capture with dma-buf Export

### `src/capture.h`

```c
#ifndef CAPTURE_H
#define CAPTURE_H

#include <stdint.h>
#include <stdbool.h>

#define CAPTURE_BUFFERS   4
#define CAPTURE_WIDTH  1920
#define CAPTURE_HEIGHT 1080
#define CAPTURE_FPS      30

/* One captured frame — carries a dma-buf fd for zero-copy to encoder */
struct frame {
    int      dmabuf_fd;     /* exported dma-buf fd (passed to encoder) */
    uint32_t index;         /* VB2 buffer index (for QBUF) */
    uint32_t bytesused;
    uint64_t timestamp_us;
};

struct capture_ctx;

struct capture_ctx *capture_open(const char *dev);
int                 capture_start(struct capture_ctx *ctx);
int                 capture_dequeue(struct capture_ctx *ctx, struct frame *f);
int                 capture_queue(struct capture_ctx *ctx, uint32_t index);
void                capture_stop(struct capture_ctx *ctx);
void                capture_close(struct capture_ctx *ctx);

#endif /* CAPTURE_H */
```

### `src/capture.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * V4L2 capture — allocates MMAP buffers, exports each as a dma-buf fd.
 * The encoder will import these fds so no CPU copy is ever needed.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <time.h>
#include <linux/videodev2.h>
#include "capture.h"

struct cap_buffer {
    void    *vaddr;
    size_t   length;
    int      dmabuf_fd;   /* exported once, reused every frame */
};

struct capture_ctx {
    int              fd;
    struct cap_buffer bufs[CAPTURE_BUFFERS];
};

/* Helper: ioctl with retry on EINTR */
static int xioctl(int fd, unsigned long req, void *arg)
{
    int r;
    do {
        r = ioctl(fd, req, arg);
    } while (r == -1 && errno == EINTR);
    return r;
}

struct capture_ctx *capture_open(const char *dev)
{
    struct capture_ctx *ctx;
    struct v4l2_capability cap;
    struct v4l2_format fmt;
    struct v4l2_requestbuffers req;
    int i;

    ctx = calloc(1, sizeof(*ctx));
    if (!ctx)
        return NULL;

    ctx->fd = open(dev, O_RDWR | O_CLOEXEC);
    if (ctx->fd < 0) {
        perror("open capture device");
        goto err_free;
    }

    /* Verify capability */
    if (xioctl(ctx->fd, VIDIOC_QUERYCAP, &cap) < 0) {
        perror("VIDIOC_QUERYCAP");
        goto err_close;
    }
    if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE) ||
        !(cap.capabilities & V4L2_CAP_STREAMING)) {
        fprintf(stderr, "device does not support capture+streaming\n");
        goto err_close;
    }

    /* Set format: 1920x1080 NV12 */
    memset(&fmt, 0, sizeof(fmt));
    fmt.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.width       = CAPTURE_WIDTH;
    fmt.fmt.pix.height      = CAPTURE_HEIGHT;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_NV12;
    fmt.fmt.pix.field       = V4L2_FIELD_NONE;
    if (xioctl(ctx->fd, VIDIOC_S_FMT, &fmt) < 0) {
        perror("VIDIOC_S_FMT");
        goto err_close;
    }

    /* Request MMAP buffers */
    memset(&req, 0, sizeof(req));
    req.count  = CAPTURE_BUFFERS;
    req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;
    if (xioctl(ctx->fd, VIDIOC_REQBUFS, &req) < 0) {
        perror("VIDIOC_REQBUFS");
        goto err_close;
    }

    for (i = 0; i < CAPTURE_BUFFERS; i++) {
        struct v4l2_buffer buf = {
            .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
            .index  = i,
        };
        struct v4l2_exportbuffer expbuf = {
            .type  = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .index = i,
            .flags = O_CLOEXEC | O_RDONLY,
        };

        if (xioctl(ctx->fd, VIDIOC_QUERYBUF, &buf) < 0) {
            perror("VIDIOC_QUERYBUF");
            goto err_unmap;
        }

        ctx->bufs[i].length = buf.length;
        ctx->bufs[i].vaddr  = mmap(NULL, buf.length,
                                   PROT_READ, MAP_SHARED,
                                   ctx->fd, buf.m.offset);
        if (ctx->bufs[i].vaddr == MAP_FAILED) {
            perror("mmap");
            goto err_unmap;
        }

        /* Export as dma-buf — this fd can be imported by the encoder */
        if (xioctl(ctx->fd, VIDIOC_EXPBUF, &expbuf) < 0) {
            perror("VIDIOC_EXPBUF");
            goto err_unmap;
        }
        ctx->bufs[i].dmabuf_fd = expbuf.fd;
    }

    return ctx;

err_unmap:
    for (i--; i >= 0; i--) {
        munmap(ctx->bufs[i].vaddr, ctx->bufs[i].length);
        close(ctx->bufs[i].dmabuf_fd);
    }
err_close:
    close(ctx->fd);
err_free:
    free(ctx);
    return NULL;
}

int capture_start(struct capture_ctx *ctx)
{
    int i;
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

    for (i = 0; i < CAPTURE_BUFFERS; i++) {
        struct v4l2_buffer buf = {
            .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
            .index  = i,
        };
        if (xioctl(ctx->fd, VIDIOC_QBUF, &buf) < 0) {
            perror("VIDIOC_QBUF");
            return -1;
        }
    }
    return xioctl(ctx->fd, VIDIOC_STREAMON, &type);
}

int capture_dequeue(struct capture_ctx *ctx, struct frame *f)
{
    struct v4l2_buffer buf = {
        .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
        .memory = V4L2_MEMORY_MMAP,
    };
    if (xioctl(ctx->fd, VIDIOC_DQBUF, &buf) < 0)
        return -1;

    f->index      = buf.index;
    f->bytesused  = buf.bytesused;
    f->dmabuf_fd  = ctx->bufs[buf.index].dmabuf_fd;
    f->timestamp_us = (uint64_t)buf.timestamp.tv_sec * 1000000ULL
                      + buf.timestamp.tv_usec;
    return 0;
}

int capture_queue(struct capture_ctx *ctx, uint32_t index)
{
    struct v4l2_buffer buf = {
        .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
        .memory = V4L2_MEMORY_MMAP,
        .index  = index,
    };
    return xioctl(ctx->fd, VIDIOC_QBUF, &buf);
}

void capture_stop(struct capture_ctx *ctx)
{
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    xioctl(ctx->fd, VIDIOC_STREAMOFF, &type);
}

void capture_close(struct capture_ctx *ctx)
{
    int i;
    for (i = 0; i < CAPTURE_BUFFERS; i++) {
        munmap(ctx->bufs[i].vaddr, ctx->bufs[i].length);
        close(ctx->bufs[i].dmabuf_fd);
    }
    close(ctx->fd);
    free(ctx);
}
```

---

## 3. User-Space: V4L2 M2M Encoder (dma-buf Import, Zero-Copy)

### `src/encoder.h`

```c
#ifndef ENCODER_H
#define ENCODER_H

#include <stdint.h>

#define ENCODER_OUTPUT_BUFFERS  4   /* input side (RAW frames) */
#define ENCODER_CAPTURE_BUFFERS 4   /* output side (H.264 NAL) */
#define ENCODER_BITRATE_BPS     8000000  /* 8 Mbps for 1080p30 */

struct nal_unit {
    void    *data;
    size_t   size;
    uint64_t timestamp_us;
    int      is_keyframe;
};

struct encoder_ctx;

struct encoder_ctx *encoder_open(const char *dev);
int                 encoder_start(struct encoder_ctx *ctx);
int  encoder_encode_frame(struct encoder_ctx *ctx,
                          int dmabuf_fd,        /* from capture */
                          uint32_t bytesused,
                          uint64_t timestamp_us,
                          struct nal_unit *out);
void encoder_stop(struct encoder_ctx *ctx);
void encoder_close(struct encoder_ctx *ctx);

#endif /* ENCODER_H */
```

### `src/encoder.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * V4L2 M2M encoder — imports capture dma-buf fds on OUTPUT side,
 * reads H.264 NAL units from CAPTURE side. Fully zero-copy.
 *
 * OUTPUT queue  = raw NV12 input  (V4L2_MEMORY_DMABUF)
 * CAPTURE queue = H.264 output    (V4L2_MEMORY_MMAP)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <linux/videodev2.h>
#include "encoder.h"

struct enc_cap_buf {
    void   *vaddr;
    size_t  length;
};

struct encoder_ctx {
    int              fd;
    struct enc_cap_buf cap_bufs[ENCODER_CAPTURE_BUFFERS];
    int              out_buf_index;   /* round-robin index */
};

static int xioctl(int fd, unsigned long req, void *arg)
{
    int r;
    do { r = ioctl(fd, req, arg); } while (r == -1 && errno == EINTR);
    return r;
}

struct encoder_ctx *encoder_open(const char *dev)
{
    struct encoder_ctx *ctx;
    struct v4l2_capability cap;
    struct v4l2_format fmt;
    struct v4l2_requestbuffers req;
    struct v4l2_control ctrl;
    int i;

    ctx = calloc(1, sizeof(*ctx));
    if (!ctx)
        return NULL;

    ctx->fd = open(dev, O_RDWR | O_CLOEXEC);
    if (ctx->fd < 0) {
        perror("open encoder device");
        goto err_free;
    }

    if (xioctl(ctx->fd, VIDIOC_QUERYCAP, &cap) < 0) {
        perror("encoder VIDIOC_QUERYCAP");
        goto err_close;
    }
    if (!(cap.capabilities & V4L2_CAP_VIDEO_M2M)) {
        fprintf(stderr, "device is not M2M\n");
        goto err_close;
    }

    /* OUTPUT side: NV12 raw input */
    memset(&fmt, 0, sizeof(fmt));
    fmt.type                = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    fmt.fmt.pix.width       = 1920;
    fmt.fmt.pix.height      = 1080;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_NV12;
    fmt.fmt.pix.field       = V4L2_FIELD_NONE;
    fmt.fmt.pix.sizeimage   = 1920 * 1080 * 3 / 2;  /* NV12 */
    if (xioctl(ctx->fd, VIDIOC_S_FMT, &fmt) < 0) {
        perror("encoder S_FMT OUTPUT");
        goto err_close;
    }

    /* CAPTURE side: H.264 bitstream output */
    memset(&fmt, 0, sizeof(fmt));
    fmt.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fmt.fmt.pix.width       = 1920;
    fmt.fmt.pix.height      = 1080;
    fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_H264;
    fmt.fmt.pix.sizeimage   = 1920 * 1080;  /* worst-case 1 frame */
    if (xioctl(ctx->fd, VIDIOC_S_FMT, &fmt) < 0) {
        perror("encoder S_FMT CAPTURE");
        goto err_close;
    }

    /* Set bitrate via V4L2 control */
    ctrl.id    = V4L2_CID_MPEG_VIDEO_BITRATE;
    ctrl.value = ENCODER_BITRATE_BPS;
    xioctl(ctx->fd, VIDIOC_S_CTRL, &ctrl);

    /* Force IDR every 30 frames (1 second at 30fps) */
    ctrl.id    = V4L2_CID_MPEG_VIDEO_H264_I_PERIOD;
    ctrl.value = 30;
    xioctl(ctx->fd, VIDIOC_S_CTRL, &ctrl);

    /* H.264 profile = High */
    ctrl.id    = V4L2_CID_MPEG_VIDEO_H264_PROFILE;
    ctrl.value = V4L2_MPEG_VIDEO_H264_PROFILE_HIGH;
    xioctl(ctx->fd, VIDIOC_S_CTRL, &ctrl);

    /* OUTPUT queue: DMABUF memory (will import capture fds) */
    memset(&req, 0, sizeof(req));
    req.count  = ENCODER_OUTPUT_BUFFERS;
    req.type   = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    req.memory = V4L2_MEMORY_DMABUF;
    if (xioctl(ctx->fd, VIDIOC_REQBUFS, &req) < 0) {
        perror("encoder REQBUFS OUTPUT");
        goto err_close;
    }

    /* CAPTURE queue: MMAP memory (we read NAL units from here) */
    memset(&req, 0, sizeof(req));
    req.count  = ENCODER_CAPTURE_BUFFERS;
    req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    req.memory = V4L2_MEMORY_MMAP;
    if (xioctl(ctx->fd, VIDIOC_REQBUFS, &req) < 0) {
        perror("encoder REQBUFS CAPTURE");
        goto err_close;
    }

    /* Map CAPTURE buffers */
    for (i = 0; i < ENCODER_CAPTURE_BUFFERS; i++) {
        struct v4l2_buffer buf = {
            .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
            .index  = i,
        };
        if (xioctl(ctx->fd, VIDIOC_QUERYBUF, &buf) < 0) {
            perror("encoder QUERYBUF CAPTURE");
            goto err_unmap;
        }
        ctx->cap_bufs[i].length = buf.length;
        ctx->cap_bufs[i].vaddr  = mmap(NULL, buf.length,
                                        PROT_READ, MAP_SHARED,
                                        ctx->fd, buf.m.offset);
        if (ctx->cap_bufs[i].vaddr == MAP_FAILED) {
            perror("encoder mmap CAPTURE");
            goto err_unmap;
        }
    }

    return ctx;

err_unmap:
    for (i--; i >= 0; i--)
        munmap(ctx->cap_bufs[i].vaddr, ctx->cap_bufs[i].length);
err_close:
    close(ctx->fd);
err_free:
    free(ctx);
    return NULL;
}

int encoder_start(struct encoder_ctx *ctx)
{
    enum v4l2_buf_type type;
    int i;

    /* Pre-queue all CAPTURE buffers */
    for (i = 0; i < ENCODER_CAPTURE_BUFFERS; i++) {
        struct v4l2_buffer buf = {
            .type   = V4L2_BUF_TYPE_VIDEO_CAPTURE,
            .memory = V4L2_MEMORY_MMAP,
            .index  = i,
        };
        if (xioctl(ctx->fd, VIDIOC_QBUF, &buf) < 0) {
            perror("encoder QBUF CAPTURE");
            return -1;
        }
    }

    type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (xioctl(ctx->fd, VIDIOC_STREAMON, &type) < 0)
        return -1;

    type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    return xioctl(ctx->fd, VIDIOC_STREAMON, &type);
}

/*
 * encoder_encode_frame — queue one raw frame (by dma-buf fd),
 * then dequeue one H.264 NAL unit into 'out'.
 * Returns 0 on success.
 */
int encoder_encode_frame(struct encoder_ctx *ctx,
                         int dmabuf_fd, uint32_t bytesused,
                         uint64_t timestamp_us, struct nal_unit *out)
{
    struct v4l2_buffer outbuf, capbuf;
    int out_idx = ctx->out_buf_index % ENCODER_OUTPUT_BUFFERS;

    /* Queue raw frame to OUTPUT side via dma-buf fd (zero-copy) */
    memset(&outbuf, 0, sizeof(outbuf));
    outbuf.type      = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    outbuf.memory    = V4L2_MEMORY_DMABUF;
    outbuf.index     = out_idx;
    outbuf.m.fd      = dmabuf_fd;           /* imported from capture */
    outbuf.bytesused = bytesused;
    outbuf.timestamp.tv_sec  = timestamp_us / 1000000;
    outbuf.timestamp.tv_usec = timestamp_us % 1000000;

    if (xioctl(ctx->fd, VIDIOC_QBUF, &outbuf) < 0) {
        perror("encoder QBUF OUTPUT");
        return -1;
    }
    ctx->out_buf_index++;

    /* Dequeue encoded NAL unit from CAPTURE side */
    memset(&capbuf, 0, sizeof(capbuf));
    capbuf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    capbuf.memory = V4L2_MEMORY_MMAP;
    if (xioctl(ctx->fd, VIDIOC_DQBUF, &capbuf) < 0) {
        perror("encoder DQBUF CAPTURE");
        return -1;
    }

    out->data         = ctx->cap_bufs[capbuf.index].vaddr;
    out->size         = capbuf.bytesused;
    out->timestamp_us = (uint64_t)capbuf.timestamp.tv_sec * 1000000ULL
                        + capbuf.timestamp.tv_usec;
    out->is_keyframe  = !!(capbuf.flags & V4L2_BUF_FLAG_KEYFRAME);

    /* Dequeue the completed OUTPUT buffer back (it was consumed by VPU) */
    memset(&outbuf, 0, sizeof(outbuf));
    outbuf.type   = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    outbuf.memory = V4L2_MEMORY_DMABUF;
    xioctl(ctx->fd, VIDIOC_DQBUF, &outbuf);   /* non-blocking; error ok */

    /* Re-queue the CAPTURE buffer for the next frame */
    memset(&capbuf, 0, sizeof(capbuf));
    capbuf.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    capbuf.memory = V4L2_MEMORY_MMAP;
    capbuf.index  = capbuf.index;
    xioctl(ctx->fd, VIDIOC_QBUF, &capbuf);

    return 0;
}

void encoder_stop(struct encoder_ctx *ctx)
{
    enum v4l2_buf_type type;
    type = V4L2_BUF_TYPE_VIDEO_OUTPUT;
    xioctl(ctx->fd, VIDIOC_STREAMOFF, &type);
    type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    xioctl(ctx->fd, VIDIOC_STREAMOFF, &type);
}

void encoder_close(struct encoder_ctx *ctx)
{
    int i;
    for (i = 0; i < ENCODER_CAPTURE_BUFFERS; i++)
        munmap(ctx->cap_bufs[i].vaddr, ctx->cap_bufs[i].length);
    close(ctx->fd);
    free(ctx);
}
```

---

## 4. User-Space: MP4 Segmenter

### `src/muxer.h`

```c
#ifndef MUXER_H
#define MUXER_H

#include <stdint.h>
#include "encoder.h"

#define SEGMENT_DURATION_SEC  60    /* rotate file every 60 seconds */
#define OUTPUT_DIR            "/data/dashcam"

struct muxer_ctx;

struct muxer_ctx *muxer_open(const char *dir);
int  muxer_write_nal(struct muxer_ctx *ctx, const struct nal_unit *nal);
void muxer_close(struct muxer_ctx *ctx);

#endif
```

### `src/muxer.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * Simple H.264 Annex-B → fragmented MP4 muxer using libavformat.
 * Rotates to a new file every SEGMENT_DURATION_SEC seconds.
 * Each segment starts with a keyframe for reliable playback.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <libavformat/avformat.h>
#include <libavcodec/avcodec.h>
#include "muxer.h"

struct muxer_ctx {
    AVFormatContext *fmt_ctx;
    AVStream        *stream;
    char             current_path[256];
    uint64_t         seg_start_us;
    int64_t          pts;          /* monotonic PTS in 90kHz ticks */
    char             out_dir[256];
};

static int open_segment(struct muxer_ctx *ctx)
{
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    const AVOutputFormat *ofmt;
    AVCodecParameters *par;
    int ret;

    if (ctx->fmt_ctx)
        av_write_trailer(ctx->fmt_ctx);

    snprintf(ctx->current_path, sizeof(ctx->current_path),
             "%s/%04d-%02d-%02d_%02d-%02d-%02d.mp4",
             ctx->out_dir,
             t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
             t->tm_hour, t->tm_min, t->tm_sec);

    ofmt = av_guess_format("mp4", NULL, NULL);
    avformat_alloc_output_context2(&ctx->fmt_ctx, ofmt, NULL,
                                   ctx->current_path);
    if (!ctx->fmt_ctx)
        return -1;

    ctx->stream = avformat_new_stream(ctx->fmt_ctx, NULL);
    if (!ctx->stream)
        return -1;

    par = ctx->stream->codecpar;
    par->codec_type = AVMEDIA_TYPE_VIDEO;
    par->codec_id   = AV_CODEC_ID_H264;
    par->width      = 1920;
    par->height     = 1080;
    par->format     = AV_PIX_FMT_YUV420P;
    ctx->stream->time_base = (AVRational){1, 90000};

    ret = avio_open(&ctx->fmt_ctx->pb, ctx->current_path, AVIO_FLAG_WRITE);
    if (ret < 0)
        return ret;

    ret = avformat_write_header(ctx->fmt_ctx, NULL);
    if (ret < 0)
        return ret;

    printf("[muxer] opened segment: %s\n", ctx->current_path);
    return 0;
}

struct muxer_ctx *muxer_open(const char *dir)
{
    struct muxer_ctx *ctx = calloc(1, sizeof(*ctx));
    if (!ctx)
        return NULL;

    mkdir(dir, 0755);
    strncpy(ctx->out_dir, dir, sizeof(ctx->out_dir) - 1);

    if (open_segment(ctx) < 0) {
        free(ctx);
        return NULL;
    }
    return ctx;
}

int muxer_write_nal(struct muxer_ctx *ctx, const struct nal_unit *nal)
{
    AVPacket pkt;
    int ret;

    /* Rotate segment on keyframe after SEGMENT_DURATION_SEC */
    if (nal->is_keyframe &&
        (nal->timestamp_us - ctx->seg_start_us) >=
        (uint64_t)SEGMENT_DURATION_SEC * 1000000ULL) {
        open_segment(ctx);
        ctx->seg_start_us = nal->timestamp_us;
        ctx->pts = 0;
    }

    av_init_packet(&pkt);
    pkt.stream_index = ctx->stream->index;
    pkt.data         = (uint8_t *)nal->data;
    pkt.size         = (int)nal->size;
    pkt.pts          = ctx->pts;
    pkt.dts          = ctx->pts;
    /* 30fps → 1/30 sec per frame → 90000/30 = 3000 ticks */
    pkt.duration     = 3000;
    ctx->pts        += 3000;

    if (nal->is_keyframe)
        pkt.flags |= AV_PKT_FLAG_KEY;

    ret = av_interleaved_write_frame(ctx->fmt_ctx, &pkt);
    if (ret < 0) {
        char errbuf[64];
        av_strerror(ret, errbuf, sizeof(errbuf));
        fprintf(stderr, "[muxer] write error: %s\n", errbuf);
    }
    return ret;
}

void muxer_close(struct muxer_ctx *ctx)
{
    if (ctx->fmt_ctx) {
        av_write_trailer(ctx->fmt_ctx);
        avio_closep(&ctx->fmt_ctx->pb);
        avformat_free_context(ctx->fmt_ctx);
    }
    free(ctx);
}
```

---

## 5. Main Pipeline Loop

### `src/main.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * dashcam — main entry point
 *
 * Ties capture → encoder → muxer into a tight loop with:
 *   - signal handling (SIGTERM / SIGINT for clean shutdown)
 *   - hardware watchdog refresh (prevent reboot on hang)
 *   - dropped-frame counter logged to stderr
 */

#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/watchdog.h>
#include <sys/ioctl.h>
#include "capture.h"
#include "encoder.h"
#include "muxer.h"

#define CAPTURE_DEV  "/dev/video0"
#define ENCODER_DEV  "/dev/video1"
#define WATCHDOG_DEV "/dev/watchdog0"
#define WATCHDOG_TIMEOUT_SEC 10

static volatile int running = 1;

static void on_signal(int sig)
{
    (void)sig;
    running = 0;
}

int main(void)
{
    struct capture_ctx *cap;
    struct encoder_ctx *enc;
    struct muxer_ctx   *mux;
    struct frame        f;
    struct nal_unit     nal;
    int wdog_fd;
    unsigned long long frames = 0, drops = 0;

    signal(SIGTERM, on_signal);
    signal(SIGINT,  on_signal);

    /* Open hardware watchdog — must be kicked every WATCHDOG_TIMEOUT_SEC */
    wdog_fd = open(WATCHDOG_DEV, O_RDWR | O_CLOEXEC);
    if (wdog_fd >= 0) {
        int timeout = WATCHDOG_TIMEOUT_SEC;
        ioctl(wdog_fd, WDIOC_SETTIMEOUT, &timeout);
        printf("[watchdog] armed (%ds)\n", timeout);
    }

    cap = capture_open(CAPTURE_DEV);
    if (!cap) { fprintf(stderr, "capture open failed\n"); return 1; }

    enc = encoder_open(ENCODER_DEV);
    if (!enc) { fprintf(stderr, "encoder open failed\n"); return 1; }

    mux = muxer_open(OUTPUT_DIR);
    if (!mux) { fprintf(stderr, "muxer open failed\n"); return 1; }

    if (capture_start(cap) < 0 || encoder_start(enc) < 0) {
        fprintf(stderr, "stream start failed\n");
        return 1;
    }

    printf("[dashcam] recording to %s\n", OUTPUT_DIR);

    while (running) {
        /* Dequeue one raw frame from camera */
        if (capture_dequeue(cap, &f) < 0) {
            drops++;
            continue;
        }

        /* Encode frame via VPU — zero-copy via dma-buf fd */
        if (encoder_encode_frame(enc, f.dmabuf_fd, f.bytesused,
                                  f.timestamp_us, &nal) == 0) {
            muxer_write_nal(mux, &nal);
            frames++;
        } else {
            drops++;
        }

        /* Return frame buffer to the capture queue */
        capture_queue(cap, f.index);

        /* Kick watchdog every frame (~33ms period vs 10s timeout) */
        if (wdog_fd >= 0)
            ioctl(wdog_fd, WDIOC_KEEPALIVE, 0);
    }

    printf("[dashcam] stopping: %llu frames, %llu drops\n", frames, drops);

    capture_stop(cap);
    encoder_stop(enc);
    muxer_close(mux);
    encoder_close(enc);
    capture_close(cap);

    /* Magic close: disable watchdog cleanly */
    if (wdog_fd >= 0) {
        write(wdog_fd, "V", 1);
        close(wdog_fd);
    }

    return 0;
}
```

---

## 6. GStreamer Production Variant (Fallback / x86 Dev Machine)

### `gst/dashcam_gst.c`

```c
// SPDX-License-Identifier: GPL-2.0-only
/*
 * GStreamer dashcam pipeline variant.
 * Used on x86 dev machines (VAAPI encode) and as a hot-standby on target.
 *
 * Pipeline:
 *   v4l2src → videoconvert → vaapih264enc → h264parse → splitmuxsink
 *
 * vaapih264enc uses GPU/media-driver for HW encode (zero-copy via dma-buf
 * when VA-API driver supports DRM PRIME import).
 */

#include <gst/gst.h>
#include <signal.h>
#include <stdio.h>

static GMainLoop *loop;

static void on_signal(int sig) { g_main_loop_quit(loop); }

static gboolean on_bus_message(GstBus *bus, GstMessage *msg, gpointer data)
{
    GError *err;
    gchar  *dbg;

    switch (GST_MESSAGE_TYPE(msg)) {
    case GST_MESSAGE_ERROR:
        gst_message_parse_error(msg, &err, &dbg);
        g_printerr("[gst] error: %s\n%s\n", err->message, dbg ? dbg : "");
        g_error_free(err);
        g_free(dbg);
        g_main_loop_quit(loop);
        break;

    case GST_MESSAGE_WARNING:
        gst_message_parse_warning(msg, &err, &dbg);
        g_printerr("[gst] warning: %s\n", err->message);
        g_error_free(err);
        g_free(dbg);
        break;

    case GST_MESSAGE_EOS:
        g_print("[gst] EOS\n");
        g_main_loop_quit(loop);
        break;

    default:
        break;
    }
    return TRUE;
}

int main(int argc, char *argv[])
{
    GstElement *pipeline;
    GstBus     *bus;
    GError     *err = NULL;

    gst_init(&argc, &argv);
    signal(SIGTERM, on_signal);
    signal(SIGINT,  on_signal);

    /*
     * Full pipeline string (adjust device and bitrate as needed):
     *
     * v4l2src            — captures NV12 frames from /dev/video0
     * video/x-raw        — enforce 1920x1080 NV12 @ 30fps
     * vaapih264enc        — hardware H.264 encode via VAAPI
     * h264parse           — parse NAL units, set stream-format=avc
     * splitmuxsink        — rotate MP4 file every 60 seconds
     */
    const char *pipe_str =
        "v4l2src device=/dev/video0 io-mode=dmabuf ! "
        "video/x-raw,format=NV12,width=1920,height=1080,framerate=30/1 ! "
        "vaapih264enc bitrate=8000 keyframe-period=30 ! "
        "h264parse ! "
        "splitmuxsink location=/data/dashcam/%Y-%m-%d_%H-%M-%S.mp4 "
        "  max-size-time=60000000000 "    /* 60 seconds in nanoseconds */
        "  muxer-factory=mp4mux "
        "  async-finalize=true";

    pipeline = gst_parse_launch(pipe_str, &err);
    if (!pipeline) {
        g_printerr("pipeline parse error: %s\n", err->message);
        return 1;
    }

    bus = gst_element_get_bus(pipeline);
    gst_bus_add_watch(bus, on_bus_message, NULL);
    gst_object_unref(bus);

    gst_element_set_state(pipeline, GST_STATE_PLAYING);
    g_print("[gst] dashcam recording...\n");

    loop = g_main_loop_new(NULL, FALSE);
    g_main_loop_run(loop);

    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    g_main_loop_unref(loop);

    return 0;
}
```

---

## 7. Build System

### `Makefile`

```makefile
# Dashcam project top-level Makefile
# Supports native (x86) and cross-compile (aarch64 i.MX8M)

CROSS ?=                          # override: make CROSS=aarch64-linux-gnu-
CC    := $(CROSS)gcc
PKG   := pkg-config

SRC_DIR := src
GST_DIR := gst
OBJ_DIR := build

CFLAGS  := -O2 -Wall -Wextra -Werror -I$(SRC_DIR)
LDFLAGS :=

# pkg-config deps
CFLAGS  += $(shell $(PKG) --cflags libavformat libavcodec libavutil 2>/dev/null)
LDFLAGS += $(shell $(PKG) --libs   libavformat libavcodec libavutil 2>/dev/null)

SRCS := $(SRC_DIR)/capture.c \
        $(SRC_DIR)/encoder.c \
        $(SRC_DIR)/muxer.c   \
        $(SRC_DIR)/main.c

OBJS := $(SRCS:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

.PHONY: all clean gst kernel

all: $(OBJ_DIR)/dashcam

$(OBJ_DIR):
	mkdir -p $@

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/dashcam: $(OBJS)
	$(CC) $^ $(LDFLAGS) -o $@
	@echo "Built: $@"

# GStreamer variant
gst: $(OBJ_DIR)/dashcam_gst

$(OBJ_DIR)/dashcam_gst: $(GST_DIR)/dashcam_gst.c | $(OBJ_DIR)
	$(CC) $(CFLAGS) \
	  $(shell $(PKG) --cflags gstreamer-1.0) \
	  $< -o $@ \
	  $(shell $(PKG) --libs gstreamer-1.0)

# Kernel sensor module
kernel:
	$(MAKE) -C /lib/modules/$(shell uname -r)/build \
	  M=$(PWD)/kernel modules \
	  CROSS_COMPILE=$(CROSS) ARCH=arm64

clean:
	rm -rf $(OBJ_DIR) kernel/*.ko kernel/*.o kernel/.*.cmd kernel/Module.symvers

install:
	install -d /usr/bin
	install -m 755 $(OBJ_DIR)/dashcam /usr/bin/dashcam
	install -m 644 systemd/dashcam.service /etc/systemd/system/
	systemctl daemon-reload
	systemctl enable dashcam.service
```

### `kernel/Makefile`

```makefile
obj-m += ov5640_dashcam.o
```

---

## 8. systemd Service

### `systemd/dashcam.service`

```ini
[Unit]
Description=ADAS Dashcam Recording Service
Documentation=https://github.com/example/dashcam
After=systemd-udevd.service
# Wait for camera and encoder devices to appear
After=dev-video0.device dev-video1.device
Wants=dev-video0.device dev-video1.device

[Service]
Type=simple
ExecStart=/usr/bin/dashcam
Restart=on-failure
RestartSec=2s

# Filesystem access
ReadWritePaths=/data/dashcam

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
DeviceAllow=/dev/video0 rw
DeviceAllow=/dev/video1 rw
DeviceAllow=/dev/watchdog0 rw
PrivateTmp=yes

# Resource limits
CPUSchedulingPolicy=fifo
CPUSchedulingPriority=50
MemoryMax=256M

# Watchdog integration (systemd pings the service every 15s)
WatchdogSec=15s
NotifyAccess=none

[Install]
WantedBy=multi-user.target
```

---

## 9. Yocto Recipe

### `yocto/dashcam_1.0.bb`

```bitbake
SUMMARY = "Zero-copy ADAS dashcam recording application"
DESCRIPTION = "V4L2 capture → VPU H.264 encode → MP4 segmenter"
LICENSE = "GPL-2.0-only"
LIC_FILES_CHKSUM = "file://LICENSE;md5=b234ee4d69f5fce4486a80fdaf4a4263"

SRC_URI = "git://github.com/example/dashcam.git;branch=main;protocol=https"
SRCREV  = "${AUTOREV}"

S = "${WORKDIR}/git"

DEPENDS = "ffmpeg gstreamer1.0 gstreamer1.0-plugins-bad virtual/kernel"

# Build kernel module too
inherit module

do_compile() {
    # User-space binary
    oe_runmake CROSS="${HOST_PREFIX}" CC="${CC}" \
               CFLAGS="${CFLAGS}" LDFLAGS="${LDFLAGS}" \
               PKG="pkg-config"

    # Kernel module
    oe_runmake kernel CROSS="${HOST_PREFIX}" \
               ARCH="${ARCH}" \
               KERNEL_PATH="${STAGING_KERNEL_DIR}"
}

do_install() {
    install -d ${D}${bindir}
    install -m 0755 build/dashcam ${D}${bindir}/

    install -d ${D}${systemd_unitdir}/system/
    install -m 0644 systemd/dashcam.service ${D}${systemd_unitdir}/system/

    install -d ${D}/lib/modules/${KERNEL_VERSION}/extra/
    install -m 0644 kernel/ov5640_dashcam.ko \
                    ${D}/lib/modules/${KERNEL_VERSION}/extra/
}

FILES:${PN} = "${bindir}/dashcam ${systemd_unitdir}/system/dashcam.service"
FILES:${PN}-modules = "/lib/modules"

SYSTEMD_SERVICE:${PN} = "dashcam.service"
inherit systemd
```

---

## 10. Device Tree Overlay

```c
/* arch/arm64/boot/dts/freescale/imx8mp-dashcam.dts */

/dts-v1/;
/plugin/;

&i2c2 {
    #address-cells = <1>;
    #size-cells = <0>;

    ov5640: camera@3c {
        compatible     = "ovti,ov5640";
        reg            = <0x3c>;
        clocks         = <&clk IMX8MP_CLK_IPP_DO_CLKO1>;
        clock-names    = "xclk";
        assigned-clocks = <&clk IMX8MP_CLK_IPP_DO_CLKO1>;
        assigned-clock-rates = <24000000>;
        reset-gpios    = <&gpio1 6 GPIO_ACTIVE_LOW>;
        powerdown-gpios = <&gpio1 7 GPIO_ACTIVE_HIGH>;
        DOVDD-supply   = <&reg_1p8v>;
        AVDD-supply    = <&reg_2p8v>;
        DVDD-supply    = <&reg_1p5v>;

        port {
            ov5640_ep: endpoint {
                remote-endpoint = <&mipi_csi_ep>;
                clock-lanes     = <0>;
                data-lanes      = <1 2>;
                link-frequencies = /bits/ 64 <336000000>;
            };
        };
    };
};

&mipi_csi_0 {
    status = "okay";
    port@0 {
        mipi_csi_ep: endpoint {
            remote-endpoint = <&ov5640_ep>;
            data-lanes      = <4>;
            csis-hs-settle  = <13>;
        };
    };
};

&isi_0 {
    status = "okay";   /* ISI → /dev/video0 */
};

&vpu_h264_encoder {
    status = "okay";   /* VPU M2M → /dev/video1 */
};
```

---

## How to Build and Run

```bash
# ── On dev machine (x86, GStreamer variant) ──────────────────────────
sudo apt install libavformat-dev libavcodec-dev libavutil-dev \
                 libgstreamer1.0-dev gstreamer1.0-plugins-bad \
                 gstreamer1.0-vaapi

make gst
sudo mkdir -p /data/dashcam
sudo ./build/dashcam_gst        # uses VAAPI encode on Intel GPU

# ── Cross-compile for i.MX8M Plus ────────────────────────────────────
export CROSS=aarch64-linux-gnu-
export PKG_CONFIG_PATH=/sysroot/usr/lib/pkgconfig

make CROSS=$CROSS
make kernel CROSS=$CROSS KDIR=/path/to/imx8m-kernel

# ── Deploy to target ─────────────────────────────────────────────────
scp build/dashcam          root@192.168.1.100:/usr/bin/
scp systemd/dashcam.service root@192.168.1.100:/etc/systemd/system/
scp kernel/ov5640_dashcam.ko root@192.168.1.100:/lib/modules/$(uname -r)/extra/

# On target:
depmod -a
modprobe ov5640_dashcam
systemctl enable --now dashcam.service
journalctl -fu dashcam.service

# ── Verify pipeline ──────────────────────────────────────────────────
v4l2-ctl --list-devices
v4l2-ctl -d /dev/video0 --list-formats-ext   # should show NV12 1920x1080
v4l2-ctl -d /dev/video1 --list-formats-ext   # should show H264 (M2M encoder)
v4l2-compliance -d /dev/video0               # full compliance test

# Watch recorded files
ls -lh /data/dashcam/
ffprobe /data/dashcam/2026-05-28_10-00-00.mp4
ffplay  /data/dashcam/2026-05-28_10-00-00.mp4
```

---

## Architecture Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│                        KERNEL SPACE                                  │
│                                                                      │
│  ov5640_dashcam.ko                  imx8m-vpu.ko                    │
│  (i2c probe → v4l2_subdev)          (platform → V4L2 M2M)           │
│         │ MIPI-CSI2                          │                       │
│         ▼                                    │                       │
│  imx8-isi.ko  ──→  /dev/video0       /dev/video1                    │
│  (DMA ring,              │                   │                       │
│   NV12 frames,           │ dma-buf export    │ dma-buf import        │
│   vb2 mmap)              └─────────► zero-copy ──────────────────┐  │
└──────────────────────────────────────────────────────────────────│──┘
                                                                   │
┌──────────────────────────────────────────────────────────────────│──┐
│                       USER SPACE                                  │  │
│                                                                   │  │
│  main.c                                                           │  │
│    │                                                              │  │
│    ├─ capture_open("/dev/video0")                                 │  │
│    │   VIDIOC_REQBUFS MMAP + VIDIOC_EXPBUF ───────────── fd ─────┘  │
│    │                                                                 │
│    ├─ encoder_open("/dev/video1")                                    │
│    │   VIDIOC_REQBUFS DMABUF (output) + MMAP (capture)              │
│    │                                                                 │
│    └─ loop:                                                          │
│         capture_dequeue()   → frame.dmabuf_fd                        │
│         encoder_encode_frame(frame.dmabuf_fd) → NAL unit            │
│         muxer_write_nal()   → /data/dashcam/YYYY-MM-DD_....mp4      │
│         capture_queue()     → recycle buffer                         │
│         watchdog kick                                                │
│                                                                      │
│  systemd watchdog monitors process liveness every 15s               │
└──────────────────────────────────────────────────────────────────────┘
```
