*** Settings ***
Documentation       Common resources, variables and setup/teardown for all ADAS robot suites.
...                 Import this file in every .robot test suite.

Library             Collections
Library             String
Library             OperatingSystem
Library             DateTime
Library             ../libraries/CANLibrary.py    channel=${CAN_CHANNEL}    interface=${CAN_INTERFACE}    bitrate=${CAN_BITRATE}
Library             ../libraries/UDSLibrary.py    tx_id=${UDS_TX_ID}        rx_id=${UDS_RX_ID}
Library             ../libraries/ADASLibrary.py
Library             ../libraries/SensorLibrary.py

Variables           ../variables/global_vars.py

*** Variables ***
${SUITE_SETUP_DONE}     False

*** Keywords ***

# ── Suite-level Setup/Teardown ─────────────────────────────────────────────

ADAS Suite Setup
    [Documentation]    Connect hardware interfaces and open diagnostic session.
    Connect To CAN Bus
    Initialize ADAS Library    channel=${CAN_CHANNEL}    interface=${CAN_INTERFACE}
    Initialize Sensor Library  lidar_host=${LIDAR_HOST}  lidar_port=${LIDAR_PORT}
    Open UDS Session           default
    Log    ADAS Suite ready: ENV=${ENVIRONMENT}    level=INFO

ADAS Suite Teardown
    [Documentation]    Disconnect all hardware, close sessions.
    Run Keyword And Ignore Error    Close UDS Session
    Run Keyword And Ignore Error    Teardown ADAS Library
    Run Keyword And Ignore Error    Teardown Sensor Library
    Run Keyword And Ignore Error    Disconnect From CAN Bus
    Log    ADAS Suite teardown complete    level=INFO

# ── Test-level Setup/Teardown ─────────────────────────────────────────────

ADAS Test Setup
    [Documentation]    Ensure vehicle is in a known state before each test.
    Set Vehicle Speed    0
    Clear DTCs
    Log    Test started: ${TEST NAME}    level=INFO

ADAS Test Teardown
    [Documentation]    Run cleanup and log result after each test.
    Run Keyword If Test Failed    Log Failure Context
    Log    Test finished: ${TEST NAME} — ${TEST STATUS}    level=INFO

Log Failure Context
    [Documentation]    Capture diagnostic info on test failure.
    ${dtcs}=    Read DTCs    0x08
    Log    DTCs at failure: ${dtcs}    level=WARN

# ── Common assertions ─────────────────────────────────────────────────────

Speed Should Be Within
    [Arguments]    ${expected_kmh}    ${tolerance_kmh}=2.0
    [Documentation]    Assert VehicleSpeed within expected ± tolerance km/h.
    ${lower}=    Evaluate    ${expected_kmh} - ${tolerance_kmh}
    ${upper}=    Evaluate    ${expected_kmh} + ${tolerance_kmh}
    Signal Should Be In Range    VehicleSpeed_kmh    ${lower}    ${upper}

Feature Status Should Be Active
    [Arguments]    ${feature_signal}    ${active_value}=2
    [Documentation]    Assert ADAS feature status is Active.
    ${val}=    Get Signal Value    ${feature_signal}
    Should Be Equal As Integers    ${val}    ${active_value}
    ...    msg=${feature_signal} not active (val=${val}, expected=${active_value})

Feature Status Should Be Off
    [Arguments]    ${feature_signal}
    [Documentation]    Assert ADAS feature status is Off (0).
    ${val}=    Get Signal Value    ${feature_signal}
    Should Be Equal As Integers    ${val}    0
    ...    msg=${feature_signal} not Off (val=${val})

Wait For ECU Recovery
    [Arguments]    ${timeout_s}=5
    [Documentation]    Wait for ECU to resume sending frames after reset.
    Sleep    ${timeout_s}s
    CAN Bus Should Be Active
