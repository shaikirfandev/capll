# Audio Subsystem — ALSA, ASoC, I2S/TDM, Audio Protocols

## Level 1: Linux Audio Stack Overview

```
User Space
┌──────────────────────────────────────────────────────┐
│  Applications: aplay, pulseaudio, pipewire, gst      │
├──────────────────────────────────────────────────────┤
│  PulseAudio / PipeWire  — Audio server               │
├──────────────────────────────────────────────────────┤
│  ALSA lib (libasound)  — /dev/snd/* user space lib   │
├──────────────────────────────────────────────────────┤
Kernel Space
├──────────────────────────────────────────────────────┤
│  ALSA Core (sound/core/) — PCM, mixer, sequencer     │
├──────────────────────────────────────────────────────┤
│  ASoC (ALSA System-on-Chip) — sound/soc/             │
│  ┌──────────────┬────────────────┬─────────────────┐ │
│  │  Platform    │   Codec        │  Machine         │ │
│  │  (DMA/I2S   │  (codec chip)  │  (board glue)    │ │
│  │   controller)│               │                  │ │
│  └──────────────┴────────────────┴─────────────────┘ │
├──────────────────────────────────────────────────────┤
│  Hardware: I2S, TDM, PDM bus → Audio codec chip      │
└──────────────────────────────────────────────────────┘
```

---

## Level 2: ALSA Core Concepts

### 2.1 ALSA PCM (Pulse Code Modulation)

```
PCM stream:
  playback: App → kernel buffer → DMA → DAC → speaker
  capture:  microphone → ADC → DMA → kernel buffer → App

Key parameters:
  rate:     8000, 44100, 48000, 96000, 192000 Hz
  channels: 1 (mono), 2 (stereo), 8 (surround)
  format:   S16_LE, S32_LE, S24_3LE, FLOAT
  periods:  number of interrupt points per buffer
  period_size: frames per period (latency vs efficiency tradeoff)
```

### 2.2 ALSA User Space API

```c
#include <alsa/asoundlib.h>

/* Playback example */
int play_pcm(const char *device, short *samples, int count)
{
    snd_pcm_t *pcm;
    snd_pcm_hw_params_t *params;
    int err;

    /* Open PCM device */
    err = snd_pcm_open(&pcm, device, SND_PCM_STREAM_PLAYBACK, 0);
    if (err < 0) {
        fprintf(stderr, "Open error: %s\n", snd_strerror(err));
        return err;
    }

    /* Set hardware parameters */
    snd_pcm_hw_params_alloca(&params);
    snd_pcm_hw_params_any(pcm, params);
    snd_pcm_hw_params_set_access(pcm, params, SND_PCM_ACCESS_RW_INTERLEAVED);
    snd_pcm_hw_params_set_format(pcm, params, SND_PCM_FORMAT_S16_LE);
    snd_pcm_hw_params_set_channels(pcm, params, 2);

    unsigned int rate = 48000;
    snd_pcm_hw_params_set_rate_near(pcm, params, &rate, 0);

    snd_pcm_uframes_t period_size = 1024;
    snd_pcm_hw_params_set_period_size_near(pcm, params, &period_size, 0);

    err = snd_pcm_hw_params(pcm, params);
    if (err < 0) return err;

    /* Write audio data */
    snd_pcm_sframes_t frames = snd_pcm_writei(pcm, samples, count / 4);
    if (frames < 0)
        snd_pcm_recover(pcm, frames, 0);

    snd_pcm_drain(pcm);
    snd_pcm_close(pcm);
    return 0;
}
```

---

## Level 3: ASoC — ALSA System-on-Chip Framework

### 3.1 ASoC Three-Component Model

```
Machine Driver (board-specific glue)
    links together:
        │
        ├── CPU DAI (Digital Audio Interface) — I2S/TDM controller
        │     Platform driver (DMA engine)
        │
        └── Codec DAI — audio codec chip (e.g., WM8960, TLV320AIC3x)
              Codec driver (I2C/SPI controlled)

DAI = Digital Audio Interface = I2S/TDM/PCM port
```

### 3.2 Codec Driver (e.g., WM8960)

```c
/* sound/soc/codecs/wm8960.c */
#include <sound/soc.h>
#include <sound/tlv.h>

struct wm8960_priv {
    struct regmap *regmap;
    int sysclk;
    int bclk;
};

/* Volume control via DAPM */
static const DECLARE_TLV_DB_SCALE(out_tlv, -12100, 100, 1);

static const struct snd_kcontrol_new wm8960_snd_controls[] = {
    SOC_DOUBLE_R_TLV("Headphone Playback Volume",
        WM8960_LOUT1, WM8960_ROUT1, 0, 127, 0, out_tlv),
    SOC_DOUBLE_R_TLV("Speaker Playback Volume",
        WM8960_LOUT2, WM8960_ROUT2, 0, 127, 0, out_tlv),
    SOC_DOUBLE("Headphone Playback Switch",
        WM8960_LOUT1, WM8960_ROUT1, 8, 1, 0),
    SOC_ENUM("ADC Polarity", wm8960_enum[0]),
};

/* DAPM (Dynamic Audio Power Management) widgets */
static const struct snd_soc_dapm_widget wm8960_dapm_widgets[] = {
    SND_SOC_DAPM_HP("HP_L", NULL),
    SND_SOC_DAPM_HP("HP_R", NULL),
    SND_SOC_DAPM_SPK("SPK_L", NULL),
    SND_SOC_DAPM_SPK("SPK_R", NULL),
    SND_SOC_DAPM_MIC("MICBIAS", wm8960_micbias_event),
    SND_SOC_DAPM_INPUT("LINPUT1"),
    SND_SOC_DAPM_INPUT("LINPUT2"),
    SND_SOC_DAPM_OUTPUT("LOUT1"),
    SND_SOC_DAPM_OUTPUT("ROUT1"),
    SND_SOC_DAPM_ADC("Left ADC", "Capture", WM8960_POWER1, 3, 0),
    SND_SOC_DAPM_DAC("Left DAC", "Playback", WM8960_POWER2, 8, 0),
    SND_SOC_DAPM_PGA("Left Input Boost Mixer", WM8960_POWER1, 5, 0, ...),
};

/* DAPM routes */
static const struct snd_soc_dapm_route wm8960_dapm_routes[] = {
    { "Left Output Mixer", "LINPUT1 Switch", "Left Input Boost Mixer" },
    { "Left DAC", NULL, "DAC CLK" },
    { "LOUT1 PGA", NULL, "Left DAC" },
    { "HP_L", NULL, "LOUT1 PGA" },
    { "SPK_L", NULL, "SPK_LP" },
    { "Left ADC", NULL, "Left Input Boost Mixer" },
};

/* DAI (I2S interface) operations */
static int wm8960_hw_params(struct snd_pcm_substream *substream,
                             struct snd_pcm_hw_params *params,
                             struct snd_soc_dai *dai)
{
    struct snd_soc_component *component = dai->component;
    u16 iface = snd_soc_component_read(component, WM8960_IFACE1) & 0xfff3;

    switch (params_width(params)) {
    case 16: break;
    case 20: iface |= 0x0004; break;
    case 24: iface |= 0x0008; break;
    case 32: iface |= 0x000c; break;
    }

    snd_soc_component_write(component, WM8960_IFACE1, iface);
    wm8960_set_pll(component, params_rate(params));
    return 0;
}

static int wm8960_set_dai_fmt(struct snd_soc_dai *dai, unsigned int fmt)
{
    struct snd_soc_component *component = dai->component;
    u16 iface = 0;

    /* Master or slave */
    switch (fmt & SND_SOC_DAIFMT_MASTER_MASK) {
    case SND_SOC_DAIFMT_CBM_CFM: iface = 0x0040; break;  /* codec master */
    case SND_SOC_DAIFMT_CBS_CFS: break;                   /* codec slave */
    default: return -EINVAL;
    }

    /* Format */
    switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
    case SND_SOC_DAIFMT_I2S:     iface |= 0x0002; break;
    case SND_SOC_DAIFMT_RIGHT_J: break;
    case SND_SOC_DAIFMT_LEFT_J:  iface |= 0x0001; break;
    default: return -EINVAL;
    }

    snd_soc_component_update_bits(component, WM8960_IFACE1, 0xffff, iface);
    return 0;
}

static const struct snd_soc_dai_ops wm8960_dai_ops = {
    .hw_params    = wm8960_hw_params,
    .set_fmt      = wm8960_set_dai_fmt,
    .set_sysclk   = wm8960_set_sysclk,
    .set_pll      = wm8960_set_pll,
    .mute_stream  = wm8960_mute,
};

static struct snd_soc_dai_driver wm8960_dai = {
    .name = "wm8960-hifi",
    .playback = {
        .stream_name  = "Playback",
        .channels_min = 1,
        .channels_max = 2,
        .rates        = WM8960_RATES,
        .formats      = WM8960_FORMATS,
    },
    .capture = {
        .stream_name  = "Capture",
        .channels_min = 1,
        .channels_max = 2,
        .rates        = WM8960_RATES,
        .formats      = WM8960_FORMATS,
    },
    .ops = &wm8960_dai_ops,
    .symmetric_rate = 1,
};
```

### 3.3 Platform Driver (I2S + DMA Controller)

```c
/* sound/soc/fsl/fsl_sai.c — I2S platform driver example */
#include <sound/dmaengine_pcm.h>

struct fsl_sai {
    struct platform_device *pdev;
    void __iomem           *base;
    struct clk             *bus_clk;
    struct clk             *mclk_clk[4];
    struct snd_dmaengine_dai_dma_data dma_params_rx;
    struct snd_dmaengine_dai_dma_data dma_params_tx;
};

static int fsl_sai_set_dai_fmt(struct snd_soc_dai *cpu_dai, unsigned int fmt)
{
    struct fsl_sai *sai = snd_soc_dai_get_drvdata(cpu_dai);
    u32 val_cr2 = 0, val_cr4 = 0;

    switch (fmt & SND_SOC_DAIFMT_FORMAT_MASK) {
    case SND_SOC_DAIFMT_I2S:
        val_cr2 |= FSL_SAI_CR2_BCP;   /* Bit Clock Polarity */
        val_cr4 |= FSL_SAI_CR4_FSE;   /* Frame sync edge */
        val_cr4 |= FSL_SAI_CR4_FSP;   /* Frame sync polarity */
        break;
    case SND_SOC_DAIFMT_DSP_A:
        val_cr4 |= FSL_SAI_CR4_MF;    /* MSB first */
        break;
    }

    regmap_update_bits(sai->regmap, FSL_SAI_xCR2(tx),
                       FSL_SAI_CR2_BCP, val_cr2);
    regmap_update_bits(sai->regmap, FSL_SAI_xCR4(tx),
                       FSL_SAI_CR4_FSE | FSL_SAI_CR4_FSP | FSL_SAI_CR4_MF,
                       val_cr4);
    return 0;
}

static int fsl_sai_hw_params(struct snd_pcm_substream *substream,
                              struct snd_pcm_hw_params *params,
                              struct snd_soc_dai *cpu_dai)
{
    struct fsl_sai *sai = snd_soc_dai_get_drvdata(cpu_dai);
    bool tx = substream->stream == SNDRV_PCM_STREAM_PLAYBACK;
    unsigned int channels = params_channels(params);
    u32 word_width = params_width(params);
    u32 val_cr4 = 0, val_cr5 = 0;

    val_cr4 |= FSL_SAI_CR4_SYWD(word_width);
    val_cr4 |= FSL_SAI_CR4_FRSZ(channels);
    val_cr5 |= FSL_SAI_CR5_WNW(word_width);
    val_cr5 |= FSL_SAI_CR5_W0W(word_width);
    val_cr5 |= FSL_SAI_CR5_FBT(word_width - 1);

    /* Setup DMA parameters */
    sai->dma_params_tx.addr = sai->res->start + FSL_SAI_TDR0;
    sai->dma_params_tx.maxburst = FSL_SAI_MAXBURST_TX;
    snd_soc_dai_set_dma_data(cpu_dai, substream, &sai->dma_params_tx);

    return 0;
}
```

### 3.4 Machine Driver (Board Glue)

```c
/* Board-specific machine driver */
#include <sound/soc.h>

/* Define DAI link between CPU (SAI/I2S) and Codec (WM8960) */
static struct snd_soc_dai_link my_board_dai_links[] = {
    {
        .name             = "HiFi",
        .stream_name      = "HiFi",
        .cpu_dai_name     = "fsl-sai.0",       /* I2S controller */
        .platform_name    = "fsl-sai.0",       /* DMA platform */
        .codec_dai_name   = "wm8960-hifi",     /* Codec DAI */
        .codec_name       = "wm8960.1-001a",   /* I2C address */
        .init             = my_board_wm8960_init,
        .dai_fmt          = SND_SOC_DAIFMT_I2S |
                            SND_SOC_DAIFMT_NB_NF |
                            SND_SOC_DAIFMT_CBM_CFM,
        .ops              = &my_board_ops,
    },
};

static struct snd_soc_card my_board_card = {
    .name         = "my-audio-board",
    .owner        = THIS_MODULE,
    .dai_link     = my_board_dai_links,
    .num_links    = ARRAY_SIZE(my_board_dai_links),
    .dapm_widgets = my_board_dapm_widgets,
    .num_dapm_widgets = ARRAY_SIZE(my_board_dapm_widgets),
    .dapm_routes  = my_board_dapm_routes,
    .num_dapm_routes = ARRAY_SIZE(my_board_dapm_routes),
};

static int my_board_probe(struct platform_device *pdev)
{
    my_board_card.dev = &pdev->dev;
    return devm_snd_soc_register_card(&pdev->dev, &my_board_card);
}
```

---

## Level 4: I2S / TDM Protocols

### 4.1 I2S (Inter-IC Sound)

```
I2S Signals:
  BCLK  — Bit Clock (serial clock for each sample bit)
  LRCLK — Left/Right Clock (word select, = sample rate)
  SDATA — Serial Data (MSB first)

I2S Timing (44.1kHz, 16-bit stereo):
  BCLK = 44100 * 2 * 16 = 1.4112 MHz
  LRCLK = 44100 Hz
  
  LRCLK:  ─────────────┐                    ┌──────
          LEFT CHANNEL  └────────────────────┘  RIGHT CHANNEL
  BCLK:   ┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐┌┐
  SDATA:  ─ D15─D14─D13─...─D1─D0─ D15─D14─...
  
  Phase: SDATA valid 1 BCLK after LRCLK edge (I2S standard)

Variants:
  Left-Justified:  SDATA valid on LRCLK edge
  Right-Justified: SDATA MSB aligned to end of frame
  I2S:             SDATA 1 cycle delayed (Philips standard)
```

### 4.2 TDM (Time Division Multiplexing)

```
TDM extends I2S to multiple channels:
  BCLK  — Bit Clock
  FSYNC — Frame Sync (pulse once per frame)
  SDATA — Multiple channels time-multiplexed

TDM8 (8 channels × 32-bit at 48kHz):
  FSYNC = 48000 Hz
  BCLK  = 48000 * 8 * 32 = 12.288 MHz
  
  Frame: |Ch0|Ch1|Ch2|Ch3|Ch4|Ch5|Ch6|Ch7|Ch0|...
  
  Used in: automotive audio (8-channel surround),
           professional audio, HDMI audio
```

```c
/* TDM configuration in ASoC driver */
static int my_codec_set_tdm_slot(struct snd_soc_dai *dai,
                                  unsigned int tx_mask, unsigned int rx_mask,
                                  int slots, int slot_width)
{
    struct my_codec *codec = snd_soc_dai_get_drvdata(dai);

    /* tx_mask / rx_mask: bitmask of active slots */
    /* slots: total number of TDM slots */
    /* slot_width: bits per slot */

    codec->slots      = slots;
    codec->slot_width = slot_width;

    /* Configure hardware */
    regmap_update_bits(codec->regmap, CODEC_TDM_REG,
        CODEC_TDM_SLOTS_MASK, (slots - 1) << CODEC_TDM_SLOTS_SHIFT);

    return 0;
}

/* DAI format for TDM */
/* SND_SOC_DAIFMT_DSP_A — DSP/PCM mode (TDM) */
```

---

## Level 5: DAPM — Dynamic Audio Power Management

```c
/*
 * DAPM automatically powers audio components when needed.
 * Only active audio paths are powered.
 * 
 * Path: LINPUT1 → ADC → DAC → LOUT1 → Headphone
 * If headphone is playing, only those blocks are powered.
 */

/* Widget types */
SND_SOC_DAPM_INPUT("LINPUT1")       /* physical input */
SND_SOC_DAPM_OUTPUT("HP_L")         /* physical output */
SND_SOC_DAPM_MIC("Mic Bias", cb)    /* microphone bias */
SND_SOC_DAPM_PGA("PGA", reg, bit, inv, NULL, 0)  /* programmable gain amp */
SND_SOC_DAPM_ADC("ADC", "Capture", reg, bit, inv) /* ADC */
SND_SOC_DAPM_DAC("DAC", "Playback", reg, bit, inv) /* DAC */
SND_SOC_DAPM_MIXER("Mixer", SND_SOC_NOPM, 0, 0, controls, num) /* mixer */
SND_SOC_DAPM_SWITCH("Headphone", SND_SOC_NOPM, 0, 0, &hp_switch) /* switch */
SND_SOC_DAPM_SUPPLY("AVDD", reg, bit, 0, supply_event, event_mask) /* supply */

/* Route: source → sink */
static const struct snd_soc_dapm_route routes[] = {
    { "ADC",     NULL,        "Mic PGA"  },
    { "Mic PGA", NULL,        "LINPUT1"  },
    { "HP_L",    NULL,        "DAC"      },
    { "DAC",     NULL,        "Playback" },   /* stream name */
};
```

---

## Audio Debugging Tools

```bash
# List ALSA devices
aplay -l             # playback devices
arecord -l           # capture devices
aplay -L             # PCM device aliases

# Test playback
aplay -D hw:0,0 -f S16_LE -r 48000 -c 2 test.wav
speaker-test -D plughw:0 -c 2 -t sine

# ALSA mixer controls
amixer -c 0 contents     # list all controls
amixer -c 0 cset "Headphone Playback Volume" 127
alsamixer                 # interactive TUI

# ASoC DAPM debug
cat /sys/kernel/debug/asoc/*/dapm_power_domains
cat /sys/kernel/debug/asoc/*/components

# Enable audio codec debug
echo 1 > /sys/module/snd_soc_core/parameters/pmdown_time

# Capture audio data
arecord -D hw:0,0 -f S16_LE -r 48000 -c 2 -d 10 captured.wav

# Check I2S/audio clock configuration
cat /sys/kernel/debug/clk/*/clk_rate | grep -i audio
```

---

## Interview Questions

1. What is ALSA? What is ASoC? What is the difference?
2. Explain the 3 components of an ASoC driver (Platform, Codec, Machine).
3. What is DAPM and why is it important for battery life?
4. Explain I2S signal timing (BCLK, LRCLK, SDATA).
5. What is TDM and when is it used instead of I2S?
6. What is a DAI (Digital Audio Interface)?
7. How does a codec driver set the sample rate?
8. What is `dai_fmt` and what options are available?
9. Explain codec master vs slave mode in I2S.
10. What does `snd_soc_dai_set_sysclk` do?
