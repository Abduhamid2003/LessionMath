import pytest

from app.services.math_service import MathService
from app.utils.expression_validator import validate_expression


def test_validate_blocks_dangerous():
    with pytest.raises(ValueError):
        validate_expression("__import__('os')")


def test_derivative_polynomial():
    r = MathService.derivative("x**2", 1)
    assert "2*x" in r["derivative"] or r["derivative"] == "2*x"


def test_definite_integral():
    r = MathService.definite_integral("x**2", 0, 2)
    assert abs(r["value"] - 8 / 3) < 0.01


def test_limit_sin_over_x():
    r = MathService.limit("sin(x)/x", 0)
    assert r["numeric"] is not None
    assert abs(r["numeric"] - 1) < 0.01


def test_indefinite_integral():
    r = MathService.indefinite_integral("2*x")
    assert "x**2" in r["antiderivative"]


def test_check_derivative():
    r = MathService.check_derivative("x**2", "2*x")
    assert r["correct"] is True
