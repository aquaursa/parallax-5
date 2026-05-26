"""Reference validator (delegates to the substrate implementation)."""
from __future__ import annotations
from pathlib import Path
import sys

# Make the substrate importable
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from parallax.standard.validator import validate_certificate as _validate
except ImportError:
    # Pure standalone: re-implement minimum schema validation
    import json
    def _validate(cert_path: Path, schema_path: Path, strict: bool = False) -> int:
        try:
            import jsonschema
            cert = json.loads(Path(cert_path).read_text())
            schema = json.loads(Path(schema_path).read_text())
            jsonschema.validate(cert, schema)
            print(f"  ✓ Certificate {cert_path.name} validates against schema")
            print(f"  Verdict: VALID")
            return 0
        except Exception as e:
            print(f"  ✗ {e}")
            print(f"  Verdict: INVALID")
            return 1


def validate_certificate(cert: Path, schema: Path, strict: bool = False) -> int:
    return _validate(cert, schema, strict)
