# Coding Guidelines — Bluetooth Firmware

## C++ Standard

C++17. C++20 features (ranges, concepts, coroutines) avoided for compiler compatibility with GCC 9 (automotive toolchains).

## File Naming

| Artefact | Convention |
|---|---|
| Public interface headers | `include/bt/IBluetoothController.hpp` |
| Concrete class headers | `src/bt/BluetoothController.hpp` |
| Implementation files | `src/bt/BluetoothController.cpp` |
| Test files | `tests/unit/test_ble_advertiser.cpp` |
| Mock files | `tests/unit/mocks/MockBtController.hpp` |

## Class Structure

```cpp
class Foo final : public IFoo {
public:
    Foo();            // Constructor — no heavy work; defer to init()
    ~Foo() override;  // Destructor — RAII cleanup only

    // Public API (matching interface)
    BtError init(const Config &cfg) override;
    void    deinit()                override;

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
```

## Error Handling

- Return `BtError` or `Result<T>` from all fallible functions.
- No exceptions (embedded targets often compile with `-fno-exceptions`).
- Use `BT_TRY(expr)` to propagate errors without nesting.
- Never return `bool` for functions that can fail with distinguishable error codes.

## Memory

- No `new` / `delete` outside of smart pointer construction.
- `std::unique_ptr` for exclusive ownership (Pimpl).
- `std::shared_ptr` only when shared ownership is genuinely required.
- Containers (`std::vector`, `std::map`, etc.) preferred over raw arrays on host.
- On embedded targets: prefer stack allocation; use `std::array<T,N>` for fixed-size.

## Threading

- Every shared mutable state guarded by a mutex or atomic.
- `std::shared_mutex` for reader-heavy data (subscriber maps).
- `std::atomic<bool>` for thread-stop flags (never `volatile`).
- Never hold a mutex across a blocking call or I/O.
- Document which thread owns each piece of state.

## Naming

| Symbol | Style | Example |
|---|---|---|
| Types / Classes | PascalCase | `GattServer`, `BtError` |
| Member functions | snake_case | `add_service()`, `start_scan()` |
| Private members | trailing `_` | `impl_`, `running_`, `mtx_` |
| Constants | SCREAMING_SNAKE | `MAX_CONNECTIONS`, `HCI_UART_BAUD` |
| Namespaces | lowercase | `bt::hal`, `bt::rtos`, `bt::app` |

## Logging

Use `BT_LOG_*` macros — never `printf` or `std::cout` in library code:
```cpp
BT_LOG_INFO(TAG, "Connection established handle=0x{:04X}", handle);
BT_LOG_WARN(TAG, "Retry attempt {}/{}", attempt, MAX_RETRIES);
BT_LOG_ERROR(TAG, "HCI command failed: {}", bt_error_str(err));
```

## Documentation

Doxygen comments on all public API headers:
```cpp
/**
 * @brief Start BLE advertising with the given parameters.
 * @param params Advertising interval and type configuration.
 * @param adv_data Advertising data (max 31 bytes).
 * @param scan_rsp Scan response data (max 31 bytes).
 * @return BtError::OK on success, BtError::ERR_INVALID_PARAM if intervals invalid.
 */
BtError start(const AdvParams &params, const AdvData &adv_data, const AdvData &scan_rsp);
```

## Forbidden

- `reinterpret_cast` outside of HAL register access
- `const_cast` (sign of a design problem)
- `static` local mutable variables outside of thread-safe Singleton
- `std::cin` / `std::cout` in library code
- Implicit numeric conversions — use `static_cast<>` explicitly
