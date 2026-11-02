"""Euler-Bernoulli cantilever beam calculations in SI units.

Assumes a uniform, slender beam, small deflection, and a tip point load.
"""
import math


def _positive(value, name):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and greater than zero")
    return value


def rectangular_inertia(width, thickness):
    """Return second moment of area (m^4); thickness is along bending."""
    return _positive(width, "width") * _positive(thickness, "thickness") ** 3 / 12


def tip_deflection(load, length, youngs_modulus, inertia):
    """Return signed tip displacement (m) for a tip load (N)."""
    if not math.isfinite(load):
        raise ValueError("load must be finite")
    return load * _positive(length, "length") ** 3 / (
        3 * _positive(youngs_modulus, "youngs_modulus") * _positive(inertia, "inertia")
    )


def first_natural_frequency(length, youngs_modulus, inertia, density, area):
    """Return the fundamental bending frequency (Hz), without tip mass."""
    beta = 1.875104068711961
    return beta ** 2 / (2 * math.pi * _positive(length, "length") ** 2) * math.sqrt(
        _positive(youngs_modulus, "youngs_modulus") * _positive(inertia, "inertia")
        / (_positive(density, "density") * _positive(area, "area"))
    )


if __name__ == "__main__":
    width, thickness, length = 0.02, 0.002, 0.2
    inertia = rectangular_inertia(width, thickness)
    print(f"Tip deflection under 1 N: {tip_deflection(1, length, 200e9, inertia) * 1000:.3f} mm")
    print(f"First bending frequency: {first_natural_frequency(length, 200e9, inertia, 7850, width * thickness):.3f} Hz")
