"""SecureDx AI — Inference Service HTTP Client"""
from types import SimpleNamespace

import httpx

from app.core.config import settings
from app.schemas.inference import DiagnosisSuggestion


class InferenceClient:
    async def predict(self, features):
        async with httpx.AsyncClient(timeout=settings.INFERENCE_TIMEOUT_SECONDS) as c:
            resp = await c.post(
                f"{settings.INFERENCE_SERVICE_URL}/predict",
                json=features.model_dump(exclude_none=True),
            )
            resp.raise_for_status()
            payload = resp.json()

        # Normalize suggestion payload from inference service into API schema.
        suggestions = [
            DiagnosisSuggestion(
                rank=s.get("rank", 1),
                icd10_code=s.get("icd10_code", "UNKNOWN"),
                icd10_display=s.get("icd10_display", "Unknown diagnosis"),
                confidence=s.get("confidence", 0.0),
                confidence_label=s.get("confidence_label", "Low"),
                evidence_narrative=s.get("evidence_narrative", ""),
                top_features=s.get("top_features", []),
                referral_recommended=s.get("referral_recommended", False),
                referral_specialty=s.get("referral_specialty"),
                urgency=s.get("urgency"),
                drug_interaction_alert=s.get("drug_interaction_alert"),
            )
            for s in payload.get("suggestions", [])
        ]

        return SimpleNamespace(
            encounter_id=payload.get("encounter_id"),
            suggestions=suggestions,
            missing_data_prompts=payload.get("missing_data_prompts", []),
            overall_confidence=payload.get("overall_confidence", 0.0),
            model_version=payload.get("model_version", "unknown"),
            inference_latency_ms=payload.get("inference_latency_ms", 0),
        )

async def check_inference_health() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{settings.INFERENCE_SERVICE_URL}/health")
            return r.status_code == 200
    except Exception:
        return False
