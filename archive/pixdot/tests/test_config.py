"""Unit tests for the pixdot.config module."""

import pytest

from pixdot import PRESETS, RenderConfig, get_preset


class TestRenderConfig:
    """Tests for RenderConfig dataclass."""

    def test_default_values(self):
        """Default config should have expected values."""
        config = RenderConfig()
        assert config.width_chars == 80
        assert config.cell_aspect == 0.5
        assert config.invert is True
        assert config.dither is True
        assert config.dither_threshold == 0.5
        assert config.auto_contrast is False
        assert config.threshold is None

    def test_custom_values(self):
        """Should accept custom values."""
        config = RenderConfig(
            width_chars=120,
            cell_aspect=0.4,
            invert=False,
            dither=False,
            dither_threshold=0.6,
            auto_contrast=True,
            threshold=0.5,
            color_mode="grayscale",
        )
        assert config.width_chars == 120
        assert config.cell_aspect == 0.4
        assert config.invert is False
        assert config.dither is False
        assert config.dither_threshold == 0.6
        assert config.auto_contrast is True
        assert config.threshold == 0.5
        assert config.color_mode == "grayscale"

    def test_default_color_mode_is_none(self):
        """Default color_mode should be None."""
        config = RenderConfig()
        assert config.color_mode is None

    def test_frozen(self):
        """RenderConfig should be immutable."""
        config = RenderConfig()
        with pytest.raises(AttributeError):
            config.width_chars = 100

    def test_with_width(self):
        """with_width should return new config with changed width."""
        original = RenderConfig()
        modified = original.with_width(120)

        assert modified.width_chars == 120
        assert original.width_chars == 80  # Original unchanged
        # Other values preserved
        assert modified.invert == original.invert
        assert modified.dither == original.dither

    def test_with_dither(self):
        """with_dither should return new config with changed dither."""
        original = RenderConfig(dither=True)
        modified = original.with_dither(False)

        assert modified.dither is False
        assert original.dither is True  # Original unchanged
        # Other values preserved
        assert modified.width_chars == original.width_chars

    def test_with_invert(self):
        """with_invert should return new config with changed invert."""
        original = RenderConfig(invert=True)
        modified = original.with_invert(False)

        assert modified.invert is False
        assert original.invert is True  # Original unchanged

    def test_with_color(self):
        """with_color should return new config with changed color_mode."""
        original = RenderConfig(color_mode=None)
        modified = original.with_color("grayscale")

        assert modified.color_mode == "grayscale"
        assert original.color_mode is None  # Original unchanged
        # Other values preserved
        assert modified.width_chars == original.width_chars

    def test_with_color_truecolor(self):
        """with_color should work with truecolor mode."""
        original = RenderConfig()
        modified = original.with_color("truecolor")

        assert modified.color_mode == "truecolor"

    def test_with_color_none_removes(self):
        """with_color(None) should remove color mode."""
        original = RenderConfig(color_mode="grayscale")
        modified = original.with_color(None)

        assert modified.color_mode is None

    def test_equality(self):
        """Configs with same values should be equal."""
        config1 = RenderConfig(width_chars=100)
        config2 = RenderConfig(width_chars=100)
        assert config1 == config2

    def test_hashable(self):
        """RenderConfig should be hashable (frozen dataclass)."""
        config = RenderConfig()
        # Should not raise
        hash(config)
        # Can be used in sets/dicts
        configs = {config}
        assert len(configs) == 1


class TestPresets:
    """Tests for configuration presets."""

    def test_all_presets_exist(self):
        """All expected presets should exist."""
        expected = [
            "default",
            "dark_terminal",
            "light_terminal",
            "high_detail",
            "compact",
            "no_dither",
            "grayscale",
            "truecolor",
        ]
        for name in expected:
            assert name in PRESETS

    def test_default_preset(self):
        """Default preset should have expected values."""
        config = PRESETS["default"]
        assert config.width_chars == 80
        assert config.invert is True
        assert config.dither is True

    def test_dark_terminal_preset(self):
        """Dark terminal preset should invert."""
        config = PRESETS["dark_terminal"]
        assert config.invert is True

    def test_light_terminal_preset(self):
        """Light terminal preset should not invert."""
        config = PRESETS["light_terminal"]
        assert config.invert is False

    def test_high_detail_preset(self):
        """High detail preset should be wider."""
        config = PRESETS["high_detail"]
        assert config.width_chars == 120
        assert config.dither is True

    def test_compact_preset(self):
        """Compact preset should be narrower."""
        config = PRESETS["compact"]
        assert config.width_chars == 40

    def test_no_dither_preset(self):
        """No dither preset should have dithering disabled."""
        config = PRESETS["no_dither"]
        assert config.dither is False
        assert config.threshold == 0.5

    def test_grayscale_preset(self):
        """Grayscale preset should have color_mode set and dithering disabled."""
        config = PRESETS["grayscale"]
        assert config.color_mode == "grayscale"
        assert config.dither is False

    def test_truecolor_preset(self):
        """Truecolor preset should have color_mode set and dithering disabled."""
        config = PRESETS["truecolor"]
        assert config.color_mode == "truecolor"
        assert config.dither is False


class TestGetPreset:
    """Tests for get_preset function."""

    def test_get_valid_preset(self):
        """Should return preset for valid name."""
        config = get_preset("default")
        assert isinstance(config, RenderConfig)
        assert config == PRESETS["default"]

    def test_get_all_presets(self):
        """Should be able to get all presets by name."""
        for name in PRESETS:
            config = get_preset(name)
            assert config == PRESETS[name]

    def test_invalid_preset_raises(self):
        """Should raise KeyError for invalid preset name."""
        with pytest.raises(KeyError) as exc_info:
            get_preset("nonexistent")
        assert "nonexistent" in str(exc_info.value)
        assert "Available:" in str(exc_info.value)

    def test_error_message_lists_available(self):
        """Error message should list available presets."""
        try:
            get_preset("bad_name")
        except KeyError as e:
            error_msg = str(e)
            for preset_name in PRESETS:
                assert preset_name in error_msg
