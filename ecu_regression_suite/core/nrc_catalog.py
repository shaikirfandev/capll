"""
NRC (Negative Response Code) catalog — ISO 14229-1 Annex A.

Maps every standard NRC hex code to a machine-readable name, human-readable
description, and whether it should be treated as transient (retry-able).

Usage::

    from core.nrc_catalog import NRCCode, describe_nrc, is_transient_nrc

    code = NRCCode.SECURITY_ACCESS_DENIED    # 0x33
    print(describe_nrc(0x33))
    # → "0x33 securityAccessDenied: Security level insufficient for this request"
"""
from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple


# ---------------------------------------------------------------------------
# NRC enum
# ---------------------------------------------------------------------------

class NRCCode(IntEnum):
    """ISO 14229-1 Negative Response Codes (Annex A, Table A.1)."""

    GENERAL_REJECT                                   = 0x10
    SERVICE_NOT_SUPPORTED                            = 0x11
    SUB_FUNCTION_NOT_SUPPORTED                       = 0x12
    INCORRECT_MSG_LENGTH_OR_INVALID_FORMAT           = 0x13
    RESPONSE_TOO_LONG                                = 0x14
    BUSY_REPEAT_REQUEST                              = 0x21
    CONDITIONS_NOT_CORRECT                           = 0x22
    REQUEST_SEQUENCE_ERROR                           = 0x24
    NO_RESPONSE_FROM_SUBNET_COMPONENT                = 0x25
    FAILURE_PREVENTS_EXECUTION_OF_REQUESTED_ACTION   = 0x26
    REQUEST_OUT_OF_RANGE                             = 0x31
    SECURITY_ACCESS_DENIED                           = 0x33
    AUTHENTICATION_REQUIRED                          = 0x34
    INVALID_KEY                                      = 0x35
    EXCEEDED_NUMBER_OF_ATTEMPTS                      = 0x36
    REQUIRED_TIME_DELAY_NOT_EXPIRED                  = 0x37
    UPLOAD_DOWNLOAD_NOT_ACCEPTED                     = 0x70
    TRANSFER_DATA_SUSPENDED                          = 0x71
    GENERAL_PROGRAMMING_FAILURE                      = 0x72
    WRONG_BLOCK_SEQUENCE_COUNTER                     = 0x73
    REQUEST_CORRECTLY_RECEIVED_RESPONSE_PENDING      = 0x78
    SUB_FUNCTION_NOT_SUPPORTED_IN_ACTIVE_SESSION     = 0x7E
    SERVICE_NOT_SUPPORTED_IN_ACTIVE_SESSION          = 0x7F


# ---------------------------------------------------------------------------
# Catalog entry
# ---------------------------------------------------------------------------

class NRCInfo(NamedTuple):
    """Rich metadata for a single NRC code."""

    code: int
    name: str
    description: str
    transient: bool = False  # True = ECU may succeed on retry (0x21, 0x78)


# ---------------------------------------------------------------------------
# Full catalog
# ---------------------------------------------------------------------------

NRC_CATALOG: dict[int, NRCInfo] = {
    0x10: NRCInfo(0x10, "generalReject",
                  "Service rejected — no specific reason given by the ECU"),
    0x11: NRCInfo(0x11, "serviceNotSupported",
                  "Service identifier not supported by this ECU"),
    0x12: NRCInfo(0x12, "subFunctionNotSupported",
                  "Sub-function parameter is not supported"),
    0x13: NRCInfo(0x13, "incorrectMessageLengthOrInvalidFormat",
                  "Request message length or format is invalid"),
    0x14: NRCInfo(0x14, "responseTooLong",
                  "Response length would exceed protocol limit"),
    0x21: NRCInfo(0x21, "busyRepeatRequest",
                  "ECU is busy; repeat the request after a short delay",
                  transient=True),
    0x22: NRCInfo(0x22, "conditionsNotCorrect",
                  "Pre-conditions for the requested service are not met"),
    0x24: NRCInfo(0x24, "requestSequenceError",
                  "Service called out of the required sequence"),
    0x25: NRCInfo(0x25, "noResponseFromSubnetComponent",
                  "No response from an addressed subnet component"),
    0x26: NRCInfo(0x26, "failurePreventsExecutionOfRequestedAction",
                  "Internal ECU failure prevents service execution"),
    0x31: NRCInfo(0x31, "requestOutOfRange",
                  "DID / RID / parameter value is out of the permitted range"),
    0x33: NRCInfo(0x33, "securityAccessDenied",
                  "Current security level is insufficient for this request"),
    0x34: NRCInfo(0x34, "authenticationRequired",
                  "Authentication must be performed before this service"),
    0x35: NRCInfo(0x35, "invalidKey",
                  "Security key does not match the issued seed"),
    0x36: NRCInfo(0x36, "exceededNumberOfAttempts",
                  "Security access locked out — too many failed attempts"),
    0x37: NRCInfo(0x37, "requiredTimeDelayNotExpired",
                  "Security access delay timer is still counting down"),
    0x70: NRCInfo(0x70, "uploadDownloadNotAccepted",
                  "RequestUpload / RequestDownload rejected"),
    0x71: NRCInfo(0x71, "transferDataSuspended",
                  "TransferData operation was suspended"),
    0x72: NRCInfo(0x72, "generalProgrammingFailure",
                  "Generic failure during flash programming"),
    0x73: NRCInfo(0x73, "wrongBlockSequenceCounter",
                  "Block sequence counter in TransferData is out of order"),
    0x78: NRCInfo(0x78, "requestCorrectlyReceivedResponsePending",
                  "ECU is processing the request; final response follows",
                  transient=True),
    0x7E: NRCInfo(0x7E, "subFunctionNotSupportedInActiveSession",
                  "Sub-function is not available in the current diagnostic session"),
    0x7F: NRCInfo(0x7F, "serviceNotSupportedInActiveSession",
                  "Service is not available in the current diagnostic session"),
}

# Quick name lookups (code → string name)
NRC_NAMES: dict[int, str] = {c: info.name for c, info in NRC_CATALOG.items()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def describe_nrc(nrc: int) -> str:
    """Return ``"0xNN name: description"`` for a known NRC, or a placeholder for OEM codes."""
    if nrc in NRC_CATALOG:
        info = NRC_CATALOG[nrc]
        return f"0x{nrc:02X} {info.name}: {info.description}"
    return f"0x{nrc:02X} Unknown/OEM-specific NRC"


def is_standard_nrc(nrc: int) -> bool:
    """Return True if *nrc* is defined in ISO 14229-1."""
    return nrc in NRC_CATALOG


def is_transient_nrc(nrc: int) -> bool:
    """Return True if the NRC indicates a transient condition (safe to retry)."""
    return NRC_CATALOG.get(nrc, NRCInfo(nrc, "", "", False)).transient
