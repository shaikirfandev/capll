#include "adas/estimation.hpp"

#include <algorithm>
#include <cmath>

namespace adas {

void RangeKalmanFilter::reset(double range_m, double range_rate_mps) noexcept {
    x_[0] = range_m;
    x_[1] = range_rate_mps;
    p_[0][0] = 25.0; p_[0][1] = 0.0;
    p_[1][0] = 0.0;  p_[1][1] = 9.0;
    initialized_ = true;
}

bool RangeKalmanFilter::update(double z_range, double z_rate, double dt_s) noexcept {
    if (!std::isfinite(z_range) || !std::isfinite(z_rate) || dt_s <= 0.0 || dt_s > 0.2) return false;
    if (!initialized_) reset(z_range, z_rate);

    x_[0] += dt_s * x_[1];
    const double q_range = 0.25 * dt_s * dt_s;
    const double q_rate = 1.0 * dt_s;
    const double p00 = p_[0][0] + dt_s * (p_[0][1] + p_[1][0]) + dt_s * dt_s * p_[1][1] + q_range;
    const double p01 = p_[0][1] + dt_s * p_[1][1];
    const double p10 = p_[1][0] + dt_s * p_[1][1];
    const double p11 = p_[1][1] + q_rate;
    p_[0][0] = p00; p_[0][1] = p01; p_[1][0] = p10; p_[1][1] = p11;

    const auto scalar_update = [this](double measurement, double measurement_variance, bool measure_range) noexcept {
        const std::size_t index = measure_range ? 0U : 1U;
        const double innovation = measurement - x_[index];
        const double innovation_variance = p_[index][index] + measurement_variance;
        if (!std::isfinite(innovation_variance) || innovation_variance <= 1e-9) return false;

        const double k0 = p_[0][index] / innovation_variance;
        const double k1 = p_[1][index] / innovation_variance;
        const double old_p00 = p_[0][0];
        const double old_p01 = p_[0][1];
        const double old_p10 = p_[1][0];
        const double old_p11 = p_[1][1];
        x_[0] += k0 * innovation;
        x_[1] += k1 * innovation;

        // Joseph form: P = (I-KH)P(I-KH)' + KRK'. It preserves symmetry and PSD better than a simplified update.
        const double h0 = measure_range ? 1.0 : 0.0;
        const double h1 = measure_range ? 0.0 : 1.0;
        const double a00 = 1.0 - k0 * h0;
        const double a01 = -k0 * h1;
        const double a10 = -k1 * h0;
        const double a11 = 1.0 - k1 * h1;
        p_[0][0] = a00 * (a00 * old_p00 + a01 * old_p10) + a01 * (a00 * old_p01 + a01 * old_p11) + k0 * measurement_variance * k0;
        p_[0][1] = a00 * (a10 * old_p00 + a11 * old_p10) + a01 * (a10 * old_p01 + a11 * old_p11) + k0 * measurement_variance * k1;
        p_[1][0] = p_[0][1];
        p_[1][1] = a10 * (a10 * old_p00 + a11 * old_p10) + a11 * (a10 * old_p01 + a11 * old_p11) + k1 * measurement_variance * k1;
        return std::isfinite(x_[0]) && std::isfinite(x_[1]);
    };

    constexpr double kRangeMeasurementVariance = 2.25;
    constexpr double kRangeRateMeasurementVariance = 0.64;
    if (!scalar_update(z_range, kRangeMeasurementVariance, true)) return false;
    if (!scalar_update(z_rate, kRangeRateMeasurementVariance, false)) return false;
    return true;
}

}  // namespace adas
