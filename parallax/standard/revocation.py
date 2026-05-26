"""PARALLAX-5 Revocation Registry — append-only log of certificate state.

Implements the lifecycle from GOVERNANCE.md:
  issue → verify → publish → active
                     │
              ┌──────┼──────┬──────────┐
              ▼      ▼      ▼          ▼
        revalidate  supersede  expire  revoke

Each event is one line of JSONL, content-addressed by the certificate's
hash. Once written, events are immutable; the only way to "undo" a
revocation is to issue a new certificate that supersedes the prior.

This is intentionally minimal — production deployments would back the
log with cryptographic accumulators (e.g., Merkle trees committed
on-chain) for tamper-evidence.
"""

from __future__ import annotations
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class RevocationRegistry:
    """Append-only log of certificate lifecycle events."""
    
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()
    
    def _cert_hash(self, cert_path: Path) -> str:
        with open(cert_path, "rb") as f:
            return "sha256:" + hashlib.sha256(f.read()).hexdigest()
    
    def _append(self, event: dict) -> None:
        event["logged_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.path, "a") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")
    
    def issue(self, cert_path: Path, issuer_did: str) -> str:
        cert_hash = self._cert_hash(cert_path)
        with open(cert_path) as f:
            cert = json.load(f)
        cert_id = cert["certificate_id"]
        self._append({
            "event": "issue",
            "certificate_id": cert_id,
            "certificate_hash": cert_hash,
            "issuer_did": issuer_did,
            "compliance_level": cert.get("compliance_level"),
            "protocol_id": cert.get("protocol_id"),
        })
        return cert_hash
    
    def revoke(self, certificate_id: str, reason: str, revoker_did: str) -> None:
        self._append({
            "event": "revoke",
            "certificate_id": certificate_id,
            "reason": reason,
            "revoker_did": revoker_did,
        })
    
    def supersede(self, old_id: str, new_cert_path: Path, issuer_did: str) -> str:
        new_hash = self._cert_hash(new_cert_path)
        with open(new_cert_path) as f:
            new_cert = json.load(f)
        self._append({
            "event": "supersede",
            "superseded_id": old_id,
            "new_certificate_id": new_cert["certificate_id"],
            "new_certificate_hash": new_hash,
            "issuer_did": issuer_did,
        })
        return new_hash
    
    def revalidate(self, cert_id: str, new_cert_path: Path) -> None:
        """Mark a certificate as revalidated — same compliance level, new evidence."""
        new_hash = self._cert_hash(new_cert_path)
        self._append({
            "event": "revalidate",
            "certificate_id": cert_id,
            "new_evidence_hash": new_hash,
        })
    
    def is_revoked(self, cert_id: str) -> bool:
        """Check if a certificate has been revoked."""
        for evt in self._read_events():
            if evt["event"] == "revoke" and evt["certificate_id"] == cert_id:
                return True
        return False
    
    def is_superseded(self, cert_id: str) -> Optional[str]:
        """If superseded, return the new certificate_id; else None."""
        for evt in self._read_events():
            if evt["event"] == "supersede" and evt["superseded_id"] == cert_id:
                return evt["new_certificate_id"]
        return None
    
    def status(self, cert_id: str) -> dict:
        """Get current status of a certificate."""
        events = [e for e in self._read_events() if 
                  e.get("certificate_id") == cert_id or 
                  e.get("superseded_id") == cert_id or
                  e.get("new_certificate_id") == cert_id]
        if not events:
            return {"certificate_id": cert_id, "status": "unknown"}
        
        if self.is_revoked(cert_id):
            return {"certificate_id": cert_id, "status": "revoked", "events": events}
        new_id = self.is_superseded(cert_id)
        if new_id:
            return {"certificate_id": cert_id, "status": "superseded",
                    "superseded_by": new_id, "events": events}
        return {"certificate_id": cert_id, "status": "active", "events": events}
    
    def _read_events(self) -> list[dict]:
        if not self.path.exists():
            return []
        events = []
        with open(self.path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events


# Tiny CLI test
if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        # Sample cert
        cert_path = td / "cert.json"
        cert_path.write_text(json.dumps({
            "certificate_id": "p5cert-test-001",
            "compliance_level": "P2",
            "protocol_id": "test-vault",
        }))
        
        reg = RevocationRegistry(td / "registry.jsonl")
        h = reg.issue(cert_path, "did:web:test.org")
        print(f"Issued: {h[:20]}...")
        print(f"Status: {reg.status('p5cert-test-001')['status']}")
        
        reg.revoke("p5cert-test-001", "Found A4 counterexample", "did:web:test.org")
        print(f"After revoke: {reg.status('p5cert-test-001')['status']}")
