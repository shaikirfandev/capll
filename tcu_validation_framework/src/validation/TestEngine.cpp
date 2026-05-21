/**
 * @file TestEngine.cpp
 * @brief Automated test execution with sequential/parallel modes, retry, timeout.
 */

#include "validation/TestEngine.h"
#include "logging/Logger.h"

#include <algorithm>
#include <future>
#include <thread>
#include <chrono>
#include <sstream>
#include <iomanip>

namespace tcu::validation {

static auto s_log = tcu::logging::Logger::get("test_engine");

// ============================================================
// Construction
// ============================================================

TestEngine::TestEngine(const EngineConfig& cfg) : m_cfg(cfg) {}

// ============================================================
// Listeners
// ============================================================

void TestEngine::add_listener(std::shared_ptr<IResultListener> listener) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_listeners.push_back(std::move(listener));
}

// ============================================================
// Test case management
// ============================================================

void TestEngine::add_test(TestCase tc) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_tests.push_back(std::move(tc));
}

void TestEngine::clear_tests() {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_tests.clear();
}

// ============================================================
// Suite execution
// ============================================================

SuiteResult TestEngine::run(const std::string& suite_name) {
    m_abort_requested = false;
    SuiteResult suite;
    suite.suite_name = suite_name;
    suite.start_time = std::chrono::system_clock::now();

    std::vector<TestCase> tests_snapshot;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        tests_snapshot = m_tests;
    }

    s_log->info("=== Suite: {} | {} tests | mode: {} ===",
                suite_name, tests_snapshot.size(),
                m_cfg.parallel ? "parallel" : "sequential");

    notify_suite_start(suite_name);

    if (m_cfg.parallel) {
        run_parallel(tests_snapshot, suite);
    } else {
        run_sequential(tests_snapshot, suite);
    }

    suite.end_time    = std::chrono::system_clock::now();
    suite.total_ms    = std::chrono::duration_cast<std::chrono::milliseconds>(
                            suite.end_time - suite.start_time).count();
    suite.total_tests = static_cast<uint32_t>(suite.results.size());

    for (const auto& r : suite.results) {
        switch (r.verdict) {
            case Verdict::PASS:    ++suite.passed;  break;
            case Verdict::FAIL:    ++suite.failed;  break;
            case Verdict::SKIP:    ++suite.skipped; break;
            case Verdict::TIMEOUT: ++suite.timed_out; break;
            default:               ++suite.errored; break;
        }
    }

    suite.all_passed = (suite.failed == 0 && suite.errored == 0 && suite.timed_out == 0);

    s_log->info("=== Suite '{}' complete: PASS={} FAIL={} ERR={} SKIP={} TO={} ({} ms) ===",
                suite_name, suite.passed, suite.failed, suite.errored,
                suite.skipped, suite.timed_out, suite.total_ms);

    notify_suite_end(suite);
    return suite;
}

TestResult TestEngine::run_single(const std::string& test_id) {
    std::lock_guard<std::mutex> lock(m_mutex);
    for (const auto& tc : m_tests) {
        if (tc.id == test_id) {
            return execute_test(tc);
        }
    }
    TestResult r;
    r.test_id    = test_id;
    r.test_name  = "UNKNOWN";
    r.verdict    = Verdict::ERROR;
    r.message    = "Test not found: " + test_id;
    return r;
}

SuiteResult TestEngine::run_filtered(const std::string& suite_name,
                                      const std::vector<std::string>& test_ids) {
    m_abort_requested = false;
    SuiteResult suite;
    suite.suite_name = suite_name;
    suite.start_time = std::chrono::system_clock::now();

    std::vector<TestCase> filtered;
    {
        std::lock_guard<std::mutex> lock(m_mutex);
        for (const auto& tc : m_tests) {
            if (std::find(test_ids.begin(), test_ids.end(), tc.id) != test_ids.end()) {
                filtered.push_back(tc);
            }
        }
    }

    s_log->info("Filtered run: {}/{} tests", filtered.size(), m_tests.size());
    run_sequential(filtered, suite);

    suite.end_time = std::chrono::system_clock::now();
    suite.total_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
                         suite.end_time - suite.start_time).count();
    return suite;
}

void TestEngine::abort() {
    m_abort_requested = true;
    s_log->warn("Test abort requested");
}

// ============================================================
// Sequential execution
// ============================================================

void TestEngine::run_sequential(const std::vector<TestCase>& tests,
                                 SuiteResult& suite) {
    for (const auto& tc : tests) {
        if (m_abort_requested.load()) {
            TestResult r;
            r.test_id   = tc.id;
            r.test_name = tc.name;
            r.verdict   = Verdict::SKIP;
            r.message   = "Aborted";
            suite.results.push_back(r);
            continue;
        }

        auto result = execute_test(tc);
        suite.results.push_back(result);

        // Bail on critical test failure
        if (result.verdict == Verdict::FAIL && tc.is_critical &&
            m_cfg.stop_on_first_fail) {
            s_log->error("Critical test '{}' failed — stopping suite", tc.name);
            m_abort_requested = true;
        }
    }
}

// ============================================================
// Parallel execution (thread pool)
// ============================================================

void TestEngine::run_parallel(const std::vector<TestCase>& tests,
                               SuiteResult& suite) {
    std::vector<std::future<TestResult>> futures;
    std::vector<std::mutex> per_tc_mutexes(tests.size());

    for (const auto& tc : tests) {
        futures.push_back(std::async(std::launch::async,
                                     [this, &tc] { return execute_test(tc); }));
    }

    suite.results.reserve(futures.size());
    for (auto& f : futures) {
        suite.results.push_back(f.get());
    }
}

// ============================================================
// Single test execution
// ============================================================

TestResult TestEngine::execute_test(const TestCase& tc) {
    TestResult result;
    result.test_id   = tc.id;
    result.test_name = tc.name;
    result.verdict   = Verdict::NOT_RUN;

    s_log->info("  [RUN ] {} ({})", tc.name, tc.id);

    // Check precondition
    if (tc.precondition && !tc.precondition()) {
        result.verdict = Verdict::SKIP;
        result.message = "Precondition not met";
        s_log->warn("  [SKIP] {} — precondition not met", tc.name);
        notify_test_result(result);
        return result;
    }

    uint32_t max_attempts = std::max(1U, tc.max_retries + 1);

    for (uint32_t attempt = 0; attempt < max_attempts; ++attempt) {
        if (attempt > 0) {
            s_log->info("  [RETRY] {} attempt {}/{}", tc.name, attempt, tc.max_retries);
            std::this_thread::sleep_for(std::chrono::milliseconds(m_cfg.retry_delay_ms));
        }

        auto t_start = std::chrono::steady_clock::now();

        // Execute with timeout
        result = run_with_timeout(tc);

        result.duration_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - t_start).count();
        result.attempt     = attempt + 1;

        if (result.verdict == Verdict::PASS) { break; }
        if (result.verdict == Verdict::TIMEOUT) { break; }  // No retry on timeout
    }

    // Run cleanup regardless of outcome
    if (tc.cleanup) {
        try { tc.cleanup(); }
        catch (const std::exception& ex) {
            s_log->warn("  Cleanup exception for {}: {}", tc.name, ex.what());
        }
    }

    const char* verdict_str = "????";
    switch (result.verdict) {
        case Verdict::PASS:    verdict_str = "PASS"; break;
        case Verdict::FAIL:    verdict_str = "FAIL"; break;
        case Verdict::ERROR:   verdict_str = "ERROR"; break;
        case Verdict::SKIP:    verdict_str = "SKIP"; break;
        case Verdict::TIMEOUT: verdict_str = "TIMEOUT"; break;
        default: break;
    }

    s_log->info("  [{}] {} — {} ms", verdict_str, tc.name, result.duration_ms);
    if (!result.message.empty()) {
        s_log->debug("       └─ {}", result.message);
    }

    notify_test_result(result);
    return result;
}

TestResult TestEngine::run_with_timeout(const TestCase& tc) {
    TestResult result;
    result.test_id   = tc.id;
    result.test_name = tc.name;

    if (tc.timeout_ms == 0) {
        // No timeout
        try {
            result = tc.execute();
        } catch (const std::exception& ex) {
            result.verdict = Verdict::ERROR;
            result.message = std::string("Exception: ") + ex.what();
        } catch (...) {
            result.verdict = Verdict::ERROR;
            result.message = "Unknown exception";
        }
        return result;
    }

    // Execute with timeout via std::future
    auto future = std::async(std::launch::async, [&tc] {
        TestResult r;
        try {
            r = tc.execute();
        } catch (const std::exception& ex) {
            r.verdict = Verdict::ERROR;
            r.message = std::string("Exception: ") + ex.what();
        } catch (...) {
            r.verdict = Verdict::ERROR;
            r.message = "Unknown exception";
        }
        return r;
    });

    auto status = future.wait_for(std::chrono::milliseconds(tc.timeout_ms));
    if (status == std::future_status::timeout) {
        result.verdict = Verdict::TIMEOUT;
        result.message = "Exceeded " + std::to_string(tc.timeout_ms) + " ms timeout";
        s_log->warn("  [TIMEOUT] {} exceeded {} ms", tc.name, tc.timeout_ms);
        // future destructor will block until thread finishes, acceptable here
        return result;
    }

    return future.get();
}

// ============================================================
// Listener notifications
// ============================================================

void TestEngine::notify_suite_start(const std::string& suite_name) {
    std::lock_guard<std::mutex> lock(m_mutex);
    for (auto& listener : m_listeners) {
        if (listener) { listener->on_suite_start(suite_name); }
    }
}

void TestEngine::notify_suite_end(const SuiteResult& result) {
    std::lock_guard<std::mutex> lock(m_mutex);
    for (auto& listener : m_listeners) {
        if (listener) { listener->on_suite_end(result); }
    }
}

void TestEngine::notify_test_result(const TestResult& result) {
    std::lock_guard<std::mutex> lock(m_mutex);
    for (auto& listener : m_listeners) {
        if (listener) { listener->on_test_result(result); }
    }
}

} // namespace tcu::validation
