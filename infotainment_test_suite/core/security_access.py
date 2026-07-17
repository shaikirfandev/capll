"""
Pluggable Security Access seed-to-key algorithm (UDS 0x27).

OEM algorithms are proprietary.  This module provides a stub + registry
so tests can reference algorithm names from YAML config without committing
any real key derivation.

Adding your OEM algorithm
-------------------------
1.  Subclass :class:`SecurityAlgorithmBase` and implement ``compute_key``.
2.  Call ``register_algorithm("my_name", MyAlgorithm())``.
3.  Set ``algorithm: my_name`` in ``config/ecu_sessions.yaml``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger


class SecurityAlgorithmBase(ABC):
    @abstractmethod
    def compute_key(self, seed: bytes, level: int) -> bytes:
        """Return the key bytes for the given seed and access level."""


class XorPlaceholderAlgorithm(SecurityAlgorithmBase):
    """
    **PLACEHOLDER** — XOR seed with 0xFF mask.

    .. warning::
        This will produce NRC 0x35 (InvalidKey) on any real ECU.
        Replace before connecting to hardware.
    """
    MASK: bytes = b"\xFF\xFF\xFF\xFF"

    def compute_key(self, seed: bytes, level: int) -> bytes:
        logger.warning(
            "[PLACEHOLDER] XorPlaceholderAlgorithm is NOT a real OEM algorithm. "
            "Replace security_access.XorPlaceholderAlgorithm before real-ECU use."
        )
        m = self.MASK
        return bytes(seed[i] ^ m[i % len(m)] for i in range(len(seed)))


class NullAlgorithm(SecurityAlgorithmBase):
    """Returns empty key — intentionally wrong, for NRC 0x35 negative tests."""

    def compute_key(self, seed: bytes, level: int) -> bytes:
        return b""


_REGISTRY: dict[str, SecurityAlgorithmBase] = {
    "xor_placeholder": XorPlaceholderAlgorithm(),
    "null":            NullAlgorithm(),
}


def register_algorithm(name: str, algorithm: SecurityAlgorithmBase) -> None:
    """Register a custom OEM algorithm under *name*."""
    _REGISTRY[name] = algorithm
    logger.info("Registered security algorithm: '{}'", name)


def get_algorithm(name: str) -> SecurityAlgorithmBase:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown algorithm '{name}'. Available: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def perform_security_access(
    uds_client: object,
    level: int,
    algorithm: SecurityAlgorithmBase,
) -> bool:
    """
    Execute the full seed→key handshake.

    Returns ``True`` if the ECU grants access, ``False`` otherwise.
    """
    seed_resp = uds_client.security_access_request_seed(level)  # type: ignore[attr-defined]
    if not seed_resp.positive:
        logger.error("SA RequestSeed failed level=0x{:02X}: {}", level, seed_resp)
        return False
    seed = seed_resp.data[1:] if len(seed_resp.data) > 1 else seed_resp.data
    key  = algorithm.compute_key(seed, level)
    logger.debug("Seed={}  Key={}", seed.hex(), key.hex())
    key_resp = uds_client.security_access_send_key(level, key)  # type: ignore[attr-defined]
    if key_resp.positive:
        logger.info("SA access GRANTED level=0x{:02X}", level)
    else:
        logger.warning("SA access DENIED level=0x{:02X} NRC={}", level, key_resp.nrc_name)
    return key_resp.positive
