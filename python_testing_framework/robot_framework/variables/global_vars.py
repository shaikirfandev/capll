"""
robot_framework/variables/global_vars.py

Global variable file for Robot Framework ADAS suites.
Values can be overridden via CLI: --variable CAN_CHANNEL:PCAN0
"""

# ── CAN Bus ───────────────────────────────────────────────────────────────────
CAN_CHANNEL    = "virtual"
CAN_INTERFACE  = "virtual"
CAN_BITRATE    = 500_000
CAN_FD_BITRATE = 2_000_000

# ── UDS ───────────────────────────────────────────────────────────────────────
UDS_TX_ID      = 0x740
UDS_RX_ID      = 0x748
UDS_P2_TIMEOUT = 2.0  # seconds

# ── LiDAR / Radar ────────────────────────────────────────────────────────────
LIDAR_HOST     = "127.0.0.1"
LIDAR_PORT     = 2368
RADAR_HOST     = "127.0.0.1"
RADAR_PORT     = 1234

# ── CAN Frame IDs ────────────────────────────────────────────────────────────
CANID_ACC_OUTPUT    = 0x120
CANID_AEB_OUTPUT    = 0x150
CANID_LKA_OUTPUT    = 0x160
CANID_BSD_OUTPUT    = 0x170
CANID_TSR_OUTPUT    = 0x180
CANID_DMS_OUTPUT    = 0x190
CANID_PARK_OUTPUT   = 0x230
CANID_VEHICLE_STATE = 0x130
CANID_DIAG_TX       = 0x740
CANID_DIAG_RX       = 0x748

# ── Timing requirements (ms) ─────────────────────────────────────────────────
AEB_LATENCY_MAX_MS  = 600
ACC_CYCLE_MAX_MS    = 100
LKA_CYCLE_MAX_MS    = 100
FUSION_LATENCY_MS   = 50
UDS_P2_MAX_MS       = 2000

# ── Safety limits ─────────────────────────────────────────────────────────────
ACC_MAX_DECEL_MPSS   = 3.0
AEB_MIN_DECEL_MPSS   = 8.0
LKA_MAX_TORQUE_NM    = 3.0
RADAR_MAX_RANGE_M    = 200.0
RADAR_MIN_UPDATE_HZ  = 10
CAMERA_MIN_FPS       = 25.0
LIDAR_MIN_POINTS     = 100

# ── Environment ───────────────────────────────────────────────────────────────
ENVIRONMENT    = "ci"
SW_VERSION     = "DEV"
DBC_PATH       = ""

# ── Test execution ────────────────────────────────────────────────────────────
GLOBAL_TIMEOUT_S = 30
SHORT_TIMEOUT_S  = 5
SETTLE_TIME_S    = 0.3
