/**
 * @file    hal_i2c.h
 * @brief   HAL I2C driver interface — sensor register access over I2C/I3C.
 *
 * Supports:
 *   - 7-bit and 10-bit device addressing
 *   - Standard (100 kHz), Fast (400 kHz), Fast-Plus (1 MHz) speeds
 *   - 8-bit and 16-bit register addressing (common in CMOS sensors)
 *   - Burst read/write for register arrays
 *   - Repeated-start (combined transactions)
 *   - DMA-backed transfers for large payloads
 *
 * @copyright  (c) 2026 Industrial Vision Systems. All rights reserved.
 */

#ifndef HAL_I2C_H
#define HAL_I2C_H

#include "platform_types.h"

/* ─────────────────────────────────────────────────────────────────────────── */
/* Configuration constants                                                     */
/* ─────────────────────────────────────────────────────────────────────────── */
#define HAL_I2C_MAX_BUS_COUNT   4U
#define HAL_I2C_MAX_PAYLOAD_BYTES 256U
#define HAL_I2C_DEFAULT_TIMEOUT_MS 50U
#define HAL_I2C_RETRY_COUNT     3U

/* ─────────────────────────────────────────────────────────────────────────── */
/* Types                                                                       */
/* ─────────────────────────────────────────────────────────────────────────── */

/** @brief I2C bus speed modes. */
typedef enum {
    HAL_I2C_SPEED_STANDARD    = 100000U,   /**< 100 kHz */
    HAL_I2C_SPEED_FAST        = 400000U,   /**< 400 kHz */
    HAL_I2C_SPEED_FAST_PLUS   = 1000000U,  /**< 1 MHz   */
    HAL_I2C_SPEED_HIGH        = 3400000U,  /**< 3.4 MHz (limited HW) */
} hal_i2c_speed_t;

/** @brief Register address width. */
typedef enum {
    HAL_I2C_REG_ADDR_8BIT  = 1U,   /**< 8-bit  register address (e.g. OV5640) */
    HAL_I2C_REG_ADDR_16BIT = 2U,   /**< 16-bit register address (e.g. Sony IMX) */
} hal_i2c_reg_addr_width_t;

/** @brief HAL I2C bus handle (opaque to caller). */
typedef struct hal_i2c_bus_s *hal_i2c_bus_t;

/** @brief I2C bus initialisation configuration. */
typedef struct {
    u8                      bus_index;         /**< Physical bus index 0..3 */
    hal_i2c_speed_t         speed_hz;          /**< Clock speed */
    bool                    use_dma;           /**< Use DMA for transfers > 4 bytes */
    u32                     timeout_ms;        /**< Per-transaction timeout */
    u8                      retry_count;       /**< Auto-retry on NAK */
    bool                    enable_pullup;     /**< Enable internal pull-ups (if hw supported) */
} hal_i2c_config_t;

/** @brief Statistics counters per bus. */
typedef struct {
    u64 tx_bytes;
    u64 rx_bytes;
    u32 nak_count;
    u32 timeout_count;
    u32 bus_error_count;
    u32 retry_success_count;
    u32 transaction_count;
} hal_i2c_stats_t;

/* ─────────────────────────────────────────────────────────────────────────── */
/* API                                                                         */
/* ─────────────────────────────────────────────────────────────────────────── */

/**
 * @brief   Initialise an I2C bus.
 * @param   config    Bus configuration.
 * @param   out_bus   Output handle (valid on ISF_OK).
 * @return  ISF_OK on success.
 */
isf_status_t hal_i2c_init(const hal_i2c_config_t *config, hal_i2c_bus_t *out_bus);

/**
 * @brief   De-initialise an I2C bus and release resources.
 * @param   bus   Handle from hal_i2c_init().
 */
isf_status_t hal_i2c_deinit(hal_i2c_bus_t bus);

/**
 * @brief   Write a single register value.
 * @param   bus           Bus handle.
 * @param   dev_addr      7-bit device address (right-aligned, no R/W bit).
 * @param   addr_width    Register address width.
 * @param   reg_addr      Register address.
 * @param   data          Byte to write.
 */
isf_status_t hal_i2c_reg_write8(hal_i2c_bus_t bus,
                                 u8 dev_addr,
                                 hal_i2c_reg_addr_width_t addr_width,
                                 u32 reg_addr,
                                 u8 data);

/**
 * @brief   Read a single register value.
 * @param   out_data   Pointer to receive the register value.
 */
isf_status_t hal_i2c_reg_read8(hal_i2c_bus_t bus,
                                u8 dev_addr,
                                hal_i2c_reg_addr_width_t addr_width,
                                u32 reg_addr,
                                u8 *out_data);

/**
 * @brief   Write 16-bit value to a 16-bit addressed register.
 *          Used for sensor gains, exposures (big-endian on the wire).
 */
isf_status_t hal_i2c_reg_write16(hal_i2c_bus_t bus,
                                  u8 dev_addr,
                                  u32 reg_addr,
                                  u16 data);

/**
 * @brief   Read 16-bit value.
 */
isf_status_t hal_i2c_reg_read16(hal_i2c_bus_t bus,
                                 u8 dev_addr,
                                 u32 reg_addr,
                                 u16 *out_data);

/**
 * @brief   Burst write: write N consecutive bytes starting at reg_addr.
 *          Uses repeated-start internally to avoid releasing the bus.
 */
isf_status_t hal_i2c_burst_write(hal_i2c_bus_t bus,
                                  u8 dev_addr,
                                  hal_i2c_reg_addr_width_t addr_width,
                                  u32 reg_addr,
                                  const u8 *data,
                                  u16 len);

/**
 * @brief   Burst read: read N consecutive bytes.
 */
isf_status_t hal_i2c_burst_read(hal_i2c_bus_t bus,
                                 u8 dev_addr,
                                 hal_i2c_reg_addr_width_t addr_width,
                                 u32 reg_addr,
                                 u8 *out_buf,
                                 u16 len);

/**
 * @brief   Execute a register table (array of {addr, val} pairs terminated by sentinel).
 *          Used for sensor initialisation sequences.
 * @param   table     Flat array: [reg_h, reg_l, val, reg_h, reg_l, val, ...], sentinel = 0xFF,0xFF,0xFF.
 * @param   entry_size  Bytes per entry: 2 (8-bit addr + 8-bit val) or 3 (16-bit addr + 8-bit val).
 */
isf_status_t hal_i2c_write_reg_table(hal_i2c_bus_t bus,
                                      u8 dev_addr,
                                      const u8 *table,
                                      u16 entry_size);

/**
 * @brief   Probe a device address — returns ISF_OK if device ACKs.
 */
isf_status_t hal_i2c_probe(hal_i2c_bus_t bus, u8 dev_addr);

/**
 * @brief   Bus recovery — toggle SCL 9 times to release stuck SDA.
 */
isf_status_t hal_i2c_recover_bus(hal_i2c_bus_t bus);

/**
 * @brief   Read bus statistics.
 */
isf_status_t hal_i2c_get_stats(hal_i2c_bus_t bus, hal_i2c_stats_t *out_stats);

/**
 * @brief   Reset statistics counters.
 */
isf_status_t hal_i2c_reset_stats(hal_i2c_bus_t bus);

#endif /* HAL_I2C_H */
