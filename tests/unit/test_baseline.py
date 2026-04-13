from __future__ import annotations

import pytest

from drift_engine.core.baseline import BaselineManager
from drift_engine.core.exceptions import BaselineValidationError


def test_signed_baseline_verifies(
    baseline_manager: BaselineManager,
    expected_resources: dict[str, dict[str, object]],
) -> None:
    baseline = baseline_manager.create(name="prod", resources=expected_resources)

    baseline_manager.verify(baseline)

    assert baseline.signature
    assert baseline.checksum


def test_tampered_baseline_fails_verification(
    baseline_manager: BaselineManager,
    expected_resources: dict[str, dict[str, object]],
) -> None:
    baseline = baseline_manager.create(name="prod", resources=expected_resources)
    baseline.resources["local::_::_::package::openssl"]["version"] = "9.9.9"

    with pytest.raises(BaselineValidationError):
        baseline_manager.verify(baseline)
