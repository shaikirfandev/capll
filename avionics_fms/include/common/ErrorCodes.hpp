/**
 * @file ErrorCodes.hpp
 * @brief Result<T,E> monad and FMS_TRY macro
 */
#pragma once
#include "fms/FmsTypes.hpp"
#include <utility>

namespace fms {

template <typename T, typename E = FmsError>
class Result {
public:
    static Result ok(T v)  noexcept { Result r; r.ok_ = true;  r.val_ = std::move(v); return r; }
    static Result err(E e) noexcept { Result r; r.ok_ = false; r.err_ = e;            return r; }

    [[nodiscard]] bool is_ok()    const noexcept { return  ok_; }
    [[nodiscard]] bool is_err()   const noexcept { return !ok_; }
    [[nodiscard]] const T& value() const noexcept { return val_; }
    [[nodiscard]] E        error() const noexcept { return err_; }

private:
    bool ok_{false};
    T    val_{};
    E    err_{FmsError::OK};
};

}  // namespace fms

#define FMS_TRY(expr)                          \
    do {                                       \
        auto _r = (expr);                      \
        if (_r != fms::FmsError::OK) {         \
            return _r;                         \
        }                                      \
    } while (false)
