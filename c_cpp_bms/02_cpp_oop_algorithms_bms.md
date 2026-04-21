# C++ OOP and Algorithms for BMS Engineering

> **Domain:** Battery Management System — EV / HEV / PHEV
> **Focus:** C++ class design, EKF SoC estimation, Strategy/Observer/FSM patterns, unit testing
> **Standards:** MISRA C++ 2008, AUTOSAR C++14, ISO 26262 Part 6

---

## 1. OOP Approach in BMS

```
BMS Software Structure
├── HAL layer             → C ISRs, DMA, SPI, ADC
├── Algorithm layer       → C++ classes (SoC, SoH, Balancing)
├── Application layer     → C++ FSMs, Fault Manager
├── Diagnostic layer      → C++ UDS server
└── Communication layer   → C++ CAN codec, AUTOSAR PDUs
```

---

## 2. Abstract Base — BMS Algorithm Interface

```cpp
#include <cstdint>
#include <cmath>

/**
 * @brief Abstract BMS estimation algorithm interface
 *        Supports Strategy Pattern — swap algorithms without changing BmsMonitor
 */
class IBmsAlgorithm {
public:
    virtual ~IBmsAlgorithm() = default;

    /**
     * @brief Update algorithm with latest measurements
     * @param current_a  Pack current [A] (positive = discharge)
     * @param voltage_v  Cell/pack voltage [V]
     * @param temp_c     Temperature [°C]
     * @param dt_s       Time step [s]
     */
    virtual void update(float current_a, float voltage_v,
                        float temp_c, float dt_s) noexcept = 0;

    /** @return SoC estimate [0.0, 1.0] */
    virtual float get_soc() const noexcept = 0;

    /** @return Estimation uncertainty (variance) */
    virtual float get_uncertainty() const noexcept = 0;

    /** @brief Reset to initial state (called at power-on with OCV) */
    virtual void reset(float initial_soc) noexcept = 0;
};
```

---

## 3. Strategy 1 — Coulomb Counting SoC

```cpp
class CoulombCountingSoC final : public IBmsAlgorithm {
public:
    explicit CoulombCountingSoC(float nominal_capacity_ah,
                                 float eta_charge    = 0.98f,
                                 float eta_discharge = 1.00f)
        : m_q_nominal_as(nominal_capacity_ah * 3600.0f)
        , m_eta_charge(eta_charge)
        , m_eta_discharge(eta_discharge)
        , m_soc(1.0f)
        , m_accumulated_as(0.0f)
    {}

    void update(float current_a, float /*voltage_v*/,
                float /*temp_c*/,  float dt_s) noexcept override
    {
        float eta     = (current_a > 0.0f) ? m_eta_discharge : m_eta_charge;
        float delta   = current_a * dt_s * eta;
        m_accumulated_as += delta;
        m_accumulated_as = clamp(m_accumulated_as, 0.0f, m_q_nominal_as);
        m_soc = 1.0f - (m_accumulated_as / m_q_nominal_as);
        m_soc = clamp(m_soc, 0.0f, 1.0f);
    }

    float get_soc()         const noexcept override { return m_soc; }
    float get_uncertainty() const noexcept override { return m_drift_variance; }

    void reset(float initial_soc) noexcept override {
        m_soc            = clamp(initial_soc, 0.0f, 1.0f);
        m_accumulated_as = (1.0f - m_soc) * m_q_nominal_as;
        m_drift_variance  = 0.0025f;  /* initial uncertainty 5% std dev */
    }

private:
    static float clamp(float v, float lo, float hi) noexcept {
        return (v < lo) ? lo : (v > hi) ? hi : v;
    }

    const float m_q_nominal_as;
    const float m_eta_charge;
    const float m_eta_discharge;
    float       m_soc;
    float       m_accumulated_as;
    float       m_drift_variance{0.0025f};  /* grows over time without correction */
};
```

---

## 4. Strategy 2 — Extended Kalman Filter SoC

```cpp
/**
 * @brief EKF-based SoC estimator using Thevenin equivalent circuit model
 *
 * State vector: x = [SoC, V_RC]
 *   SoC  = State of Charge [0..1]
 *   V_RC = Voltage across polarization RC element [V]
 *
 * Measurement: y = terminal voltage V_t
 *
 * Battery model:
 *   V_t = OCV(SoC) - I*R0 - V_RC
 *   dV_RC/dt = -V_RC / (R1*C1) + I/C1
 *
 * Discrete-time (Euler):
 *   SoC[k]  = SoC[k-1]  - (eta * I * dt) / Q_nom
 *   V_RC[k] = V_RC[k-1] * exp(-dt / tau) + I * R1 * (1 - exp(-dt/tau))
 *
 * Observation:
 *   y[k] = OCV(SoC[k]) - I[k]*R0 - V_RC[k]
 */
class EkfSoC final : public IBmsAlgorithm {
public:
    struct Params {
        float q_nominal_ah{60.0f};
        float eta{0.99f};          /* Coulombic efficiency */
        float R0{0.002f};          /* Ohmic resistance [Ω] */
        float R1{0.001f};          /* Polarisation resistance [Ω] */
        float C1{3000.0f};         /* Polarisation capacitance [F] */
        float Q_soc{1e-6f};        /* Process noise: SoC */
        float Q_vrc{1e-4f};        /* Process noise: V_RC */
        float R_meas{1e-4f};       /* Measurement noise [V²] */
    };

    explicit EkfSoC(const Params& p = {})
        : m_p(p)
        , m_tau(p.R1 * p.C1)
        , m_q_as(p.q_nominal_ah * 3600.0f)
    {
        reset(1.0f);
    }

    void reset(float initial_soc) noexcept override
    {
        m_x[0] = clamp(initial_soc, 0.0f, 1.0f);
        m_x[1] = 0.0f;
        /* P = diag(0.01, 0.001) */
        m_P[0][0] = 0.01f;  m_P[0][1] = 0.0f;
        m_P[1][0] = 0.0f;   m_P[1][1] = 0.001f;
    }

    void update(float current_a, float voltage_v,
                float /*temp_c*/, float dt_s) noexcept override
    {
        /* ---- PREDICT ---- */
        float soc_pred  = m_x[0] - (m_p.eta * current_a * dt_s) / m_q_as;
        float vrc_decay = expf(-dt_s / m_tau);
        float vrc_pred  = m_x[1] * vrc_decay
                        + current_a * m_p.R1 * (1.0f - vrc_decay);

        soc_pred = clamp(soc_pred, 0.0f, 1.0f);

        /* State Jacobian F = [[1, 0], [0, exp(-dt/tau)]] (linear model) */
        /* P_pred = F * P * F^T + Q */
        m_P[0][0] += m_p.Q_soc;
        m_P[1][1] = m_P[1][1] * vrc_decay * vrc_decay + m_p.Q_vrc;
        /* Off-diagonals vanish because F is diagonal */
        m_P[0][1] = m_P[1][0] = 0.0f;

        /* ---- UPDATE ---- */
        /* Measurement prediction */
        float ocv_pred = ocv_from_soc(soc_pred);
        float y_pred   = ocv_pred - current_a * m_p.R0 - vrc_pred;
        float y_err    = voltage_v - y_pred;

        /* Observation Jacobian H = [dOCV/dSoC, -1] at soc_pred */
        float h0 = docv_dsoc(soc_pred);   /* ≈ 0.8 V for NMC */
        float h1 = -1.0f;

        /* Innovation covariance S = H * P * H^T + R */
        float S = h0*h0 * m_P[0][0] + 2.0f*h0*h1 * m_P[0][1]
                + h1*h1 * m_P[1][1] + m_p.R_meas;
        if (S < 1e-8f) S = 1e-8f;   /* Numerical guard */

        /* Kalman gain K = P * H^T / S */
        float K0 = (h0 * m_P[0][0] + h1 * m_P[0][1]) / S;
        float K1 = (h0 * m_P[1][0] + h1 * m_P[1][1]) / S;

        /* Update state */
        m_x[0] = clamp(soc_pred + K0 * y_err, 0.0f, 1.0f);
        m_x[1] = vrc_pred + K1 * y_err;

        /* Update covariance P = (I - K*H) * P_pred */
        float IKH00 = 1.0f - K0 * h0;
        float IKH01 =       -K0 * h1;
        float IKH10 =       -K1 * h0;
        float IKH11 = 1.0f - K1 * h1;

        float P00 = IKH00 * m_P[0][0] + IKH01 * m_P[1][0];
        float P01 = IKH00 * m_P[0][1] + IKH01 * m_P[1][1];
        float P10 = IKH10 * m_P[0][0] + IKH11 * m_P[1][0];
        float P11 = IKH10 * m_P[0][1] + IKH11 * m_P[1][1];

        m_P[0][0] = P00;  m_P[0][1] = P01;
        m_P[1][0] = P10;  m_P[1][1] = P11;
    }

    float get_soc()         const noexcept override { return m_x[0]; }
    float get_uncertainty() const noexcept override { return m_P[0][0]; }

private:
    /* OCV-SoC polynomial fit (NMC): coefficients from datasheet characterisation */
    static float ocv_from_soc(float soc) noexcept {
        /* 5th-order polynomial: OCV = a5*s^5 + ... + a0 */
        const float a[] = {-20.0f, 69.0f, -89.5f, 57.0f, -17.5f, 4.00f + 2.80f};
        float s = soc, s2 = s*s, s3 = s2*s, s4 = s3*s, s5 = s4*s;
        return a[0]*s5 + a[1]*s4 + a[2]*s3 + a[3]*s2 + a[4]*s + a[5];
    }

    static float docv_dsoc(float soc) noexcept {
        /* Derivative of OCV polynomial */
        const float a[] = {-20.0f, 69.0f, -89.5f, 57.0f, -17.5f};
        float s=soc, s2=s*s, s3=s2*s, s4=s3*s;
        return 5.0f*a[0]*s4 + 4.0f*a[1]*s3 + 3.0f*a[2]*s2 + 2.0f*a[3]*s + a[4];
    }

    static float clamp(float v, float lo, float hi) noexcept {
        return (v < lo) ? lo : (v > hi) ? hi : v;
    }

    const Params m_p;
    const float  m_tau;
    const float  m_q_as;
    float        m_x[2]{1.0f, 0.0f};   /* [SoC, V_RC] */
    float        m_P[2][2]{};
};
```

---

## 5. BmsMonitor — Central Class (Observer Pattern)

```cpp
#include <array>
#include <functional>

class IBmsConsumer {
public:
    virtual ~IBmsConsumer() = default;
    virtual void on_bms_update(float soc, uint8_t fault_level) noexcept = 0;
};

class BmsMonitor {
public:
    static constexpr uint8_t NUM_MODULES      = 12U;
    static constexpr uint8_t CELLS_PER_MODULE = 8U;
    static constexpr uint8_t TOTAL_CELLS      = NUM_MODULES * CELLS_PER_MODULE;
    static constexpr uint8_t MAX_CONSUMERS    = 4U;

    explicit BmsMonitor(IBmsAlgorithm& soc_algo) : m_algo(soc_algo) {}

    /* Inject new cell voltages from AFE driver */
    void set_cell_voltages(const std::array<uint16_t, TOTAL_CELLS>& mv_array)
    {
        m_cell_voltages_mv = mv_array;
        check_voltage_faults();
    }

    void set_pack_current_a(float i_a)    noexcept { m_current_a = i_a; }
    void set_pack_voltage_v(float v_v)     noexcept { m_pack_voltage_v = v_v; }
    void set_cell_temperature_c(float t)   noexcept { m_temp_c = t; }

    /** @brief Called at fixed interval (e.g., 10ms) by RTOS task */
    void run_10ms(float dt_s = 0.010f)
    {
        m_algo.update(m_current_a, m_pack_voltage_v, m_temp_c, dt_s);
        m_soc = m_algo.get_soc();
        notify_consumers();
    }

    float   get_soc()         const noexcept { return m_soc; }
    uint8_t get_fault_level() const noexcept { return m_fault_level; }

    bool register_consumer(IBmsConsumer* c)
    {
        for (auto& slot : m_consumers) {
            if (slot == nullptr) { slot = c; return true; }
        }
        return false;  /* Full */
    }

private:
    void check_voltage_faults()
    {
        m_fault_level = 0U;
        for (auto& v : m_cell_voltages_mv) {
            if (v >= 4250U || v <= 2800U) { m_fault_level = 3U; return; }
            if (v >= 4200U || v <= 3000U) { m_fault_level = std::max(m_fault_level, uint8_t{1U}); }
        }
    }

    void notify_consumers()
    {
        for (auto* c : m_consumers) {
            if (c != nullptr) c->on_bms_update(m_soc, m_fault_level);
        }
    }

    IBmsAlgorithm&                        m_algo;
    std::array<uint16_t, TOTAL_CELLS>     m_cell_voltages_mv{};
    std::array<IBmsConsumer*, MAX_CONSUMERS> m_consumers{};

    float   m_current_a{0.0f};
    float   m_pack_voltage_v{0.0f};
    float   m_temp_c{25.0f};
    float   m_soc{1.0f};
    uint8_t m_fault_level{0U};
};
```

---

## 6. Contactor FSM — Class-Based

```cpp
class ContactorFsm {
public:
    enum class State : uint8_t {
        STANDBY    = 0,
        MAIN_NEG   = 1,
        PRECHARGE  = 2,
        MAIN_POS   = 3,
        HV_READY   = 4,
        OPENING    = 5,
        FAULT      = 6
    };

    struct Io {
        std::function<void(bool)> main_neg;
        std::function<void(bool)> main_pos;
        std::function<void(bool)> precharge;
        std::function<float()>    read_dc_link_v;
        std::function<float()>    read_battery_v;
        std::function<void(uint32_t)> report_dtc;
    };

    explicit ContactorFsm(Io io,
                           float precharge_pct = 0.95f,
                           uint32_t timeout_ms = 2000U)
        : m_io(std::move(io))
        , m_precharge_pct(precharge_pct)
        , m_timeout_ms(timeout_ms)
    {}

    void request_hv_on()  noexcept { m_hv_request = true;  }
    void request_hv_off() noexcept { m_hv_request = false; }

    void run(uint32_t now_ms)
    {
        uint32_t elapsed = now_ms - m_entry_ms;

        switch (m_state) {
            case State::STANDBY:
                if (m_hv_request) {
                    m_io.main_neg(true);
                    transition(State::PRECHARGE, now_ms);
                }
                break;

            case State::PRECHARGE: {
                float bat_v    = m_io.read_battery_v();
                float dc_link  = m_io.read_dc_link_v();
                if (dc_link >= bat_v * m_precharge_pct) {
                    m_io.main_pos(true);
                    m_io.precharge(false);
                    transition(State::HV_READY, now_ms);
                } else if (elapsed > m_timeout_ms) {
                    m_io.report_dtc(0xD00701UL);   /* Precharge timeout DTC */
                    open_all();
                    transition(State::FAULT, now_ms);
                }
                break;
            }

            case State::HV_READY:
                if (!m_hv_request) {
                    transition(State::OPENING, now_ms);
                }
                break;

            case State::OPENING:
                m_io.main_pos(false);
                m_io.main_neg(false);
                transition(State::STANDBY, now_ms);
                break;

            case State::FAULT:
                open_all();   /* Continuously hold open */
                break;

            default: break;
        }
    }

    State get_state() const noexcept { return m_state; }
    void  clear_fault() noexcept { if (m_state == State::FAULT) transition(State::STANDBY, 0U); }

private:
    void transition(State s, uint32_t now_ms) noexcept {
        m_state    = s;
        m_entry_ms = now_ms;
    }
    void open_all() {
        m_io.main_pos(false);
        m_io.precharge(false);
        m_io.main_neg(false);
    }

    Io       m_io;
    State    m_state{State::STANDBY};
    uint32_t m_entry_ms{0U};
    bool     m_hv_request{false};
    float    m_precharge_pct;
    uint32_t m_timeout_ms;
};
```

---

## 7. Cell Balancer — Passive Balancing Manager

```cpp
class CellBalancer {
public:
    static constexpr uint8_t TOTAL_CELLS      = 96U;
    static constexpr uint8_t CELLS_PER_MODULE = 8U;
    static constexpr uint16_t BALANCE_THRESHOLD_MV = 10U;
    static constexpr uint16_t MIN_BALANCE_VOLTAGE_MV = 3300U;  /* Don't balance below 3.3V */

    struct BalanceCommand {
        uint8_t module;
        uint8_t balance_mask;   /* Bit n = cell n should discharge */
    };

    /**
     * @brief Compute balance commands from cell voltages
     * @param voltages  96-element array of cell voltages [mV]
     * @param cmds_out  Output commands (one per module)
     * @return Number of cells currently balancing
     */
    uint8_t compute(const std::array<uint16_t, TOTAL_CELLS>& voltages,
                    std::array<BalanceCommand, 12U>&           cmds_out)
    {
        /* Find global minimum */
        uint16_t min_v = *std::min_element(voltages.begin(), voltages.end());
        uint8_t  active = 0U;

        for (uint8_t m = 0U; m < 12U; ++m) {
            cmds_out[m].module       = m;
            cmds_out[m].balance_mask = 0U;

            for (uint8_t c = 0U; c < CELLS_PER_MODULE; ++c) {
                uint16_t v = voltages[m * CELLS_PER_MODULE + c];
                if (v >= MIN_BALANCE_VOLTAGE_MV &&
                    v > (min_v + BALANCE_THRESHOLD_MV)) {
                    cmds_out[m].balance_mask |= static_cast<uint8_t>(1U << c);
                    ++active;
                }
            }
        }
        return active;
    }
};
```

---

## 8. Fault Manager — Observer Pattern with DTC Ring Buffer

```cpp
#include <array>
#include <cstdint>

struct Dtc {
    uint32_t code;
    uint8_t  status;      /* 0x01=active, 0x02=pending, 0x04=confirmed */
    uint8_t  occurrences;
    uint32_t first_ts_ms;
    uint32_t last_ts_ms;
};

class IDtcObserver {
public:
    virtual ~IDtcObserver() = default;
    virtual void on_dtc_set(const Dtc& dtc) noexcept = 0;
    virtual void on_dtc_cleared(uint32_t code) noexcept = 0;
};

class FaultManager {
public:
    static constexpr uint8_t MAX_DTCS     = 32U;
    static constexpr uint8_t MAX_OBSERVERS = 4U;

    bool set_dtc(uint32_t code, uint8_t status, uint32_t ts_ms)
    {
        /* Check if already present */
        for (auto& d : m_dtcs) {
            if (d.code == code) {
                d.status   = status;
                d.last_ts_ms = ts_ms;
                ++d.occurrences;
                notify_set(d);
                return true;
            }
        }
        /* New DTC — find free slot */
        for (auto& d : m_dtcs) {
            if (d.code == 0U) {
                d = {code, status, 1U, ts_ms, ts_ms};
                notify_set(d);
                return true;
            }
        }
        return false;   /* Buffer full */
    }

    void clear_dtc(uint32_t code) {
        for (auto& d : m_dtcs) {
            if (d.code == code) {
                notify_cleared(code);
                d = {};
            }
        }
    }

    void clear_all() {
        for (auto& d : m_dtcs) { if (d.code != 0U) notify_cleared(d.code); }
        m_dtcs.fill({});
    }

    bool add_observer(IDtcObserver* obs) {
        for (auto& slot : m_observers) {
            if (slot == nullptr) { slot = obs; return true; }
        }
        return false;
    }

    const std::array<Dtc, MAX_DTCS>& get_all_dtcs() const { return m_dtcs; }

private:
    void notify_set(const Dtc& d) {
        for (auto* o : m_observers) if (o) o->on_dtc_set(d);
    }
    void notify_cleared(uint32_t code) {
        for (auto* o : m_observers) if (o) o->on_dtc_cleared(code);
    }

    std::array<Dtc, MAX_DTCS>               m_dtcs{};
    std::array<IDtcObserver*, MAX_OBSERVERS> m_observers{};
};
```

---

## 9. SoH Estimation — Capacity Fade Tracker

```cpp
class SohEstimator {
public:
    explicit SohEstimator(float nominal_ah = 60.0f)
        : m_nominal_ah(nominal_ah) {}

    /**
     * @brief Signal start of charge event (current becomes negative)
     * @param soc_at_start  SoC when charging began [0..1]
     */
    void on_charge_start(float soc_at_start, uint32_t ts_ms) noexcept {
        m_soc_start  = soc_at_start;
        m_ah_start   = m_ah_acc;
        m_charge_started = true;
        m_start_ts_ms = ts_ms;
        (void)ts_ms;
    }

    /**
     * @brief Signal end of charge (current ~0 near full SoC)
     */
    void on_charge_end(float soc_at_end, uint32_t /*ts_ms*/) noexcept {
        if (!m_charge_started) return;
        float delta_soc = soc_at_end - m_soc_start;
        float delta_ah  = m_ah_acc - m_ah_start;

        if (delta_soc > 0.05f && delta_ah > 1.0f) {
            float measured_cap_ah = delta_ah / delta_soc;
            /* Exponential moving average to smooth SoH */
            m_capacity_ah = 0.9f * m_capacity_ah + 0.1f * measured_cap_ah;
            m_soh         = m_capacity_ah / m_nominal_ah;
            if (m_soh > 1.0f) m_soh = 1.0f;
        }
        m_charge_started = false;
    }

    /** @brief Accumulate Ah (call every 10ms) */
    void integrate_ah(float current_a, float dt_s) noexcept {
        m_ah_acc += (current_a < 0.0f) ? (-current_a * dt_s / 3600.0f) : 0.0f;
    }

    float get_soh_fraction() const noexcept { return m_soh; }
    float get_capacity_ah()  const noexcept { return m_capacity_ah; }

private:
    const float m_nominal_ah;
    float       m_capacity_ah{60.0f};
    float       m_soh{1.0f};
    float       m_ah_acc{0.0f};
    float       m_soc_start{0.0f};
    float       m_ah_start{0.0f};
    uint32_t    m_start_ts_ms{0U};
    bool        m_charge_started{false};
};
```

---

## 10. Google Test — BMS Algorithms

```cpp
#include <gtest/gtest.h>
#include <gmock/gmock.h>

/* ---- Coulomb Counting Tests ---- */
TEST(CoulombCountingSoC, InitialSocIsOne) {
    CoulombCountingSoC cc(60.0f);
    cc.reset(1.0f);
    EXPECT_FLOAT_EQ(cc.get_soc(), 1.0f);
}

TEST(CoulombCountingSoC, DischargesCorrectly) {
    CoulombCountingSoC cc(60.0f);   /* 60 Ah */
    cc.reset(1.0f);
    /* 60 A for 3600 s = 60 Ah → SoC = 0 */
    for (int i = 0; i < 360000; ++i) {
        cc.update(60.0f, 0.0f, 25.0f, 0.010f);
    }
    EXPECT_NEAR(cc.get_soc(), 0.0f, 0.01f);
}

TEST(CoulombCountingSoC, ClampedAtZero) {
    CoulombCountingSoC cc(60.0f);
    cc.reset(0.0f);
    cc.update(100.0f, 0.0f, 25.0f, 10.0f);   /* Big discharge */
    EXPECT_GE(cc.get_soc(), 0.0f);
}

/* ---- EKF SoC Tests ---- */
TEST(EkfSoC, ConvergesFromPoorInitialisation) {
    EkfSoC::Params p;
    EkfSoC ekf(p);
    ekf.reset(0.5f);   /* Wrong initial guess; true SoC = 0.80 */

    /* Simulate 60 seconds at rest with correct OCV */
    /* OCV at 80% ≈ 3.98V */
    for (int i = 0; i < 6000; ++i) {
        ekf.update(0.0f, 3.98f, 25.0f, 0.010f);
    }
    EXPECT_NEAR(ekf.get_soc(), 0.80f, 0.05f);
}

/* ---- ContactorFsm Tests ---- */
class MockContactorIo {
public:
    bool main_neg_state{false};
    bool main_pos_state{false};
    bool precharge_state{false};
    float battery_v{400.0f};
    float dc_link_v{0.0f};
    uint32_t reported_dtc{0U};

    ContactorFsm::Io make_io() {
        return {
            [this](bool s){ main_neg_state = s; },
            [this](bool s){ main_pos_state = s; },
            [this](bool s){ precharge_state = s; },
            [this]() { return dc_link_v; },
            [this]() { return battery_v; },
            [this](uint32_t dtc){ reported_dtc = dtc; }
        };
    }
};

TEST(ContactorFsm, PrechargeCompletes) {
    MockContactorIo io_mock;
    ContactorFsm fsm(io_mock.make_io(), 0.95f, 2000U);

    fsm.request_hv_on();
    fsm.run(0U);    /* → PRECHARGE */
    EXPECT_EQ(fsm.get_state(), ContactorFsm::State::PRECHARGE);

    io_mock.dc_link_v = 382.0f;  /* 95.5% of 400V */
    fsm.run(100U);   /* → HV_READY */
    EXPECT_EQ(fsm.get_state(), ContactorFsm::State::HV_READY);
    EXPECT_TRUE(io_mock.main_pos_state);
    EXPECT_FALSE(io_mock.precharge_state);
}

TEST(ContactorFsm, PrechargeTimeout_SetsDtc) {
    MockContactorIo io_mock;
    ContactorFsm fsm(io_mock.make_io(), 0.95f, 2000U);
    fsm.request_hv_on();
    fsm.run(0U);
    io_mock.dc_link_v = 100.0f;   /* Stuck low */
    fsm.run(3000U);   /* Elapsed 3000ms > 2000ms timeout */
    EXPECT_EQ(fsm.get_state(), ContactorFsm::State::FAULT);
    EXPECT_EQ(io_mock.reported_dtc, 0xD00701UL);
}

/* ---- Fault Manager Tests ---- */
class MockDtcObserver : public IDtcObserver {
public:
    MOCK_METHOD(void, on_dtc_set,     (const Dtc&), (noexcept, override));
    MOCK_METHOD(void, on_dtc_cleared, (uint32_t),   (noexcept, override));
};

TEST(FaultManager, SetAndObserveDtc) {
    FaultManager fm;
    MockDtcObserver obs;
    fm.add_observer(&obs);

    EXPECT_CALL(obs, on_dtc_set(testing::_)).Times(1);
    fm.set_dtc(0xD00101UL, 0x01U, 1000U);
}
```

---

*File: 02_cpp_oop_algorithms_bms.md | c_cpp_bms learning series*
