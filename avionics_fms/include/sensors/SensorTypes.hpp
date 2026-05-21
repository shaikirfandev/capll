/**
 * @file SensorTypes.hpp
 * @brief Raw sensor data structures for Air Data, INS, GPS
 */
#pragma once
#include <cstdint>

namespace fms::sensors {

struct GpsRaw {
    double   lat_deg{0.0};
    double   lon_deg{0.0};
    double   alt_wgs84_m{0.0};
    double   vel_north_ms{0.0};
    double   vel_east_ms{0.0};
    double   vel_down_ms{0.0};
    double   hdop{99.0};
    double   vdop{99.0};
    double   pdop{99.0};
    uint8_t  num_satellites{0U};
    uint8_t  fix_quality{0U};  // 0=no fix, 1=2D, 2=3D, 3=DGPS, 5=RTK
    bool     valid{false};
    uint64_t timestamp_us{0U};
};

struct InsRaw {
    double   accel_x_ms2{0.0};
    double   accel_y_ms2{0.0};
    double   accel_z_ms2{0.0};
    double   gyro_x_rads{0.0};
    double   gyro_y_rads{0.0};
    double   gyro_z_rads{0.0};
    double   pitch_deg{0.0};
    double   roll_deg{0.0};
    double   true_heading_deg{0.0};
    double   mag_heading_deg{0.0};
    double   vel_north_ms{0.0};
    double   vel_east_ms{0.0};
    double   vel_down_ms{0.0};
    bool     aligned{false};
    bool     valid{false};
    uint64_t timestamp_us{0U};
};

struct AdcRaw {
    double   static_pressure_pa{101325.0};
    double   total_pressure_pa{101325.0};
    double   tat_c{15.0};       // Total Air Temp
    double   sat_c{15.0};       // Static Air Temp
    double   pressure_alt_ft{0.0};
    double   density_alt_ft{0.0};
    double   cas_kt{0.0};
    double   tas_kt{0.0};
    double   mach{0.0};
    double   isa_deviation_c{0.0};
    double   vspeed_fpm{0.0};   // Barometric
    bool     valid{false};
    uint64_t timestamp_us{0U};
};

struct VorRaw {
    uint16_t freq_khz{0U};
    double   radial_deg{0.0};   // Magnetic bearing from VOR
    double   cdi_dots{0.0};     // CDI deflection [-2.5, +2.5] dots
    bool     valid{false};
};

struct DmeRaw {
    uint16_t freq_khz{0U};
    double   distance_nm{0.0};
    double   groundspeed_kt{0.0};
    bool     valid{false};
};

}  // namespace fms::sensors
