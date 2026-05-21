/**
 * @file test_test_engine.cpp
 * @brief Unit tests for TestEngine (sequential, parallel, retry, timeout, abort).
 */

#include <gtest/gtest.h>
#include <gmock/gmock.h>

#include "validation/TestEngine.h"
#include "logging/Logger.h"

#include <atomic>
#include <chrono>
#include <thread>

using namespace tcu::validation;
using namespace testing;

// ============================================================
// Helpers
// ============================================================

static TestCase make_pass_test(const std::string& id, const std::string& name = "") {
    TestCase tc;
    tc.id       = id;
    tc.name     = name.empty() ? id : name;
    tc.timeout_ms = 1000;
    tc.execute  = [id, &name = tc.name]() {
        TestResult r;
        r.test_id   = id;
        r.test_name = name;
        r.verdict   = Verdict::PASS;
        return r;
    };
    return tc;
}

static TestCase make_fail_test(const std::string& id) {
    TestCase tc;
    tc.id   = id;
    tc.name = id;
    tc.execute = [id]() {
        TestResult r;
        r.test_id = id;
        r.verdict = Verdict::FAIL;
        r.message = "Intentional fail";
        return r;
    };
    return tc;
}

static TestCase make_sleep_test(const std::string& id, uint32_t sleep_ms,
                                 uint32_t timeout_ms = 0) {
    TestCase tc;
    tc.id         = id;
    tc.name       = id;
    tc.timeout_ms = timeout_ms;
    tc.execute    = [id, sleep_ms]() {
        std::this_thread::sleep_for(std::chrono::milliseconds(sleep_ms));
        TestResult r;
        r.test_id = id;
        r.verdict = Verdict::PASS;
        return r;
    };
    return tc;
}

// ============================================================
// Fixture
// ============================================================

class TestEngineTest : public ::testing::Test {
protected:
    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir       = "/tmp/tcu_test_logs";
        lc.enable_console= false;
        tcu::logging::Logger::init(lc);
    }
};

// ============================================================
// Basic run tests
// ============================================================

TEST_F(TestEngineTest, EmptySuiteRunsCleanly) {
    EngineConfig cfg;
    TestEngine engine(cfg);
    auto result = engine.run("empty");
    EXPECT_EQ(result.total_tests, 0U);
    EXPECT_TRUE(result.all_passed);
}

TEST_F(TestEngineTest, SinglePassTest) {
    TestEngine engine({});
    engine.add_test(make_pass_test("T001", "Single Pass"));
    auto r = engine.run("suite");
    EXPECT_EQ(r.passed,  1U);
    EXPECT_EQ(r.failed,  0U);
    EXPECT_TRUE(r.all_passed);
}

TEST_F(TestEngineTest, SingleFailTest) {
    TestEngine engine({});
    engine.add_test(make_fail_test("T002"));
    auto r = engine.run("suite");
    EXPECT_EQ(r.passed, 0U);
    EXPECT_EQ(r.failed, 1U);
    EXPECT_FALSE(r.all_passed);
}

TEST_F(TestEngineTest, MultipleTests) {
    TestEngine engine({});
    engine.add_test(make_pass_test("T001"));
    engine.add_test(make_pass_test("T002"));
    engine.add_test(make_fail_test("T003"));
    engine.add_test(make_pass_test("T004"));
    auto r = engine.run("multi");
    EXPECT_EQ(r.total_tests, 4U);
    EXPECT_EQ(r.passed,      3U);
    EXPECT_EQ(r.failed,      1U);
    EXPECT_FALSE(r.all_passed);
}

// ============================================================
// Precondition / Skip tests
// ============================================================

TEST_F(TestEngineTest, FailedPreconditionSkipsTest) {
    TestCase tc = make_pass_test("T010");
    tc.precondition = [] { return false; };
    TestEngine engine({});
    engine.add_test(tc);
    auto r = engine.run("skip_suite");
    EXPECT_EQ(r.skipped, 1U);
    EXPECT_EQ(r.passed,  0U);
}

TEST_F(TestEngineTest, PassedPreconditionRunsTest) {
    TestCase tc = make_pass_test("T011");
    tc.precondition = [] { return true; };
    TestEngine engine({});
    engine.add_test(tc);
    auto r = engine.run("suite");
    EXPECT_EQ(r.passed,  1U);
    EXPECT_EQ(r.skipped, 0U);
}

// ============================================================
// Timeout tests
// ============================================================

TEST_F(TestEngineTest, TimeoutTriggered) {
    TestCase tc = make_sleep_test("T_TIMEOUT", 500, /*timeout_ms=*/100);
    TestEngine engine({});
    engine.add_test(tc);
    auto r = engine.run("suite");
    EXPECT_EQ(r.timed_out, 1U);
    EXPECT_FALSE(r.all_passed);
}

TEST_F(TestEngineTest, NoTimeoutWhenZero) {
    // timeout_ms=0 means unlimited
    TestCase tc = make_sleep_test("T_NOTIMEOUT", 50, /*timeout_ms=*/0);
    TestEngine engine({});
    engine.add_test(tc);
    auto r = engine.run("suite");
    EXPECT_EQ(r.passed,    1U);
    EXPECT_EQ(r.timed_out, 0U);
}

// ============================================================
// Retry tests
// ============================================================

TEST_F(TestEngineTest, RetryOnFailThenPass) {
    static std::atomic<int> attempt_count{0};
    TestCase tc;
    tc.id          = "T_RETRY";
    tc.name        = "Retry Test";
    tc.max_retries = 2;
    tc.timeout_ms  = 2000;
    tc.execute     = []() {
        TestResult r;
        r.test_id = "T_RETRY";
        ++attempt_count;
        if (attempt_count.load() < 3) {
            r.verdict = Verdict::FAIL;
            r.message = "Fail attempt " + std::to_string(attempt_count.load());
        } else {
            r.verdict = Verdict::PASS;
        }
        return r;
    };

    EngineConfig cfg;
    cfg.retry_delay_ms = 10;
    TestEngine engine(cfg);
    engine.add_test(tc);
    auto r = engine.run("retry_suite");
    EXPECT_EQ(r.passed, 1U);
    EXPECT_GE(attempt_count.load(), 3);
}

// ============================================================
// Cleanup tests
// ============================================================

TEST_F(TestEngineTest, CleanupCalledOnPass) {
    static bool cleanup_called = false;
    TestCase tc = make_pass_test("T_CLEANUP");
    tc.cleanup = [] { cleanup_called = true; };
    TestEngine engine({});
    engine.add_test(tc);
    engine.run("suite");
    EXPECT_TRUE(cleanup_called);
}

TEST_F(TestEngineTest, CleanupCalledOnFail) {
    static bool cleanup_called = false;
    TestCase tc = make_fail_test("T_CLEANUP_FAIL");
    tc.cleanup = [] { cleanup_called = true; };
    TestEngine engine({});
    engine.add_test(tc);
    engine.run("suite");
    EXPECT_TRUE(cleanup_called);
}

// ============================================================
// run_single tests
// ============================================================

TEST_F(TestEngineTest, RunSingleKnownTest) {
    TestEngine engine({});
    engine.add_test(make_pass_test("T_SINGLE"));
    auto r = engine.run_single("T_SINGLE");
    EXPECT_EQ(r.test_id, "T_SINGLE");
    EXPECT_EQ(r.verdict, Verdict::PASS);
}

TEST_F(TestEngineTest, RunSingleUnknownTestReturnsError) {
    TestEngine engine({});
    auto r = engine.run_single("NONEXISTENT");
    EXPECT_EQ(r.verdict, Verdict::ERROR);
}

// ============================================================
// run_filtered tests
// ============================================================

TEST_F(TestEngineTest, RunFilteredOnlyRunsSpecified) {
    TestEngine engine({});
    engine.add_test(make_pass_test("A"));
    engine.add_test(make_fail_test("B"));
    engine.add_test(make_pass_test("C"));
    auto r = engine.run_filtered("filtered", {"A", "C"});
    EXPECT_EQ(r.total_tests, 2U);
    EXPECT_EQ(r.passed, 2U);
    EXPECT_EQ(r.failed, 0U);
}

// ============================================================
// Listener tests
// ============================================================

class MockListener : public IResultListener {
public:
    MOCK_METHOD(void, on_suite_start, (const std::string&), (override));
    MOCK_METHOD(void, on_suite_end,   (const SuiteResult&), (override));
    MOCK_METHOD(void, on_test_result, (const TestResult&),  (override));
};

TEST_F(TestEngineTest, ListenerReceivesAllNotifications) {
    auto listener = std::make_shared<MockListener>();
    EXPECT_CALL(*listener, on_suite_start(_)).Times(1);
    EXPECT_CALL(*listener, on_suite_end(_)).Times(1);
    EXPECT_CALL(*listener, on_test_result(_)).Times(2);

    TestEngine engine({});
    engine.add_listener(listener);
    engine.add_test(make_pass_test("T1"));
    engine.add_test(make_fail_test("T2"));
    engine.run("listener_suite");
}

// ============================================================
// Parallel mode test
// ============================================================

TEST_F(TestEngineTest, ParallelModeRunsAllTests) {
    EngineConfig cfg;
    cfg.parallel = true;
    TestEngine engine(cfg);
    for (int i = 0; i < 5; ++i) {
        engine.add_test(make_pass_test("P" + std::to_string(i)));
    }
    auto r = engine.run("parallel_suite");
    EXPECT_EQ(r.passed, 5U);
    EXPECT_TRUE(r.all_passed);
}

// ============================================================
// clear_tests test
// ============================================================

TEST_F(TestEngineTest, ClearTestsEmptiesSuite) {
    TestEngine engine({});
    engine.add_test(make_pass_test("X1"));
    engine.add_test(make_pass_test("X2"));
    engine.clear_tests();
    auto r = engine.run("empty_after_clear");
    EXPECT_EQ(r.total_tests, 0U);
}
