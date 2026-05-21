/**
 * @file FixedPoint.hpp
 * @brief Q15.16 fixed-point arithmetic — deterministic, no FPU required
 */
#pragma once
#include <cstdint>

namespace fms {

class FixedQ16 {
public:
    static constexpr int FRAC_BITS = 16;
    static constexpr int32_t ONE   = 1 << FRAC_BITS;

    constexpr FixedQ16() noexcept : raw_(0) {}
    explicit constexpr FixedQ16(int32_t raw) noexcept : raw_(raw) {}

    static constexpr FixedQ16 from_float(float v) noexcept {
        return FixedQ16{static_cast<int32_t>(v * static_cast<float>(ONE))};
    }
    [[nodiscard]] constexpr float to_float() const noexcept {
        return static_cast<float>(raw_) / static_cast<float>(ONE);
    }
    [[nodiscard]] constexpr int32_t raw() const noexcept { return raw_; }

    constexpr FixedQ16 operator+(FixedQ16 o) const noexcept { return FixedQ16{raw_ + o.raw_}; }
    constexpr FixedQ16 operator-(FixedQ16 o) const noexcept { return FixedQ16{raw_ - o.raw_}; }
    constexpr FixedQ16 operator*(FixedQ16 o) const noexcept {
        return FixedQ16{static_cast<int32_t>((static_cast<int64_t>(raw_) * o.raw_) >> FRAC_BITS)};
    }
    constexpr FixedQ16 operator/(FixedQ16 o) const noexcept {
        return FixedQ16{static_cast<int32_t>((static_cast<int64_t>(raw_) << FRAC_BITS) / o.raw_)};
    }
    constexpr bool operator<(FixedQ16 o)  const noexcept { return raw_ < o.raw_; }
    constexpr bool operator>(FixedQ16 o)  const noexcept { return raw_ > o.raw_; }
    constexpr bool operator==(FixedQ16 o) const noexcept { return raw_ == o.raw_; }

private:
    int32_t raw_;
};

}  // namespace fms
