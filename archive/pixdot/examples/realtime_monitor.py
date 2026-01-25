#!/usr/bin/env python3
"""Live data visualization and monitoring with pixdot.

Demonstrates real-time updating charts and sparklines - useful for
monitoring system metrics, live data feeds, or any streaming data.

Requires: pip install matplotlib

Usage:
    python realtime_monitor.py
    python realtime_monitor.py --demo sparkline
    python realtime_monitor.py --demo live
"""

from __future__ import annotations

import sys
import time
from collections import deque
from typing import Iterator

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


def sparkline(data: np.ndarray, width: int = 40) -> str:
    """Render a compact sparkline visualization.

    Sparklines are tiny inline charts that show trends at a glance.
    No axes, no labels - just the data.

    Args:
        data: 1D array of values.
        width: Terminal width in characters.

    Returns:
        Multi-line braille string (typically 2-3 lines tall).

    Example:
        >>> data = np.cumsum(np.random.randn(50))
        >>> print(sparkline(data))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(4, 1), dpi=100)

    ax.plot(data, 'k-', linewidth=2)
    ax.fill_between(range(len(data)), data, alpha=0.15, color='black')
    ax.axis('off')
    ax.margins(0)
    fig.patch.set_facecolor('white')

    # Sparklines use minimal config
    config = RenderConfig(width_chars=width, invert=True, dither=False, threshold=0.5)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def sparkline_row(
    data: np.ndarray,
    label: str = "",
    width: int = 40,
    show_value: bool = True,
) -> str:
    """Sparkline with optional label and current value.

    Creates a single-line dashboard-style row:
        Label    [sparkline]    current_value

    Args:
        data: 1D array of values.
        label: Text label for the metric.
        width: Width for the sparkline portion.
        show_value: Show the last value.

    Returns:
        Formatted string with label, sparkline, and value.

    Example:
        >>> data = np.random.rand(50) * 100
        >>> print(sparkline_row(data, "CPU %", show_value=True))
    """
    spark = sparkline(data, width=width)
    lines = spark.split('\n')

    # Build the output
    result_lines = []
    current_val = f"{data[-1]:.1f}" if show_value else ""

    for i, line in enumerate(lines):
        if i == 0 and label:
            prefix = f"{label:12s}"
        else:
            prefix = " " * 12
        suffix = f"  {current_val}" if i == 0 and show_value else ""
        result_lines.append(f"{prefix} {line}{suffix}")

    return '\n'.join(result_lines)


def live_chart(
    data: np.ndarray,
    title: str = "",
    width: int = 80,
    y_range: tuple[float, float] | None = None,
) -> str:
    """Render a live-updating style chart.

    Shows the most recent data window with a clear time axis.
    Suitable for refreshing displays.

    Args:
        data: 1D array of recent values.
        title: Chart title.
        width: Terminal width in characters.
        y_range: Optional (min, max) for y-axis.

    Returns:
        Multi-line braille string of the chart.

    Example:
        >>> buffer = deque(maxlen=100)
        >>> for _ in range(100):
        ...     buffer.append(np.random.randn())
        >>> print(live_chart(np.array(buffer), "Live Data"))
    """
    _check_matplotlib()
    from pixdot.adapters import figure_to_braille
    from pixdot import RenderConfig

    fig, ax = plt.subplots(figsize=(10, 4), dpi=150)

    ax.plot(data, 'k-', linewidth=2)
    ax.fill_between(range(len(data)), data, alpha=0.1, color='black')

    if y_range:
        ax.set_ylim(y_range)

    if title:
        ax.set_title(title, fontsize=12, fontweight='bold')

    ax.set_xlabel(f"Last {len(data)} samples")
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    config = RenderConfig(width_chars=width, invert=True, dither=True)
    result = figure_to_braille(fig, config)
    plt.close(fig)
    return result


def multi_metric_dashboard(
    metrics: dict[str, np.ndarray],
    width: int = 80,
) -> str:
    """Dashboard showing multiple metrics as sparklines.

    Args:
        metrics: Dictionary mapping metric names to data arrays.
        width: Total width in characters.

    Returns:
        Multi-line string showing all metrics.

    Example:
        >>> metrics = {
        ...     "CPU %": np.random.rand(50) * 100,
        ...     "Memory %": np.random.rand(50) * 80 + 20,
        ...     "Network KB/s": np.random.rand(50) * 1000,
        ... }
        >>> print(multi_metric_dashboard(metrics))
    """
    lines = []
    spark_width = width - 25  # Leave room for label and value

    for name, data in metrics.items():
        row = sparkline_row(data, label=name, width=spark_width, show_value=True)
        lines.append(row)
        lines.append("")  # Blank line between metrics

    return '\n'.join(lines)


def generate_fake_metrics() -> Iterator[dict[str, float]]:
    """Generate fake system metrics for demo.

    Yields:
        Dictionary with CPU, Memory, and Network values.
    """
    cpu_base = 30.0
    mem_base = 50.0
    net_base = 100.0

    while True:
        # Random walk with mean reversion
        cpu_base += np.random.randn() * 5
        cpu_base = np.clip(cpu_base * 0.95 + 30 * 0.05, 0, 100)

        mem_base += np.random.randn() * 2
        mem_base = np.clip(mem_base * 0.98 + 50 * 0.02, 0, 100)

        net_base += np.random.randn() * 50
        net_base = np.clip(net_base * 0.9 + 100 * 0.1, 0, 1000)

        # Add some noise
        cpu = cpu_base + np.random.randn() * 3
        mem = mem_base + np.random.randn() * 1
        net = net_base + np.random.randn() * 20

        yield {
            "CPU %": np.clip(cpu, 0, 100),
            "Memory %": np.clip(mem, 0, 100),
            "Network KB/s": max(0, net),
        }


class MetricsBuffer:
    """Rolling buffer for storing metric history."""

    def __init__(self, maxlen: int = 100):
        """Initialize buffers for each metric.

        Args:
            maxlen: Maximum history length per metric.
        """
        self.maxlen = maxlen
        self.buffers: dict[str, deque] = {}

    def add(self, metrics: dict[str, float]) -> None:
        """Add new metric values.

        Args:
            metrics: Dictionary of metric name to value.
        """
        for name, value in metrics.items():
            if name not in self.buffers:
                self.buffers[name] = deque(maxlen=self.maxlen)
            self.buffers[name].append(value)

    def get_arrays(self) -> dict[str, np.ndarray]:
        """Get all metrics as numpy arrays.

        Returns:
            Dictionary mapping metric names to arrays.
        """
        return {
            name: np.array(buf)
            for name, buf in self.buffers.items()
        }


def demo_sparklines() -> None:
    """Demo: sparkline visualizations."""
    print("=" * 60)
    print("SPARKLINES")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Random Walk ---")
    walk = np.cumsum(np.random.randn(50))
    print(sparkline(walk, width=60))

    print("\n--- Sine Wave ---")
    x = np.linspace(0, 4 * np.pi, 50)
    sine = np.sin(x)
    print(sparkline(sine, width=60))

    print("\n--- CPU Usage Style ---")
    cpu = np.random.rand(50) * 40 + 30  # 30-70%
    print(sparkline_row(cpu, "CPU %", width=50))

    print("\n--- Memory Usage Style ---")
    mem = np.random.rand(50) * 20 + 60  # 60-80%
    print(sparkline_row(mem, "Memory %", width=50))


def demo_live_chart() -> None:
    """Demo: live-updating chart style."""
    print("\n" + "=" * 60)
    print("LIVE CHART STYLE")
    print("=" * 60)

    np.random.seed(42)

    print("\n--- Simulated Live Data ---")
    # Simulate 100 recent samples
    data = np.cumsum(np.random.randn(100)) + 50
    print(live_chart(data, title="Server Response Time (ms)"))


def demo_dashboard() -> None:
    """Demo: multi-metric dashboard."""
    print("\n" + "=" * 60)
    print("METRICS DASHBOARD")
    print("=" * 60)

    np.random.seed(42)

    metrics = {
        "CPU %": np.random.rand(50) * 40 + 30,
        "Memory %": np.random.rand(50) * 20 + 55,
        "Disk I/O": np.random.rand(50) * 100 + 20,
        "Network": np.random.rand(50) * 500 + 100,
    }

    print("\n" + multi_metric_dashboard(metrics))


def demo_animated(duration: int = 10, interval: float = 0.5) -> None:
    """Demo: animated live updating (clears screen).

    Args:
        duration: How long to run in seconds.
        interval: Update interval in seconds.
    """
    print("\n" + "=" * 60)
    print("ANIMATED LIVE MONITORING")
    print("=" * 60)
    print(f"\nRunning for {duration} seconds (Ctrl+C to stop)...")
    print()

    buffer = MetricsBuffer(maxlen=50)
    generator = generate_fake_metrics()

    # Pre-fill buffer
    for _ in range(50):
        buffer.add(next(generator))

    start_time = time.time()

    try:
        while time.time() - start_time < duration:
            # Clear screen (ANSI escape)
            print("\033[2J\033[H", end="")

            # Add new data
            buffer.add(next(generator))

            # Render dashboard
            print("Real-time Metrics Dashboard")
            print("=" * 50)
            print(f"Elapsed: {time.time() - start_time:.1f}s")
            print()
            print(multi_metric_dashboard(buffer.get_arrays(), width=60))

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\nStopped.")


def main(argv: list[str] | None = None) -> int:
    """Run the realtime monitoring demo."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Real-time visualization demo with pixdot",
    )
    parser.add_argument(
        "--demo",
        choices=["all", "sparkline", "live", "dashboard", "animated"],
        default="all",
        help="Which demo to run",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Duration for animated demo in seconds",
    )

    args = parser.parse_args(argv)

    if not MATPLOTLIB_AVAILABLE:
        print(
            "Error: matplotlib is required for this demo.\n\n"
            "Install it with:\n"
            "    pip install matplotlib",
            file=sys.stderr,
        )
        return 1

    print("Real-time Visualization with pixdot")
    print()

    if args.demo in ("all", "sparkline"):
        demo_sparklines()

    if args.demo in ("all", "live"):
        demo_live_chart()

    if args.demo in ("all", "dashboard"):
        demo_dashboard()

    if args.demo == "animated":
        demo_animated(duration=args.duration)

    if args.demo == "all":
        print("\n" + "=" * 60)
        print("FUNCTIONS AVAILABLE")
        print("=" * 60)
        print("""
sparkline(data, width=40)
    Compact inline chart, no axes

sparkline_row(data, label="CPU", width=40)
    Sparkline with label and current value

live_chart(data, title="", width=80)
    Full chart for streaming data

multi_metric_dashboard({"CPU": cpu_data, "Mem": mem_data})
    Multiple metrics in one view

For animated demo: python realtime_monitor.py --demo animated
""")

    return 0


if __name__ == "__main__":
    sys.exit(main())
