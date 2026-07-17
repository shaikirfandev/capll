// SPDX-License-Identifier: GPL-2.0-or-later
/*
 * isf_imx477.c — Linux V4L2 / media framework driver for Sony IMX477
 *
 * Architecture:
 *   - Registers as a V4L2 sub-device (v4l2_subdev).
 *   - Exposes sensor controls via V4L2 Controls API (gain, exposure, FPS, HDR).
 *   - Interfaces with CSI-2 bridge driver via the Media Controller pipeline.
 *   - Follows the V4L2 async sub-device registration model.
 *   - Supports runtime power management (RPM) and camera common clock framework.
 *   - Compliant with: Documentation/driver-api/media/v4l2-subdev.rst
 *
 * DT binding (arch/arm64/boot/dts/...):
 *   &i2c1 {
 *       imx477: camera@1a {
 *           compatible = "sony,imx477";
 *           reg = <0x1a>;
 *           clocks = <&clk IMX477_CLK_24M>;
 *           clock-names = "xclk";
 *           VANA-supply = <&reg_2v8>;
 *           VDIG-supply = <&reg_1v8>;
 *           reset-gpios = <&gpio1 3 GPIO_ACTIVE_LOW>;
 *           port {
 *               imx477_out: endpoint {
 *                   remote-endpoint = <&mipi_csi2_in>;
 *                   data-lanes = <1 2>;
 *                   clock-lanes = <0>;
 *                   link-frequencies = /bits/ 64 <750000000>;
 *               };
 *           };
 *       };
 *   };
 *
 * Copyright (c) 2026 Industrial Vision Systems.
 */

#include <linux/clk.h>
#include <linux/delay.h>
#include <linux/gpio/consumer.h>
#include <linux/i2c.h>
#include <linux/module.h>
#include <linux/of_device.h>
#include <linux/pm_runtime.h>
#include <linux/regmap.h>
#include <linux/regulator/consumer.h>
#include <media/v4l2-ctrls.h>
#include <media/v4l2-device.h>
#include <media/v4l2-fwnode.h>
#include <media/v4l2-subdev.h>

#define DRIVER_NAME "isf-imx477"

/* ─────────────────────────────────────────────────────────────────────────── */
/* Registers                                                                   */
/* ─────────────────────────────────────────────────────────────────────────── */
#define IMX477_REG_CHIP_ID_H    0x0016
#define IMX477_REG_CHIP_ID_L    0x0017
#define IMX477_CHIP_ID          0x0477

#define IMX477_REG_MODE_SELECT  0x0100
#define IMX477_REG_RESET        0x0103
#define IMX477_REG_HOLD         0x0104
#define IMX477_REG_ANA_GAIN_H   0x0204
#define IMX477_REG_ANA_GAIN_L   0x0205
#define IMX477_REG_COARSE_INT_H 0x0202
#define IMX477_REG_COARSE_INT_L 0x0203
#define IMX477_REG_FLL_H        0x0340
#define IMX477_REG_FLL_L        0x0341
#define IMX477_REG_X_OUT_H      0x034C
#define IMX477_REG_X_OUT_L      0x034D
#define IMX477_REG_Y_OUT_H      0x034E
#define IMX477_REG_Y_OUT_L      0x034F
#define IMX477_REG_TEMPERATURE  0x013A
#define IMX477_REG_TEST_PATT_H  0x0600

/* ─────────────────────────────────────────────────────────────────────────── */
/* Mode table                                                                  */
/* ─────────────────────────────────────────────────────────────────────────── */
struct imx477_mode {
    u32 width;
    u32 height;
    u32 pixel_rate;
    u32 link_freq_index;
    u16 fll_def;
    u16 llpck;
    u32 code;    /* MEDIA_BUS_FMT_SRGGB12_1X12 etc. */
    u8  lanes;
};

static const u64 imx477_link_freqs[] = {
    750000000ULL,   /* 1500 Mbps / 2 */
    594000000ULL,   /* 1188 Mbps / 2 */
};

static const struct imx477_mode imx477_modes_table[] = {
    {   /* Full 12MP */
        .width = 4056, .height = 3040,
        .pixel_rate = 280000000,
        .link_freq_index = 0,
        .fll_def = 3134, .llpck = 5760,
        .code = 0x3012, /* MEDIA_BUS_FMT_SRGGB12_1X12 */
        .lanes = 2,
    },
    {   /* 1080p60 */
        .width = 1920, .height = 1080,
        .pixel_rate = 280000000,
        .link_freq_index = 1,
        .fll_def = 1130, .llpck = 4420,
        .code = 0x3012,
        .lanes = 2,
    },
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* Per-device state                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */
struct imx477 {
    struct v4l2_subdev      sd;
    struct media_pad        pad;
    struct v4l2_mbus_framefmt fmt;

    struct clk             *xclk;
    struct regmap          *regmap;
    struct gpio_desc       *reset_gpio;
    struct regulator_bulk_data regulators[2];  /* VANA, VDIG */

    struct v4l2_ctrl_handler ctrl_handler;
    struct v4l2_ctrl        *pixel_rate;
    struct v4l2_ctrl        *link_freq;
    struct v4l2_ctrl        *exposure;
    struct v4l2_ctrl        *analogue_gain;
    struct v4l2_ctrl        *hflip;
    struct v4l2_ctrl        *vflip;
    struct v4l2_ctrl        *test_pattern;

    const struct imx477_mode *current_mode;
    bool streaming;
    struct mutex lock;  /* Serialise s_ctrl / set_fmt / start/stop */
};

static inline struct imx477 *to_imx477(struct v4l2_subdev *sd)
{
    return container_of(sd, struct imx477, sd);
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* regmap configuration                                                        */
/* ─────────────────────────────────────────────────────────────────────────── */
static const struct regmap_config imx477_regmap_config = {
    .reg_bits    = 16,
    .val_bits    = 8,
    .cache_type  = REGCACHE_NONE,  /* No caching — registers change asynchronously */
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* I2C helpers                                                                 */
/* ─────────────────────────────────────────────────────────────────────────── */
static int imx477_write(struct imx477 *priv, u16 reg, u8 val)
{
    return regmap_write(priv->regmap, reg, val);
}

static int imx477_write16(struct imx477 *priv, u16 reg, u16 val)
{
    int ret;
    ret = regmap_write(priv->regmap, reg, (val >> 8) & 0xFF);
    if (ret) return ret;
    return regmap_write(priv->regmap, reg + 1, val & 0xFF);
}

static int imx477_read(struct imx477 *priv, u16 reg, u32 *val)
{
    return regmap_read(priv->regmap, reg, val);
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* Power management                                                            */
/* ─────────────────────────────────────────────────────────────────────────── */
static int imx477_power_on(struct device *dev)
{
    struct v4l2_subdev *sd = dev_get_drvdata(dev);
    struct imx477 *priv = to_imx477(sd);
    int ret;

    ret = regulator_bulk_enable(ARRAY_SIZE(priv->regulators), priv->regulators);
    if (ret) {
        dev_err(dev, "Failed to enable regulators: %d\n", ret);
        return ret;
    }
    usleep_range(1000, 1200);

    gpiod_set_value_cansleep(priv->reset_gpio, 0);  /* De-assert reset (active low) */
    usleep_range(5000, 6000);  /* Wait for sensor to come out of reset */

    ret = clk_prepare_enable(priv->xclk);
    if (ret) {
        dev_err(dev, "Failed to enable XCLK: %d\n", ret);
        goto err_regulator;
    }
    usleep_range(10000, 11000);  /* Allow PLL to lock */
    return 0;

err_regulator:
    gpiod_set_value_cansleep(priv->reset_gpio, 1);
    regulator_bulk_disable(ARRAY_SIZE(priv->regulators), priv->regulators);
    return ret;
}

static int imx477_power_off(struct device *dev)
{
    struct v4l2_subdev *sd = dev_get_drvdata(dev);
    struct imx477 *priv = to_imx477(sd);

    clk_disable_unprepare(priv->xclk);
    gpiod_set_value_cansleep(priv->reset_gpio, 1);  /* Assert reset */
    regulator_bulk_disable(ARRAY_SIZE(priv->regulators), priv->regulators);
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────────── */
/* V4L2 sub-device operations                                                  */
/* ─────────────────────────────────────────────────────────────────────────── */
static int imx477_set_ctrl(struct v4l2_ctrl *ctrl)
{
    struct imx477 *priv = container_of(ctrl->handler, struct imx477, ctrl_handler);
    int ret = 0;

    if (!pm_runtime_get_if_in_use(priv->sd.dev))
        return 0;

    switch (ctrl->id) {
    case V4L2_CID_ANALOGUE_GAIN:
        ret = imx477_write16(priv, IMX477_REG_ANA_GAIN_H, (u16)ctrl->val);
        break;
    case V4L2_CID_EXPOSURE:
        ret = imx477_write16(priv, IMX477_REG_COARSE_INT_H, (u16)ctrl->val);
        break;
    case V4L2_CID_TEST_PATTERN:
        ret = imx477_write16(priv, IMX477_REG_TEST_PATT_H, (u16)ctrl->val);
        break;
    default:
        ret = -EINVAL;
    }
    pm_runtime_put(priv->sd.dev);
    return ret;
}

static const struct v4l2_ctrl_ops imx477_ctrl_ops = {
    .s_ctrl = imx477_set_ctrl,
};

static int imx477_s_stream(struct v4l2_subdev *sd, int enable)
{
    struct imx477 *priv = to_imx477(sd);
    int ret = 0;

    mutex_lock(&priv->lock);
    if (enable) {
        ret = pm_runtime_resume_and_get(sd->dev);
        if (ret < 0) goto unlock;
        ret = imx477_write(priv, IMX477_REG_MODE_SELECT, 0x01);
        if (ret) {
            pm_runtime_put(sd->dev);
            goto unlock;
        }
        priv->streaming = true;
    } else {
        ret = imx477_write(priv, IMX477_REG_MODE_SELECT, 0x00);
        pm_runtime_put(sd->dev);
        priv->streaming = false;
    }
unlock:
    mutex_unlock(&priv->lock);
    return ret;
}

static int imx477_get_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *state,
                           struct v4l2_subdev_format *fmt)
{
    struct imx477 *priv = to_imx477(sd);
    mutex_lock(&priv->lock);
    fmt->format = priv->fmt;
    mutex_unlock(&priv->lock);
    return 0;
}

static int imx477_set_fmt(struct v4l2_subdev *sd,
                           struct v4l2_subdev_state *state,
                           struct v4l2_subdev_format *fmt)
{
    struct imx477 *priv = to_imx477(sd);
    const struct imx477_mode *mode = NULL;
    u32 best_dist = UINT_MAX;

    /* Find closest mode */
    for (size_t i = 0; i < ARRAY_SIZE(imx477_modes_table); i++) {
        u32 dw = abs((int)imx477_modes_table[i].width  - (int)fmt->format.width);
        u32 dh = abs((int)imx477_modes_table[i].height - (int)fmt->format.height);
        if (dw + dh < best_dist) {
            best_dist = dw + dh;
            mode = &imx477_modes_table[i];
        }
    }
    if (!mode) return -EINVAL;

    mutex_lock(&priv->lock);
    fmt->format.width  = mode->width;
    fmt->format.height = mode->height;
    fmt->format.code   = mode->code;
    fmt->format.field  = V4L2_FIELD_NONE;
    fmt->format.colorspace = V4L2_COLORSPACE_RAW;
    if (fmt->which == V4L2_SUBDEV_FORMAT_ACTIVE) {
        priv->fmt = fmt->format;
        priv->current_mode = mode;
    }
    mutex_unlock(&priv->lock);
    return 0;
}

static int imx477_enum_mbus_code(struct v4l2_subdev *sd,
                                  struct v4l2_subdev_state *state,
                                  struct v4l2_subdev_mbus_code_enum *code)
{
    if (code->index != 0) return -EINVAL;
    code->code = 0x3012; /* MEDIA_BUS_FMT_SRGGB12_1X12 */
    return 0;
}

static const struct v4l2_subdev_video_ops imx477_video_ops = {
    .s_stream = imx477_s_stream,
};

static const struct v4l2_subdev_pad_ops imx477_pad_ops = {
    .get_fmt        = imx477_get_fmt,
    .set_fmt        = imx477_set_fmt,
    .enum_mbus_code = imx477_enum_mbus_code,
};

static const struct v4l2_subdev_ops imx477_subdev_ops = {
    .video = &imx477_video_ops,
    .pad   = &imx477_pad_ops,
};

/* ─────────────────────────────────────────────────────────────────────────── */
/* Probe / remove                                                              */
/* ─────────────────────────────────────────────────────────────────────────── */
static int imx477_probe(struct i2c_client *client)
{
    struct device *dev = &client->dev;
    struct imx477 *priv;
    u32 chip_id_h, chip_id_l;
    int ret;

    priv = devm_kzalloc(dev, sizeof(*priv), GFP_KERNEL);
    if (!priv) return -ENOMEM;

    priv->regmap = devm_regmap_init_i2c(client, &imx477_regmap_config);
    if (IS_ERR(priv->regmap)) return PTR_ERR(priv->regmap);

    priv->xclk = devm_clk_get(dev, "xclk");
    if (IS_ERR(priv->xclk)) {
        dev_err(dev, "Failed to get xclk: %ld\n", PTR_ERR(priv->xclk));
        return PTR_ERR(priv->xclk);
    }

    priv->reset_gpio = devm_gpiod_get_optional(dev, "reset", GPIOD_OUT_HIGH);
    if (IS_ERR(priv->reset_gpio)) return PTR_ERR(priv->reset_gpio);

    priv->regulators[0].supply = "VANA";
    priv->regulators[1].supply = "VDIG";
    ret = devm_regulator_bulk_get(dev, ARRAY_SIZE(priv->regulators), priv->regulators);
    if (ret) return ret;

    mutex_init(&priv->lock);
    v4l2_i2c_subdev_init(&priv->sd, client, &imx477_subdev_ops);
    priv->sd.flags |= V4L2_SUBDEV_FL_HAS_DEVNODE;
    priv->sd.entity.function = MEDIA_ENT_F_CAM_SENSOR;
    priv->pad.flags = MEDIA_PAD_FL_SOURCE;
    ret = media_entity_pads_init(&priv->sd.entity, 1, &priv->pad);
    if (ret) return ret;

    /* Power on and verify chip ID */
    ret = imx477_power_on(dev);
    if (ret) goto err_entity;

    ret = imx477_read(priv, IMX477_REG_CHIP_ID_H, &chip_id_h);
    if (ret) goto err_power;
    ret = imx477_read(priv, IMX477_REG_CHIP_ID_L, &chip_id_l);
    if (ret) goto err_power;

    if (((chip_id_h & 0xFF) << 8 | (chip_id_l & 0xFF)) != IMX477_CHIP_ID) {
        dev_err(dev, "Unexpected chip ID: 0x%02X%02X\n", chip_id_h, chip_id_l);
        ret = -ENODEV;
        goto err_power;
    }
    dev_info(dev, "IMX477 detected (chip ID 0x%04X)\n", IMX477_CHIP_ID);

    /* Initialise V4L2 controls */
    v4l2_ctrl_handler_init(&priv->ctrl_handler, 6);
    priv->analogue_gain = v4l2_ctrl_new_std(&priv->ctrl_handler,
        &imx477_ctrl_ops, V4L2_CID_ANALOGUE_GAIN, 0, 978, 1, 0);
    priv->exposure = v4l2_ctrl_new_std(&priv->ctrl_handler,
        &imx477_ctrl_ops, V4L2_CID_EXPOSURE, 1, 0xFFFF, 1, 1000);
    priv->sd.ctrl_handler = &priv->ctrl_handler;

    priv->current_mode = &imx477_modes_table[0];
    priv->fmt.width    = priv->current_mode->width;
    priv->fmt.height   = priv->current_mode->height;
    priv->fmt.code     = priv->current_mode->code;

    pm_runtime_set_active(dev);
    pm_runtime_enable(dev);
    pm_runtime_idle(dev);

    dev_set_drvdata(dev, &priv->sd);
    ret = v4l2_async_register_subdev_sensor(&priv->sd);
    if (ret) goto err_pm;

    return 0;

err_pm:
    pm_runtime_disable(dev);
err_power:
    imx477_power_off(dev);
err_entity:
    media_entity_cleanup(&priv->sd.entity);
    return ret;
}

static void imx477_remove(struct i2c_client *client)
{
    struct v4l2_subdev *sd = i2c_get_clientdata(client);
    struct imx477 *priv = to_imx477(sd);

    v4l2_async_unregister_subdev(&priv->sd);
    v4l2_ctrl_handler_free(&priv->ctrl_handler);
    media_entity_cleanup(&priv->sd.entity);
    pm_runtime_disable(&client->dev);
    imx477_power_off(&client->dev);
    mutex_destroy(&priv->lock);
}

static const struct dev_pm_ops imx477_pm_ops = {
    SET_RUNTIME_PM_OPS(imx477_power_on, imx477_power_off, NULL)
};

static const struct of_device_id imx477_of_match[] = {
    { .compatible = "sony,imx477" },
    { }
};
MODULE_DEVICE_TABLE(of, imx477_of_match);

static const struct i2c_device_id imx477_id[] = {
    { "imx477", 0 },
    { }
};
MODULE_DEVICE_TABLE(i2c, imx477_id);

static struct i2c_driver imx477_i2c_driver = {
    .driver = {
        .name           = DRIVER_NAME,
        .pm             = &imx477_pm_ops,
        .of_match_table = imx477_of_match,
    },
    .probe    = imx477_probe,
    .remove   = imx477_remove,
    .id_table = imx477_id,
};

module_i2c_driver(imx477_i2c_driver);

MODULE_AUTHOR("Industrial Vision Systems");
MODULE_DESCRIPTION("Sony IMX477 camera sensor driver");
MODULE_LICENSE("GPL v2");
