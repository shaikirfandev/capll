/**
 * @file IArinc429.hpp
 * @brief ARINC 429 bus interface — bi-directional (Tx/Rx)
 */
#pragma once
#include "comms/CommsTypes.hpp"
#include "fms/FmsTypes.hpp"
#include <functional>

namespace fms::comms {

using Arinc429RxCb = std::function<void(const Arinc429Frame &)>;

class IArinc429 {
public:
    virtual ~IArinc429() = default;

    virtual fms::FmsError init(uint8_t channel, uint32_t speed_kbps) = 0;
    virtual void          deinit() = 0;

    /** Transmit a single word. Odd parity computed internally. */
    virtual fms::FmsError transmit(uint8_t label, uint8_t sdi,
                                    uint32_t data_bits,
                                    Arinc429Ssm ssm) = 0;

    /** Transmit a pre-built 32-bit word */
    virtual fms::FmsError transmit_raw(Arinc429Word word) = 0;

    /** Register receive callback invoked on label match */
    virtual void set_rx_callback(uint8_t label, Arinc429RxCb cb) = 0;

    /** Encode BNR (Binary) value to ARINC word */
    static Arinc429Word encode_bnr(uint8_t label, uint8_t sdi,
                                    double value, double resolution,
                                    int8_t msb_position,
                                    Arinc429Ssm ssm);

    /** Decode BNR word to engineering units */
    static double decode_bnr(Arinc429Word word, double resolution,
                               int8_t msb_position);

    /** Compute odd parity bit for 32-bit word (bit 32) */
    static uint32_t compute_parity(uint32_t word);

    virtual fms::SystemStatus get_status() const = 0;
};

}  // namespace fms::comms
