"""Fire tests for the tool-mapping registry (substrate v1.1.0+).

The registry under mappings/ holds one or more registered tool-mappings
conforming to schemas/mapping_protocol_v1.json. These tests verify:

  - every registered mapping validates against the protocol schema;
  - the substrate ships at least the reference aquaursa-v1 mapping;
  - load_mapping(aquaursa-v1) returns capabilities that match the
    legacy module-level constants (SLITHER_CAPABILITY, …), so the
    refactor introduces no drift.

If a new mapping is dropped into mappings/, these tests will catch
schema violations and obligation/depth-vocabulary divergence at PR
time.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MAPPINGS_DIR = ROOT / "mappings"
PROTOCOL_SCHEMA = ROOT / "schemas" / "mapping_protocol_v1.json"


def _all_mapping_files() -> list[Path]:
    return sorted(MAPPINGS_DIR.glob("*.json"))


def test_registry_is_non_empty() -> None:
    files = _all_mapping_files()
    assert files, "mappings/ contains no JSON files; substrate must ship aquaursa-v1"


def test_aquaursa_v1_is_present() -> None:
    assert (MAPPINGS_DIR / "aquaursa-v1.json").exists()


def test_every_mapping_validates_against_protocol_schema() -> None:
    """Hard CI requirement: every JSON in mappings/ must validate."""
    pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    schema = json.loads(PROTOCOL_SCHEMA.read_text())
    validator = Draft202012Validator(schema)
    for f in _all_mapping_files():
        if f.name == "README.md":
            continue
        doc = json.loads(f.read_text())
        errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
        assert not errors, f"{f.name} fails schema: {[e.message for e in errors[:3]]}"


def test_aquaursa_v1_namespace_matches_filename() -> None:
    doc = json.loads((MAPPINGS_DIR / "aquaursa-v1.json").read_text())
    assert doc["namespace"] == "tool-mapping/aquaursa-v1"
    # Major component of version must match -v{major} in the namespace
    major = doc["version"].split(".")[0]
    assert doc["namespace"].endswith(f"-v{major}"), (
        f"namespace {doc['namespace']!r} disagrees with version {doc['version']!r}"
    )


def test_aquaursa_v1_carries_five_obligations() -> None:
    doc = json.loads((MAPPINGS_DIR / "aquaursa-v1.json").read_text())
    assert set(doc["obligation_legend"].keys()) == {"A1", "A2", "A3", "A4", "A5"}


def test_aquaursa_v1_carries_six_depth_levels() -> None:
    doc = json.loads((MAPPINGS_DIR / "aquaursa-v1.json").read_text())
    assert set(doc["depth_legend"].keys()) == {"0", "1", "2", "3", "4", "5"}


def test_load_mapping_matches_legacy_constants() -> None:
    """The dynamic load of aquaursa-v1 must agree with the legacy
    SLITHER_CAPABILITY, MYTHRIL_CAPABILITY, HALMOS_CAPABILITY,
    AXIOMSOL_CAPABILITY constants exactly.

    This guards against drift between the JSON registry and the Python
    constants; the constants will eventually be deprecated, but until
    then they MUST agree.
    """
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parallax5_coordinator.capability import (
        load_mapping,
        Obligation,
        SLITHER_CAPABILITY,
        MYTHRIL_CAPABILITY,
        HALMOS_CAPABILITY,
        AXIOMSOL_CAPABILITY,
    )

    caps = load_mapping("tool-mapping/aquaursa-v1")
    pairs = [
        ("slither",       SLITHER_CAPABILITY),
        ("mythril",       MYTHRIL_CAPABILITY),
        ("halmos",        HALMOS_CAPABILITY),
        ("obligationsol", AXIOMSOL_CAPABILITY),
    ]
    for tool_id, legacy in pairs:
        assert tool_id in caps, f"loaded mapping lacks {tool_id}"
        loaded = caps[tool_id]
        for ob in Obligation:
            assert loaded.depth(ob) == legacy.depth(ob), (
                f"{tool_id} {ob.name}: legacy={legacy.depth(ob)} "
                f"loaded={loaded.depth(ob)} — drift in registry vs constants"
            )


def test_list_registered_mappings_includes_aquaursa_v1() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parallax5_coordinator.capability import list_registered_mappings
    assert "tool-mapping/aquaursa-v1" in list_registered_mappings()


def test_load_mapping_rejects_invalid_namespace() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parallax5_coordinator.capability import load_mapping_document
    with pytest.raises(ValueError):
        load_mapping_document("not-a-namespace-pattern")
    with pytest.raises(FileNotFoundError):
        load_mapping_document("tool-mapping/nonexistent-v9")


def test_cli_resolve_mapping_field_with_override() -> None:
    """The certify subcommand's --mapping override is honored."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parallax5_coordinator.cli import _resolve_mapping_field
    out = _resolve_mapping_field({}, "tool-mapping/aquaursa-v1")
    assert out["namespace"] == "tool-mapping/aquaursa-v1"
    assert out["version"] == "1.0.0"
    assert "doi" in out


def test_cli_resolve_mapping_field_default() -> None:
    """No spec, no override → aquaursa-v1 default."""
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parallax5_coordinator.cli import _resolve_mapping_field
    out = _resolve_mapping_field({}, None)
    assert out["namespace"] == "tool-mapping/aquaursa-v1"
