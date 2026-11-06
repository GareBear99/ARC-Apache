"""ARC-Core route contract models (integration/ARC_CORE_ROUTES.py).

The file is a template ARC-Core adopts, not a live route in this repo,
but its request/response models are the wire contract — so they are
tested here. Requires pydantic (test extra only; the core CLI stays
dependency-free).
"""
import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("pydantic")
from pydantic import ValidationError  # noqa: E402

ROUTES_PATH = Path(__file__).resolve().parents[1] / "integration" / "ARC_CORE_ROUTES.py"


def load_routes_module():
    spec = importlib.util.spec_from_file_location("arc_core_routes", ROUTES_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_payload_register_request_validates():
    routes = load_routes_module()
    req = routes.PayloadRegisterRequest(
        manifest_sha256="a" * 64,
        envelope_sha256="b" * 64,
        merkle_root="c" * 64,
        content_class="generic_blob",
        source="test",
    )
    assert req.policy_status == "quarantine"
    assert req.receipt_sha256 is None
    assert req.signature_key_name is None


def test_payload_register_request_rejects_short_hash():
    routes = load_routes_module()
    with pytest.raises(ValidationError):
        routes.PayloadRegisterRequest(
            manifest_sha256="abc",
            envelope_sha256="b" * 64,
            merkle_root="c" * 64,
            content_class="generic_blob",
            source="test",
        )


def test_payload_register_response_round_trip():
    routes = load_routes_module()
    resp = routes.PayloadRegisterResponse(
        ok=True,
        manifest_sha256="a" * 64,
        receipt_sha256="d" * 64,
        policy_status="accepted",
    )
    assert resp.arc_event_type == "payload.registered"
    assert resp.model_dump()["manifest_sha256"] == "a" * 64
