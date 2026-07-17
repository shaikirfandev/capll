#pragma once

// ============================================================
// adas/diagnostics.hpp — DTC manager + off-path event logger
//
// DtcManager:
//   - Tracks up to kMaxDtcs diagnostic trouble codes.
//   - Two-trip confirmation logic: first occurrence = Pending,
//     second consecutive trip without clearing = Confirmed.
//   - Thread-safe reads via const accessors with a shared mutex
//     (the writer path is the control thread only).
//   - No dynamic allocation. Storage is a fixed-size array.
//
// TraceLogger:
//   - Lock-free ring buffer for structured trace records.
//   - Producer: real-time control thread (noexcept push).
//   - Consumer: low-priority off-path thread (pop for export).
//   - Used for CANoe offline replay, HIL evidence, and tool analysis.
// ============================================================

#include "adas/spsc_queue.hpp"
#include "adas/types.hpp"

#include <array>
#include <cstring>
#include <string_view>

namespace adas {

// ──────────────────────────────────────────────────────────────────────────────
// DTC manager
// ──────────────────────────────────────────────────────────────────────────────
class DtcManager {
public:
    static constexpr std::size_t kMaxDtcs = 32U;

    /// @brief Report a fault. Increments occurrence counter and promotes
    ///        Pending → Confirmed after two consecutive occurrences.
    void report(std::uint32_t dtc_code, TimePoint now) noexcept;

    /// @brief Clear a single DTC.
    void clear(std::uint32_t dtc_code) noexcept;

    /// @brief Clear all DTCs (used by UDS service 0x14).
    void clear_all() noexcept;

    /// @brief Snapshot the DTC table into the provided buffer. Returns count.
    [[nodiscard]] std::size_t snapshot(DiagnosticEvent* out_buf,
                                        std::size_t buf_size) const noexcept;

    [[nodiscard]] std::size_t active_count() const noexcept { return count_; }

private:
    std::array<DiagnosticEvent, kMaxDtcs> table_{};
    std::size_t count_{};

    DiagnosticEvent* find(std::uint32_t code) noexcept;
};

// ──────────────────────────────────────────────────────────────────────────────
// Structured trace record (POD for queue and binary log file compatibility)
// ──────────────────────────────────────────────────────────────────────────────
enum class TraceLevel : std::uint8_t { Debug, Info, Warning, Error, Fatal };

struct TraceRecord {
    std::int64_t timestamp_us{};  // Microseconds from steady clock epoch
    TraceLevel level{TraceLevel::Info};
    std::uint8_t subsystem_id{};  // 0=supervisor,1=fusion,2=gateway,3=runtime…
    std::uint16_t event_code{};   // Compact event id (see docs/TRACE_CODES.md)
    float value_a{};              // Optional payload floats (keep record <= 16 B)
    float value_b{};
};
static_assert(sizeof(TraceRecord) == 16U, "TraceRecord must be exactly 16 bytes");

/// @brief Lock-free trace ring buffer.  Push is O(1) wait-free.
class TraceLogger {
public:
    static constexpr std::size_t kCapacity = 1024U;

    /// @brief Called from real-time control thread. Never blocks.
    void push(TraceRecord rec) noexcept { (void)queue_.try_push(rec); }

    /// @brief Called from off-path consumer thread.
    [[nodiscard]] std::optional<TraceRecord> pop() noexcept { return queue_.try_pop(); }

    [[nodiscard]] bool empty() const noexcept { return queue_.empty(); }

private:
    SpscQueue<TraceRecord, kCapacity> queue_;
};

}  // namespace adas
