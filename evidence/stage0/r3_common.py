#!/usr/bin/env python3
"""Shared exact definitions for the Furter R(3) Stage 0 experiments."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Iterator


class R3Error(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise R3Error(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def atomic_json_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def weighted_compositions_3(total: int) -> Iterator[tuple[int, int, int]]:
    require(total >= 0, "weighted total must be nonnegative")
    for a3 in range(total // 3 + 1):
        remainder = total - 3 * a3
        for a2 in range(remainder // 2 + 1):
            yield remainder - 2 * a2, a2, a3


@lru_cache(maxsize=1024)
def g_terms(n: int) -> tuple[tuple[tuple[int, int, int], int], ...]:
    """Return the exact integer sparse terms of g_(n,3)."""
    require(n >= 0, "coefficient index must be nonnegative")
    n_factorial = math.factorial(n)
    rows: list[tuple[tuple[int, int, int], int]] = []
    for exponents in weighted_compositions_3(n):
        size = sum(exponents)
        numerator = math.factorial(n + size)
        denominator = (n + 1) * n_factorial * math.prod(
            math.factorial(a) for a in exponents
        )
        quotient, remainder = divmod(numerator, denominator)
        require(remainder == 0, f"coefficient integrality failure at n={n}")
        coefficient = -quotient if size % 2 else quotient
        rows.append((exponents, coefficient))
    require(rows, f"g_{n} unexpectedly has no terms")
    return tuple(rows)


def singular_polynomial(n: int, prime: int) -> str:
    require(prime >= 2, "prime must be at least two")
    terms: list[str] = []
    variables = ("x1", "x2", "x3")
    for exponents, coefficient in g_terms(n):
        residue = coefficient % prime
        if residue == 0:
            continue
        factors = [str(residue)]
        for variable, exponent in zip(variables, exponents):
            if exponent == 1:
                factors.append(variable)
            elif exponent > 1:
                factors.append(f"{variable}^{exponent}")
        terms.append("*".join(factors))
    return "+".join(terms) if terms else "0"


def singular_polynomial_integer(n: int) -> str:
    terms: list[str] = []
    variables = ("x1", "x2", "x3")
    for exponents, coefficient in g_terms(n):
        factors = [str(abs(coefficient))]
        for variable, exponent in zip(variables, exponents):
            if exponent == 1:
                factors.append(variable)
            elif exponent > 1:
                factors.append(f"{variable}^{exponent}")
        term = "*".join(factors)
        if not terms:
            terms.append(("-" if coefficient < 0 else "") + term)
        else:
            terms.append(("-" if coefficient < 0 else "+") + term)
    return "".join(terms) if terms else "0"


def bezout_colength(d: int) -> int:
    require(d >= 2, "R(3) windows require d>=2")
    numerator = d * (d + 1) * (d + 2)
    quotient, remainder = divmod(numerator, 6)
    require(remainder == 0, "three-consecutive-integer product was not divisible by six")
    return quotient


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    if value % 2 == 0:
        return value == 2
    factor = 3
    while factor * factor <= value:
        if value % factor == 0:
            return False
        factor += 2
    return True


def primes_through(limit: int) -> list[int]:
    require(limit >= 2, "prime limit must be at least two")
    return [value for value in range(2, limit + 1) if is_prime(value)]
