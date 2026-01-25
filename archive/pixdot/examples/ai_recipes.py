#!/usr/bin/env python3
"""Ready-to-use recipes for Claude Code.

Each recipe is self-contained and produces immediate output.
Claude Code can copy these directly into terminal conversations.

These are minimal, working examples that demonstrate common visualization
patterns. Copy-paste any recipe and it will work immediately (assuming
the required dependencies are installed).

Requires: pip install matplotlib (for most recipes)

Usage:
    python ai_recipes.py             # Run all demos
    python ai_recipes.py --recipe 1  # Run specific recipe
"""

from __future__ import annotations

import sys

import numpy as np


def recipe_1_function_plot() -> str:
    """Recipe 1: Plot any mathematical function.

    Copy this recipe to quickly visualize a mathematical function.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    x = np.linspace(-10, 10, 500)
    ax.plot(x, np.sin(x), 'k-', linewidth=3)
    ax.set_title("sin(x)", fontweight='bold')
    ax.grid(True)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_2_histogram() -> str:
    """Recipe 2: Quick histogram of data.

    Copy this recipe to visualize data distribution.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your data
    data = np.random.normal(0, 1, 1000)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.hist(data, bins=30, color='black', edgecolor='white')
    ax.set_title(f"Distribution (n={len(data)}, mean={data.mean():.2f})", fontweight='bold')
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_3_scatter_regression() -> str:
    """Recipe 3: Scatter plot with linear regression.

    Copy this recipe to show correlation between two variables.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your data
    x = np.random.rand(50) * 10
    y = 2 * x + 3 + np.random.randn(50) * 2

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.scatter(x, y, c='black', s=40)

    # Fit and plot trend line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), 'k--', linewidth=2,
            label=f'y = {z[0]:.2f}x + {z[1]:.2f}')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_title("Linear Correlation", fontweight='bold')
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_4_bar_chart() -> str:
    """Recipe 4: Simple bar chart.

    Copy this recipe to compare categorical values.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your data
    categories = ['A', 'B', 'C', 'D', 'E']
    values = [23, 45, 12, 67, 38]

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.bar(categories, values, color='black', edgecolor='black')
    ax.set_title("Bar Chart", fontweight='bold')
    ax.set_ylabel("Value")
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_5_time_series() -> str:
    """Recipe 5: Time series plot.

    Copy this recipe to visualize data over time.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your data
    t = np.arange(100)
    values = np.cumsum(np.random.randn(100)) + 50  # Random walk

    fig, ax = plt.subplots(figsize=(12, 4), dpi=150)
    ax.plot(t, values, 'k-', linewidth=2)
    ax.fill_between(t, values, alpha=0.1, color='black')
    ax.set_title("Time Series", fontweight='bold')
    ax.set_xlabel("Time")
    ax.grid(True, alpha=0.3)
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_6_multiple_lines() -> str:
    """Recipe 6: Multiple lines on same plot.

    Copy this recipe to compare multiple series.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    x = np.linspace(0, 10, 200)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.plot(x, np.sin(x), 'k-', linewidth=3, label='sin(x)')
    ax.plot(x, np.cos(x), 'k--', linewidth=3, label='cos(x)')
    ax.plot(x, np.sin(x) * np.cos(x), 'k:', linewidth=3, label='sin(x)cos(x)')
    ax.legend()
    ax.grid(True, alpha=0.5)
    ax.set_title("Multiple Functions", fontweight='bold')
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_7_subplots() -> str:
    """Recipe 7: Multiple subplots in a grid.

    Copy this recipe for multi-panel visualizations.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), dpi=150)

    x = np.linspace(-5, 5, 200)

    # Top-left: line plot
    axes[0, 0].plot(x, x**2, 'k-', linewidth=3)
    axes[0, 0].set_title("Parabola", fontweight='bold')
    axes[0, 0].grid(True)

    # Top-right: scatter
    xs = np.random.randn(50)
    ys = np.random.randn(50)
    axes[0, 1].scatter(xs, ys, c='black', s=30)
    axes[0, 1].set_title("Random Points", fontweight='bold')

    # Bottom-left: histogram
    data = np.random.normal(0, 1, 500)
    axes[1, 0].hist(data, bins=20, color='black', edgecolor='white')
    axes[1, 0].set_title("Histogram", fontweight='bold')

    # Bottom-right: bar chart
    axes[1, 1].bar(['A', 'B', 'C'], [3, 7, 5], color='black')
    axes[1, 1].set_title("Bar Chart", fontweight='bold')

    plt.tight_layout()
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_8_heatmap() -> str:
    """Recipe 8: 2D heatmap visualization.

    Copy this recipe to show 2D data intensity.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your 2D data
    x = np.linspace(-3, 3, 100)
    y = np.linspace(-3, 3, 100)
    X, Y = np.meshgrid(x, y)
    Z = np.exp(-(X**2 + Y**2))  # 2D Gaussian

    fig, ax = plt.subplots(figsize=(8, 8), dpi=150)
    ax.imshow(Z, cmap='gray', extent=[-3, 3, -3, 3])
    ax.set_title("2D Gaussian", fontweight='bold')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_9_box_whisker() -> str:
    """Recipe 9: Box-and-whisker plot.

    Copy this recipe to compare distributions.
    """
    from pixdot.adapters import figure_to_braille
    import matplotlib.pyplot as plt

    # Replace with your data
    data = [
        np.random.normal(100, 10, 100),
        np.random.normal(90, 15, 100),
        np.random.normal(110, 8, 100),
    ]
    labels = ['Group A', 'Group B', 'Group C']

    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    for box in bp['boxes']:
        box.set_facecolor('white')
        box.set_edgecolor('black')
        box.set_linewidth(2)
    for median in bp['medians']:
        median.set_color('black')
        median.set_linewidth(3)
    ax.set_title("Distribution Comparison", fontweight='bold')
    ax.grid(True, axis='y', alpha=0.3)
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result


def recipe_10_direct_array() -> str:
    """Recipe 10: Direct numpy array to braille (no matplotlib).

    Copy this recipe for simple bitmap rendering.
    """
    from pixdot import render

    # Create a simple pattern - a circle
    size = 80
    fb = np.zeros((size, size * 2), dtype=np.float32)

    # Draw a circle
    y, x = np.ogrid[:size, :size * 2]
    center_x, center_y = size, size // 2
    mask = (x - center_x)**2 + (y - center_y)**2 <= (size // 3)**2
    fb[mask] = 1.0

    return render(fb)


def recipe_11_image_to_braille() -> str:
    """Recipe 11: Load and display an image.

    Copy this recipe to show images in the terminal.
    """
    from pixdot.adapters import load_and_render

    # Replace with your image path
    # This will fail if the file doesn't exist
    # return load_and_render("your_image.png", "dark_terminal")

    # Demo: create a synthetic image
    from pixdot import render
    img = np.random.rand(100, 200).astype(np.float32)
    # Add some structure
    img[30:70, 60:140] = 0.9
    img[40:60, 80:120] = 0.1
    return render(img)


def recipe_12_sparkline() -> str:
    """Recipe 12: Compact sparkline visualization.

    Copy this recipe for inline mini-charts.
    """
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig
    import matplotlib.pyplot as plt

    # Replace with your data
    data = np.cumsum(np.random.randn(50))

    fig, ax = plt.subplots(figsize=(6, 1.5), dpi=150)
    ax.plot(data, 'k-', linewidth=2)
    ax.fill_between(range(len(data)), data, alpha=0.1, color='black')
    ax.axis('off')
    ax.margins(0)

    config = RenderConfig(width_chars=40, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close()
    return result


RECIPES = [
    (recipe_1_function_plot, "Function Plot"),
    (recipe_2_histogram, "Histogram"),
    (recipe_3_scatter_regression, "Scatter with Regression"),
    (recipe_4_bar_chart, "Bar Chart"),
    (recipe_5_time_series, "Time Series"),
    (recipe_6_multiple_lines, "Multiple Lines"),
    (recipe_7_subplots, "Subplots Grid"),
    (recipe_8_heatmap, "Heatmap"),
    (recipe_9_box_whisker, "Box-and-Whisker"),
    (recipe_10_direct_array, "Direct Array (no matplotlib)"),
    (recipe_11_image_to_braille, "Image to Braille"),
    (recipe_12_sparkline, "Sparkline"),
]


def main(argv: list[str] | None = None) -> int:
    """Run recipe demos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="pixdot recipes for Claude Code",
    )
    parser.add_argument(
        "--recipe", "-r",
        type=int,
        choices=range(1, len(RECIPES) + 1),
        help=f"Run specific recipe (1-{len(RECIPES)})",
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all recipes",
    )

    args = parser.parse_args(argv)

    if args.list:
        print("Available Recipes:")
        print()
        for i, (_, name) in enumerate(RECIPES, 1):
            print(f"  {i:2d}. {name}")
        return 0

    # Check matplotlib for most recipes
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        mpl_available = True
    except ImportError:
        mpl_available = False

    if args.recipe:
        # Run specific recipe
        recipe_func, recipe_name = RECIPES[args.recipe - 1]

        if not mpl_available and args.recipe not in [10, 11]:
            print(
                "Error: matplotlib required for this recipe.\n"
                "Install with: pip install matplotlib",
                file=sys.stderr,
            )
            return 1

        print(f"Recipe {args.recipe}: {recipe_name}")
        print("=" * 50)
        print()
        try:
            result = recipe_func()
            print(result)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        return 0

    # Run all recipes
    print("pixdot Recipes for Claude Code")
    print("=" * 60)
    print()
    print("Each recipe is self-contained and can be copied directly")
    print("into a Claude Code conversation.")
    print()

    for i, (recipe_func, recipe_name) in enumerate(RECIPES, 1):
        print(f"\n{'=' * 60}")
        print(f"Recipe {i}: {recipe_name}")
        print("=" * 60)
        print()

        # Skip matplotlib recipes if not available
        if not mpl_available and i not in [10, 11]:
            print("(Skipped - requires matplotlib)")
            continue

        try:
            result = recipe_func()
            print(result)
        except Exception as e:
            print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Usage Tips")
    print("=" * 60)
    print("""
1. Each recipe function is self-contained
2. Copy the function body directly into your code
3. Modify the data to use your own values
4. All recipes use 'dark_terminal' preset (inverted for dark bg)

For light terminal backgrounds, use 'light_terminal' preset instead.
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
