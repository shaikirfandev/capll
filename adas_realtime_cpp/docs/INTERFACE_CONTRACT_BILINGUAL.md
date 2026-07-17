# Bilingual Interface Contract / 双语接口约定

This document is a communication aid. The controlled program baseline must retain the official requirement IDs, signal names, units, and data definitions without translation changes. 本文用于中英文技术沟通；受控基线中的需求编号、信号名称、单位和数据定义不得因翻译而改变。

## Core terms / 核心术语

| English | 中文 | Contract meaning / 约定含义 |
|---|---|---|
| Adaptive Cruise Control (ACC) | 自适应巡航控制 | Time-gap based longitudinal speed and gap control / 基于时间间距的纵向速度和车距控制 |
| Autonomous Emergency Braking (AEB) | 自动紧急制动 | Collision-risk braking request subject to vehicle safety concept / 受整车安全概念约束的碰撞风险制动请求 |
| Lane Keeping Assist (LKA) | 车道保持辅助 | Lateral assistance that respects driver override / 支持驾驶员接管的横向辅助 |
| Lane Centering | 车道居中 | Continuous lane-centre tracking within the approved ODD / 在已批准运行设计域内持续跟踪车道中心 |
| Operational Design Domain (ODD) | 运行设计域 | Conditions in which the function is approved to operate / 功能获准运行的条件集合 |
| Time to Collision (TTC) | 碰撞时间 | Estimated time before impact at current closing speed / 按当前接近速度估算的碰撞剩余时间 |
| Kalman filter | 卡尔曼滤波器 | State estimator combining prediction and measurement / 融合预测和测量的状态估计器 |
| Fault | 故障 | Explicit diagnostic/safety state, never silently ignored / 显式诊断或安全状态，不得静默忽略 |
| Freshness | 新鲜度 | Age of source data against its acceptance deadline / 源数据相对于接收截止时间的年龄 |
| End-to-end protection | 端到端保护 | Counter/CRC/profile integrity mechanism across communication path / 通信路径中的计数器、CRC 和配置文件完整性机制 |

## `SensorFrame` / 传感器帧

| Field | 中文说明 | Unit / 单位 | Validation / 校验 |
|---|---|---:|---|
| `timestamp` | 源帧时间戳 | monotonic time / 单调时间 | Not future-dated; maximum age 100 ms by default / 不得晚于当前时间，默认最大年龄 100 ms |
| `vehicle.speed_mps` | 自车速度 | m/s | $0 \le v \le 70$ by default; vehicle-specific calibration required / 默认范围，需整车标定 |
| `lead.longitudinal_distance_m` | 前方目标纵向距离 | m | Positive finite value if object is valid / 目标有效时为有限正值 |
| `lead.relative_speed_mps` | 相对速度（目标减自车） | m/s | Negative means closing / 负值表示正在接近 |
| `lane.lateral_offset_m` | 车道横向偏差 | m | Positive means ego vehicle is right of lane centre / 正值表示自车位于车道中心右侧 |
| `lane.heading_error_rad` | 航向角偏差 | rad | Positive means ego heading points right / 正值表示自车航向指向右侧 |
| `confidence` | 置信度 | [0, 1] | Must meet configured function threshold / 必须满足功能配置阈值 |

## `ActuatorCommand` / 执行器命令

| Field | 中文说明 | Unit / 单位 | Safety rule / 安全规则 |
|---|---|---:|---|
| `requested_acceleration_mps2` | 请求纵向加速度 | m/s² | Final actuator gateway must re-check limits and authority / 最终执行器网关必须再次校验限值和控制权限 |
| `requested_steering_angle_rad` | 请求转向角 | rad | Rate and angle constraints apply / 受转角和转向速率限制 |
| `aeb_request` | AEB 请求标志 | Boolean / 布尔值 | Not an actuator-enable signal by itself / 不是单独的执行器使能信号 |
| `faults` | 故障位 | bit mask / 位掩码 | Forward to diagnostic and health management / 上报诊断与健康管理 |

## Communication practice / 沟通规范

- Use the English identifiers from the C++ interface in DBC, ARXML, SOME/IP IDL, test cases, CANoe panels, and defect reports. 在 DBC、ARXML、SOME/IP IDL、测试用例、CANoe 面板和缺陷报告中使用 C++ 接口中的英文标识符。
- Attach Chinese explanation next to requirements only after an approved English statement exists. 只有在英文需求获批后才添加中文说明。
- Record units explicitly; do not translate or omit SI symbols. 明确记录单位；不得翻译或省略 SI 符号。
- Escalate contradictions between translations to the requirements owner before implementation. 翻译存在冲突时，实施前应提交给需求负责人澄清。
