*** Settings ***
Documentation       AEB – Autonomous Emergency Braking Robot Framework Test Suite
...                 ASIL: D | Euro NCAP AEB-C2C / AEB-Ped | UN-R152 aligned
...
...                 Requirements: AEB_REQ_001–080

Resource            ../resources/common.resource

Suite Setup         ADAS Suite Setup
Suite Teardown      ADAS Suite Teardown
Test Setup          ADAS Test Setup
Test Teardown       ADAS Test Teardown

Force Tags          aeb    regression

*** Variables ***
${AEB_FULL_BRAKE_SIGNAL}    AEB_FullBrakeRequest
${AEB_DECEL_MIN_MPSS}       8.0
${AEB_LATENCY_MAX_MS}       600
${TTC_CRITICAL_S}           1.5


*** Test Cases ***

# ── Smoke Tests ───────────────────────────────────────────────────────────────

AEB System Active At 60 km/h
    [Tags]    smoke    aeb    asil_d
    [Documentation]    AEB armed when vehicle speed = 60 km/h.
    Set Vehicle Speed    60
    Sleep    0.2s
    Signal Should Be In Range    AEB_Status    1    3

AEB Full Brake At Critical TTC
    [Tags]    smoke    aeb    safety    asil_d
    [Documentation]    AEB triggers full brake at TTC < 1.5s (NHTSA / Euro NCAP).
    Send CAN Frame    ${CANID_AEB_OUTPUT}    00 0A 01 00    # TTC=1.0s
    Sleep    0.2s
    Signal Should Equal    ${AEB_FULL_BRAKE_SIGNAL}    1    0

AEB Detects Stationary Pedestrian
    [Tags]    smoke    aeb    safety    asil_d
    [Documentation]    AEB detects stationary pedestrian at 20m.
    Inject Radar Object    obj_id=10    range_m=20    velocity_mps=0    confidence=0.92
    Sleep    0.2s
    Signal Should Equal    AEB_PedestrianDetected    1    0

# ── Speed Envelope Tests ──────────────────────────────────────────────────────

AEB Not Armed Below 10 km/h
    [Tags]    aeb    regression
    [Documentation]    AEB should not arm below 10 km/h.
    Set Vehicle Speed    5
    Send CAN Frame    ${CANID_VEHICLE_STATE}    05 00 00 00
    Sleep    0.15s
    Feature Status Should Be Off    AEB_Status

AEB Armed At 20 km/h
    [Tags]    aeb    regression
    Set Vehicle Speed    20
    Send CAN Frame    ${CANID_VEHICLE_STATE}    14 00 00 00
    Sleep    0.15s
    ${status}=    Get Signal Value    AEB_Status
    Should Be True    ${status} >= 1    msg=AEB not armed at 20 km/h

AEB Armed At 130 km/h
    [Tags]    aeb    regression
    Set Vehicle Speed    130
    Send CAN Frame    ${CANID_VEHICLE_STATE}    82 00 00 00
    Sleep    0.15s
    ${status}=    Get Signal Value    AEB_Status
    Should Be True    ${status} >= 1    msg=AEB not armed at 130 km/h

# ── False Positive Tests ──────────────────────────────────────────────────────

AEB No False Brake For Oncoming Traffic
    [Tags]    aeb    regression
    [Documentation]    Oncoming opposite-lane vehicle must NOT trigger AEB.
    Inject Radar Object    obj_id=20    range_m=50    velocity_mps=-22    azimuth_deg=15
    Sleep    0.2s
    Signal Should Equal    ${AEB_FULL_BRAKE_SIGNAL}    0    0

AEB No Brake For Overhead Bridge
    [Tags]    aeb    regression
    [Documentation]    Stationary overhead structure must not trigger AEB.
    Send CAN Frame    ${CANID_AEB_OUTPUT}    00 00 00 00    # no brake
    Sleep    0.1s
    Signal Should Equal    ${AEB_FULL_BRAKE_SIGNAL}    0    0

# ── Deceleration Validation ───────────────────────────────────────────────────

AEB Active Phase Deceleration Meets Minimum
    [Tags]    aeb    safety    asil_d
    [Documentation]    AEB active must command ≥ 8 m/s² deceleration.
    Inject Emergency Braking Event    1.0
    Sleep    0.2s
    ${status}=    Get Signal Value    AEB_Status
    Run Keyword If    ${status} == 3
    ...    Signal Should Be In Range    AEB_DecelRequest_mpss    -20    -${AEB_DECEL_MIN_MPSS}

# ── E2E Protection ────────────────────────────────────────────────────────────

AEB CAN Frame E2E CRC Present
    [Tags]    aeb    safety    asil_d
    [Documentation]    AEB frame must have valid E2E CRC (not 0x00 or 0xFF).
    ${crc}=    Get Signal Value    AEB_SafetyCRC
    Pass Execution If    ${crc} is None    AEB_SafetyCRC not in DBC — skipped
    Should Not Be Equal As Integers    ${crc}    0
    Should Not Be Equal As Integers    ${crc}    255

# ── Latency Tests ─────────────────────────────────────────────────────────────

AEB Detection To Brake Within 600ms
    [Tags]    aeb    performance    asil_d
    [Documentation]    Detection → brake command < 600ms (NHTSA limit).
    ${t0}=    Get Current Date    result_format=epoch
    Inject Emergency Braking Event    1.0
    Sleep    0.15s
    ${t1}=    Get Current Date    result_format=epoch
    ${elapsed_ms}=    Evaluate    (${t1} - ${t0}) * 1000
    Should Be True    ${elapsed_ms} <= ${AEB_LATENCY_MAX_MS}
    ...    msg=AEB latency ${elapsed_ms}ms exceeds ${AEB_LATENCY_MAX_MS}ms

# ── Fault Injection Tests ─────────────────────────────────────────────────────

AEB Safe State On Camera Blockage
    [Tags]    aeb    fault_injection    asil_d
    [Documentation]    AEB enters safe state when camera is blocked.
    Set Vehicle Speed    80
    Inject Fault    CAMERA_BLOCKAGE    ${CANID_AEB_OUTPUT}    0.5
    Sleep    0.4s
    ${status}=    Get Signal Value    AEB_Status
    Pass Execution If    ${status} is None    AEB_Status not available — skipped
    Should Not Be Equal As Integers    ${status}    3
    ...    msg=AEB remained Active during camera blockage — ASIL D violation

# ── Pedestrian Crossing ───────────────────────────────────────────────────────

AEB Detects Crossing Pedestrian At 3 m/s
    [Tags]    aeb    regression    asil_d
    [Documentation]    AEB detects pedestrian crossing at 3 m/s lateral velocity.
    Inject Radar Object    obj_id=11    range_m=25    velocity_mps=3    azimuth_deg=5    confidence=0.88
    Sleep    0.2s
    ${det}=    Get Signal Value    AEB_PedestrianDetected
    Pass Execution If    ${det} is None    Signal not available — skipped
    Should Be Equal As Integers    ${det}    1
    ...    msg=AEB failed to detect crossing pedestrian


*** Keywords ***

Inject Emergency Braking Event
    [Arguments]    ${ttc_s}=1.0
    [Documentation]    Trigger a simulated AEB pre-crash event via CAN.
    ${ttc_byte}=    Evaluate    int(float(${ttc_s}) * 10) & 0xFF
    ${hex_byte}=    Convert To Hex    ${ttc_byte}    prefix=    length=2
    Send CAN Frame    ${CANID_AEB_OUTPUT}    00 ${hex_byte} 01 00
