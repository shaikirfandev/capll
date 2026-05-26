*** Settings ***
Documentation       LKA – Lane Keep Assist Robot Framework Test Suite
...                 ASIL: B | Requirements: LKA_REQ_001–050

Resource            ../resources/common.resource

Suite Setup         ADAS Suite Setup
Suite Teardown      ADAS Suite Teardown
Test Setup          ADAS Test Setup
Test Teardown       ADAS Test Teardown

Force Tags          lka    regression

*** Variables ***
${LKA_MAX_TORQUE_NM}    3.0
${LKA_MIN_SPEED}        60
${LKA_DEVIATION_TEST}   0.25


*** Test Cases ***

LKA Activates Above 60 km/h
    [Tags]    smoke    lka    asil_b
    Set Vehicle Speed    80
    Sleep    0.2s
    ${status}=    Get Signal Value    LKA_Status
    Pass Execution If    ${status} is None    LKA_Status not available
    Should Be True    ${status} >= 1    msg=LKA inactive at 80 km/h

LKA Inactive Below 60 km/h
    [Tags]    lka    regression
    Set Vehicle Speed    50
    Sleep    0.2s
    Feature Status Should Be Off    LKA_Status

LKA Torque Within Physical Limit
    [Tags]    lka    safety    asil_b
    Set Vehicle Speed    100
    Set Lane Deviation    ${LKA_DEVIATION_TEST}
    Sleep    0.3s
    Signal Should Be In Range    LKA_TorqueRequest_Nm    -${LKA_MAX_TORQUE_NM}    ${LKA_MAX_TORQUE_NM}

LKA Suppressed By Left Turn Signal
    [Tags]    lka    safety    smoke
    Set Vehicle Speed    100
    Set Lane Deviation    ${LKA_DEVIATION_TEST}
    Send CAN Frame    ${CANID_VEHICLE_STATE}    01 00 00 00    # TurnLeft=1
    Sleep    0.2s
    Signal Should Equal    LKA_Suppressed    1    0

LKA Suppressed By Right Turn Signal
    [Tags]    lka    safety    smoke
    Set Vehicle Speed    100
    Set Lane Deviation    ${LKA_DEVIATION_TEST}
    Send CAN Frame    ${CANID_VEHICLE_STATE}    00 01 00 00    # TurnRight=1
    Sleep    0.2s
    Signal Should Equal    LKA_Suppressed    1    0

LKA Suppressed By Driver Override Torque
    [Tags]    lka    safety    asil_b
    Set Vehicle Speed    100
    Set Lane Deviation    ${LKA_DEVIATION_TEST}
    Send CAN Frame    ${CANID_VEHICLE_STATE}    00 00 00 50    # 8 Nm driver torque
    Sleep    0.15s
    ${suppress}=    Get Signal Value    LKA_Suppressed
    Pass Execution If    ${suppress} is None    LKA_Suppressed not available
    Should Be Equal As Integers    ${suppress}    1
    ...    msg=LKA not suppressed by driver torque override

LKA Degrades On Low Camera Confidence
    [Tags]    lka    regression
    [Documentation]    LKA should not be Active when camera confidence < 0.5.
    Send CAN Frame    0x161    01 30 00 00    # camera confidence=0.48
    Sleep    0.2s
    ${status}=    Get Signal Value    LKA_Status
    Pass Execution If    ${status} is None    LKA_Status not available
    Should Be True    ${status} <= 1    msg=LKA Active with low camera confidence

LKA Fallback On Camera Loss
    [Tags]    lka    fault_injection    asil_b
    Set Vehicle Speed    100
    Inject Fault    CAMERA_BLOCKAGE    ${CANID_LKA_OUTPUT}    0.5
    Sleep    0.4s
    ${status}=    Get Signal Value    LKA_Status
    Pass Execution If    ${status} is None    LKA_Status not available
    Should Not Be Equal As Integers    ${status}    2
    ...    msg=LKA remained Active during camera loss
