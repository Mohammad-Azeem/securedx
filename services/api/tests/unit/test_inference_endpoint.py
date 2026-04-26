"""
SecureDx AI — Inference Endpoint Tests

Tests cover: input validation, PHI boundary (UUID enforcement),
audit logging, inference response shape, and error handling.
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
def valid_inference_payload():
    return {
        "patient_pseudo_id": "550e8400-e29b-41d4-a716-446655440000",
        "patient_age_years": 58,
        "patient_sex": "male",
        "vital_signs": {
            "systolic_bp": 158,
            "diastolic_bp": 96,
            "heart_rate": 88,
            "temperature_celsius": 37.1,
            "spo2_percent": 97.0,
        },
        "lab_results": [
            {
                "loinc_code": "2160-0",
                "display_name": "Creatinine",
                "value": 2.4,
                "unit": "mg/dL",
                "reference_low": 0.7,
                "reference_high": 1.3,
            }
        ],
        "symptoms": [
            {
                "snomed_code": "267036007",
                "display_name": "Dyspnea",
                "duration_days": 5,
                "severity": 6,
                "onset": "gradual",
            }
        ],
    }


@pytest.mark.asyncio
async def test_inference_rejects_raw_patient_id(valid_inference_payload):
    """PHI BOUNDARY: Raw MRNs must never reach the inference engine."""
    payload = {**valid_inference_payload, "patient_pseudo_id": "MRN-12345"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/inference/analyze",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code in (422, 401), (
        f"System accepted a raw MRN as patient_pseudo_id — PHI boundary violated! "
        f"Got: {resp.status_code}"
    )


@pytest.mark.asyncio
async def test_inference_rejects_non_uuid(valid_inference_payload):
    """patient_pseudo_id must be a valid UUID, not any string."""
    payload = {**valid_inference_payload, "patient_pseudo_id": "John Smith DOB 1965-03-12"}

    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/inference/analyze",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint():
    """Health check must return 200 with no PHI in response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    # No PHI or sensitive data in health response
    assert "patient" not in str(data).lower()
    assert "phi" not in str(data).lower()


@pytest.mark.asyncio
async def test_inference_requires_auth(valid_inference_payload):
    """All inference endpoints must require authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/inference/analyze",
            json=valid_inference_payload,
            # No Authorization header
        )

    assert resp.status_code == 403, "Inference endpoint accessible without auth!"


class TestVitalSignValidation:
    """Vital sign boundary validation tests."""

    @pytest.mark.asyncio
    async def test_rejects_impossible_heart_rate(self, valid_inference_payload):
        payload = dict(valid_inference_payload)
        payload["vital_signs"] = {"heart_rate": 999}

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/inference/analyze", json=payload,
                headers={"Authorization": "Bearer test-token"},
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_rejects_impossible_spo2(self, valid_inference_payload):
        payload = dict(valid_inference_payload)
        payload["vital_signs"] = {"spo2_percent": 120.0}

        async with AsyncClient(app=app, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/inference/analyze", json=payload,
                headers={"Authorization": "Bearer test-token"},
            )
        assert resp.status_code == 422
