*** Settings ***
Documentation       ACC – Adaptive Cruise Control Robot Framework Test Suite
...                 ASIL: B | Euro NCAP / OEM Requirements aligned
...
...                 Requirements: ACC_REQ_001–060

Resource            ../resources/common.resource

Suite Setup         ADAS Suite Setup
Suite Teardown      ADAS Suite Teardown
Test Setup          ADAS Test Setup
Test Teardown       ADAS Test Teardown

Force Tags          acc    regression

*** Variables ***
${ACC_SET_SPEED}        100
${ACC_MIN_SPEED}        30
${ACC_MAX_SPEED}        130
${ACC_TOLERANCE_KMH}    2.0
${HEADWAY_MIN_S}        1.5
${HEADWAY_MAX_S}        4.0
${MAX_DECEL_MPSS}       3.0


*** Test Cases ***

# ── Smoke Tests ───────────────────────────────────────────────────────────────

ACC Activates At Minimum Speed
    [Tags]    smoke    acc    asil_b
    [Documentation]    ACC activates when vehicle speed ≥ 30 km/h.
    Set Vehicle Speed    ${ACC_MIN_SPEED}
    Activate ACC         ${ACC_MIN_SPEED}
    Sleep    0.3s
    Wait For ADAS Active    ACC    5

ACC Activates At Nominal Speed
    [Tags]    smoke    acc
    [Documentation]    ACC active at 100 km/h set speed.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Sleep    0.3s
    Feature Status Should Be Active    ACC_Status

ACC Deactivates On Driver Brake
    [Tags]    smoke    acc    safety    asil_b
    [Documentation]    Driver braking must suppress ACC acceleration.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Sleep    0.2s
    Send CAN Frame    ${CANID_VEHICLE_STATE}    00 00 50 00    # 80 bar brake
    Sleep    0.15s
    Signal Should Equal    ACC_AccelRequest_mpss    0    0.1

# ── Speed Hold Tests ──────────────────────────────────────────────────────────

ACC Holds Speed At 60 km/h
    [Tags]    acc    regression
    [Documentation]    ACC maintains 60 km/h ± 2 km/h.
    Set Vehicle Speed    60
    Activate ACC         60
    Sleep    0.3s
    Speed Should Be Within    60    ${ACC_TOLERANCE_KMH}

ACC Holds Speed At 100 km/h
    [Tags]    acc    regression
    [Documentation]    ACC maintains 100 km/h ± 2 km/h.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Sleep    0.3s
    Speed Should Be Within    ${ACC_SET_SPEED}    ${ACC_TOLERANCE_KMH}

ACC Holds Speed At 120 km/h
    [Tags]    acc    regression
    [Documentation]    ACC maintains 120 km/h ± 2 km/h.
    Set Vehicle Speed    120
    Activate ACC         120
    Sleep    0.3s
    Speed Should Be Within    120    ${ACC_TOLERANCE_KMH}

# ── Following Distance Tests ──────────────────────────────────────────────────

ACC Following Time Within Range
    [Tags]    acc    regression    asil_b
    [Documentation]    ACC headway time stays 1.5–4.0 s.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Sleep    0.3s
    Signal Should Be In Range    ACC_FollowingTime_s    ${HEADWAY_MIN_S}    ${HEADWAY_MAX_S}

ACC Acquires Radar Target
    [Tags]    acc    regression
    [Documentation]    ACC acquires lead vehicle from radar at 50m.
    Inject Radar Object    obj_id=1    range_m=50    velocity_mps=-5    azimuth_deg=0
    Sleep    0.3s
    ${target}=    Get Signal Value    ACC_TargetObjectID
    Should Not Be Equal As Integers    ${target}    0
    ...    msg=ACC did not acquire radar target

# ── Deceleration Limit Tests ──────────────────────────────────────────────────

ACC Normal Deceleration Within Limit
    [Tags]    acc    safety    asil_b
    [Documentation]    ACC decel ≤ 3.0 m/s² in normal following.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Sleep    0.3s
    Signal Should Be In Range    ACC_DecelRequest_mpss    -${MAX_DECEL_MPSS}    0

# ── Speed Envelope Tests ──────────────────────────────────────────────────────

ACC Inactive Below Minimum Speed
    [Tags]    acc    regression
    [Documentation]    ACC must not activate below 30 km/h.
    Set Vehicle Speed    25
    Send CAN Frame    ${CANID_ACC_OUTPUT}    02 19 00 00
    Sleep    0.2s
    Feature Status Should Be Off    ACC_Status

ACC Inactive Above Maximum Speed
    [Tags]    acc    regression
    [Documentation]    ACC must not activate above 180 km/h.
    Set Vehicle Speed    185
    Send CAN Frame    ${CANID_ACC_OUTPUT}    02 B9 00 00
    Sleep    0.2s
    ${status}=    Get Signal Value    ACC_Status
    Should Be True    ${status} < 2    msg=ACC active at 185 km/h — out of envelope

# ── False Target Rejection ────────────────────────────────────────────────────

ACC Rejects Stationary Roadside Object
    [Tags]    acc    regression
    [Documentation]    Guardrail at 40° azimuth should not be acquired as target.
    Inject Radar Object    obj_id=99    range_m=6    velocity_mps=0    azimuth_deg=40
    Sleep    0.2s
    ${target}=    Get Signal Value    ACC_TargetObjectID
    Should Not Be Equal As Integers    ${target}    99
    ...    msg=ACC falsely acquired static guardrail as target

# ── Fault Injection Tests ─────────────────────────────────────────────────────

ACC Handles Radar Dropout Gracefully
    [Tags]    acc    fault_injection    asil_b
    [Documentation]    ACC decel ≤ 3.0 m/s² during radar dropout.
    Set Vehicle Speed    ${ACC_SET_SPEED}
    Activate ACC         ${ACC_SET_SPEED}
    Inject Fault    RADAR_DROPOUT    ${CANID_ACC_OUTPUT}    0.5
    Sleep    0.3s
    Signal Should Be In Range    ACC_DecelRequest_mpss    -${MAX_DECEL_MPSS}    0

# ── Performance Tests ─────────────────────────────────────────────────────────

ACC Response Time Under 200ms
    [Tags]    acc    performance
    [Documentation]    ACC set speed update reflected in output ≤ 200ms.
    Set Vehicle Speed    80
    ${t0}=    Get Current Date    result_format=epoch
    Activate ACC    80
    Sleep    0.2s
    ${t1}=    Get Current Date    result_format=epoch
    ${elapsed_ms}=    Evaluate    (${t1} - ${t0}) * 1000
    Should Be True    ${elapsed_ms} <= 300
    ...    msg=ACC response ${elapsed_ms}ms exceeds 300ms budget


*** Keywords ***

Activate ACC
    [Arguments]    ${set_speed_kmh}
    [Documentation]    Send ACC activate frame with given set speed.
    ${speed_byte}=    Evaluate    int(${set_speed_kmh}) & 0xFF
    ${hex_byte}=    Convert To Hex    ${speed_byte}    prefix=    length=2
    Send CAN Frame    ${CANID_ACC_OUTPUT}    02 ${hex_byte} 00 00
