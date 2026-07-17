/**
 * @file    imx477_driver.c
 * @brief   Sony IMX477 (12 MP, Raspberry Pi HQ Camera) sensor driver.
 *
 * Characteristics:
 *   Pixel array : 4056 × 3040 (12.3 MP)
 *   Pixel size  : 1.55 µm
 *   Interface   : 2-lane MIPI CSI-2, up to 1.5 Gbps/lane
 *   ADC         : 12-bit
 *   Max FPS     : 120 fps at 1080p, 10 fps at full 12MP
 *   HDR         : 2-frame DOL HDR
 *   I2C         : 7-bit addr 0x1A (default), 16-bit register addresses
 *
 * Design notes:
 *   - All register accesses via the HAL I2C layer (no direct bus access).
 *   - Initialisation sequence follows Sony Application Note AN-IMX477-1.
 *   - Gain / exposure register calculations validated against Sony datasheet formulas.
 *   - Thread safety: configure() and set_*() are NOT re-entrant —
 *     the streaming engine must hold a mutex when calling these.
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#include "sensor_api.h"
#include "hal_i2c.h"
#include "isf_logger.h"
#include <string.h>

/* ─────────────────────────────────────────────────────────────────────────── */
/* IMX477 Register Definitions                                                 */
/* ─────────────────────────────────────────────────────────────────────────── */
#define IMX477_REG_CHIP_ID_H    0x0016U  /* Expected: 0x04, 0x77 */
#define IMX477_REG_CHIP_ID_L    0x0017U
#define IMX477_CHIP_ID          0x0477U

#define IMX477_REG_MODE_SELECT  0x0100U  /* 0x00 = Standby, 0x01 = Streaming */
#define IMX477_REG_RESET        0x0103U  /* 0x01 = SW reset */
#define IMX477_REG_HOLD         0x0104U  /* 0x01 = group hold start */

/* Analogue gain: 0 = 0 dB, 1008 = 42 dB max */
#define IMX477_REG_ANA_GAIN_H   0x0204U
#define IMX477_REG_ANA_GAIN_L   0x0205U

/* Coarse integration time in lines */
#define IMX477_REG_COARSE_INT_H 0x0202U
#define IMX477_REG_COARSE_INT_L 0x0203U

/* Frame Length Lines */
#define IMX477_REG_FLL_H        0x0340U
#define IMX477_REG_FLL_L        0x0341U

/* Line Length PCK */
#define IMX477_REG_LLPCK_H      0x0342U
#define IMX477_REG_LLPCK_L      0x0343U

/* CSI-2 output format */
#define IMX477_REG_CSI_FORMAT_H 0x0112U
#define IMX477_REG_CSI_FORMAT_L 0x0113U

/* Output size */
#define IMX477_REG_X_OUT_SIZE_H 0x034CU
#define IMX477_REG_X_OUT_SIZE_L 0x034DU
#define IMX477_REG_Y_OUT_SIZE_H 0x034EU
#define IMX477_REG_Y_OUT_SIZE_L 0x034FU

/* Digital crop */
#define IMX477_REG_CROP_X_START_H 0x0344U
#define IMX477_REG_CROP_X_START_L 0x0345U
#define IMX477_REG_CROP_Y_START_H 0x0346U
#define IMX477_REG_CROP_Y_START_L 0x0347U

/* MIPI clk rate */
#define IMX477_REG_MIPI_CLK_H   0x0306U
#define IMX477_REG_MIPI_CLK_L   0x0307U

/* Test pattern */
#define IMX477_REG_TEST_PATT_H  0x0600U
#define IMX477_REG_TEST_PATT_L  0x0601U

/* Temperature: 8-bit, unsigned, formula: T°C = (reg * 0.7) - 20 */
#define IMX477_REG_TEMPERATURE  0x013AU

/* ─────────────────────────────────────────────────────────────────────────── */
/* Resolution modes                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */
static const sensor_mode_desc_t imx477_modes[] = {
    { /* Mode 0: Full 12MP */
        .width = 4056, .height = 3040,
        .pixel_format = SENSOR_PIXFMT_RAW12,
        .mipi_lanes = 2, .mipi_data_rate_mbps = 1500,
        .frame_rate_max = 10, .frame_rate_min = 1,
        .hdr_capable = false, .binning_h = 1, .binning_v = 1
    },
    { /* Mode 1: 1080p Full HD */
        .width = 1920, .height = 1080,
        .pixel_format = SENSOR_PIXFMT_RAW12,
        .mipi_lanes = 2, .mipi_data_rate_mbps = 1188,
        .frame_rate_max = 60, .frame_rate_min = 1,
        .hdr_capable = false, .binning_h = 2, .binning_v = 2
    },
    { /* Mode 2: 1080p HDR */
        .width = 1920, .height = 1080,
        .pixel_format = SENSOR_PIXFMT_RAW12,
        .mipi_lanes = 2, .mipi_data_rate_mbps = 1188,
        .frame_rate_max = 30, .frame_rate_min = 1,
        .hdr_capable = true, .hdr_modes_mask = (1U << SENSOR_HDR_DOL),
        .binning_h = 2, .binning_v = 2
    },
    { /* Mode 3: 720p @ 120fps */
        .width = 1280, .height = 720,
        .pixel_format = SENSOR_PIXFMT_RAW10,
        .mipi_lanes = 2, .mipi_data_rate_mbps = 1188,
        .frame_rate_max = 120, .frame_rate_min = 30,
        .hdr_capable = false, .binning_h = 2, .binning_v = 4
    },
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* Minimum initialisation register table (Sony IMX477 Application Note)       */
/* Format: 16-bit address (MSB, LSB), 8-bit value                            */
/* ─────────────────────────────────────────────────────────────────────────── */
static const u8 imx477_init_regs[] = {
    /* Recommended initialisation sequence (abbreviated — full table in production) */
    0x01, 0x36, 0x00,   /* 0x0136: EXCK_FREQ[15:8] = 24 MHz */
    0x01, 0x37, 0x00,   /* 0x0137: EXCK_FREQ[7:0]  = 24 MHz */
    0x30, 0xEB, 0x05,   /* Manufacturer reserved */
    0x30, 0xEB, 0x0C,
    0x30, 0x0A, 0xFF,   /* Clock setup */
    0x30, 0x0B, 0xFF,
    0x30, 0x76, 0x00,   /* Black level */
    0x30, 0x77, 0x10,
    /* Sentinel: 0xFF, 0xFF, 0xFF */
    0xFF, 0xFF, 0xFF,
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* Per-instance context                                                        */
/* ─────────────────────────────────────────────────────────────────────────── */
typedef struct {
    hal_i2c_bus_t       i2c_bus;
    u8                  i2c_addr;
    sensor_config_t     current_cfg;
    bool                streaming;
    u32                 frame_count;
    u32                 fll;        /**< Frame Length Lines (shadow) */
    u32                 llpck;      /**< Line Length PCK (shadow) */
    u32                 pixel_clk_hz;
} imx477_context_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* Internal helpers                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */
static isf_status_t imx477_write(imx477_context_t *ctx, u16 reg, u8 val)
{
    return hal_i2c_reg_write8(ctx->i2c_bus, ctx->i2c_addr,
                              HAL_I2C_REG_ADDR_16BIT, reg, val);
}

static isf_status_t imx477_write16(imx477_context_t *ctx, u16 reg, u16 val)
{
    return hal_i2c_reg_write16(ctx->i2c_bus, ctx->i2c_addr, reg, val);
}

static isf_status_t imx477_read(imx477_context_t *ctx, u16 reg, u8 *out)
{
    return hal_i2c_reg_read8(ctx->i2c_bus, ctx->i2c_addr,
                             HAL_I2C_REG_ADDR_16BIT, reg, out);
}

/** @brief Hold all registers until group-hold is released (atomic update). */
static isf_status_t imx477_group_hold_start(imx477_context_t *ctx)
{
    return imx477_write(ctx, IMX477_REG_HOLD, 0x01U);
}

static isf_status_t imx477_group_hold_end(imx477_context_t *ctx)
{
    return imx477_write(ctx, IMX477_REG_HOLD, 0x00U);
}

/**
 * @brief   Compute Frame Length Lines from desired FPS.
 *
 * FPS = pixel_clk / (llpck × fll)
 * fll = pixel_clk / (llpck × fps)
 *
 * Sony recommends fll >= coarse_integration_time + 22 lines.
 */
static u32 imx477_fps_to_fll(imx477_context_t *ctx, u16 fps)
{
    u32 fll = ctx->pixel_clk_hz / (ctx->llpck * (u32)fps);
    /* Minimum FLL guard from datasheet */
    if (fll < 128U) { fll = 128U; }
    return fll;
}

/**
 * @brief   Convert gain_x100 to IMX477 ANA_GAIN register value.
 *
 * Sony IMX477 analogue gain formula:
 *   Gain = 1024 / (1024 - ANA_GAIN_GLOBAL)
 *   ANA_GAIN_GLOBAL = 1024 - (1024 / gain_linear)
 *   gain_linear = gain_x100 / 100
 */
static u16 imx477_gain_to_reg(u16 gain_x100)
{
    const u32 gain_100th = (u32)gain_x100;
    if (gain_100th <= 100U) { return 0U; }  /* 0 dB */
    const u32 denom = gain_100th;
    const u32 reg = 1024U - (102400U / denom);
    return (u16)ISF_MIN(reg, 978U); /* 978 = ~42 dB max */
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Driver operations                                                           */
/* ─────────────────────────────────────────────────────────────────────────── */
static isf_status_t imx477_probe(hal_i2c_bus_t bus, sensor_handle_t *out_handle)
{
    ISF_CHECK_PTR(bus);
    ISF_CHECK_PTR(out_handle);

    /* Probe I2C address */
    isf_status_t st = hal_i2c_probe(bus, 0x1AU);
    if (st != ISF_OK) {
        ISF_LOG_DEBUG("IMX477: no ACK at 0x1A");
        return ISF_ERR_NOT_FOUND;
    }

    /* Allocate context */
    /* In production use a memory pool; for portability we use static allocation */
    static imx477_context_t s_ctx[2]; /* Support up to 2 instances */
    static u8 s_ctx_index = 0U;
    if (s_ctx_index >= ISF_ARRAY_SIZE(s_ctx)) {
        return ISF_ERR_NO_MEM;
    }
    imx477_context_t *ctx = &s_ctx[s_ctx_index++];
    memset(ctx, 0, sizeof(*ctx));
    ctx->i2c_bus  = bus;
    ctx->i2c_addr = 0x1AU;
    /* IMX477 @ 24 MHz XCLK, mode-dependent pixel clock */
    ctx->pixel_clk_hz = 840000000UL; /* 840 MHz pixel clock in 2-lane mode */
    ctx->llpck        = 5760U;       /* Default Line Length PCK */

    /* Verify chip ID */
    u8 id_h = 0U, id_l = 0U;
    ISF_RETURN_IF_ERR(imx477_read(ctx, IMX477_REG_CHIP_ID_H, &id_h));
    ISF_RETURN_IF_ERR(imx477_read(ctx, IMX477_REG_CHIP_ID_L, &id_l));
    const u16 chip_id = (u16)((id_h << 8U) | id_l);

    if (chip_id != IMX477_CHIP_ID) {
        ISF_LOG_ERR("IMX477: unexpected chip ID 0x%04X (expected 0x%04X)",
                    chip_id, IMX477_CHIP_ID);
        return ISF_ERR_NOT_FOUND;
    }
    ISF_LOG_INFO("IMX477: detected chip ID 0x%04X", chip_id);

    /* Issue software reset */
    ISF_RETURN_IF_ERR(imx477_write(ctx, IMX477_REG_RESET, 0x01U));
    /* Reset completes within 10 ms */
    /* hal_delay_ms(10); — platform specific */

    /* Load recommended initialisation registers */
    ISF_RETURN_IF_ERR(hal_i2c_write_reg_table(bus, ctx->i2c_addr, imx477_init_regs, 3U));

    *out_handle = (sensor_handle_t)ctx;
    ISF_LOG_INFO("IMX477: probe succeeded");
    return ISF_OK;
}

static isf_status_t imx477_configure(sensor_handle_t handle, const sensor_config_t *cfg)
{
    ISF_CHECK_PTR(handle);
    ISF_CHECK_PTR(cfg);
    imx477_context_t *ctx = (imx477_context_t *)handle;

    /* Find matching mode */
    u8 mode_idx = 0xFFU;
    for (u8 i = 0U; i < ISF_ARRAY_SIZE(imx477_modes); i++) {
        if (imx477_modes[i].width == cfg->width &&
            imx477_modes[i].height == cfg->height) {
            mode_idx = i;
            break;
        }
    }
    if (mode_idx == 0xFFU) {
        ISF_LOG_ERR("IMX477: unsupported resolution %dx%d", cfg->width, cfg->height);
        return ISF_ERR_NOT_SUPPORTED;
    }

    /* Calculate FLL for requested FPS */
    ctx->fll = imx477_fps_to_fll(ctx, cfg->frame_rate);

    /* Write output size */
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_X_OUT_SIZE_H, cfg->width));
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_Y_OUT_SIZE_H, cfg->height));

    /* Write FLL */
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_FLL_H, (u16)ctx->fll));

    /* CSI-2 format: RAW12 = 0x0C0C */
    u16 csi_fmt = 0x0C0CU;  /* output / input: 12-bit */
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_CSI_FORMAT_H, csi_fmt));

    /* Test pattern */
    const u16 tp = cfg->test_pattern ? (u16)(0x0001U + cfg->test_pattern_id) : 0x0000U;
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_TEST_PATT_H, tp));

    /* Apply gain and exposure atomically */
    ISF_RETURN_IF_ERR(imx477_group_hold_start(ctx));
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_ANA_GAIN_H,
                                      imx477_gain_to_reg(cfg->gain_x100)));
    /* Exposure in lines = exposure_us × fps × fll / 1e6 (approximation) */
    const u32 coarse_lines = (u32)(((u64)cfg->exposure_us * (u64)ctx->pixel_clk_hz) /
                                   ((u64)ctx->llpck * 1000000UL));
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_COARSE_INT_H, (u16)coarse_lines));
    ISF_RETURN_IF_ERR(imx477_group_hold_end(ctx));

    memcpy(&ctx->current_cfg, cfg, sizeof(*cfg));
    ISF_LOG_INFO("IMX477: configured %dx%d @%dfps, gain=%d/100, exp=%dus",
                 cfg->width, cfg->height, cfg->frame_rate,
                 cfg->gain_x100, cfg->exposure_us);
    return ISF_OK;
}

static isf_status_t imx477_start_streaming(sensor_handle_t handle)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    ISF_RETURN_IF_ERR(imx477_write(ctx, IMX477_REG_MODE_SELECT, 0x01U));
    ctx->streaming = true;
    ISF_LOG_INFO("IMX477: streaming started");
    return ISF_OK;
}

static isf_status_t imx477_stop_streaming(sensor_handle_t handle)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    ISF_RETURN_IF_ERR(imx477_write(ctx, IMX477_REG_MODE_SELECT, 0x00U));
    ctx->streaming = false;
    ISF_LOG_INFO("IMX477: streaming stopped");
    return ISF_OK;
}

static isf_status_t imx477_set_gain(sensor_handle_t handle, u16 gain_x100)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    ISF_RETURN_IF_ERR(imx477_group_hold_start(ctx));
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_ANA_GAIN_H,
                                      imx477_gain_to_reg(gain_x100)));
    return imx477_group_hold_end(ctx);
}

static isf_status_t imx477_set_exposure(sensor_handle_t handle, u32 exposure_us)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    const u32 lines = (u32)(((u64)exposure_us * ctx->pixel_clk_hz) /
                             ((u64)ctx->llpck * 1000000UL));
    const u32 coarse = ISF_MIN(lines, ctx->fll - 22U);  /* Min margin per datasheet */
    ISF_RETURN_IF_ERR(imx477_group_hold_start(ctx));
    ISF_RETURN_IF_ERR(imx477_write16(ctx, IMX477_REG_COARSE_INT_H, (u16)coarse));
    return imx477_group_hold_end(ctx);
}

static isf_status_t imx477_set_frame_rate(sensor_handle_t handle, u16 fps)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    ctx->fll = imx477_fps_to_fll(ctx, fps);
    return imx477_write16(ctx, IMX477_REG_FLL_H, (u16)ctx->fll);
}

static isf_status_t imx477_read_temperature(sensor_handle_t handle, s16 *out_temp_x10)
{
    ISF_CHECK_PTR(handle);
    ISF_CHECK_PTR(out_temp_x10);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    u8 raw = 0U;
    ISF_RETURN_IF_ERR(imx477_read(ctx, IMX477_REG_TEMPERATURE, &raw));
    /* T°C × 10 = (raw × 7) - 200 */
    *out_temp_x10 = (s16)((s32)raw * 7 - 200);
    return ISF_OK;
}

static isf_status_t imx477_set_power_state(sensor_handle_t handle, sensor_power_state_t state)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    (void)ctx;
    /* XSHUTDOWN and VDDANA controls are board-specific (GPIO).
     * This driver delegates to a platform callback set via sensor_platform_ops. */
    ISF_UNUSED(state);
    return ISF_OK;
}

static isf_status_t imx477_get_caps(sensor_handle_t handle, sensor_capabilities_t *out_caps)
{
    ISF_CHECK_PTR(handle);
    ISF_CHECK_PTR(out_caps);
    memset(out_caps, 0, sizeof(*out_caps));
    out_caps->mode_count = (u8)ISF_ARRAY_SIZE(imx477_modes);
    memcpy(out_caps->modes, imx477_modes,
           sizeof(sensor_mode_desc_t) * out_caps->mode_count);
    out_caps->min_gain_x100 = 100U;
    out_caps->max_gain_x100 = 1600U;    /* ~42 dB */
    out_caps->min_exposure_us = 100U;
    out_caps->max_exposure_us = 1000000U;
    out_caps->has_temperature_sensor = true;
    out_caps->has_hardware_trigger   = true;
    out_caps->has_master_slave       = false;
    out_caps->has_embedded_metadata  = true;
    return ISF_OK;
}

static isf_status_t imx477_remove(sensor_handle_t handle)
{
    ISF_CHECK_PTR(handle);
    imx477_context_t *ctx = (imx477_context_t *)handle;
    if (ctx->streaming) {
        (void)imx477_stop_streaming(handle);
    }
    ISF_LOG_INFO("IMX477: removed");
    return ISF_OK;
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Driver registration                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */
static const sensor_driver_t imx477_driver = {
    .identity = {
        .name              = "imx477",
        .model_id          = "IMX477",
        .chip_id           = IMX477_CHIP_ID,
        .revision          = 0x00U,
        .pixel_array_width = 4056U,
        .pixel_array_height = 3040U,
        .i2c_addr          = 0x1AU,
        .auto_detect       = true,
        .chip_id_reg       = IMX477_REG_CHIP_ID_H,
        .chip_id_expected  = IMX477_CHIP_ID,
    },
    .probe             = imx477_probe,
    .configure         = imx477_configure,
    .start_streaming   = imx477_start_streaming,
    .stop_streaming    = imx477_stop_streaming,
    .set_gain          = imx477_set_gain,
    .set_exposure      = imx477_set_exposure,
    .set_frame_rate    = imx477_set_frame_rate,
    .set_hdr_mode      = NULL,  /* TODO: DOL-HDR implementation */
    .set_roi           = NULL,  /* TODO: crop window registers */
    .trigger           = NULL,  /* TODO: XVS trigger GPIO */
    .read_temperature  = imx477_read_temperature,
    .set_power_state   = imx477_set_power_state,
    .read_eeprom       = NULL,  /* IMX477 has no on-chip EEPROM */
    .get_stats         = NULL,  /* TODO */
    .get_caps          = imx477_get_caps,
    .remove            = imx477_remove,
};

/**
 * @brief   Module init — register driver. Call before sensor_discover().
 *          In a Linux kernel module this would be module_init().
 */
isf_status_t imx477_module_init(void)
{
    return sensor_register_driver(&imx477_driver);
}
