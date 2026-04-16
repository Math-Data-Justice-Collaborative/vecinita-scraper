"""Regression tests for Modal deployment configuration.

These tests guard against the ModuleNotFoundError that occurs when the
vecinita_scraper package is not mounted into the Modal container image.
Reproduces: ModuleNotFoundError: No module named 'vecinita_scraper' at
/root/app.py line 5 inside the deployed container.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SRC_ROOT = Path(__file__).parent.parent.parent / "src"
_WORKERS_APP = _SRC_ROOT / "vecinita_scraper" / "app.py"
_API_APP = _SRC_ROOT / "vecinita_scraper" / "api" / "app.py"

_REQUIRED_CALL = 'add_local_python_source("vecinita_scraper")'


@pytest.mark.unit
def test_workers_app_image_mounts_local_package() -> None:
    """Workers app must call add_local_python_source so the package is
    importable inside the Modal container.

    Without this, Modal copies only the entry-point script to /root/app.py
    but the vecinita_scraper package is absent from the container's Python
    path, causing ModuleNotFoundError on every worker invocation.
    """
    content = _WORKERS_APP.read_text()
    assert _REQUIRED_CALL in content, (
        f"{_WORKERS_APP.relative_to(_SRC_ROOT.parent)} must contain "
        f"'{_REQUIRED_CALL}' in the image definition so the "
        "vecinita_scraper package is available inside the Modal container."
    )


@pytest.mark.unit
def test_api_app_image_mounts_local_package() -> None:
    """API app must call add_local_python_source so the package is
    importable inside the Modal container.

    Imports from ``vecinita_scraper.api.server`` (e.g. ``create_app``) run when
    Modal loads the script in the container, so the package must be present in
    the image.
    """
    content = _API_APP.read_text()
    assert _REQUIRED_CALL in content, (
        f"{_API_APP.relative_to(_SRC_ROOT.parent)} must contain "
        f"'{_REQUIRED_CALL}' in the image definition so the "
        "vecinita_scraper package is available inside the Modal container."
    )
