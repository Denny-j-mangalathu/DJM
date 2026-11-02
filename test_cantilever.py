import math
import unittest
from cantilever import rectangular_inertia, tip_deflection, first_natural_frequency


class CantileverTests(unittest.TestCase):
    def test_known_static_result(self):
        inertia = rectangular_inertia(0.02, 0.002)
        self.assertAlmostEqual(inertia, 1.3333333333333334e-11)
        self.assertAlmostEqual(tip_deflection(1, 0.2, 200e9, inertia), 0.001)

    def test_frequency_and_length_scaling(self):
        inertia = rectangular_inertia(0.02, 0.002)
        frequency = first_natural_frequency(0.2, 200e9, inertia, 7850, 0.00004)
        self.assertAlmostEqual(frequency, 40.77, delta=0.02)
        self.assertAlmostEqual(first_natural_frequency(0.4, 200e9, inertia, 7850, 0.00004), frequency / 4)

    def test_load_sign_and_zero(self):
        self.assertEqual(tip_deflection(0, 1, 1, 1), 0)
        self.assertAlmostEqual(tip_deflection(-3, 1, 1, 1), -1)

    def test_invalid_parameters(self):
        for value in (0, -1, math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rectangular_inertia(value, 0.002)
                with self.assertRaises(ValueError):
                    first_natural_frequency(value, 1, 1, 1, 1)
        with self.assertRaises(ValueError):
            tip_deflection(math.nan, 1, 1, 1)


if __name__ == "__main__":
    unittest.main()
