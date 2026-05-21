/**
 * @file ReportGenerator.cpp
 * @brief HTML/JSON/CSV test report generation.
 */

#include "reporting/ReportGenerator.h"
#include "logging/Logger.h"

#include <fstream>
#include <iomanip>
#include <sstream>
#include <ctime>
#include <filesystem>
#include <nlohmann/json.hpp>

namespace tcu::reporting {

using json = nlohmann::json;
static auto s_log = tcu::logging::Logger::get("reporting");

// ============================================================
// Construction
// ============================================================

ReportGenerator::ReportGenerator(const std::string& output_dir)
    : m_output_dir(output_dir)
{
    std::filesystem::create_directories(output_dir);
}

// ============================================================
// Main generate
// ============================================================

bool ReportGenerator::generate(const tcu::validation::SuiteResult& suite,
                                ReportFormat fmt,
                                const std::string& filename_prefix) {
    bool ok = true;
    if (fmt == ReportFormat::HTML || fmt == ReportFormat::ALL) {
        ok &= generate_html(suite, filename_prefix);
    }
    if (fmt == ReportFormat::JSON || fmt == ReportFormat::ALL) {
        ok &= generate_json(suite, filename_prefix);
    }
    if (fmt == ReportFormat::CSV || fmt == ReportFormat::ALL) {
        ok &= generate_csv(suite, filename_prefix);
    }
    return ok;
}

// ============================================================
// HTML Report
// ============================================================

bool ReportGenerator::generate_html(const tcu::validation::SuiteResult& suite,
                                     const std::string& prefix) {
    std::string path = m_output_dir + "/" + prefix + ".html";
    std::ofstream f(path);
    if (!f.is_open()) {
        s_log->error("Cannot open HTML output: {}", path);
        return false;
    }

    float pass_pct = suite.total_tests > 0
                     ? 100.0f * suite.passed / suite.total_tests
                     : 0.0f;

    f << R"(<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TCU Validation Report — )" << suite.suite_name << R"(</title>
<style>
  :root { --pass:#22c55e; --fail:#ef4444; --skip:#f59e0b; --to:#8b5cf6; --err:#6b7280; }
  body  { font-family:'Segoe UI',Arial,sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:20px; }
  h1    { color:#38bdf8; border-bottom:2px solid #1e3a5f; padding-bottom:10px; }
  .summary { display:flex; gap:16px; flex-wrap:wrap; margin:20px 0; }
  .card  { background:#1e293b; border-radius:8px; padding:16px 24px; min-width:110px; text-align:center; }
  .card .num { font-size:2em; font-weight:700; }
  .card .lbl { font-size:.8em; color:#94a3b8; text-transform:uppercase; letter-spacing:.05em; }
  .pass { color:var(--pass); } .fail { color:var(--fail); } .skip { color:var(--skip); }
  .timeout { color:var(--to); } .error { color:var(--err); }
  table { width:100%; border-collapse:collapse; margin-top:20px; }
  th    { background:#1e3a5f; color:#bae6fd; padding:10px; text-align:left; }
  td    { padding:10px; border-bottom:1px solid #1e293b; }
  tr:hover td { background:#1e293b; }
  .badge { border-radius:4px; padding:2px 8px; font-size:.8em; font-weight:600; }
  .badge-pass    { background:#14532d; color:var(--pass); }
  .badge-fail    { background:#450a0a; color:var(--fail); }
  .badge-skip    { background:#451a03; color:var(--skip); }
  .badge-timeout { background:#2e1065; color:var(--to); }
  .badge-error   { background:#1f2937; color:var(--err); }
  .progress-bar  { background:#1e293b; border-radius:4px; height:12px; overflow:hidden; margin-top:8px; }
  .progress-fill { height:100%; background:var(--pass); transition:width .3s; }
</style>
</head>
<body>
<h1>TCU Validation Framework — Test Report</h1>
<p>Suite: <b>)" << suite.suite_name << R"(</b> &nbsp;|&nbsp; Duration: <b>)" << suite.total_ms
       << R"( ms</b></p>
<div class="progress-bar"><div class="progress-fill" style="width:)" << static_cast<int>(pass_pct)
       << R"(%;"></div></div>
<div class="summary">
  <div class="card"><div class="num">)" << suite.total_tests << R"(</div><div class="lbl">Total</div></div>
  <div class="card pass"><div class="num">)" << suite.passed << R"(</div><div class="lbl">Pass</div></div>
  <div class="card fail"><div class="num">)" << suite.failed << R"(</div><div class="lbl">Fail</div></div>
  <div class="card skip"><div class="num">)" << suite.skipped << R"(</div><div class="lbl">Skip</div></div>
  <div class="card timeout"><div class="num">)" << suite.timed_out << R"(</div><div class="lbl">Timeout</div></div>
  <div class="card error"><div class="num">)" << suite.errored << R"(</div><div class="lbl">Error</div></div>
</div>
<table>
<thead><tr>
  <th>#</th><th>Test ID</th><th>Test Name</th><th>Verdict</th>
  <th>Duration (ms)</th><th>Attempt</th><th>Message</th>
</tr></thead>
<tbody>
)";

    int row = 0;
    for (const auto& r : suite.results) {
        ++row;
        std::string badge, verdict_str;
        switch (r.verdict) {
            case tcu::validation::Verdict::PASS:
                badge = "badge-pass"; verdict_str = "PASS"; break;
            case tcu::validation::Verdict::FAIL:
                badge = "badge-fail"; verdict_str = "FAIL"; break;
            case tcu::validation::Verdict::SKIP:
                badge = "badge-skip"; verdict_str = "SKIP"; break;
            case tcu::validation::Verdict::TIMEOUT:
                badge = "badge-timeout"; verdict_str = "TIMEOUT"; break;
            default:
                badge = "badge-error"; verdict_str = "ERROR"; break;
        }
        f << "<tr>\n"
          << "  <td>" << row << "</td>\n"
          << "  <td><code>" << r.test_id << "</code></td>\n"
          << "  <td>" << r.test_name << "</td>\n"
          << "  <td><span class=\"badge " << badge << "\">" << verdict_str << "</span></td>\n"
          << "  <td>" << r.duration_ms << "</td>\n"
          << "  <td>" << r.attempt << "</td>\n"
          << "  <td>" << r.message << "</td>\n"
          << "</tr>\n";
    }

    f << R"(</tbody></table>
<p style="color:#475569;font-size:.8em;margin-top:24px;">
  Generated by TCU Validation Framework v2.0.0
</p>
</body>
</html>)";

    s_log->info("HTML report: {}", path);
    return true;
}

// ============================================================
// JSON Report
// ============================================================

bool ReportGenerator::generate_json(const tcu::validation::SuiteResult& suite,
                                     const std::string& prefix) {
    std::string path = m_output_dir + "/" + prefix + ".json";
    std::ofstream f(path);
    if (!f.is_open()) {
        s_log->error("Cannot open JSON output: {}", path);
        return false;
    }

    json doc;
    doc["suite_name"]  = suite.suite_name;
    doc["total_tests"] = suite.total_tests;
    doc["passed"]      = suite.passed;
    doc["failed"]      = suite.failed;
    doc["skipped"]     = suite.skipped;
    doc["timed_out"]   = suite.timed_out;
    doc["errored"]     = suite.errored;
    doc["total_ms"]    = suite.total_ms;
    doc["all_passed"]  = suite.all_passed;

    json results = json::array();
    for (const auto& r : suite.results) {
        json item;
        item["test_id"]     = r.test_id;
        item["test_name"]   = r.test_name;
        item["verdict"]     = static_cast<int>(r.verdict);
        item["duration_ms"] = r.duration_ms;
        item["attempt"]     = r.attempt;
        item["message"]     = r.message;
        results.push_back(item);
    }
    doc["results"] = results;

    f << doc.dump(2);
    s_log->info("JSON report: {}", path);
    return true;
}

// ============================================================
// CSV Report
// ============================================================

bool ReportGenerator::generate_csv(const tcu::validation::SuiteResult& suite,
                                    const std::string& prefix) {
    std::string path = m_output_dir + "/" + prefix + ".csv";
    std::ofstream f(path);
    if (!f.is_open()) {
        s_log->error("Cannot open CSV output: {}", path);
        return false;
    }

    // Header
    f << "test_id,test_name,verdict,duration_ms,attempt,message\n";

    auto escape_csv = [](const std::string& s) -> std::string {
        if (s.find_first_of(",\"\n\r") == std::string::npos) { return s; }
        std::string out = "\"";
        for (char c : s) {
            if (c == '"') { out += '"'; }
            out += c;
        }
        out += '"';
        return out;
    };

    auto verdict_to_str = [](tcu::validation::Verdict v) -> std::string {
        switch (v) {
            case tcu::validation::Verdict::PASS:    return "PASS";
            case tcu::validation::Verdict::FAIL:    return "FAIL";
            case tcu::validation::Verdict::SKIP:    return "SKIP";
            case tcu::validation::Verdict::TIMEOUT: return "TIMEOUT";
            default:                                return "ERROR";
        }
    };

    for (const auto& r : suite.results) {
        f << escape_csv(r.test_id)   << ","
          << escape_csv(r.test_name) << ","
          << verdict_to_str(r.verdict) << ","
          << r.duration_ms           << ","
          << r.attempt               << ","
          << escape_csv(r.message)   << "\n";
    }

    s_log->info("CSV report: {}", path);
    return true;
}

} // namespace tcu::reporting
