"""
Pluggable Security Access (UDS 0x27) seed-to-key algorithm interface.

OEM seed/key algorithms are proprietary and must **never** be committed to
source control.  This module provides:

* :class:`SecurityAlgorithmBase` — abstract interface to implement.
* :class:`XorPlaceholderAlgorithm` — non-secure example; **replace before use**.
* :class:`NullAlgorithm` — returns empty key (negative-response testing).
* :func:`register_algorithm` / :func:`get_algorithm` — name-based registry.
* :func:`perform_security_access` — full seed→key handshake helper.

Adding your OEM algorithm
-------------------------
1. Create a subclass of :class:`SecurityAlgorithmBase` and implement
   :meth:`compute_key`.
2. Register it::

       from core.security_access import register_algorithm
       from my_oem_algo import MyAlgorithm

       register_algorithm("my_ecu_algo", MyAlgorithm())

3. Reference the name in the ECU YAML config::

       security_access:
         level: 0x01
         algorithm: my_ecu_algo
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------
class SecurityAlgorithmBase(ABC):
    """
    Abstract interface for a UDS Security Access seed-to-key algorithm.

    Sub-classes must override :meth:`compute_key`.
    """

    @abstractmethod
    def compute_key(self, seed: bytes, level: int) -> bytes:
        """
        Derive the security key from the ECU-provided seed.

        Args:
            seed:  Raw seed bytes from the 0x27 RequestSeed response
                   (sub-function byte already stripped).
            level: Access level integer (e.g. 1 for level 0x01/0x02).

        Returns:
            Key bytes to transmit in the 0x27 SendKey request.
        """


# ---------------------------------------------------------------------------
# Built-in algorithms
# ---------------------------------------------------------------------------
class XorPlaceholderAlgorithm(SecurityAlgorithmBase):
    """
    **PLACEHOLDER** — XOR each seed byte with a fixed mask.

    .. warning::
        This is **not** a real OEM algorithm.  Using it against a real ECU
        will produce NRC 0x35 (InvalidKey).  Replace with the actual
        OEM-provided derivation before connecting to hardware.
    """

    #: Override this mask in a subclass to match your ECU's expected constant.
    MASK: bytes = b"\xFF\xFF\xFF\xFF"

    def compute_key(self, seed: bytes, level: int) -> bytes:
        logger.warning(
            "[PLACEHOLDER] XorPlaceholderAlgorithm is not an OEM algorithm. "
            "Replace core.security_access.XorPlaceholderAlgorithm before real ECU use."
        )
        mask = self.MASK
        return bytes(seed[i] ^ mask[i % len(mask)] for i in range(len(seed)))


class NullAlgorithm(SecurityAlgorithmBase):
    """
    Always returns an empty key.

    Useful for verifying that the ECU correctly rejects an invalid key
    with NRC 0x35 (InvalidKey).
    """

    def compute_key(self, seed: bytes, level: int) -> bytes:  # noqa: D102
        logger.debug("NullAlgorithm — returning empty key (expected to fail on real ECU)")
        return b""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
_REGISTRY: dict[str, SecurityAlgorithmBase] = {
    "xor_placeholder": XorPlaceholderAlgorithm(),
    "null":            NullAlgorithm(),
}


def register_algorithm(name: str, algorithm: SecurityAlgorithmBase) -> None:
    """
    Register a custom algorithm under a string name.

    The name is referenced from ECU YAML configs under
    ``security_access.algorithm``.

    Args:
        name:      Unique string identifier (e.g. ``"adas_level1"``).
        algorithm: Concrete :class:`SecurityAlgorithmBase` instance.
    """
    if name in _REGISTRY:
        logger.warning("Overwriting existing security algorithm: '{}'", name)
    _REGISTRY[name] = algorithm
    logger.info("Registered security algorithm: '{}'", name)


def get_algorithm(name: str) -> SecurityAlgorithmBase:
    """
    Retrieve a registered algorithm by name.

    Args:
        name: Algorithm name as registered via :func:`register_algorithm`.

    Raises:
        KeyError: If *name* is not in the registry.
    """
    if name not in _REGISTRY:
        raise KeyError(
            f"Unknown security algorithm '{name}'. "
            f"Available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]


# ---------------------------------------------------------------------------
# High-level handshake helper
# ---------------------------------------------------------------------------
def perform_security_access(
    uds_client: object,
    level: int,
    algorithm: SecurityAlgorithmBase,
) -> bool:
    """
    Execute the full Security Access handshake (seed request + key send).

    This function:
    1. Calls ``uds_client.security_access_request_seed(level)``.
    2. Derives the key via ``algorithm.compute_key(seed, level)``.
    3. Calls ``uds_client.security_access_send_key(level, key)``.

    Args:
        uds_client: Any :class:`~core.uds_client.UDSClientBase` instance.
        level:      Odd access level integer (e.g. 1 for 0x01/0x02 pair).
        algorithm:  :class:`SecurityAlgorithmBase` implementation.

    Returns:
        ``True`` if the ECU granted access (positive response to SendKey),
        ``False`` otherwise.
    """
    seed_resp = uds_client.security_access_request_seed(level)  # type: ignore[attr-defined]
    if not seed_resp.positive:
        logger.error(
            "SecurityAccess RequestSeed failed for level 0x{:02X}: {}",
            level, seed_resp,
        )
        return False

    # Seed starts at byte index 1 (byte 0 is the level echo)
    seed_bytes = seed_resp.data[1:] if len(seed_resp.data) > 1 else seed_resp.data
    key = algorithm.compute_key(seed_bytes, level)
    logger.debug("Seed={}  Key={}", seed_bytes.hex(), key.hex())

    key_resp = uds_client.security_access_send_key(level, key)  # type: ignore[attr-defined]
    if key_resp.positive:
        logger.info("Security access GRANTED for level 0x{:02X}", level)
    else:
        logger.warning(
            "Security access DENIED for level 0x{:02X}  NRC={}",
            level, key_resp.nrc_name,
        )
    return key_resp.positive
