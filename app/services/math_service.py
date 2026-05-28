from typing import Any

import numpy as np
import sympy as sp
from sympy import Integral, Derivative, Limit, latex, series, simplify, sympify

from app.utils.expression_validator import validate_expression


class MathService:
  VARIABLE = sp.Symbol("x")

  @classmethod
  def parse_expression(cls, expr_str: str) -> sp.Expr:
    cleaned = validate_expression(expr_str).replace("^", "**")
    if cleaned.startswith("y=") or cleaned.startswith("y ="):
      cleaned = cleaned.split("=", 1)[1].strip()
    return sympify(cleaned, locals={"x": cls.VARIABLE})

  @classmethod
  def plot_data(
    cls,
    expr_str: str,
    x_min: float = -10,
    x_max: float = 10,
    points: int = 400,
  ) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    f = sp.lambdify(cls.VARIABLE, expr, modules=["numpy"])
    xs = np.linspace(x_min, x_max, points)
    ys = []
    for x_val in xs:
      try:
        y_val = float(f(x_val))
        if np.isfinite(y_val):
          ys.append(y_val)
        else:
          ys.append(None)
      except (TypeError, ValueError, ZeroDivisionError):
        ys.append(None)
    return {
      "x": xs.tolist(),
      "y": ys,
      "expression": str(expr),
      "latex": latex(expr),
    }

  @classmethod
  def derivative(cls, expr_str: str, order: int = 1) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    deriv = sp.diff(expr, cls.VARIABLE, order)
    simplified = simplify(deriv)
    steps = [
      f"f(x) = {latex(expr)}",
      f"f^'({order})(x) = {latex(Derivative(expr, cls.VARIABLE, order))}",
      f"f^'({order})(x) = {latex(simplified)}",
    ]
    return {
      "derivative": str(simplified),
      "latex": latex(simplified),
      "steps": steps,
      "order": order,
    }

  @classmethod
  def tangent_line(
    cls,
    expr_str: str,
    x0: float,
    x_range: float = 5,
    points: int = 100,
  ) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    deriv = sp.diff(expr, cls.VARIABLE)
    f = sp.lambdify(cls.VARIABLE, expr, modules=["numpy"])
    df = sp.lambdify(cls.VARIABLE, deriv, modules=["numpy"])
    y0 = float(f(x0))
    slope = float(df(x0))
    xs = np.linspace(x0 - x_range, x0 + x_range, points)
    tangent_ys = [slope * (x - x0) + y0 for x in xs]
    return {
      "x0": x0,
      "y0": y0,
      "slope": slope,
      "tangent_x": xs.tolist(),
      "tangent_y": tangent_ys,
      "tangent_equation": f"y = {slope:.4f}(x - {x0}) + {y0:.4f}",
    }

  @classmethod
  def definite_integral(
    cls,
    expr_str: str,
    a: float,
    b: float,
    method: str = "symbolic",
  ) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    symbolic = sp.integrate(expr, (cls.VARIABLE, a, b))
    numeric = float(sp.N(symbolic))

    xs = np.linspace(a, b, 200)
    f = sp.lambdify(cls.VARIABLE, expr, modules=["numpy"])
    ys = [float(f(x)) if np.isfinite(float(f(x))) else 0 for x in xs]

    methods = {}
    if method in ("trapezoid", "all"):
      methods["trapezoid"] = float(np.trapz([f(x) for x in xs], xs))
    if method in ("simpson", "all"):
      from scipy.integrate import simpson

      methods["simpson"] = float(simpson([f(x) for x in xs], xs))

    return {
      "value": numeric,
      "symbolic": str(symbolic),
      "latex": latex(Integral(expr, (cls.VARIABLE, a, b))),
      "area_x": xs.tolist(),
      "area_y": ys,
      "a": a,
      "b": b,
      "numerical_methods": methods,
    }

  @classmethod
  def intersections(cls, expr_str: str, x_min: float = -10, x_max: float = 10) -> list[dict]:
    expr = cls.parse_expression(expr_str)
    roots = sp.solve(expr, cls.VARIABLE)
    result = []
    for r in roots:
      try:
        val = float(r.evalf())
        if x_min <= val <= x_max and abs(r.as_real_imag()[1]) < 1e-10:
          result.append({"x": val, "y": 0})
      except (TypeError, ValueError):
        continue
    return result

  @classmethod
  def evaluate(cls, expr_str: str, x_value: float) -> float:
    expr = cls.parse_expression(expr_str)
    f = sp.lambdify(cls.VARIABLE, expr, modules=["numpy"])
    return float(f(x_value))

  @classmethod
  def evaluate_numeric(cls, expr_str: str) -> dict[str, Any]:
    cleaned = validate_expression(expr_str).replace("^", "**")
    locals_map = {
        "x": cls.VARIABLE,
        "pi": sp.pi,
        "e": sp.E,
        "sin": sp.sin,
        "cos": sp.cos,
        "tan": sp.tan,
        "sqrt": sp.sqrt,
        "log": sp.log,
        "ln": sp.log,
        "exp": sp.exp,
        "abs": sp.Abs,
    }
    expr = sympify(cleaned, locals=locals_map)
    simplified = simplify(expr)
    value = float(sp.N(simplified))
    return {
        "value": value,
        "simplified": str(simplified),
        "latex": latex(simplified),
    }

  @classmethod
  def calculator_derivative_at(cls, expr_str: str, x_value: float) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    deriv = simplify(sp.diff(expr, cls.VARIABLE))
    f = sp.lambdify(cls.VARIABLE, deriv, modules=["numpy"])
    slope = float(f(x_value))
    f0 = sp.lambdify(cls.VARIABLE, expr, modules=["numpy"])
    y0 = float(f0(x_value))
    return {
        "derivative": str(deriv),
        "latex": latex(deriv),
        "slope": slope,
        "y_at_x": y0,
      "x": x_value,
    }

  @classmethod
  def multi_plot(
    cls,
    expressions: list[str],
    x_min: float = -10,
    x_max: float = 10,
    points: int = 400,
  ) -> dict[str, Any]:
    series_list = []
    for expr_str in expressions[:5]:
      data = cls.plot_data(expr_str, x_min, x_max, points)
      series_list.append(data)
    return {"series": series_list}

  @classmethod
  def limit(cls, expr_str: str, point: float, direction: str = "both") -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    pt = sp.sympify(point)
    if direction == "+":
      val = sp.limit(expr, cls.VARIABLE, pt, dir="+")
    elif direction == "-":
      val = sp.limit(expr, cls.VARIABLE, pt, dir="-")
    else:
      val = sp.limit(expr, cls.VARIABLE, pt)
    return {
      "value": str(val),
      "numeric": float(sp.N(val)) if val.is_real else None,
      "latex": latex(Limit(expr, cls.VARIABLE, pt)),
      "expression": str(expr),
    }

  @classmethod
  def taylor_series(cls, expr_str: str, x0: float = 0, order: int = 5) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    pt = sp.sympify(x0)
    poly = series(expr, cls.VARIABLE, pt, order + 1).removeO()
    simplified = simplify(poly)
    plot_orig = cls.plot_data(expr_str)
    plot_taylor = cls.plot_data(str(simplified))
    return {
      "polynomial": str(simplified),
      "latex": latex(simplified),
      "order": order,
      "x0": x0,
      "function_plot": plot_orig,
      "taylor_plot": plot_taylor,
    }

  @classmethod
  def indefinite_integral(cls, expr_str: str) -> dict[str, Any]:
    expr = cls.parse_expression(expr_str)
    antideriv = sp.integrate(expr, cls.VARIABLE)
    simplified = simplify(antideriv)
    return {
      "antiderivative": str(simplified),
      "latex": latex(simplified),
      "expression": str(expr),
    }

  @classmethod
  def check_derivative(cls, expr_str: str, user_answer: str) -> dict[str, Any]:
    correct = cls.derivative(expr_str, 1)["derivative"]
    try:
      user_expr = simplify(cls.parse_expression(user_answer))
      correct_expr = simplify(cls.parse_expression(correct))
      match = sp.simplify(user_expr - correct_expr) == 0
    except Exception:
      match = False
    return {
      "correct": bool(match),
      "expected": correct,
      "expected_latex": latex(simplify(cls.parse_expression(correct))),
    }
