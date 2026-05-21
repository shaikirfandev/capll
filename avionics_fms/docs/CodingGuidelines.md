# Coding Guidelines
## Avionics FMS v3.2.1 — MISRA C++:2008 + DO-178C DAL-B

## 1. Language Standard
- C++17 for host/simulation builds
- C++14 minimum for embedded target
- No RTTI (`-fno-rtti`)
- No C++ exceptions (`-fno-exceptions`) on embedded targets

## 2. Naming Conventions

| Entity | Convention | Example |
|--------|-----------|---------|
| Classes | PascalCase | `NavigationEngine` |
| Interfaces | I + PascalCase | `INavigationEngine` |
| Member variables | snake_case + `_` | `nav_state_`, `is_valid_` |
| Constants | UPPER_SNAKE_CASE | `MAX_WAYPOINTS` |
| Enum class values | UPPER_SNAKE_CASE | `FmsError::ERR_NOT_FOUND` |
| Functions/methods | snake_case | `update_gps()`, `get_nav_state()` |
| Template params | T, E, N | `Result<T, E>`, `RingBuffer<T, N>` |

## 3. Memory Management Rules

- NO `new` / `delete` in safety-critical paths (FaultManager, GuidanceComputer, etc.)
- NO `std::vector`, `std::map`, `std::string` in safety paths
- NO exceptions in safety paths
- Static arrays only: `FaultRecord fault_table_[MAX_FAULT_RECORDS]`
- Stack allocation permitted: local POD variables
- `std::array<T, N>` is allowed (fixed size)
- `std::atomic<T>` is allowed for lock-free flags

## 4. Error Handling

- Return `FmsError` enum from all public methods that can fail
- Use `Result<T, FmsError>` for functions returning a value
- Use `FMS_TRY(expr)` macro for error propagation
- NO C++ exceptions in flight-critical code
- Validate at system boundary (first entry point), not internally

## 5. Thread Safety

- Use `FreeRtosMutex` (wraps `std::mutex`) for shared state
- Release mutex BEFORE invoking callbacks (prevent priority inversion)
- Use `std::atomic<bool>` for simple flags
- Document thread ownership of each class member

## 6. DO-178C Annotations

Every public method must have:
```cpp
/**
 * @brief Brief description
 * @req SRS-XXX-NNN  (links to requirement)
 * @param name Description
 * @return Description
 */
```

## 7. Static Analysis Compliance

Run before every commit:
```bash
cppcheck --enable=all --std=c++17 src/
clang-tidy -checks="clang-analyzer-*,bugprone-*" src/
```

Zero MISRA violations allowed in safety-critical paths.

## 8. Test Requirements

- Every public method tested
- Every fault path tested
- Every enum value exercised
- `@req SRS-XXX-NNN` annotation on every TEST_F
- Mocks used for all dependencies (GMock)
