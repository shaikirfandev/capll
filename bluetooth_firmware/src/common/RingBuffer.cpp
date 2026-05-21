/**
 * @file RingBuffer.cpp
 * @brief Explicit template instantiations for RingBuffer
 *
 * Ensures linker finds all expected template specialisations without
 * repeating the full template definition in each translation unit.
 */

#include "common/RingBuffer.hpp"

namespace bt {

// Automotive HCI byte stream (UART H4 transport)
template class RingBuffer<uint8_t,   256U>;

// ACL data buffer (max BT packet ~1021 bytes, we buffer at L2CAP boundary)
template class RingBuffer<uint8_t,  1024U>;

// HCI event code dispatch queue
template class RingBuffer<uint32_t,   64U>;

// CAN-style telemetry message IDs for automotive diagnostic integration
template class RingBuffer<uint32_t,  128U>;

}  // namespace bt
