"""Operational falsification challenge submission validator.

Per external review §10. The challenge is a real submission-and-review
pipeline, not just a document. This module implements:

  - JSON schema for challenge submissions
  - parallax5 challenge validate <submission.json>
  - parallax5 challenge status (registry of open + adjudicated submissions)
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


CHALLENGE_SUBMISSION_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://parallax5.org/schemas/challenge/v1.0",
    "title": "PARALLAX-5 Basis Counterexample Challenge Submission",
    "type": "object",
    "required": [
        "challenge_id", "submitted_at", "submitter", "transition",
        "trust_base_check", "five_obligation_check", "observation_set_used",
    ],
    "properties": {
        "challenge_id": {
            "type": "string",
            "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
        },
        "submitted_at": {"type": "string", "format": "date-time"},
        "submitter": {
            "type": "object",
            "required": ["did"],
            "properties": {
                "did": {"type": "string", "pattern": "^did:"},
                "name": {"type": "string"},
                "contact": {"type": "string"}
            }
        },
        "transition": {
            "type": "object",
            "required": ["protocol", "transition_description"],
            "properties": {
                "protocol": {"type": "string"},
                "pre_state_description": {"type": "string"},
                "transition_description": {"type": "string"},
                "post_state_description": {"type": "string"},
                "loss_description": {"type": "string"},
                "loss_usd": {"type": "number", "minimum": 0}
            }
        },
        "trust_base_check": {
            "type": "object",
            "required": ["OA1_key_integrity_held",
                         "OA2_signer_sovereignty_held",
                         "OA3_infrastructure_integrity_held"],
            "properties": {
                "OA1_key_integrity_held": {"type": "boolean"},
                "OA2_signer_sovereignty_held": {"type": "boolean"},
                "OA3_infrastructure_integrity_held": {"type": "boolean"},
                "evidence": {"type": "string"}
            }
        },
        "five_obligation_check": {
            "type": "object",
            "required": ["A1_value_conservation", "A2_authorization_closure",
                         "A3_signature_integrity", "A4_temporal_distinctness",
                         "A5_external_attestation"],
            "properties": {
                "A1_value_conservation": {"$ref": "#/$defs/obligation_check"},
                "A2_authorization_closure": {"$ref": "#/$defs/obligation_check"},
                "A3_signature_integrity": {"$ref": "#/$defs/obligation_check"},
                "A4_temporal_distinctness": {"$ref": "#/$defs/obligation_check"},
                "A5_external_attestation": {"$ref": "#/$defs/obligation_check"}
            }
        },
        "observation_set_used": {
            "enum": ["chain", "config", "intent", "infra"]
        },
        "reproducibility": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "tool_outputs": {"type": "array", "items": {"type": "string"}}
            }
        }
    },
    "$defs": {
        "obligation_check": {
            "type": "object",
            "required": ["satisfied"],
            "properties": {
                "satisfied": {"type": "boolean"},
                "evidence": {"type": "string"}
            }
        }
    }
}


def validate_submission(submission_path: Path) -> tuple[bool, list[str]]:
    """Validate a challenge submission against the schema.
    
    Returns (is_valid, errors).
    """
    errors = []
    try:
        with open(submission_path) as f:
            submission = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"JSON parse error: {e}"]
    
    try:
        import jsonschema
        jsonschema.validate(submission, CHALLENGE_SUBMISSION_SCHEMA)
    except ImportError:
        errors.append("jsonschema not installed; structural validation skipped")
    except jsonschema.ValidationError as e:
        return False, [str(e.message)]
    
    # ────────────────────────────────────────────────────────────
    # Semantic validation: a refutation requires that ALL FIVE
    # obligations are claimed satisfied AND the trust base holds AND
    # there is loss.
    # ────────────────────────────────────────────────────────────
    obligation_check = submission["five_obligation_check"]
    all_satisfied = all(
        obligation_check[k]["satisfied"]
        for k in ["A1_value_conservation", "A2_authorization_closure",
                  "A3_signature_integrity", "A4_temporal_distinctness",
                  "A5_external_attestation"]
    )
    if not all_satisfied:
        errors.append(
            "Not a refutation: at least one obligation is reported violated. "
            "A counterexample requires ALL FIVE obligations satisfied (basis "
            "violations are basis hits, not misses)."
        )
    
    trust_base = submission["trust_base_check"]
    all_held = all(
        trust_base[k] for k in
        ["OA1_key_integrity_held", "OA2_signer_sovereignty_held",
         "OA3_infrastructure_integrity_held"]
    )
    if not all_held:
        errors.append(
            "Not a refutation: at least one trust-base assumption fails. "
            "Off-chain key/signer/infrastructure failures are documented "
            "framework limitations under stated adequacy, not refutations."
        )
    
    transition = submission["transition"]
    if not transition.get("loss_description") and not transition.get("loss_usd"):
        errors.append(
            "Submission must demonstrate protected-value loss to qualify "
            "as a counterexample."
        )
    
    return len(errors) == 0, errors


def compute_submission_hash(submission_path: Path) -> str:
    """SHA-256 of the canonical submission for registry indexing."""
    with open(submission_path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


# ────────────────────────────────────────────────────────────────
# Challenge registry — append-only log
# ────────────────────────────────────────────────────────────────

class ChallengeRegistry:
    """Append-only log of challenge submissions + adjudications.
    
    Backed by a JSONL file (one event per line). Events:
      - submit  : new submission
      - triage  : passed initial completeness check
      - confirm : adjudicated as confirmed refutation (framework updates)
      - reject  : adjudicated as not-refuting (preserved as null result)
    """
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
    
    def append(self, event: dict) -> None:
        """Append an event to the log. Each event is immutable."""
        event["logged_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "a") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
    
    def submit(self, submission_path: Path, submission_hash: str) -> None:
        with open(submission_path) as f:
            submission = json.load(f)
        self.append({
            "event_type": "submit",
            "challenge_id": submission["challenge_id"],
            "submission_hash": submission_hash,
            "submitter": submission["submitter"].get("did", "unknown"),
        })
    
    def confirm(self, challenge_id: str, adjudicator: str, reasoning: str) -> None:
        """Mark as confirmed refutation."""
        self.append({
            "event_type": "confirm",
            "challenge_id": challenge_id,
            "adjudicator": adjudicator,
            "reasoning": reasoning,
        })
    
    def reject(self, challenge_id: str, adjudicator: str, reasoning: str) -> None:
        """Mark as considered, not refuting."""
        self.append({
            "event_type": "reject",
            "challenge_id": challenge_id,
            "adjudicator": adjudicator,
            "reasoning": reasoning,
        })
    
    def status(self) -> dict:
        """Aggregate status across all events."""
        events = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        
        submissions = {e["challenge_id"]: e for e in events if e["event_type"] == "submit"}
        confirmed = {e["challenge_id"]: e for e in events if e["event_type"] == "confirm"}
        rejected = {e["challenge_id"]: e for e in events if e["event_type"] == "reject"}
        pending = {cid: e for cid, e in submissions.items() 
                   if cid not in confirmed and cid not in rejected}
        
        return {
            "total_submissions": len(submissions),
            "confirmed_refutations": len(confirmed),
            "rejected_as_not_refuting": len(rejected),
            "pending": len(pending),
            "events": events,
        }
