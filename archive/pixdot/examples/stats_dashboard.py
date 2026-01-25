#!/usr/bin/env python3
"""Statistical visualization toolkit for terminal.

What Claude Code would generate during data analysis sessions.
Histograms, box plots, scatter plots with regression, and summary statistics.

Requires: pip install matplotlib

Usage:
    python stats_dashboard.py
"""

from __future__ import annotations

import sys
from typing import Any

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


def histogram(
    data: np.ndarray,
    bins: int = 30,
    title: str = "Distribution",
    width: int = 80,
    show_stats: bool = True,
) -> str:
    """Render histogram of data.

    Args:
        data: 1D array of values.
        bins: Number of histogram bins.
        title: Plot title.
        width: Terminal width in characters.
        show_stats: Include mean/std/median annotations.

    Returns:
        Multi-line braille string of the histogram.

    Example:
        >>> data = np.random.normal(0, 1, 1000)
        >>> print(histogram(data, title="Normal Distribution"))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    ax.hist(data, bins=bins, color='black', edgecolor='white', alpha=0.9)

    if show_stats:
        stats_text = f"n={len(data)}, mean={data.mean():.2f}, std={data.std():.2f}"
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel("Value", fontsize=11)
    ax.set_ylabel("Frequency", fontsize=11)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def boxplot_compare(
    datasets: dict[str, np.ndarray],
    title: str = "Comparison",
    width: int = 80,
) -> str:
    """Side-by-side box plots for comparing distributions.

    Args:
        datasets: Dictionary mapping names to arrays.
        title: Plot title.
        width: Terminal width in characters.

    Returns:
        Multi-line braille string of box plots.

    Example:
        >>> data = {"A": np.random.normal(0, 1, 100), "B": np.random.normal(2, 1.5, 100)}
        >>> print(boxplot_compare(data))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    labels = list(datasets.keys())
    data = [datasets[k] for k in labels]

    bp = ax.boxplot(data, labels=labels, patch_artist=True)

    # Style the boxes
    for box in bp['boxes']:
        box.set_facecolor('white')
        box.set_edgecolor('black')
        box.set_linewidth(2)
    for whisker in bp['whiskers']:
        whisker.set_linewidth(2)
    for cap in bp['caps']:
        cap.set_linewidth(2)
    for median in bp['medians']:
        median.set_color('black')
        median.set_linewidth(3)

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_ylabel("Value", fontsize=11)
    ax.grid(True, axis='y', alpha=0.5)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def scatter_with_fit(
    x: np.ndarray,
    y: np.ndarray,
    fit_type: str = "linear",
    title: str = "",
    width: int = 80,
) -> str:
    """Scatter plot with trend line and R-squared.

    Args:
        x: X coordinates.
        y: Y coordinates.
        fit_type: "linear", "quadratic", or "none".
        title: Plot title.
        width: Terminal width in characters.

    Returns:
        Multi-line braille string of scatter plot.

    Example:
        >>> x = np.random.rand(100) * 10
        >>> y = 2 * x + 3 + np.random.randn(100) * 2
        >>> print(scatter_with_fit(x, y, title="Linear Correlation"))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)

    ax.scatter(x, y, c='black', s=40, alpha=0.6, edgecolors='black', linewidths=0.5)

    if fit_type != "none":
        degree = 2 if fit_type == "quadratic" else 1
        z = np.polyfit(x, y, degree)
        p = np.poly1d(z)

        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, p(x_line), 'k-', linewidth=2)

        # Calculate R-squared
        y_pred = p(x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y.mean()) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        if degree == 1:
            eq_text = f"y = {z[0]:.2f}x + {z[1]:.2f}\nR^2 = {r_squared:.3f}"
        else:
            eq_text = f"R^2 = {r_squared:.3f}"

        ax.text(0.02, 0.98, eq_text, transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel("X", fontsize=11)
    ax.set_ylabel("Y", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def correlation_matrix(
    data: dict[str, np.ndarray],
    title: str = "Correlation Matrix",
    width: int = 80,
) -> str:
    """Heatmap of correlation matrix.

    Args:
        data: Dictionary mapping variable names to arrays.
        title: Plot title.
        width: Terminal width in characters.

    Returns:
        Multi-line braille string of correlation matrix.

    Example:
        >>> data = {"A": np.random.randn(100), "B": np.random.randn(100), "C": np.random.randn(100)}
        >>> data["B"] = data["A"] + np.random.randn(100) * 0.5  # Correlated
        >>> print(correlation_matrix(data))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    names = list(data.keys())
    n = len(names)
    matrix = np.zeros((n, n))

    for i, name_i in enumerate(names):
        for j, name_j in enumerate(names):
            matrix[i, j] = np.corrcoef(data[name_i], data[name_j])[0, 1]

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)

    im = ax.imshow(matrix, cmap='RdBu', vmin=-1, vmax=1)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_yticklabels(names, fontsize=10)

    # Add correlation values as text
    for i in range(n):
        for j in range(n):
            text_color = 'white' if abs(matrix[i, j]) > 0.5 else 'black'
            ax.text(j, i, f'{matrix[i, j]:.2f}',
                    ha='center', va='center', color=text_color, fontsize=9)

    ax.set_title(title, fontsize=14, fontweight='bold')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def quick_stats(data: np.ndarray, name: str = "Data") -> str:
    """Print summary statistics and histogram.

    Args:
        data: 1D array of values.
        name: Name of the variable.

    Returns:
        String with statistics and histogram.

    Example:
        >>> data = np.random.normal(100, 15, 500)
        >>> print(quick_stats(data, "Test Scores"))
    """
    stats_lines = [
        f"=== {name} ===",
        f"n:      {len(data)}",
        f"mean:   {data.mean():.4f}",
        f"std:    {data.std():.4f}",
        f"min:    {data.min():.4f}",
        f"25%:    {np.percentile(data, 25):.4f}",
        f"median: {np.median(data):.4f}",
        f"75%:    {np.percentile(data, 75):.4f}",
        f"max:    {data.max():.4f}",
        "",
    ]

    hist_str = histogram(data, title=name, show_stats=False, width=60)

    return "\n".join(stats_lines) + hist_str


def time_series(
    data: np.ndarray,
    timestamps: np.ndarray | None = None,
    title: str = "Time Series",
    width: int = 80,
    show_trend: bool = True,
) -> str:
    """Plot time series data with optional trend line.

    Args:
        data: 1D array of values.
        timestamps: Optional x-axis values (defaults to range).
        title: Plot title.
        width: Terminal width in characters.
        show_trend: Show linear trend line.

    Returns:
        Multi-line braille string of time series.

    Example:
        >>> data = np.cumsum(np.random.randn(100))
        >>> print(time_series(data, title="Random Walk"))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    if timestamps is None:
        timestamps = np.arange(len(data))

    fig, ax = plt.subplots(figsize=(12, 4), dpi=150)

    ax.plot(timestamps, data, 'k-', linewidth=2)

    if show_trend:
        z = np.polyfit(timestamps, data, 1)
        p = np.poly1d(z)
        ax.plot(timestamps, p(timestamps), 'k--', linewidth=1, alpha=0.7)

        trend_dir = "increasing" if z[0] > 0 else "decreasing"
        ax.text(0.02, 0.98, f"Trend: {trend_dir} ({z[0]:.4f}/unit)",
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel("Time", fontsize=11)
    ax.set_ylabel("Value", fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def demo_histograms() -> None:
    """Demo: histogram visualizations."""
    print("=" * 60)
    print("HISTOGRAMS")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Normal Distribution ---")
    normal = np.random.normal(0, 1, 1000)
    print(histogram(normal, title="Normal Distribution (mean=0, std=1)"))

    print("\n--- Skewed Distribution ---")
    skewed = np.random.exponential(2, 1000)
    print(histogram(skewed, title="Exponential Distribution"))

    print("\n--- Bimodal Distribution ---")
    bimodal = np.concatenate([
        np.random.normal(-2, 0.5, 500),
        np.random.normal(2, 0.5, 500)
    ])
    print(histogram(bimodal, title="Bimodal Distribution"))


def demo_boxplots() -> None:
    """Demo: box plot comparisons."""
    print("\n" + "=" * 60)
    print("BOX PLOTS")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Distribution Comparison ---")
    datasets = {
        "Control": np.random.normal(100, 15, 100),
        "Treatment A": np.random.normal(110, 12, 100),
        "Treatment B": np.random.normal(95, 20, 100),
    }
    print(boxplot_compare(datasets, title="Treatment Effects"))


def demo_scatter() -> None:
    """Demo: scatter plots with regression."""
    print("\n" + "=" * 60)
    print("SCATTER PLOTS")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Strong Linear Correlation ---")
    x = np.random.rand(100) * 10
    y = 2.5 * x + 3 + np.random.randn(100) * 2
    print(scatter_with_fit(x, y, title="Strong Linear Correlation"))

    print("\n--- Weak Correlation ---")
    x = np.random.rand(100) * 10
    y = 0.5 * x + np.random.randn(100) * 5
    print(scatter_with_fit(x, y, title="Weak Linear Correlation"))

    print("\n--- Quadratic Relationship ---")
    x = np.random.rand(100) * 6 - 3
    y = x**2 + np.random.randn(100) * 0.5
    print(scatter_with_fit(x, y, fit_type="quadratic", title="Quadratic Fit"))


def demo_time_series() -> None:
    """Demo: time series visualization."""
    print("\n" + "=" * 60)
    print("TIME SERIES")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Random Walk ---")
    walk = np.cumsum(np.random.randn(200))
    print(time_series(walk, title="Random Walk"))

    print("\n--- Seasonal Pattern ---")
    t = np.linspace(0, 10, 200)
    seasonal = np.sin(t * 2 * np.pi / 2) + 0.1 * t + np.random.randn(200) * 0.2
    print(time_series(seasonal, timestamps=t, title="Seasonal + Trend"))


def demo_quick_stats() -> None:
    """Demo: quick statistics summary."""
    print("\n" + "=" * 60)
    print("QUICK STATISTICS")
    print("=" * 60)

    np.random.seed(42)
    test_scores = np.random.normal(75, 10, 150)
    test_scores = np.clip(test_scores, 0, 100)

    print("\n" + quick_stats(test_scores, "Test Scores"))


def main() -> int:
    """Run the statistics dashboard demo."""
    if not MATPLOTLIB_AVAILABLE:
        print(
            "Error: matplotlib is required for this demo.\n\n"
            "Install it with:\n"
            "    pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    print("Statistical Visualization Dashboard")
    print("Using pixdot for braille visualization")
    print()

    demo_histograms()
    demo_boxplots()
    demo_scatter()
    demo_time_series()
    demo_quick_stats()

    print("\n" + "=" * 60)
    print("AVAILABLE FUNCTIONS")
    print("=" * 60)
    print("""
histogram(data, bins=30, title="Distribution")
boxplot_compare({"A": data_a, "B": data_b}, title="Comparison")
scatter_with_fit(x, y, fit_type="linear", title="Scatter")
correlation_matrix({"A": a, "B": b, "C": c})
time_series(data, title="Time Series")
quick_stats(data, name="Variable")
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
