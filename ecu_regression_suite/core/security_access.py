"""
Pluggable Security Access (UDS 0x27) seed-to-key algorithm interface.

OEM seed/key algorithms are proprietary.  This module provides:

* :class:`SecurityAlgorithmBase` — abstract interface.
* :class:`XorPlaceholderAlgorithm` — non-secure placeholder; **replace before use**.
* :class:`NullAlgorithm` — returns empty key (for negative-response NRC 0x35 testing).
* :func:`register_algorithm` / :func:`get_algorithm` — name-based registry.
* :func:`perform_security_access` — full seed→key handshake helper that
  works with any :class:`~core.uds_client.UDSClient` instance.

Adding an OEM algorithm
-----------------------
1. Subclass :class:`SecurityAlgorithmBase`, implement :meth:`compute_key`.
2. Register it with a name that matches the ``algorithm`` field in
   ``sessions_security.yaml``::

       from core.security_access import register_algorithm
       from my_oem.algo import MyAlgo
       register_algorithm("adas_level1", MyAlgo())
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict

from loguru import logger

if TYPE_CHECKING:
    from .uds_client import UDSClient


# ---------------------------------------------------------------------------
# Abstract base
# ---------------------------------------------------------------------------

class SecurityAlgorithmBase(ABC):
    """Seed-to-key algorithm contract."""

    @abstractmethod
    def compute_key(self, seed: bytes, level: int) -> bytes:
        """
        Derive the security key from the ECU-provided seed.

        Args:
            seed:  Seed bytes (sub-function byte stripped).
            level: Numeric security level (1, 3, 5 …).

        Returns:
            Key bytes to send in the 0x27 SendKey request.
        """


# ---------------------------------------------------------------------------
# Built-in algorithms
# ---------------------------------------------------------------------------

class XorPlaceholderAlgorithm(SecurityAlgorithmBase):
    """
    **PLACEHOLDER** — XOR each seed byte with ``0xFF``.

    .. warning::
        This is **not** a real OEM algorithm.  It matches the mock ECU engine's
        expected key so the test suite can complete a security access handshake
        in mock mode.  Replace with the actual OEM derivation before connecting
        to real hardware.

    [MOCK/SIMULATED — not a real security algorithm]
    """

    def compute_key(self, seed: bytes, level: int) -> bytes:
        logger.debug(
            "[PLACEHOLDER] XorPlaceholderAlgorithm.compute_key(level={}) — not an OEM algorithm",
            level,
        )
        return bytes(b ^ 0xFF for b in seed)


class NullAlgorithm(SecurityAlgorithmBase):
    """
    Returns an empty byte string.

    Used to deliberately trigger NRC 0x35 (invalidKey) in negative-response tests.
    """

    def compute_key(self, seed: bytes, level: int) -> bytes:
        return b""


# ---------------------------------------------------------------------------
# Algorithm registry
# ---------------------------------------------------------------------------

_REGISTRY: Dict[str, SecurityAlgorithmBase] = {
    "xor_placeholder": XorPlaceholderAlgorithm(),
    "null":            NullAlgorithm(),
}


def register_algorithm(name: str, algorithm: SecurityAlgorithmBase) -> None:
    """
    Register an algorithm under a string name.

    The name must match the ``algorithm`` field in ``sessions_security.yaml``.
    """
    _REGISTRY[name] = algorithm
    logger.info("Security algorithm '{}' registered.", name)


def get_algorithm(name: str) -> SecurityAlgorithmBase:
    """
    Retrieve a registered algorithm by name.

    Raises:
        KeyError: If no algorithm with that name is registered.
    """
    if name not in _REGISTRY:
        available = list(_REGISTRY.keys())
        raise KeyError(
            f"Security algorithm '{name}' not registered. Available: {available}. "
            "Register your OEM algorithm via register_algorithm()."
        )
    return _REGISTRY[name]


# ---------------------------------------------------------------------------
# Handshake helper
# ---------------------------------------------------------------------------

def perform_security_access(
    client: "UDSClient",
    level: int,
    algorithm: SecurityAlgorithmBase | None = None,
) -> bool:
    """
    Execute the full UDS security access handshake.

    Steps:
        1. Send 0x27 seed-request (odd sub-function = ``level``).
        2. Compute key from seed via ``algorithm``.
        3. Send 0x27 key-send (even sub-function = ``level + 1``).

    Args:
        client:    Connected :class:`~core.uds_client.UDSClient` instance.
        level:     Security access level (e.g. 1 for level 0x01/0x02).
        algorithm: Algorithm to use; defaults to ``xor_placeholder``.

    Returns:
        True on successful access grant.

    Raises:
        :class:`~core.uds_client.UDSNegativeResponseError` on NRC.
    """
    if algorithm is None:
        algorithm = get_algorithm("xor_placeholder")

    seed_resp = client.request_seed(level)
    if not seed_resp.positive:
        from .uds_client import UDSNegativeResponseError
        raise UDSNegativeResponseError(0x27, seed_resp.nrc or 0x00)

    seed = seed_resp.data[1:]   # strip the sub-function echo byte
    key = algorithm.compute_key(seed, level)

    key_resp = client.send_key(level, key)
    if not key_resp.positive:
        from .uds_client import UDSNegativeResponseError
        raise UDSNegativeResponseError(0x27, key_resp.nrc or 0x00)

    logger.info("Security access granted at level {}", level)
    return True
