/**
 * @file IGpsReceiver.hpp
 * @brief GPS/GNSS Receiver interface — GPS, GLONASS, Galileo
 */
#pragma once
#include "sensors/SensorTypes.hpp"
#include "fms/FmsTypes.hpp"

namespace fms::sensors {
class IGpsReceiver {
public:
    virtual ~IGpsReceiver() = default;
    virtual fms::FmsError init()       = 0;
    virtual void          deinit()     = 0;
    virtual fms::FmsError update()     = 0;  // Called at 10Hz
    virtual const GpsRaw &get_data() const = 0;
    virtual bool          has_fix() const = 0;
    virtual fms::SystemStatus get_status() const = 0;
};
}
