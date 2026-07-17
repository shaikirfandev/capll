// ============================================================
// adas/diagnostics.cpp — DtcManager implementation
// ============================================================

#include "adas/diagnostics.hpp"

#include <cstring>

namespace adas {

DiagnosticEvent* DtcManager::find(std::uint32_t code) noexcept {
    for (std::size_t i = 0; i < count_; ++i) {
        if (table_[i].dtc_code == code) return &table_[i];
    }
    return nullptr;
}

void DtcManager::report(std::uint32_t dtc_code, TimePoint now) noexcept {
    if (auto* ev = find(dtc_code)) {
        ev->last_occurrence = now;
        if (ev->occurrence_counter < 255U) ++ev->occurrence_counter;
        if (ev->status == DtcStatus::Pending) ev->status = DtcStatus::Confirmed;
        return;
    }
    if (count_ >= kMaxDtcs) return;  // Table full; drop oldest-first would be better in production
    DiagnosticEvent& ev = table_[count_++];
    ev.dtc_code          = dtc_code;
    ev.status            = DtcStatus::Pending;
    ev.occurrence_counter = 1U;
    ev.first_occurrence  = now;
    ev.last_occurrence   = now;
}

void DtcManager::clear(std::uint32_t dtc_code) noexcept {
    for (std::size_t i = 0; i < count_; ++i) {
        if (table_[i].dtc_code == dtc_code) {
            table_[i] = table_[--count_];
            return;
        }
    }
}

void DtcManager::clear_all() noexcept { count_ = 0; }

std::size_t DtcManager::snapshot(DiagnosticEvent* out_buf, std::size_t buf_size) const noexcept {
    const std::size_t n = (count_ < buf_size) ? count_ : buf_size;
    for (std::size_t i = 0; i < n; ++i) out_buf[i] = table_[i];
    return n;
}

}  // namespace adas
