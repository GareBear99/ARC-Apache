"""ARC-Core integration contract for ARC-Apache v5.

This file is the contract template ARC-Core's FastAPI route layer adopts
(request/response models for registering a v5 manifest and receipt).
It is NOT a live route in this repo: the route itself must be implemented
in ARC-Core, against ARC-Core's auth dependencies and database services,
and ARC-Core has no payload-registration routes yet — so there is nothing
to wire up from this side. Do not uncomment the skeleton below and expect
it to run here; it is a drop-in pattern for ARC-Core, kept in sync with
the v5 manifest fields in schemas/binary_manifest.schema.json.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class PayloadRegisterRequest(BaseModel):
    manifest_sha256: str = Field(min_length=64, max_length=64)
    envelope_sha256: str = Field(min_length=64, max_length=64)
    merkle_root: str = Field(min_length=64, max_length=64)
    content_class: str
    source: str
    policy_status: str = "quarantine"
    receipt_sha256: str | None = None
    signature_key_name: str | None = None


class PayloadRegisterResponse(BaseModel):
    ok: bool
    arc_event_type: str = "payload.registered"
    manifest_sha256: str
    receipt_sha256: str | None = None
    policy_status: str


# Example FastAPI route skeleton:
#
# @router.post("/payloads/register", response_model=PayloadRegisterResponse)
# def register_payload(req: PayloadRegisterRequest, user=Depends(require_operator)):
#     # 1. Validate hash syntax.
#     # 2. Verify receipt if provided.
#     # 3. Insert payload reference into ARC-Core DB.
#     # 4. Append ARC authority event.
#     # 5. Return accepted/quarantine status.
#     return PayloadRegisterResponse(
#         ok=True,
#         manifest_sha256=req.manifest_sha256,
#         receipt_sha256=req.receipt_sha256,
#         policy_status=req.policy_status,
#     )
