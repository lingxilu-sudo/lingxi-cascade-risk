"""Tests for YAML configuration validation."""

from unittest.mock import patch

import pytest

from cascade_risk import config as cfg


def test_unknown_section_raises():
    """A misspelled section used to be dropped, silently reverting to defaults."""
    with patch.object(cfg, "_load_yaml",
                      return_value={"physic": {"altitude_km": 900.0}}):
        with pytest.raises(ValueError, match="Unknown config sections"):
            cfg.Config.from_yaml("typo.yaml")


def test_unknown_key_raises():
    """A misspelled parameter must not fall back to the dataclass default."""
    with patch.object(cfg, "_load_yaml",
                      return_value={"physics": {"shell_thicknes_km": 300.0}}):
        with pytest.raises(ValueError, match="Unknown config keys"):
            cfg.Config.from_yaml("typo.yaml")


def test_baseline_loads():
    config = cfg.Config.from_yaml("baseline.yaml")
    assert config.physics.n_debris_large == 36500
    assert config.economics.n_policies == 500


def test_missing_default_falls_back_to_identical_defaults():
    """A pip-installed package has no configs/ directory; the console script
    must still run, and the fallback must reproduce baseline.yaml exactly."""
    with patch.object(cfg, "_load_yaml",
                      side_effect=FileNotFoundError("no configs dir")):
        with pytest.warns(RuntimeWarning, match="baseline.yaml not found"):
            fallback = cfg.Config.from_yaml()
    assert fallback == cfg.Config()
    assert fallback == cfg.Config.from_yaml("baseline.yaml")


def test_missing_explicit_file_still_raises():
    with patch.object(cfg, "_load_yaml",
                      side_effect=FileNotFoundError("no such file")):
        with pytest.raises(FileNotFoundError):
            cfg.Config.from_yaml("calibration_missing.yaml")
