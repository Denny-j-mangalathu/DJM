# DJM — Mechanical Engineering Utilities

A small collection of transparent, dependency-free engineering calculations.

## Cantilever beam calculator

`cantilever.py` calculates rectangular second moment of area, tip deflection
under a point load, and the first bending natural frequency.

Requires Python 3. No third-party packages are needed.

```bash
python cantilever.py
python -m unittest -v test_cantilever.py
```

### Example

```python
from cantilever import rectangular_inertia, tip_deflection, first_natural_frequency

# Steel beam: length 200 mm, width 20 mm, thickness 2 mm.
# These are illustrative material values.
L, b, h = 0.2, 0.02, 0.002
E, rho = 200e9, 7850
I = rectangular_inertia(b, h)

print(tip_deflection(1, L, E, I))  # 0.001 m under a 1 N tip load
print(first_natural_frequency(L, E, I, rho, b * h))  # approximately 40.77 Hz
```

### Units and equations

All inputs use SI: N, m, Pa, kg/m³, m² and m⁴. Results are m and Hz.
Thickness is the cross-section dimension along the bending direction.

- Rectangular second moment: I = b h³ / 12
- Tip displacement: δ = F L³ / (3 E I)
- First bending frequency: f₁ = β₁² / (2πL²) × √(EI / (ρA)), with β₁ ≈ 1.875104

The frequency constant is the first positive root of
cosh(β) cos(β) = −1 for a fixed-free Euler–Bernoulli beam.

### Assumptions and limitations

Uniform, slender, linearly elastic beam; ideal fixed end; small deflection.
Frequency excludes damping, tip mass, shear deformation and rotary inertia.
Thick or short beams require a more suitable model. These calculations are
educational and should be checked against the requirements of the application.

### Validation

Four unit tests cover a known static result, a frequency benchmark,
length scaling, load direction, and invalid inputs.

## Contributing

Keep units explicit, document assumptions, and include a reproducible example
or a meaningful check when adding calculations.
