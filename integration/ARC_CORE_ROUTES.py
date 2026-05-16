"""ARC-Core integration stub for ARC-Apache v5.

Drop this pattern into ARC-Core's FastAPI route layer after adapting imports,
auth dependencies, and database services.
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
