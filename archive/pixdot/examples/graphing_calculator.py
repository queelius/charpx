#!/usr/bin/env python3
"""Terminal graphing calculator using pixdot.

Demonstrates mathematical function plotting - the quintessential
use case for AI assistants doing quick visualizations in the terminal.

Requires: pip install matplotlib

Usage:
    python graphing_calculator.py
"""

from __future__ import annotations

import sys

import numpy as np

# Check matplotlib availability
try:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def _check_matplotlib() -> None:
    """Exit with helpful message if matplotlib unavailable."""
    if not MATPLOTLIB_AVAILABLE:
        print(
            "Error: matplotlib is required for this example.\n\n"
            "Install it with:\n"
            "    pip install matplotlib",
            file=sys.stderr,
        )
        sys.exit(1)


def plot_function(
    expr: str,
    domain: tuple[float, float] = (-10, 10),
    width: int = 80,
    title: str | None = None,
    samples: int = 500,
) -> str:
    """Plot a mathematical expression as braille.

    Args:
        expr: Expression using 'x' as variable and numpy functions.
              Examples: "np.sin(x)", "x**2 - 4", "np.exp(-x**2)"
        domain: (min, max) tuple for x-axis.
        width: Terminal width in characters.
        title: Optional title for the plot.
        samples: Number of points to sample (higher = smoother).

    Returns:
        Multi-line braille string of the plot.

    Example:
        >>> print(plot_function("np.sin(x)", domain=(0, 4*np.pi)))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    x = np.linspace(domain[0], domain[1], samples)
    y = eval(expr)  # expr uses 'x' as variable

    ax.plot(x, y, 'k-', linewidth=3)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.5, linewidth=1.5)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def plot_multiple(
    expressions: list[str],
    domain: tuple[float, float] = (-10, 10),
    width: int = 80,
    labels: list[str] | None = None,
    title: str | None = None,
) -> str:
    """Plot multiple functions on the same axes.

    Args:
        expressions: List of expressions using 'x' as variable.
        domain: (min, max) tuple for x-axis.
        width: Terminal width in characters.
        labels: Optional labels for legend.
        title: Optional title for the plot.

    Returns:
        Multi-line braille string of the plot.

    Example:
        >>> print(plot_multiple(["np.sin(x)", "np.cos(x)"], labels=["sin", "cos"]))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    x = np.linspace(domain[0], domain[1], 500)
    linestyles = ['-', '--', '-.', ':']

    for i, expr in enumerate(expressions):
        y = eval(expr)
        label = labels[i] if labels and i < len(labels) else expr
        ax.plot(x, y, 'k' + linestyles[i % len(linestyles)], linewidth=3, label=label)

    if labels:
        ax.legend(loc='best', fontsize=10)

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.5)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def plot_parametric(
    x_expr: str,
    y_expr: str,
    t_range: tuple[float, float] = (0, 2 * np.pi),
    width: int = 80,
    title: str | None = None,
) -> str:
    """Plot a parametric curve.

    Args:
        x_expr: Expression for x(t) using 't' as variable.
        y_expr: Expression for y(t) using 't' as variable.
        t_range: (min, max) tuple for parameter t.
        width: Terminal width in characters.
        title: Optional title for the plot.

    Returns:
        Multi-line braille string of the plot.

    Example:
        >>> print(plot_parametric("np.cos(t)", "np.sin(t)", title="Circle"))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)

    t = np.linspace(t_range[0], t_range[1], 500)
    x = eval(x_expr)
    y = eval(y_expr)

    ax.plot(x, y, 'k-', linewidth=3)
    ax.set_aspect('equal')

    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')

    ax.grid(True, alpha=0.5)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def quick_plot(expr: str, domain: tuple[float, float] = (-10, 10)) -> None:
    """One-liner for instant visualization.

    Args:
        expr: Expression using 'x' as variable.
        domain: (min, max) tuple for x-axis.

    Example:
        >>> quick_plot("np.sin(x) * np.exp(-x/5)", domain=(0, 20))
    """
    print(plot_function(expr, domain=domain))


def demo_basic_functions() -> None:
    """Demo: basic mathematical functions."""
    print("=" * 60)
    print("BASIC FUNCTIONS")
    print("=" * 60)

    print("\n--- Sine Wave ---")
    print(plot_function("np.sin(x)", domain=(0, 4 * np.pi), title="sin(x)"))

    print("\n--- Cosine Wave ---")
    print(plot_function("np.cos(x)", domain=(0, 4 * np.pi), title="cos(x)"))

    print("\n--- Exponential ---")
    print(plot_function("np.exp(x)", domain=(-3, 3), title="exp(x)"))

    print("\n--- Natural Log ---")
    print(plot_function("np.log(x)", domain=(0.1, 10), title="ln(x)"))


def demo_polynomials() -> None:
    """Demo: polynomial functions."""
    print("\n" + "=" * 60)
    print("POLYNOMIALS")
    print("=" * 60)

    print("\n--- Parabola: x^2 ---")
    print(plot_function("x**2", domain=(-5, 5), title="x^2"))

    print("\n--- Cubic: x^3 - 6x^2 + 9x ---")
    print(plot_function("x**3 - 6*x**2 + 9*x", domain=(-1, 5), title="x^3 - 6x^2 + 9x"))

    print("\n--- Quartic: x^4 - 5x^2 + 4 ---")
    print(plot_function("x**4 - 5*x**2 + 4", domain=(-3, 3), title="x^4 - 5x^2 + 4"))


def demo_physics() -> None:
    """Demo: physics-related functions."""
    print("\n" + "=" * 60)
    print("PHYSICS & ENGINEERING")
    print("=" * 60)

    print("\n--- Damped Oscillation ---")
    print(plot_function(
        "np.sin(x) * np.exp(-x/10)",
        domain=(0, 40),
        title="Damped Oscillation: sin(x) * exp(-x/10)"
    ))

    print("\n--- Gaussian (Normal Distribution) ---")
    print(plot_function(
        "np.exp(-x**2 / 2) / np.sqrt(2 * np.pi)",
        domain=(-4, 4),
        title="Gaussian: exp(-x^2/2) / sqrt(2*pi)"
    ))

    print("\n--- Sinc Function ---")
    print(plot_function(
        "np.sinc(x/np.pi)",
        domain=(-15, 15),
        title="sinc(x)"
    ))


def demo_comparisons() -> None:
    """Demo: comparing multiple functions."""
    print("\n" + "=" * 60)
    print("FUNCTION COMPARISONS")
    print("=" * 60)

    print("\n--- Trig Functions ---")
    print(plot_multiple(
        ["np.sin(x)", "np.cos(x)"],
        domain=(0, 2 * np.pi),
        labels=["sin(x)", "cos(x)"],
        title="Sine vs Cosine"
    ))

    print("\n--- Power Functions ---")
    print(plot_multiple(
        ["x", "x**2", "x**3"],
        domain=(-2, 2),
        labels=["x", "x^2", "x^3"],
        title="Powers of x"
    ))


def demo_parametric() -> None:
    """Demo: parametric curves."""
    print("\n" + "=" * 60)
    print("PARAMETRIC CURVES")
    print("=" * 60)

    print("\n--- Circle ---")
    print(plot_parametric("np.cos(t)", "np.sin(t)", title="Circle"))

    print("\n--- Lissajous Figure ---")
    print(plot_parametric(
        "np.sin(3*t)",
        "np.sin(2*t)",
        title="Lissajous (3:2)"
    ))

    print("\n--- Spiral ---")
    print(plot_parametric(
        "t * np.cos(t)",
        "t * np.sin(t)",
        t_range=(0, 6 * np.pi),
        title="Archimedean Spiral"
    ))


def main() -> int:
    """Run the graphing calculator demo."""
    if not MATPLOTLIB_AVAILABLE:
        print(
            "Error: matplotlib is required for this demo.\n\n"
            "Install it with:\n"
            "    pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    print("Terminal Graphing Calculator")
    print("Using pixdot for braille visualization")
    print()

    demo_basic_functions()
    demo_polynomials()
    demo_physics()
    demo_comparisons()
    demo_parametric()

    print("\n" + "=" * 60)
    print("USAGE")
    print("=" * 60)
    print("""
Functions available for use in expressions:
  - All numpy functions: np.sin, np.cos, np.exp, np.log, np.sqrt, etc.
  - Arithmetic: +, -, *, /, **, %
  - Constants: np.pi, np.e

Examples:
  plot_function("np.sin(x)", domain=(0, 10))
  plot_function("x**2 - 3*x + 2", domain=(-2, 5))
  plot_multiple(["np.sin(x)", "np.cos(x)"], labels=["sin", "cos"])
  plot_parametric("np.cos(t)", "np.sin(t)", title="Circle")
  quick_plot("np.exp(-x**2)")  # One-liner
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
