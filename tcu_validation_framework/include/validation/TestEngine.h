/**
 * @file TestEngine.h
 * @brief TCU Validation Engine — automated test execution framework.
 *
 * Provides:
 *   - Test case registration and parameterisation
 *   - Sequential and parallel execution modes
 *   - Timeout handling per test case
 *   - Retry logic for flaky tests
 *   - Pass/Fail/Skip/Error verdict management
 *   - Pre/post condition hooks
 *   - Fault injection integration
 *   - Live result streaming to registered listeners
 */

#pragma once

#include <atomic>
#include <chrono>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <thread>
#include <vector>
#include <optional>

namespace tcu::validation {

// ============================================================
// Verdict
// ============================================================

enum class Verdict : uint8_t {
    NOT_RUN = 0,
    PASS,
    FAIL,
    ERROR,
    SKIP,
    TIMEOUT,
};

inline const char* to_string(Verdict v) noexcept {
    switch (v) {
        case Verdict::NOT_RUN: return "NOT_RUN";
        case Verdict::PASS:    return "PASS";
        case Verdict::FAIL:    return "FAIL";
        case Verdict::ERROR:   return "ERROR";
        case Verdict::SKIP:    return "SKIP";
        case Verdict::TIMEOUT: return "TIMEOUT";
        default:               return "UNKNOWN";
    }
}

// ============================================================
// Test Case
// ============================================================

/**
 * @brief Individual test case definition.
 */
struct TestCase {
    std::string  id;                    ///< Unique test ID (e.g. "TC-OTA-001")
    std::string  name;                  ///< Human-readable title
    std::string  description;           ///< What the test verifies
    std::string  requirement_id;        ///< Linked requirement (JIRA/DOORS ID)
    uint32_t     timeout_ms{5000};      ///< Per-test timeout (ms)
    uint8_t      max_retries{0};        ///< Retry count on FAIL/TIMEOUT (0 = no retry)
    bool         is_critical{false};    ///< If true, engine stops on FAIL
    bool         enabled{true};         ///< Skip if false

    std::function<bool()>  precondition;  ///< Optional: returns false → SKIP
    std::function<Verdict()> execute;     ///< Required: main test body
    std::function<void()>  cleanup;       ///< Optional: post-test cleanup
};

// ============================================================
// Test Result
// ============================================================

/**
 * @brief Execution result for one test case.
 */
struct TestResult {
    std::string  test_id;
    std::string  test_name;
    Verdict      verdict{Verdict::NOT_RUN};
    std::string  message;               ///< Pass/fail message or exception text
    uint32_t     duration_ms{0};
    uint8_t      retry_count{0};
    std::string  timestamp;             ///< ISO 8601 UTC timestamp
};

// ============================================================
// Suite Result
// ============================================================

/**
 * @brief Aggregate result for a test suite run.
 */
struct SuiteResult {
    std::string suite_name;
    std::vector<TestResult> results;
    uint32_t    total{0};
    uint32_t    passed{0};
    uint32_t    failed{0};
    uint32_t    errors{0};
    uint32_t    skipped{0};
    uint32_t    timeouts{0};
    uint32_t    total_duration_ms{0};
    double      pass_rate{0.0};         ///< 0.0–100.0
    std::string start_time;
    std::string end_time;
};

// ============================================================
// Engine Configuration
// ============================================================

enum class ExecutionMode : uint8_t {
    SEQUENTIAL = 0,
    PARALLEL,
};

struct EngineConfig {
    std::string     suite_name{"TCU_Regression"};
    ExecutionMode   mode{ExecutionMode::SEQUENTIAL};
    uint8_t         thread_count{4};         ///< For PARALLEL mode
    bool            stop_on_critical{true};  ///< Stop suite on critical failure
    bool            enable_fault_injection{false};
    std::string     report_output_dir{"reports"};
};

// ============================================================
// Result Listener (observer pattern)
// ============================================================

/**
 * @brief Interface for live test result streaming.
 */
class IResultListener {
public:
    virtual ~IResultListener() = default;
    virtual void on_test_start(const TestCase& tc)             = 0;
    virtual void on_test_complete(const TestResult& result)    = 0;
    virtual void on_suite_complete(const SuiteResult& summary) = 0;
};

// ============================================================
// Test Engine
// ============================================================

/**
 * @brief Main test execution engine.
 *
 * Usage:
 * @code
 *   TestEngine engine(cfg);
 *   engine.add_test({
 *       .id = "TC-CAN-001",
 *       .name = "CAN Rx Frame Validation",
 *       .execute = [&]() -> Verdict {
 *           auto frame = can->wait_frame(100);
 *           return frame ? Verdict::PASS : Verdict::FAIL;
 *       }
 *   });
 *   auto suite_result = engine.run();
 * @endcode
 */
class TestEngine {
public:
    explicit TestEngine(const EngineConfig& cfg = {});
    ~TestEngine();

    TestEngine(const TestEngine&)            = delete;
    TestEngine& operator=(const TestEngine&) = delete;

    /**
     * @brief Add a single test case to the suite.
     */
    void add_test(TestCase tc);

    /**
     * @brief Add multiple test cases at once.
     */
    void add_tests(std::vector<TestCase> cases);

    /**
     * @brief Remove all registered test cases.
     */
    void clear();

    /**
     * @brief Register a result listener (observer).
     */
    void add_listener(std::shared_ptr<IResultListener> listener);

    /**
     * @brief Execute the full suite and return aggregate results.
     */
    SuiteResult run();

    /**
     * @brief Execute a single test case by ID and return its result.
     */
    TestResult run_single(const std::string& test_id);

    /**
     * @brief Execute tests matching a filter predicate.
     */
    SuiteResult run_filtered(std::function<bool(const TestCase&)> filter);

    /**
     * @brief Request abort of a running suite (thread-safe).
     */
    void abort();

    /**
     * @brief Returns true if a suite is currently executing.
     */
    bool is_running() const noexcept;

    /**
     * @brief Get the total number of registered test cases.
     */
    size_t test_count() const noexcept;

private:
    TestResult execute_test(const TestCase& tc);
    SuiteResult finalise_suite(const std::vector<TestResult>& results,
                               const std::string& start_time) const;
    void        notify_start(const TestCase& tc);
    void        notify_complete(const TestResult& result);
    void        notify_suite_complete(const SuiteResult& summary);
    std::string current_timestamp() const;

    EngineConfig                                  m_cfg;
    std::vector<TestCase>                         m_tests;
    std::vector<std::shared_ptr<IResultListener>> m_listeners;
    std::atomic<bool>                             m_running{false};
    std::atomic<bool>                             m_abort_requested{false};
    mutable std::mutex                            m_mutex;
};

} // namespace tcu::validation
