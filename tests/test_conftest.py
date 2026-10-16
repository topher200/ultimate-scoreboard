"""Tests for the pytest setup in conftest.py."""

from fakes import FakeGroup


def test_display_manager_uses_fake_displayio(display_manager, fake_matrix_portal):
    assert isinstance(fake_matrix_portal.display.root_group, FakeGroup)
