/**
 * @file ErrorCodes.hpp
 * @brief Error code utilities and result type for the Bluetooth stack
 */
#pragma once
#include "../bt/BluetoothTypes.hpp"
#include <variant>

namespace bt {

/// Lightweight result type (either a value T or a BtError)
template<typename T>
class Result {
public:
    static Result ok(T val)         { Result r; r.value_ = std::move(val); return r; }
    static Result err(BtError e)    { Result r; r.error_ = e; return r; }

    bool     is_ok()  const { return error_ == BtError::OK; }
    bool     is_err() const { return error_ != BtError::OK; }
    const T &value()  const { return value_; }
    BtError  error()  const { return error_; }

private:
    T       value_{};
    BtError error_{BtError::OK};
};

/// Macro for early-return on error (similar to Rust's ? operator)
#define BT_TRY(expr)                        \
    do {                                    \
        BtError _e = (expr);                \
        if (_e != BtError::OK) return _e;   \
    } while (false)

}  // namespace bt
