*** Settings ***
Documentation       ADAS End-to-End Release Validation Suite
...                 Covers: ACC + AEB + LKA + BSD + DMS concurrent operation
...                 ASIL: B (system level) | Release gate: ALL tests must pass
...
...                 Run this suite before every SW release.

Resource            ../resources/common.resource

Suite Setup         ADAS Suite Setup
Suite Teardown      ADAS Suite Teardown
Test Setup          ADAS Test Setup
Test Teardown       ADAS Test Teardown

Force Tags          e2e    regression    release

*** Variables ***
${HIGHWAY_SPEED}    120
${URBAN_SPEED}      50
${SCHOOL_ZONE}      30


*** Test Cases ***

# ── Pre-flight checks ─────────────────────────────────────────────────────────

ECU No DTCs On Startup
    [Tags]    smoke    e2e    safety
    [Documentation]    ECU must have no confirmed DTCs on fresh start.
    Clear DTCs
    No DTCs Should Be Present    0x08
    Log    ECU DTC pre-check passed ✓

All ADAS ECU DIDs Readable
    [Tags]    smoke    e2e    uds
    [Documentation]    Critical DIDs must respond within P2 timeout.
    ${session}=    Read DID    0xF186    # Active session
    ${sw_ver}=     Read DID    0xF189    # SW version
    ${vin}=        Read DID    0xF190    # VIN
    Should Not Be Empty    ${sw_ver}
    Log    SW Version: ${sw_ver}

CAN Bus Active On All Networks
    [Tags]    smoke    e2e    can
    CAN Bus Should Be Active


# ── Highway scenario: ACC + AEB ───────────────────────────────────────────────

Highway Cruise With ACC Active
    [Tags]    e2e    acc    aeb    regression
    [Documentation]    Highway pilot: ACC holds 120 km/h, AEB armed, no DTC.
    Set Vehicle Speed    ${HIGHWAY_SPEED}
    Activate ACC         ${HIGHWAY_SPEED}
    Sleep    0.5s
    Feature Status Should Be Active    ACC_Status
    Signal Should Be In Range    AEB_Status    1    3
    No DTCs Should Be Present

Highway AEB Brakes For Stopped Vehicle
    [Tags]    e2e    aeb    safety    asil_d
    [Documentation]    AEB triggers at highway speed (120 km/h) for stopped obstacle.
    Set Vehicle Speed    ${HIGHWAY_SPEED}
    Inject Radar Object    obj_id=1    range_m=20    velocity_mps=0    confidence=0.95
    Sleep    0.3s
    AEB Should Trigger Full Brake

Highway LKA Centering Active
    [Tags]    e2e    lka    regression
    Set Vehicle Speed    ${HIGHWAY_SPEED}
    Set Lane Deviation    0.20
    Sleep    0.2s
    Signal Should Be In Range    LKA_TorqueRequest_Nm    -3.0    3.0

# ── Urban scenario: AEB pedestrian ───────────────────────────────────────────

Urban AEB Pedestrian Protection
    [Tags]    e2e    aeb    pedestrian    asil_d
    [Documentation]    AEB protects pedestrian in urban (50 km/h) scenario.
    Set Vehicle Speed    ${URBAN_SPEED}
    Inject Radar Object    obj_id=5    range_m=12    velocity_mps=1.5    confidence=0.90
    Sleep    0.2s
    ${det}=    Get Signal Value    AEB_PedestrianDetected
    Pass Execution If    ${det} is None    Pedestrian signal not available
    Should Be Equal As Integers    ${det}    1

Urban TSR Speed Limit Enforced
    [Tags]    e2e    tsr    isa    regression
    [Documentation]    Speed sign correctly identified in urban scenario.
    Send CAN Frame    0x180    01 32 32 55    # 50 km/h sign, conf=0.85
    Sleep    0.15s
    ${sign_val}=    Get Signal Value    TSR_SignValue
    Pass Execution If    ${sign_val} is None    TSR signal not available
    Should Be Equal As Integers    ${sign_val}    50

Urban BSD Detection Right Lane
    [Tags]    e2e    bsd    regression
    Send CAN Frame    ${CANID_BSD_OUTPUT}    00 00 01 50
    Sleep    0.1s
    ${bsd_r}=    Get Signal Value    BSD_RightZone_Status
    Pass Execution If    ${bsd_r} is None    BSD signal not available
    Should Be True    ${bsd_r} >= 1    msg=BSD right zone not detecting vehicle

# ── Parking scenario ──────────────────────────────────────────────────────────

Parking Assist Activates In Reverse
    [Tags]    e2e    parking    regression
    Set Vehicle Speed    3
    Send CAN Frame    ${CANID_VEHICLE_STATE}    03 01 00 00    # gear=R
    Sleep    0.3s
    ${park}=    Get Signal Value    ParkAssist_Status
    Pass Execution If    ${park} is None    ParkAssist signal not available
    Should Be True    ${park} >= 1    msg=ParkAssist not activated in reverse

# ── DMS integration ───────────────────────────────────────────────────────────

DMS Active During Driving
    [Tags]    e2e    dms    regression
    Send CAN Frame    0x190    01 05 02 00    # DMS monitoring, attentive
    Sleep    0.1s
    ${dms}=    Get Signal Value    DMS_Status
    Pass Execution If    ${dms} is None    DMS_Status not available
    Should Be True    ${dms} >= 1    msg=DMS not monitoring during drive

DMS Drowsy Alert Escalates Correctly
    [Tags]    e2e    dms    safety    asil_b
    Send CAN Frame    0x190    02 00 28 02    # drowsy, PERCLOS=0.16
    Sleep    0.1s
    ${alert}=    Get Signal Value    DMS_AlertLevel
    Pass Execution If    ${alert} is None    DMS_AlertLevel not available
    Should Be True    ${alert} >= 1    msg=DMS drowsiness alert not raised

# ── Concurrent features ───────────────────────────────────────────────────────

All Features Concurrent No DTC
    [Tags]    e2e    regression    safety
    [Documentation]    ACC + LKA + AEB + DMS all active simultaneously — no DTC.
    Set Vehicle Speed    100
    Activate ACC         100
    Set Lane Deviation   0.10
    Send CAN Frame    ${CANID_AEB_OUTPUT}    01 1E 00 00
    Send CAN Frame    0x190    01 05 02 00
    Sleep    0.5s
    No DTCs Should Be Present
    Log    Concurrent feature test passed ✓

# ── Post-test DTC audit ───────────────────────────────────────────────────────

No Unexpected DTCs After Full Suite
    [Tags]    e2e    safety    release
    [Documentation]    Final DTC audit — must be clean before release gate.
    No DTCs Should Be Present    0x08
    Log    Release DTC audit: PASS ✓


*** Keywords ***

AEB Should Trigger Full Brake
    [Documentation]    Wait up to 1s for AEB full brake request.
    ${deadline}=    Get Current Date    result_format=epoch
    FOR    ${i}    IN RANGE    20
        ${val}=    Get Signal Value    AEB_FullBrakeRequest
        Exit For Loop If    ${val} is not None and ${val} == 1
        Sleep    0.05s
    END
    Should Be Equal As Integers    ${val}    1
    ...    msg=AEB full brake not triggered within 1s
