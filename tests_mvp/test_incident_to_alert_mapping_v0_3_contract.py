from __future__ import annotations

from tools.observability.incident_keys_v0_3 import ALLOWED_INCIDENT_KEYS_V0_3
from tools.observability.incident_to_alert_mapping_v0_3 import (
    INCIDENT_TO_ALERT_V0_3,
    map_incident_to_alert,
    validate_mapping_contract_v0_3,
)


def test_mapping_contract_valid():
    # SSOT validator should pass (no exception)
    validate_mapping_contract_v0_3()


def test_mapping_keys_are_allowed_incident_keys():
    assert set(INCIDENT_TO_ALERT_V0_3.keys()).issubset(ALLOWED_INCIDENT_KEYS_V0_3)


def test_mapping_values_have_required_fields():
    for incident_key, meta in INCIDENT_TO_ALERT_V0_3.items():
        assert isinstance(meta, dict)

        assert "alert_name" in meta
        assert isinstance(meta["alert_name"], str)
        assert meta["alert_name"].strip() != ""

        assert "runbook" in meta
        assert isinstance(meta["runbook"], str)
        assert meta["runbook"].strip() != ""


def test_mapping_alert_names_are_strings_and_non_empty():
    alert_names = {meta["alert_name"] for meta in INCIDENT_TO_ALERT_V0_3.values()}
    assert all(isinstance(x, str) and x.strip() for x in alert_names)


def test_map_incident_to_alert_returns_dict_for_known_key():
    any_key = next(iter(INCIDENT_TO_ALERT_V0_3.keys()))
    meta = map_incident_to_alert(any_key)
    assert isinstance(meta, dict)
    assert meta["alert_name"] == INCIDENT_TO_ALERT_V0_3[any_key]["alert_name"]
    assert meta["runbook"] == INCIDENT_TO_ALERT_V0_3[any_key]["runbook"]