"""Tests for the pixdot.adapters module."""

import numpy as np
import pytest

from pixdot import RenderConfig
from pixdot.adapters import BitmapAdapter, NumpyAdapter, array_to_braille


class TestBitmapAdapterValidation:
    """Tests for BitmapAdapter validation methods."""

    def test_validate_bitmap_accepts_valid_2d_array(self):
        """validate_bitmap accepts valid 2D arrays."""
        bitmap = np.zeros((100, 200), dtype=np.float32)
        # Should not raise
        BitmapAdapter.validate_bitmap(bitmap)

    def test_validate_bitmap_accepts_integer_array(self):
        """validate_bitmap accepts integer arrays."""
        bitmap = np.zeros((100, 200), dtype=np.uint8)
        # Should not raise
        BitmapAdapter.validate_bitmap(bitmap)

    def test_validate_bitmap_rejects_3d_array(self):
        """validate_bitmap rejects 3D arrays."""
        bitmap = np.zeros((100, 200, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="must be 2D"):
            BitmapAdapter.validate_bitmap(bitmap)

    def test_validate_bitmap_rejects_1d_array(self):
        """validate_bitmap rejects 1D arrays."""
        bitmap = np.zeros((100,), dtype=np.float32)
        with pytest.raises(ValueError, match="must be 2D"):
            BitmapAdapter.validate_bitmap(bitmap)

    def test_validate_bitmap_rejects_wrong_dtype(self):
        """validate_bitmap rejects non-numeric dtypes."""
        bitmap = np.array([["a", "b"], ["c", "d"]])
        with pytest.raises(ValueError, match="must be numeric"):
            BitmapAdapter.validate_bitmap(bitmap)

    def test_validate_bitmap_uses_custom_name(self):
        """validate_bitmap uses custom name in error messages."""
        bitmap = np.zeros((100,), dtype=np.float32)
        with pytest.raises(ValueError, match="my_bitmap"):
            BitmapAdapter.validate_bitmap(bitmap, name="my_bitmap")

    def test_validate_color_bitmap_accepts_valid_3d_array(self):
        """validate_color_bitmap accepts valid 3D RGB arrays."""
        colors = np.zeros((100, 200, 3), dtype=np.float32)
        # Should not raise
        BitmapAdapter.validate_color_bitmap(colors, (100, 200))

    def test_validate_color_bitmap_rejects_2d_array(self):
        """validate_color_bitmap rejects 2D arrays."""
        colors = np.zeros((100, 200), dtype=np.float32)
        with pytest.raises(ValueError, match="must be 3D"):
            BitmapAdapter.validate_color_bitmap(colors, (100, 200))

    def test_validate_color_bitmap_rejects_wrong_channels(self):
        """validate_color_bitmap rejects arrays without 3 channels."""
        colors = np.zeros((100, 200, 4), dtype=np.float32)
        with pytest.raises(ValueError, match="3 color channels"):
            BitmapAdapter.validate_color_bitmap(colors, (100, 200))

    def test_validate_color_bitmap_rejects_shape_mismatch(self):
        """validate_color_bitmap rejects shape mismatches."""
        colors = np.zeros((50, 100, 3), dtype=np.float32)
        with pytest.raises(ValueError, match="doesn't match"):
            BitmapAdapter.validate_color_bitmap(colors, (100, 200))


class TestNumpyAdapter:
    """Tests for NumpyAdapter."""

    def test_to_bitmap_passthrough_float32(self):
        """NumpyAdapter passes through float32 2D arrays."""
        adapter = NumpyAdapter()
        source = np.random.rand(100, 200).astype(np.float32)
        config = RenderConfig()

        result = adapter.to_bitmap(source, config)

        assert result.shape == (100, 200)
        assert result.dtype == np.float32

    def test_to_bitmap_normalizes_integer(self):
        """NumpyAdapter normalizes integer arrays to 0-1."""
        adapter = NumpyAdapter()
        source = np.full((10, 20), 255, dtype=np.uint8)
        config = RenderConfig()

        result = adapter.to_bitmap(source, config)

        assert result.dtype == np.float32
        assert result.max() == pytest.approx(1.0)

    def test_to_bitmap_converts_rgb_to_grayscale(self):
        """NumpyAdapter converts RGB arrays to grayscale."""
        adapter = NumpyAdapter()
        # Pure white RGB
        source = np.ones((10, 20, 3), dtype=np.float32)
        config = RenderConfig()

        result = adapter.to_bitmap(source, config)

        assert result.shape == (10, 20)
        assert result.dtype == np.float32
        # White should remain close to 1.0
        assert result.mean() == pytest.approx(1.0)

    def test_to_bitmap_converts_rgba_to_grayscale(self):
        """NumpyAdapter converts RGBA arrays to grayscale."""
        adapter = NumpyAdapter()
        source = np.ones((10, 20, 4), dtype=np.float32)
        config = RenderConfig()

        result = adapter.to_bitmap(source, config)

        assert result.shape == (10, 20)
        assert result.dtype == np.float32

    def test_to_bitmap_rejects_invalid_dimensions(self):
        """NumpyAdapter rejects arrays with invalid dimensions."""
        adapter = NumpyAdapter()
        source = np.zeros((10, 20, 5), dtype=np.float32)  # 5 channels
        config = RenderConfig()

        with pytest.raises(ValueError):
            adapter.to_bitmap(source, config)

    def test_to_color_bitmap_extracts_rgb(self):
        """NumpyAdapter extracts RGB from 3D arrays."""
        adapter = NumpyAdapter()
        source = np.random.rand(10, 20, 3).astype(np.float32)
        config = RenderConfig()

        result = adapter.to_color_bitmap(source, config)

        assert result is not None
        assert result.shape == (10, 20, 3)

    def test_to_color_bitmap_extracts_rgb_from_rgba(self):
        """NumpyAdapter extracts RGB from RGBA arrays."""
        adapter = NumpyAdapter()
        source = np.random.rand(10, 20, 4).astype(np.float32)
        config = RenderConfig()

        result = adapter.to_color_bitmap(source, config)

        assert result is not None
        assert result.shape == (10, 20, 3)

    def test_to_color_bitmap_returns_none_for_grayscale(self):
        """NumpyAdapter returns None for 2D grayscale arrays."""
        adapter = NumpyAdapter()
        source = np.random.rand(10, 20).astype(np.float32)
        config = RenderConfig()

        result = adapter.to_color_bitmap(source, config)

        assert result is None

    def test_render_produces_braille_output(self):
        """NumpyAdapter.render produces braille characters."""
        adapter = NumpyAdapter()
        # Diagonal line pattern
        source = np.eye(16, dtype=np.float32)

        result = adapter.render(source, "default")

        # Should contain braille characters
        assert len(result) > 0
        # Braille range is U+2800-U+28FF
        braille_chars = [c for c in result if "\u2800" <= c <= "\u28FF"]
        assert len(braille_chars) > 0

    def test_render_with_preset_string(self):
        """NumpyAdapter.render accepts preset strings."""
        adapter = NumpyAdapter()
        source = np.random.rand(32, 64).astype(np.float32)

        # Should not raise
        result = adapter.render(source, "dark_terminal")
        assert len(result) > 0

    def test_render_with_config_object(self):
        """NumpyAdapter.render accepts RenderConfig objects."""
        adapter = NumpyAdapter()
        source = np.random.rand(32, 64).astype(np.float32)
        config = RenderConfig(width_chars=40, dither=True)

        result = adapter.render(source, config)
        assert len(result) > 0


class TestArrayToBraille:
    """Tests for the array_to_braille convenience function."""

    def test_array_to_braille_produces_output(self):
        """array_to_braille produces braille output."""
        bitmap = np.eye(16, dtype=np.float32)

        result = array_to_braille(bitmap)

        assert len(result) > 0
        braille_chars = [c for c in result if "\u2800" <= c <= "\u28FF"]
        assert len(braille_chars) > 0

    def test_array_to_braille_accepts_preset(self):
        """array_to_braille accepts preset strings."""
        bitmap = np.random.rand(32, 64).astype(np.float32)

        result = array_to_braille(bitmap, "high_detail")

        assert len(result) > 0


class TestPILAdapter:
    """Tests for PILAdapter (requires pillow)."""

    @pytest.fixture
    def pil_available(self):
        """Check if PIL is available."""
        try:
            import PIL  # noqa: F401

            return True
        except ImportError:
            pytest.skip("PIL not available")

    def test_pil_adapter_import_error_message(self, monkeypatch):
        """PILAdapter raises clear error when pillow not installed."""
        # Mock PIL not being available
        import sys

        # Remove PIL from modules if present
        pil_modules = [k for k in sys.modules if k.startswith("PIL")]
        original_modules = {k: sys.modules.pop(k) for k in pil_modules}

        # Make import fail
        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "PIL" or name.startswith("PIL."):
                raise ImportError("No module named 'PIL'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        try:
            from pixdot.adapters.pil import _require_pillow

            with pytest.raises(ImportError, match="pip install pixdot\\[pil\\]"):
                _require_pillow()
        finally:
            # Restore modules
            sys.modules.update(original_modules)

    def test_pil_adapter_converts_rgb_image(self, pil_available):
        """PILAdapter converts RGB images to grayscale."""
        from PIL import Image

        from pixdot.adapters import PILAdapter

        image = Image.new("RGB", (100, 50), color=(255, 255, 255))
        adapter = PILAdapter()
        config = RenderConfig()

        result = adapter.to_bitmap(image, config)

        assert result.shape == (50, 100)
        assert result.dtype == np.float32
        assert result.max() == pytest.approx(1.0)

    def test_pil_adapter_converts_rgba_image(self, pil_available):
        """PILAdapter converts RGBA images to grayscale."""
        from PIL import Image

        from pixdot.adapters import PILAdapter

        image = Image.new("RGBA", (100, 50), color=(128, 128, 128, 255))
        adapter = PILAdapter()
        config = RenderConfig()

        result = adapter.to_bitmap(image, config)

        assert result.shape == (50, 100)

    def test_pil_adapter_passthrough_grayscale(self, pil_available):
        """PILAdapter passes through grayscale images."""
        from PIL import Image

        from pixdot.adapters import PILAdapter

        image = Image.new("L", (100, 50), color=200)
        adapter = PILAdapter()
        config = RenderConfig()

        result = adapter.to_bitmap(image, config)

        assert result.shape == (50, 100)
        assert result.mean() == pytest.approx(200 / 255.0, rel=0.01)

    def test_pil_adapter_to_color_bitmap(self, pil_available):
        """PILAdapter extracts RGB from images."""
        from PIL import Image

        from pixdot.adapters import PILAdapter

        # Red image
        image = Image.new("RGB", (10, 10), color=(255, 0, 0))
        adapter = PILAdapter()
        config = RenderConfig()

        result = adapter.to_color_bitmap(image, config)

        assert result.shape == (10, 10, 3)
        # Red channel should be 1.0
        assert result[:, :, 0].mean() == pytest.approx(1.0)
        # Green/Blue should be 0.0
        assert result[:, :, 1].mean() == pytest.approx(0.0)
        assert result[:, :, 2].mean() == pytest.approx(0.0)

    def test_pil_adapter_render_integration(self, pil_available):
        """PILAdapter full pipeline produces braille output."""
        from PIL import Image

        from pixdot.adapters import PILAdapter

        # Create a gradient image
        arr = np.linspace(0, 255, 100 * 50).reshape(50, 100).astype(np.uint8)
        image = Image.fromarray(arr, mode="L")
        adapter = PILAdapter()

        result = adapter.render(image, "default")

        assert len(result) > 0


class TestMatplotlibAdapter:
    """Tests for MatplotlibAdapter (requires matplotlib)."""

    @pytest.fixture
    def matplotlib_available(self):
        """Check if matplotlib is available."""
        try:
            import matplotlib  # noqa: F401

            return True
        except ImportError:
            pytest.skip("matplotlib not available")

    def test_matplotlib_adapter_import_error_message(self, monkeypatch):
        """MatplotlibAdapter raises clear error when matplotlib not installed."""
        import sys

        # Remove matplotlib from modules if present
        mpl_modules = [k for k in sys.modules if k.startswith("matplotlib")]
        original_modules = {k: sys.modules.pop(k) for k in mpl_modules}

        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "matplotlib" or name.startswith("matplotlib."):
                raise ImportError("No module named 'matplotlib'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        try:
            from pixdot.adapters.matplotlib import _require_matplotlib

            with pytest.raises(
                ImportError, match="pip install pixdot\\[matplotlib\\]"
            ):
                _require_matplotlib()
        finally:
            sys.modules.update(original_modules)

    def test_matplotlib_adapter_captures_figure(self, matplotlib_available):
        """MatplotlibAdapter captures figure as bitmap."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from pixdot.adapters import MatplotlibAdapter

        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        ax.plot([0, 1], [0, 1])

        adapter = MatplotlibAdapter(dpi=100)
        config = RenderConfig()

        result = adapter.to_bitmap(fig, config)
        plt.close(fig)

        assert result.ndim == 2
        assert result.dtype == np.float32
        # Figure should have some content
        assert result.shape[0] > 0
        assert result.shape[1] > 0

    def test_matplotlib_adapter_to_color_bitmap(self, matplotlib_available):
        """MatplotlibAdapter captures RGB from figures."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from pixdot.adapters import MatplotlibAdapter

        fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
        ax.plot([0, 1], [0, 1], color="red", linewidth=4)

        adapter = MatplotlibAdapter(dpi=100)
        config = RenderConfig()

        result = adapter.to_color_bitmap(fig, config)
        plt.close(fig)

        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_matplotlib_adapter_restores_dpi(self, matplotlib_available):
        """MatplotlibAdapter restores original DPI after rendering."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from pixdot.adapters import MatplotlibAdapter

        fig, ax = plt.subplots(dpi=72)  # Custom DPI
        original_dpi = fig.get_dpi()

        adapter = MatplotlibAdapter(dpi=150)
        adapter.to_bitmap(fig, RenderConfig())

        assert fig.get_dpi() == original_dpi
        plt.close(fig)

    def test_matplotlib_adapter_render_integration(self, matplotlib_available):
        """MatplotlibAdapter full pipeline produces braille output."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from pixdot.adapters import MatplotlibAdapter

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(["A", "B", "C"], [1, 2, 3])

        adapter = MatplotlibAdapter()
        result = adapter.render(fig, "dark_terminal")
        plt.close(fig)

        assert len(result) > 0


class TestCairoAdapter:
    """Tests for CairoAdapter (requires pycairo)."""

    @pytest.fixture
    def cairo_available(self):
        """Check if cairo is available."""
        try:
            import cairo  # noqa: F401

            return True
        except ImportError:
            pytest.skip("cairo not available")

    def test_cairo_adapter_import_error_message(self, monkeypatch):
        """CairoAdapter raises clear error when pycairo not installed."""
        import sys

        # Remove cairo from modules if present
        cairo_modules = [k for k in sys.modules if k == "cairo"]
        original_modules = {k: sys.modules.pop(k) for k in cairo_modules}

        import builtins

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "cairo":
                raise ImportError("No module named 'cairo'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        try:
            from pixdot.adapters.cairo import _require_cairo

            with pytest.raises(ImportError, match="pip install pixdot\\[cairo\\]"):
                _require_cairo()
        finally:
            sys.modules.update(original_modules)

    def test_cairo_adapter_converts_surface(self, cairo_available):
        """CairoAdapter converts ImageSurface to grayscale."""
        import cairo

        from pixdot.adapters import CairoAdapter

        # Create a white surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 50)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(1, 1, 1)  # White
        ctx.paint()

        adapter = CairoAdapter()
        config = RenderConfig()

        result = adapter.to_bitmap(surface, config)

        assert result.shape == (50, 100)
        assert result.dtype == np.float32
        assert result.max() == pytest.approx(1.0)

    def test_cairo_adapter_to_color_bitmap(self, cairo_available):
        """CairoAdapter extracts RGB from surfaces."""
        import cairo

        from pixdot.adapters import CairoAdapter

        # Create a red surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 10, 10)
        ctx = cairo.Context(surface)
        ctx.set_source_rgb(1, 0, 0)  # Red
        ctx.paint()

        adapter = CairoAdapter()
        config = RenderConfig()

        result = adapter.to_color_bitmap(surface, config)

        assert result.shape == (10, 10, 3)
        # Red channel should be 1.0
        assert result[:, :, 0].mean() == pytest.approx(1.0)

    def test_cairo_adapter_render_integration(self, cairo_available):
        """CairoAdapter full pipeline produces braille output."""
        import cairo

        from pixdot.adapters import CairoAdapter

        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        ctx = cairo.Context(surface)
        # White background
        ctx.set_source_rgb(1, 1, 1)
        ctx.paint()
        # Black circle
        ctx.set_source_rgb(0, 0, 0)
        ctx.arc(50, 50, 30, 0, 2 * 3.14159)
        ctx.fill()

        adapter = CairoAdapter()
        result = adapter.render(surface, "dark_terminal")

        assert len(result) > 0


class TestAdaptersModuleImports:
    """Tests for the adapters module imports."""

    def test_base_imports_are_available(self):
        """Core imports are always available."""
        from pixdot.adapters import BitmapAdapter, NumpyAdapter, array_to_braille

        assert BitmapAdapter is not None
        assert NumpyAdapter is not None
        assert array_to_braille is not None

    def test_lazy_import_pil_adapter(self):
        """PILAdapter can be lazily imported."""
        try:
            import PIL  # noqa: F401

            from pixdot.adapters import PILAdapter

            assert PILAdapter is not None
        except ImportError:
            # PIL not available, skip
            pass

    def test_lazy_import_matplotlib_adapter(self):
        """MatplotlibAdapter can be lazily imported."""
        try:
            import matplotlib  # noqa: F401

            from pixdot.adapters import MatplotlibAdapter

            assert MatplotlibAdapter is not None
        except ImportError:
            # matplotlib not available, skip
            pass

    def test_lazy_import_cairo_adapter(self):
        """CairoAdapter can be lazily imported."""
        try:
            import cairo  # noqa: F401

            from pixdot.adapters import CairoAdapter

            assert CairoAdapter is not None
        except ImportError:
            # cairo not available, skip
            pass

    def test_invalid_attribute_raises(self):
        """Invalid attribute access raises AttributeError."""
        import pixdot.adapters as adapters

        with pytest.raises(AttributeError, match="has no attribute"):
            _ = adapters.NonexistentAdapter


class TestIntegrationWithPresets:
    """Integration tests with RenderConfig presets."""

    def test_numpy_adapter_with_all_presets(self):
        """NumpyAdapter works with all standard presets."""
        from pixdot.config import PRESETS

        adapter = NumpyAdapter()
        bitmap = np.random.rand(64, 128).astype(np.float32)

        for preset_name in PRESETS:
            result = adapter.render(bitmap, preset_name)
            assert len(result) > 0, f"Preset {preset_name} produced empty output"

    def test_adapter_color_mode_integration(self):
        """Adapters work with color mode presets."""
        adapter = NumpyAdapter()
        # RGB input
        rgb = np.random.rand(32, 64, 3).astype(np.float32)

        # Test with grayscale color mode
        result = adapter.render(rgb, "grayscale")
        assert len(result) > 0
        # Should contain ANSI escape codes
        assert "\x1b[" in result

        # Test with truecolor mode
        result = adapter.render(rgb, "truecolor")
        assert len(result) > 0
        assert "\x1b[" in result
