/**
 * @file test_report_generator.cpp
 * @brief Unit tests for ReportGenerator (HTML/JSON/CSV output validation).
 */

#include <gtest/gtest.h>
#include "reporting/ReportGenerator.h"
#include "validation/TestEngine.h"
#include "logging/Logger.h"

#include <fstream>
#include <sstream>
#include <filesystem>
#include <nlohmann/json.hpp>

using namespace tcu::reporting;
using namespace tcu::validation;

// ============================================================
// Helpers
// ============================================================

static SuiteResult make_suite(const std::string& name = "TestSuite") {
    SuiteResult suite;
    suite.suite_name   = name;
    suite.total_ms     = 1234;
    suite.start_time   = std::chrono::system_clock::now();
    suite.end_time     = suite.start_time + std::chrono::milliseconds(1234);

    auto make_result = [](const std::string& id, const std::string& n,
                          Verdict v, const std::string& msg = "") {
        TestResult r;
        r.test_id     = id;
        r.test_name   = n;
        r.verdict     = v;
        r.message     = msg;
        r.duration_ms = 100;
        r.attempt     = 1;
        return r;
    };

    suite.results.push_back(make_result("TC001", "CAN Health",      Verdict::PASS));
    suite.results.push_back(make_result("TC002", "UDS Session",     Verdict::FAIL, "Timeout"));
    suite.results.push_back(make_result("TC003", "OTA Check",       Verdict::SKIP, "No ECU"));
    suite.results.push_back(make_result("TC004", "Fault Injection", Verdict::PASS));
    suite.results.push_back(make_result("TC005", "Stress Test",     Verdict::TIMEOUT));

    suite.total_tests = static_cast<uint32_t>(suite.results.size());
    suite.passed      = 2;
    suite.failed      = 1;
    suite.skipped     = 1;
    suite.timed_out   = 1;
    suite.errored     = 0;
    suite.all_passed  = false;
    return suite;
}

// ============================================================
// Fixture
// ============================================================

class ReportGeneratorTest : public ::testing::Test {
protected:
    std::string tmp_dir;

    void SetUp() override {
        tcu::logging::LogConfig lc;
        lc.log_dir       = "/tmp/tcu_test_logs";
        lc.enable_console= false;
        tcu::logging::Logger::init(lc);

        tmp_dir = "/tmp/tcu_report_test_" + std::to_string(getpid());
        std::filesystem::create_directories(tmp_dir);
    }

    void TearDown() override {
        std::filesystem::remove_all(tmp_dir);
    }

    std::string read_file(const std::string& path) {
        std::ifstream f(path);
        return std::string(std::istreambuf_iterator<char>(f),
                           std::istreambuf_iterator<char>());
    }
};

// ============================================================
// HTML report tests
// ============================================================

TEST_F(ReportGeneratorTest, HTMLFileCreated) {
    ReportGenerator gen(tmp_dir);
    auto suite = make_suite("HTML_Suite");
    EXPECT_TRUE(gen.generate(suite, ReportFormat::HTML, "report"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/report.html"));
}

TEST_F(ReportGeneratorTest, HTMLContainsSuiteName) {
    ReportGenerator gen(tmp_dir);
    auto suite = make_suite("MySuite");
    gen.generate(suite, ReportFormat::HTML, "out");
    std::string content = read_file(tmp_dir + "/out.html");
    EXPECT_NE(content.find("MySuite"), std::string::npos);
}

TEST_F(ReportGeneratorTest, HTMLContainsAllVerdicts) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::HTML, "r");
    std::string content = read_file(tmp_dir + "/r.html");
    EXPECT_NE(content.find("PASS"),    std::string::npos);
    EXPECT_NE(content.find("FAIL"),    std::string::npos);
    EXPECT_NE(content.find("SKIP"),    std::string::npos);
    EXPECT_NE(content.find("TIMEOUT"), std::string::npos);
}

TEST_F(ReportGeneratorTest, HTMLContainsTestIDs) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::HTML, "r");
    std::string content = read_file(tmp_dir + "/r.html");
    EXPECT_NE(content.find("TC001"), std::string::npos);
    EXPECT_NE(content.find("TC005"), std::string::npos);
}

TEST_F(ReportGeneratorTest, HTMLIsValidDoctype) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::HTML, "r");
    std::string content = read_file(tmp_dir + "/r.html");
    EXPECT_EQ(content.find("<!DOCTYPE html>"), 0U);
}

// ============================================================
// JSON report tests
// ============================================================

TEST_F(ReportGeneratorTest, JSONFileCreated) {
    ReportGenerator gen(tmp_dir);
    EXPECT_TRUE(gen.generate(make_suite(), ReportFormat::JSON, "report"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/report.json"));
}

TEST_F(ReportGeneratorTest, JSONIsValidAndHasCorrectFields) {
    ReportGenerator gen(tmp_dir);
    auto suite = make_suite("JSON_Suite");
    gen.generate(suite, ReportFormat::JSON, "r");

    std::string content = read_file(tmp_dir + "/r.json");
    ASSERT_FALSE(content.empty());

    auto doc = nlohmann::json::parse(content);
    EXPECT_EQ(doc["suite_name"].get<std::string>(), "JSON_Suite");
    EXPECT_EQ(doc["total_tests"].get<int>(), 5);
    EXPECT_EQ(doc["passed"].get<int>(), 2);
    EXPECT_EQ(doc["failed"].get<int>(), 1);
    EXPECT_EQ(doc["skipped"].get<int>(), 1);
    EXPECT_EQ(doc["timed_out"].get<int>(), 1);
    EXPECT_FALSE(doc["all_passed"].get<bool>());
    EXPECT_TRUE(doc["results"].is_array());
    EXPECT_EQ(doc["results"].size(), 5U);
}

TEST_F(ReportGeneratorTest, JSONResultsHaveRequiredFields) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::JSON, "r");
    auto doc = nlohmann::json::parse(read_file(tmp_dir + "/r.json"));
    const auto& first = doc["results"][0];
    EXPECT_TRUE(first.contains("test_id"));
    EXPECT_TRUE(first.contains("test_name"));
    EXPECT_TRUE(first.contains("verdict"));
    EXPECT_TRUE(first.contains("duration_ms"));
    EXPECT_TRUE(first.contains("attempt"));
    EXPECT_TRUE(first.contains("message"));
}

// ============================================================
// CSV report tests
// ============================================================

TEST_F(ReportGeneratorTest, CSVFileCreated) {
    ReportGenerator gen(tmp_dir);
    EXPECT_TRUE(gen.generate(make_suite(), ReportFormat::CSV, "report"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/report.csv"));
}

TEST_F(ReportGeneratorTest, CSVHasHeader) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::CSV, "r");
    std::string content = read_file(tmp_dir + "/r.csv");
    EXPECT_EQ(content.find("test_id"), 0U);
    EXPECT_NE(content.find("verdict"),     std::string::npos);
    EXPECT_NE(content.find("duration_ms"), std::string::npos);
}

TEST_F(ReportGeneratorTest, CSVHasCorrectRowCount) {
    ReportGenerator gen(tmp_dir);
    gen.generate(make_suite(), ReportFormat::CSV, "r");
    std::string content = read_file(tmp_dir + "/r.csv");
    int lines = 0;
    for (char c : content) { if (c == '\n') ++lines; }
    EXPECT_EQ(lines, 6);  // 1 header + 5 data rows
}

// ============================================================
// ALL format test
// ============================================================

TEST_F(ReportGeneratorTest, AllFormatCreatesThreeFiles) {
    ReportGenerator gen(tmp_dir);
    EXPECT_TRUE(gen.generate(make_suite(), ReportFormat::ALL, "all_report"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/all_report.html"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/all_report.json"));
    EXPECT_TRUE(std::filesystem::exists(tmp_dir + "/all_report.csv"));
}

// ============================================================
// Edge cases
// ============================================================

TEST_F(ReportGeneratorTest, EmptySuiteGeneratesReports) {
    SuiteResult empty;
    empty.suite_name   = "Empty";
    empty.total_tests  = 0;
    empty.all_passed   = true;
    ReportGenerator gen(tmp_dir);
    EXPECT_TRUE(gen.generate(empty, ReportFormat::ALL, "empty"));
}

TEST_F(ReportGeneratorTest, OutputDirectoryCreatedIfMissing) {
    std::string subdir = tmp_dir + "/new_subdir/reports";
    ReportGenerator gen(subdir);
    EXPECT_TRUE(gen.generate(make_suite(), ReportFormat::JSON, "r"));
    EXPECT_TRUE(std::filesystem::exists(subdir + "/r.json"));
}
