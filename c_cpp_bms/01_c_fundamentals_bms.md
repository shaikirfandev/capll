# C Fundamentals for BMS Engineering

> **Domain:** Battery Management System (BMS) — EV / HEV / PHEV
> **Systems:** Cell monitoring, SoC/SoH estimation, contactor control, CAN comms, UDS diagnostics
> **Standards:** ISO 26262, IEC 62619, UN R100, MISRA C:2012, AUTOSAR Classic

---

## 1. Why C in BMS?

| BMS Layer | Language | Reason |
|---|---|---|
| MCAL / ADC drivers | C | Direct register access, ISR-based |
| Contactor control | C | Deterministic < 1ms response, ASIL B/D |
| Cell voltage sampling | C | DMA-driven, zero-copy, 96-cell @ 1ms |
| CAN frame TX/RX | C | ISR callback, minimal latency |
| UDS diagnostic handler | C | AUTOSAR DCM integration |
| SoC/SoH algorithms | C++ | EKF, Kalman, OOP simulation model |

---

## 2. Fixed-Width Types — BMS Signal Representation

```c
#include <stdint.h>
#include <stdbool.h>

/* Cell measurement types */
typedef uint16_t  cell_voltage_mv_t;      /* 0–65535 mV (max cell: 4250 mV NMC) */
typedef int16_t   cell_temp_c_t;          /* Scaled: raw/2 - 40 → °C */
typedef uint32_t  pack_voltage_dv_t;      /* Pack voltage in deci-Volts (×10) */
typedef int32_t   pack_current_da_t;      /* Pack current in deci-Amps (×10), signed */
typedef uint8_t   soc_pct_t;             /* 0–100 % */
typedef uint8_t   soh_pct_t;             /* 0–100 % */
typedef uint16_t  capacity_ah_x10_t;     /* Capacity ×10 (e.g., 600 = 60.0 Ah) */

/* BMS configuration constants */
#define BMS_NUM_MODULES         12U
#define BMS_CELLS_PER_MODULE     8U
#define BMS_TOTAL_CELLS         (BMS_NUM_MODULES * BMS_CELLS_PER_MODULE)   /* 96 */
#define BMS_TEMP_SENSORS         (BMS_NUM_MODULES * 2U)                    /* 24 */

/* Protection thresholds (NMC chemistry) */
#define BMS_OV1_THRESHOLD_MV    4200U   /* Over-voltage warning */
#define BMS_OV2_THRESHOLD_MV    4250U   /* Over-voltage critical */
#define BMS_UV1_THRESHOLD_MV    3000U   /* Under-voltage warning */
#define BMS_UV2_THRESHOLD_MV    2800U   /* Under-voltage critical */
#define BMS_OT1_THRESHOLD_C       50    /* Over-temperature warning */
#define BMS_OT2_THRESHOLD_C       60    /* Over-temperature critical */
#define BMS_UT1_THRESHOLD_C        0    /* Under-temperature warning (charge) */
#define BMS_ISO_WARN_OHM_PER_V  500U   /* ISO 6469-3: 500 Ω/V */
#define BMS_ISO_CRIT_OHM_PER_V  100U   /* Critical isolation */

/* Cell data structure */
typedef struct {
    cell_voltage_mv_t voltage_mv;
    bool              is_balancing;
    bool              ov_flag;
    bool              uv_flag;
} CellData_t;

/* Module data structure */
typedef struct {
    CellData_t  cells[BMS_CELLS_PER_MODULE];
    int8_t      temp1_c;           /* Cell group temperature 1 */
    int8_t      temp2_c;           /* Cell group temperature 2 */
    bool        ot_flag;
    uint8_t     balance_mask;      /* Bitmask: which cells are balancing */
} ModuleData_t;

/* Pack-level BMS data */
typedef struct {
    ModuleData_t modules[BMS_NUM_MODULES];
    uint32_t     pack_voltage_mv;
    int32_t      pack_current_ma;    /* Signed: positive = discharging */
    soc_pct_t    soc_pct;
    soh_pct_t    soh_pct;
    uint32_t     insulation_ohm;     /* IMD measurement */
    uint8_t      bms_state;          /* BmsState enum */
    uint8_t      fault_level;        /* 0=none, 1=warn, 2=error, 3=emergency */
    uint32_t     timestamp_ms;
} BmsPackData_t;
```

---

## 3. Pointers — BMS Data Access Patterns

```c
/* Read-only access to cell array */
void log_cell_voltages(const CellData_t* cells, uint8_t count)
{
    if (cells == NULL || count == 0U) return;

    for (uint8_t i = 0U; i < count; ++i) {
        if (cells[i].voltage_mv > BMS_OV2_THRESHOLD_MV ||
            cells[i].voltage_mv < BMS_UV2_THRESHOLD_MV) {
            bms_log_fault(i, cells[i].voltage_mv);
        }
    }
}

/* Output: write through pointer */
bool find_highest_cell(const BmsPackData_t* pack,
                        uint8_t* out_module,
                        uint8_t* out_cell,
                        cell_voltage_mv_t* out_voltage)
{
    if (pack == NULL || out_module == NULL ||
        out_cell == NULL || out_voltage == NULL) return false;

    cell_voltage_mv_t max_v = 0U;
    *out_module = 0U;
    *out_cell   = 0U;

    for (uint8_t m = 0U; m < BMS_NUM_MODULES; ++m) {
        for (uint8_t c = 0U; c < BMS_CELLS_PER_MODULE; ++c) {
            if (pack->modules[m].cells[c].voltage_mv > max_v) {
                max_v       = pack->modules[m].cells[c].voltage_mv;
                *out_module = m;
                *out_cell   = c;
            }
        }
    }
    *out_voltage = max_v;
    return true;
}

/* Function pointer — contactor command table */
typedef bool (*ContactorCmdFn_t)(bool enable);

typedef struct {
    const char*     name;
    ContactorCmdFn_t set_state;
} ContactorEntry_t;

static bool set_main_negative(bool en);
static bool set_precharge(bool en);
static bool set_main_positive(bool en);

static const ContactorEntry_t g_contactors[] = {
    {"MainNeg",    set_main_negative},
    {"Precharge",  set_precharge},
    {"MainPos",    set_main_positive}
};

#define NUM_CONTACTORS (sizeof(g_contactors) / sizeof(g_contactors[0]))
```

---

## 4. Structures — BMS State, DTCs, NVM

```c
/* BMS operating states */
typedef enum {
    BMS_STATE_INIT      = 0U,
    BMS_STATE_SLEEP     = 1U,
    BMS_STATE_STANDBY   = 2U,
    BMS_STATE_PRECHARGE = 3U,
    BMS_STATE_HV_READY  = 4U,
    BMS_STATE_DRIVING   = 5U,
    BMS_STATE_CHARGING  = 6U,
    BMS_STATE_FAULT     = 7U
} BmsState_t;

/* DTC structure */
typedef struct {
    uint32_t dtc_code;
    uint8_t  status;          /* 0x01=active, 0x02=pending, 0x04=confirmed */
    uint8_t  occurrence_count;
    uint32_t first_timestamp_ms;
    uint32_t last_timestamp_ms;
    uint16_t snapshot_voltage_mv;   /* Freeze frame */
    int8_t   snapshot_temp_c;
} DtcRecord_t;

#define BMS_MAX_DTCS 32U
static DtcRecord_t s_dtc_table[BMS_MAX_DTCS];

/* DTC codes */
#define DTC_CELL_OV2              0xD00101UL
#define DTC_CELL_UV2              0xD00201UL
#define DTC_CELL_OT2              0xD00301UL
#define DTC_IMD_LOW_RESISTIVITY   0xD00401UL
#define DTC_CONTACTOR_WELD        0xD00501UL
#define DTC_CURRENT_SENSOR_FAIL   0xD00601UL
#define DTC_PRECHARGE_TIMEOUT     0xD00701UL
#define DTC_12V_SUPPLY_LOW        0xD00801UL

/* NVM persistent data */
typedef struct {
    float    soc_at_shutdown;
    float    soh_pct;
    uint32_t total_cycle_count;
    uint64_t total_energy_discharged_wh;
    uint16_t nominal_capacity_ah_x10;
    char     battery_serial[20U];
    uint8_t  eol_complete_flag;
    uint8_t  crc8;
} BmsNvmData_t;
```

---

## 5. Bit Manipulation — AFE Register Control & CAN Frame

```c
/* AFE (Analog Front End) register config — e.g., LTC6811 */
#define AFE_CFG_GPIO5_EN     (1U << 7U)   /* GPIO 5 enable */
#define AFE_CFG_REFON        (1U << 2U)   /* Reference always on */
#define AFE_CFG_ADCOPT       (1U << 0U)   /* ADC speed option */

/* Build AFE configuration register */
uint8_t build_afe_cfgr0(bool ref_on, bool adc_fast, bool gpio5)
{
    uint8_t reg = 0U;
    if (ref_on)  reg |= AFE_CFG_REFON;
    if (adc_fast) reg |= AFE_CFG_ADCOPT;
    if (gpio5)   reg |= AFE_CFG_GPIO5_EN;
    return reg;
}

/* BMS CAN frame (0x3A0) — pack status
   Byte 0:   SoC [%] (raw × 0.5 = %)
   Byte 1:   Fault level [3:2] | BMS State [1:0]
   Byte 2-3: Pack voltage [dV] (raw × 0.1 = V)
   Byte 4-5: Pack current [dA] signed (raw × 0.1 = A, offset 0)
   Byte 6:   Max cell temp [°C] (raw - 40 = °C)
   Byte 7:   SoH [%] */

void encode_pack_status_frame(uint8_t* frame, const BmsPackData_t* pack)
{
    if (frame == NULL || pack == NULL) return;

    frame[0] = (uint8_t)(pack->soc_pct * 2U);          /* SoC × 2 = raw */

    frame[1] = (uint8_t)((pack->fault_level & 0x03U) << 2U) |
               (uint8_t)(pack->bms_state   & 0x03U);

    uint16_t pack_v_dv = (uint16_t)(pack->pack_voltage_mv / 100U);
    frame[2] = (uint8_t)(pack_v_dv >> 8U);
    frame[3] = (uint8_t)(pack_v_dv & 0xFFU);

    int16_t curr_da = (int16_t)(pack->pack_current_ma / 100);
    frame[4] = (uint8_t)((uint16_t)curr_da >> 8U);
    frame[5] = (uint8_t)((uint16_t)curr_da & 0xFFU);

    int8_t max_temp = get_max_module_temp(pack);
    frame[6] = (uint8_t)(max_temp + 40);

    frame[7] = pack->soh_pct;
}

void decode_pack_status_frame(const uint8_t* frame, BmsPackData_t* out)
{
    if (frame == NULL || out == NULL) return;

    out->soc_pct       = frame[0] / 2U;
    out->fault_level   = (frame[1] >> 2U) & 0x03U;
    out->bms_state     = frame[1] & 0x03U;

    uint16_t v_raw = (uint16_t)((uint16_t)frame[2] << 8U) | frame[3];
    out->pack_voltage_mv = (uint32_t)v_raw * 100U;

    int16_t i_raw = (int16_t)(((uint16_t)frame[4] << 8U) | frame[5]);
    out->pack_current_ma = (int32_t)i_raw * 100;

    out->soh_pct = frame[7];
}
```

---

## 6. Arrays — ADC Sampling & Voltage Matrix

```c
/* Cell voltage raw ADC readings — filled by DMA from AFE SPI */
static volatile uint16_t s_adc_raw[BMS_NUM_MODULES][BMS_CELLS_PER_MODULE];
static cell_voltage_mv_t s_cell_voltage_mv[BMS_NUM_MODULES][BMS_CELLS_PER_MODULE];

/* LTC6811 decoding: raw 16-bit ADC → voltage
   Vx = (Dx × 100µV) - 0V = Dx * 0.0001 V */
void decode_afe_voltages(uint8_t module)
{
    for (uint8_t c = 0U; c < BMS_CELLS_PER_MODULE; ++c) {
        uint16_t raw = s_adc_raw[module][c];
        /* LTC6811 format: 16-bit, 100µV/LSB */
        s_cell_voltage_mv[module][c] = (cell_voltage_mv_t)(raw / 10U);  /* /10 converts 100µV→mV */
    }
}

/* Min/Max/Delta computation */
typedef struct {
    cell_voltage_mv_t max_mv;
    cell_voltage_mv_t min_mv;
    cell_voltage_mv_t delta_mv;
    uint8_t           max_module;
    uint8_t           max_cell;
    uint8_t           min_module;
    uint8_t           min_cell;
} CellStatistics_t;

void compute_cell_statistics(CellStatistics_t* stats)
{
    if (stats == NULL) return;

    stats->max_mv = 0U;
    stats->min_mv = 0xFFFFU;

    for (uint8_t m = 0U; m < BMS_NUM_MODULES; ++m) {
        for (uint8_t c = 0U; c < BMS_CELLS_PER_MODULE; ++c) {
            cell_voltage_mv_t v = s_cell_voltage_mv[m][c];

            if (v > stats->max_mv) {
                stats->max_mv    = v;
                stats->max_module = m;
                stats->max_cell   = c;
            }
            if (v < stats->min_mv) {
                stats->min_mv    = v;
                stats->min_module = m;
                stats->min_cell   = c;
            }
        }
    }
    stats->delta_mv = (stats->max_mv > stats->min_mv)
                    ? (stats->max_mv - stats->min_mv) : 0U;
}

/* Cell balance mask update — passive balancing */
#define BALANCE_THRESHOLD_MV   10U   /* Balance if cell > (min + 10 mV) */

void update_balance_mask(BmsPackData_t* pack, cell_voltage_mv_t min_mv)
{
    for (uint8_t m = 0U; m < BMS_NUM_MODULES; ++m) {
        pack->modules[m].balance_mask = 0U;
        for (uint8_t c = 0U; c < BMS_CELLS_PER_MODULE; ++c) {
            if (pack->modules[m].cells[c].voltage_mv > (min_mv + BALANCE_THRESHOLD_MV)) {
                pack->modules[m].balance_mask |= (uint8_t)(1U << c);
            }
        }
    }
}
```

---

## 7. Control Flow — Contactor State Machine

```c
/* Precharge state machine variables */
typedef struct {
    BmsState_t  state;
    uint32_t    state_entry_ms;
    float       precharge_voltage_v;
    uint8_t     retry_count;
} ContactorFsm_t;

static ContactorFsm_t s_fsm;

#define PRECHARGE_TARGET_PCT      95U
#define PRECHARGE_TIMEOUT_MS    2000U
#define PRECHARGE_RETRY_LIMIT      3U
#define WELD_DETECT_CURRENT_A    0.5f

void contactor_fsm_run_1ms(BmsPackData_t* pack, ContactorFsm_t* fsm)
{
    uint32_t now_ms   = get_system_tick_ms();
    uint32_t elapsed  = now_ms - fsm->state_entry_ms;
    float    bat_v    = (float)pack->pack_voltage_mv / 1000.0f;
    float    dc_link_v = read_dc_link_voltage_v();

    switch (fsm->state) {
        case BMS_STATE_STANDBY:
            if (is_hv_request_active() && pack->fault_level == 0U) {
                set_contactor(MAIN_NEGATIVE, true);
                fsm->state          = BMS_STATE_PRECHARGE;
                fsm->state_entry_ms = now_ms;
            }
            break;

        case BMS_STATE_PRECHARGE:
            /* Precharge complete when DC link ≥ 95% of battery voltage */
            fsm->precharge_voltage_v = dc_link_v;
            if (dc_link_v >= (bat_v * (float)PRECHARGE_TARGET_PCT / 100.0f)) {
                /* Close main positive, open precharge */
                set_contactor(MAIN_POSITIVE, true);
                vTaskDelay_ms(10U);    /* Small settling delay */
                set_contactor(PRECHARGE, false);
                fsm->state          = BMS_STATE_HV_READY;
                fsm->state_entry_ms = now_ms;
            } else if (elapsed > PRECHARGE_TIMEOUT_MS) {
                /* Timeout */
                open_all_contactors();
                report_dtc(DTC_PRECHARGE_TIMEOUT, pack, now_ms);
                if (++fsm->retry_count < PRECHARGE_RETRY_LIMIT) {
                    fsm->state = BMS_STATE_STANDBY;
                } else {
                    fsm->state = BMS_STATE_FAULT;
                }
                fsm->state_entry_ms = now_ms;
            }
            break;

        case BMS_STATE_HV_READY:
        case BMS_STATE_DRIVING:
            /* Monitor for weld: after opening main positive,
               if current > 0.5A residual → weld detected */
            if (pack->fault_level >= 3U) {
                open_all_contactors();
                fsm->state = BMS_STATE_FAULT;
            }
            break;

        case BMS_STATE_FAULT:
            /* Locked out until cleared by diagnostic */
            all_contactors_open_safety();
            break;

        default:
            break;
    }
}
```

---

## 8. SoC: Coulomb Counting in C

```c
/* SoC estimation via Coulomb Counting (CC)
   SoC[k] = SoC[k-1] - (I × dt × η) / Q_nominal

   I       = pack current [A] (positive = discharge)
   dt      = sampling interval [s]
   η       = Coulombic efficiency (charge: 0.98, discharge: 1.0)
   Q_nom   = nominal capacity [Ah]
*/

#define SOC_DT_S            (0.001f)   /* 1ms sampling */
#define SOC_ETA_CHARGE      (0.98f)
#define SOC_ETA_DISCHARGE   (1.00f)
#define SOC_NOMINAL_AH      (60.0f)
#define SOC_NOMINAL_AS      (SOC_NOMINAL_AH * 3600.0f)  /* 216000 As */

static float s_soc_fraction = 1.0f;   /* 0.0–1.0 */
static float s_accumulated_as = 0.0f; /* Coulombs discharged from full */

void soc_update_coulomb(float current_a)
{
    float eta = (current_a > 0.0f) ? SOC_ETA_DISCHARGE : SOC_ETA_CHARGE;
    float delta_as = current_a * SOC_DT_S * eta;

    s_accumulated_as += delta_as;

    /* Clamp accumulated charge */
    if (s_accumulated_as < 0.0f)              s_accumulated_as = 0.0f;
    if (s_accumulated_as > SOC_NOMINAL_AS)    s_accumulated_as = SOC_NOMINAL_AS;

    s_soc_fraction = 1.0f - (s_accumulated_as / SOC_NOMINAL_AS);

    /* Clamp SoC */
    if (s_soc_fraction < 0.0f) s_soc_fraction = 0.0f;
    if (s_soc_fraction > 1.0f) s_soc_fraction = 1.0f;
}

uint8_t soc_get_percent(void)
{
    return (uint8_t)(s_soc_fraction * 100.0f);
}

/* OCV-SoC initialisation at power-on (rest state) */
typedef struct { float ocv_v; float soc_frac; } OcvSocPoint_t;

/* NMC OCV-SoC lookup table */
static const OcvSocPoint_t k_ocv_soc_table[] = {
    {4.20f, 1.00f}, {4.15f, 0.95f}, {4.10f, 0.90f},
    {4.00f, 0.80f}, {3.90f, 0.70f}, {3.80f, 0.60f},
    {3.70f, 0.50f}, {3.60f, 0.40f}, {3.50f, 0.30f},
    {3.40f, 0.20f}, {3.30f, 0.10f}, {3.10f, 0.05f},
    {2.80f, 0.00f}
};
#define OCV_TABLE_SIZE (sizeof(k_ocv_soc_table) / sizeof(k_ocv_soc_table[0]))

float soc_from_ocv(float ocv_v)
{
    /* Linear interpolation in OCV-SoC table */
    for (uint8_t i = 0U; i < (OCV_TABLE_SIZE - 1U); ++i) {
        if (ocv_v <= k_ocv_soc_table[i].ocv_v &&
            ocv_v >= k_ocv_soc_table[i+1U].ocv_v) {
            float span_v   = k_ocv_soc_table[i].ocv_v   - k_ocv_soc_table[i+1U].ocv_v;
            float span_soc = k_ocv_soc_table[i].soc_frac - k_ocv_soc_table[i+1U].soc_frac;
            if (span_v < 1e-6f) return k_ocv_soc_table[i].soc_frac;
            float ratio = (ocv_v - k_ocv_soc_table[i+1U].ocv_v) / span_v;
            return k_ocv_soc_table[i+1U].soc_frac + ratio * span_soc;
        }
    }
    if (ocv_v >= k_ocv_soc_table[0].ocv_v) return k_ocv_soc_table[0].soc_frac;
    return 0.0f;
}
```

---

## 9. ISR — AFE SPI DMA & Current Sensor

```c
/* AFE SPI DMA complete ISR — cell voltage conversion done */
static volatile bool    g_afe_data_ready = false;
static volatile uint8_t g_afe_module_idx = 0U;

void DMA2_Stream3_IRQHandler(void)
{
    if (DMA2->LISR & DMA_LISR_TCIF3) {
        DMA2->LIFCR = DMA_LIFCR_CTCIF3;
        g_afe_data_ready = true;     /* Signal main task */
    }
}

/* High-rate current ADC ISR (100 µs) — critical for Coulomb counting */
static volatile int32_t g_current_raw_sum = 0L;
static volatile uint16_t g_current_sample_count = 0U;

void TIM6_DAC_IRQHandler(void)
{
    TIM6->SR &= ~TIM_SR_UIF;  /* Clear flag */

    /* Read current ADC */
    int16_t adc_raw = (int16_t)ADC1->DR;
    /* Hall sensor: midpoint = 2048 (0A), sensitivity = 66 mV/A */
    /* At 3.3V ref, 4096 counts: 1 count = 0.806 mV → 0.012 A */
    g_current_raw_sum   += (int32_t)adc_raw - 2048L;
    g_current_sample_count++;

    if (g_current_sample_count >= 10U) {
        /* Average 10 samples (= 1ms at 100µs ISR rate) */
        float avg_a = (float)g_current_raw_sum / 10.0f * 0.012f;
        soc_update_coulomb(avg_a);
        g_current_raw_sum      = 0L;
        g_current_sample_count = 0U;
    }
}
```

---

## 10. UDS in C — Service 0x22 (RDBI) Handler

```c
/* ISO 14229 ReadDataByIdentifier handler */
typedef struct {
    uint16_t did;
    uint8_t (*encode_fn)(uint8_t* resp_data, uint8_t max_len);
} DidEntry_t;

static uint8_t encode_soc(uint8_t* d, uint8_t max) {
    if (max < 1U) return 0U;
    d[0] = soc_get_percent() * 2U;   /* Resolution 0.5% */
    return 1U;
}

static uint8_t encode_pack_voltage(uint8_t* d, uint8_t max) {
    if (max < 2U) return 0U;
    uint16_t v_dv = (uint16_t)(get_pack_voltage_mv() / 100U);
    d[0] = (uint8_t)(v_dv >> 8U);
    d[1] = (uint8_t)(v_dv & 0xFFU);
    return 2U;
}

static const DidEntry_t k_did_table[] = {
    {0xF190U, encode_soc},
    {0xF192U, encode_pack_voltage},
    /* ... */
};

#define DID_TABLE_SIZE (sizeof(k_did_table) / sizeof(k_did_table[0]))

/* Return: response length, 0 = NRC */
uint8_t uds_handle_rdbi(const uint8_t* req, uint8_t req_len,
                         uint8_t* resp, uint8_t max_resp)
{
    if (req == NULL || resp == NULL || req_len < 3U || max_resp < 4U) return 0U;

    uint16_t did = (uint16_t)((uint16_t)req[1] << 8U) | req[2];

    for (uint8_t i = 0U; i < DID_TABLE_SIZE; ++i) {
        if (k_did_table[i].did == did) {
            resp[0] = 0x62U;   /* Positive response */
            resp[1] = req[1];
            resp[2] = req[2];
            uint8_t data_len = k_did_table[i].encode_fn(&resp[3], max_resp - 3U);
            if (data_len == 0U) {
                resp[0] = 0x7FU; resp[1] = 0x22U; resp[2] = 0x22U; /* conditionsNotCorrect */
                return 3U;
            }
            return 3U + data_len;
        }
    }

    /* DID not found */
    resp[0] = 0x7FU; resp[1] = 0x22U; resp[2] = 0x31U;  /* requestOutOfRange */
    return 3U;
}
```

---

*File: 01_c_fundamentals_bms.md | c_cpp_bms learning series*
