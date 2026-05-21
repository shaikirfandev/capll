/**
 * @file ReportGenerator.h
 * @brief Test Report Generator — produces HTML, JSON, and CSV reports.
 *
 * Consumes a SuiteResult and renders it in multiple output formats.
 * HTML output includes a pass/fail dashboard with colour-coded verdicts.
 */

#pragma once

#include <string>
#include <memory>
#include "validation/TestEngine.h"

namespace tcu::reporting {

enum class ReportFormat : uint8_t {
    HTML  = 0,
    JSON,
    CSV,
    ALL,   ///< Generate all formats
};

struct ReportConfig {
    std::string  output_dir{"reports"};
    std::string  project_name{"TCU Validation Framework"};
    std::string  build_version{"N/A"};
    std::string  environment{"HIL-Bench-01"};
    bool         embed_styles{true};    ///< Embed CSS in HTML (portable)
    bool         open_on_complete{false}; ///< Open HTML report in browser
};

/**
 * @brief Report Generator.
 *
 * Usage:
 * @code
 *   ReportGenerator gen(cfg);
 *   gen.generate(suite_result, ReportFormat::ALL);
 * @endcode
 */
class ReportGenerator {
public:
    explicit ReportGenerator(const ReportConfig& cfg = {});
    ~ReportGenerator() = default;

    /**
     * @brief Generate report(s) for the given suite result.
     * @return Path to primary report file (HTML if ALL or HTML requested)
     */
    std::string generate(const tcu::validation::SuiteResult& result,
                         ReportFormat fmt = ReportFormat::ALL);

    /**
     * @brief Generate HTML report only.
     */
    std::string generate_html(const tcu::validation::SuiteResult& result);

    /**
     * @brief Generate JSON report only.
     */
    std::string generate_json(const tcu::validation::SuiteResult& result);

    /**
     * @brief Generate CSV report only.
     */
    std::string generate_csv(const tcu::validation::SuiteResult& result);

private:
    std::string html_verdict_badge(tcu::validation::Verdict v) const;
    std::string html_css() const;
    std::string ensure_output_dir() const;
    std::string make_filename(const std::string& suite_name,
                              const std::string& ext) const;

    ReportConfig m_cfg;
};

} // namespace tcu::reporting
