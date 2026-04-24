/**
 * @file    can_driver.cpp
 * @brief   CAN driver implementation — simulation variant uses a loopback queue.
 *
 * On an actual Cortex-M4 with bxCAN peripheral:
 *   - init() would configure CAN1->BTR for 500kbps timing
 *   - transmit() would write to CAN1->sTxMailBox[free_mailbox]
 *   - Receive ISR would push incoming frames into the ring buffer
 *   - Filter banks configured via CAN1->sFilterRegister
 */

#include "drivers/can_driver.hpp"
#include "hal/hal_timer.hpp"
#include <cstdio>

#ifdef SIMULATION_BUILD
#include <cstring>
#endif

namespace drivers {

// ── Initialise ────────────────────────────────────────────────────────────────

Status CanDriver::init(const CanConfig& cfg) {
    cfg_ = cfg;

#ifdef SIMULATION_BUILD
    // Simulation: nothing to configure in hardware
    std::printf("[CAN] Simulation driver initialised — channel %u, %u bps\n",
                cfg.channel, static_cast<uint32_t>(cfg.bitrate));
#else
    // Embedded: configure bxCAN peripheral
    // RCC->APB1ENR |= RCC_APB1ENR_CAN1EN;
    // GPIOA->MODER |= ...
    // CAN1->MCR |= CAN_MCR_INRQ;  // Request init mode
    // while (!(CAN1->MSR & CAN_MSR_INAK));
    // CAN1->BTR = compute_btr(cfg.bitrate);
    // CAN1->MCR &= ~CAN_MCR_INRQ;  // Leave init mode
    // NVIC_EnableIRQ(CAN1_RX0_IRQn);
#endif

    initialised_ = true;
    return Status::OK;
}

// ── Transmit ──────────────────────────────────────────────────────────────────

Status CanDriver::transmit(const CanFrame& frame) {
    if (!initialised_) return Status::NOT_READY;
    if (bus_off_)      return Status::FAULT;

#ifdef SIMULATION_BUILD
    // Simulation: echo tx back to own rx buffer (loopback)
    onRxIsr(frame);
    return Status::OK;
#else
    // Embedded: wait for free TX mailbox (up to 50ms)
    TickType_t start = hal::Timer::getTick();
    while ((CAN1->TSR & CAN_TSR_TME0) == 0u) {
        if (hal::Timer::elapsed(start) > 50u) return Status::TIMEOUT;
    }
    // Fill mailbox 0
    CAN1->sTxMailBox[0].TIR  = (frame.id << 21u) | CAN_TI0R_TXRQ;
    CAN1->sTxMailBox[0].TDTR = frame.dlc & 0x0Fu;
    CAN1->sTxMailBox[0].TDLR =
        (frame.data[3] << 24u) | (frame.data[2] << 16u) |
        (frame.data[1] << 8u)  |  frame.data[0];
    CAN1->sTxMailBox[0].TDHR =
        (frame.data[7] << 24u) | (frame.data[6] << 16u) |
        (frame.data[5] << 8u)  |  frame.data[4];
    return Status::OK;
#endif
}

// ── Receive ───────────────────────────────────────────────────────────────────

Status CanDriver::receive(CanFrame& out) {
    if (rx_count_ == 0u) return Status::NOT_READY;

    out = rx_buf_[rx_tail_];
    rx_tail_ = (rx_tail_ + 1u) % RX_BUFFER_SIZE;
    rx_count_--;
    return Status::OK;
}

// ── ISR callback ──────────────────────────────────────────────────────────────

void CanDriver::onRxIsr(const CanFrame& frame) {
    if (rx_count_ >= RX_BUFFER_SIZE) {
        // Ring buffer full — drop oldest frame
        rx_tail_ = (rx_tail_ + 1u) % RX_BUFFER_SIZE;
        rx_count_--;
    }
    rx_buf_[rx_head_] = frame;
    rx_buf_[rx_head_].timestamp = hal::Timer::getTick();
    rx_head_ = (rx_head_ + 1u) % RX_BUFFER_SIZE;
    rx_count_++;
}

// ── Filter ────────────────────────────────────────────────────────────────────

Status CanDriver::addFilter(uint32_t id, uint32_t mask) {
#ifdef SIMULATION_BUILD
    UNUSED(id); UNUSED(mask);
    return Status::OK;
#else
    // Configure a filter bank pair (simplified — bank 0)
    // CAN1->FMR  |= CAN_FMR_FINIT;
    // CAN1->FA1R &= ~BIT(0);
    // CAN1->sFilterRegister[0].FR1 = (id   << 21u);
    // CAN1->sFilterRegister[0].FR2 = (mask << 21u);
    // CAN1->FM1R &= ~BIT(0);   // Mask mode
    // CAN1->FS1R |=  BIT(0);   // 32-bit scale
    // CAN1->FA1R |=  BIT(0);
    // CAN1->FMR  &= ~CAN_FMR_FINIT;
    return Status::OK;
#endif
}

} // namespace drivers
