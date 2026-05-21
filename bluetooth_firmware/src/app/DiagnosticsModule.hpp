/**
 * @file DiagnosticsModule.hpp
 */
#pragma once
#include "app/IDiagnosticsModule.hpp"
#include <memory>
namespace bt::app {
class DiagnosticsModule final : public IDiagnosticsModule {
public:
    DiagnosticsModule(); ~DiagnosticsModule() override;
    const BtHealthStats &get_stats() const          override;
    void reset_stats()                               override;
    std::string generate_report() const             override;
    void record_event(std::string_view comp, std::string_view event) override;
private:
    struct Impl; std::unique_ptr<Impl> impl_;
};
}
