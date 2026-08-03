"""Functional proof tooling for the declared AEGIS MVP boundary."""

from aegis_os.proof.domain_a import run_domain_a
from aegis_os.proof.domain_b import run_domain_b
from aegis_os.proof.domain_c import run_domain_c
from aegis_os.proof.domain_d import run_domain_d
from aegis_os.proof.domain_e import run_domain_e
from aegis_os.proof.domain_f import run_domain_f

__all__ = [
    "run_domain_a",
    "run_domain_b",
    "run_domain_c",
    "run_domain_d",
    "run_domain_e",
    "run_domain_f",
]
