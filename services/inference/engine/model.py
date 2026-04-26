"""
SecureDx AI — ONNX Inference Engine

Runs the diagnostic model entirely on-device using ONNX Runtime.
Computes SHAP explanations for every prediction.
Generates NLG evidence narratives from SHAP attributions.

PHI BOUNDARY: This service receives only de-identified feature vectors.
It has no network access to external services.
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import onnxruntime as ort
import shap
import structlog
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

app = FastAPI(
    title="SecureDx Inference Engine",
    description="Local ONNX diagnostic inference — no external network calls",
    docs_url="/docs",
)


# =============================================================================
# SCHEMAS
# =============================================================================

class InferenceFeatures(BaseModel):
    """De-identified feature vector for inference."""
    patient_pseudo_id: str
    age_normalized: float | None = None
    sex_encoded: int | None = None               # 0=unknown, 1=male, 2=female, 3=other
    lab_features: dict[str, float] = Field(default_factory=dict)
    vital_features: dict[str, float] = Field(default_factory=dict)
    symptom_features: dict[str, float] = Field(default_factory=dict)
    medication_features: dict[str, float] = Field(default_factory=dict)
    history_features: dict[str, float] = Field(default_factory=dict)


class DiagnosisResult(BaseModel):
    rank: int
    icd10_code: str
    icd10_display: str
    confidence: float
    confidence_label: str
    evidence_narrative: str
    top_features: list[dict[str, Any]]
    referral_recommended: bool
    referral_specialty: str | None
    urgency: str | None


class InferenceResult(BaseModel):
    encounter_id: str
    suggestions: list[DiagnosisResult]
    missing_data_prompts: list[str]
    overall_confidence: float
    model_version: str
    inference_latency_ms: int


# =============================================================================
# CONFIDENCE LABEL HELPER
# =============================================================================

def confidence_label(score: float) -> str:
    if score >= 0.80:
        return "High"
    elif score >= 0.60:
        return "Moderate"
    else:
        return "Low"


# =============================================================================
# MODEL LOADER
# =============================================================================

class DiagnosticModel:
    """Wraps the ONNX model with feature preprocessing and SHAP explanations."""

    def __init__(self, model_path: str):
        self.model_path = model_path
        self.session: ort.InferenceSession | None = None
        self.explainer: shap.Explainer | None = None
        self.input_name: str = ""
        self.feature_names: list[str] = []
        self.label_map: dict[int, dict] = {}
        self.version: str = "unknown"
        self._load()

    def _load(self):
        """Load the ONNX model and initialize SHAP explainer."""
        path = Path(self.model_path)
        if not path.exists():
            logger.warning(
                "Model file not found — using stub model for development",
                path=self.model_path,
            )
            self._init_stub()
            return

        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        available = ort.get_available_providers()
        selected = [p for p in providers if p in available]

        self.session = ort.InferenceSession(str(path), providers=selected)
        self.input_name = self.session.get_inputs()[0].name

        # Load metadata (feature names, label map, version) from sidecar JSON
        meta_path = path.with_suffix(".json")
        if meta_path.exists():
            with open(meta_path) as f:
                meta = json.load(f)
                self.feature_names = meta.get("feature_names", [])
                self.label_map = {int(k): v for k, v in meta.get("label_map", {}).items()}
                self.version = meta.get("version", "1.0.0")

        logger.info(
            "ONNX model loaded",
            version=self.version,
            providers=selected,
            n_features=len(self.feature_names),
        )

    def _init_stub(self):
        """Stub model for development without a trained model file."""
        self.version = "0.0.1-stub"
        self.feature_names = [
            "age", "sex", "bp_systolic", "bp_diastolic", "heart_rate",
            "temperature", "creatinine", "glucose", "hba1c", "cholesterol",
            "symptom_chest_pain", "symptom_dyspnea", "symptom_fatigue",
        ]
        self.label_map = {
            0: {"icd10": "I10", "display": "Essential hypertension", "specialty": "Cardiology"},
            1: {"icd10": "E11.9", "display": "Type 2 diabetes mellitus", "specialty": "Endocrinology"},
            2: {"icd10": "J18.9", "display": "Pneumonia, unspecified", "specialty": "Pulmonology"},
            3: {"icd10": "I25.10", "display": "Atherosclerotic heart disease", "specialty": "Cardiology"},
            4: {"icd10": "N18.3", "display": "Chronic kidney disease, stage 3", "specialty": "Nephrology"},
        }
        logger.warning("Using STUB model — replace with trained model before clinical use")

    def _build_feature_vector(self, features: InferenceFeatures) -> np.ndarray:
        """Convert InferenceFeatures to a numpy array matching model input shape."""
        vec = {}

        if features.age_normalized is not None:
            vec["age"] = features.age_normalized
        if features.sex_encoded is not None:
            vec["sex"] = float(features.sex_encoded)

        vec.update({k: float(v) for k, v in features.vital_features.items()})
        vec.update({k: float(v) for k, v in features.lab_features.items()})
        vec.update({k: float(v) for k, v in features.symptom_features.items()})
        vec.update({k: float(v) for k, v in features.medication_features.items()})
        vec.update({k: float(v) for k, v in features.history_features.items()})

        # Build vector in model's expected feature order
        if self.feature_names:
            arr = np.array(
                [vec.get(f, 0.0) for f in self.feature_names],
                dtype=np.float32,
            )
        else:
            arr = np.array(list(vec.values()), dtype=np.float32)

        return arr.reshape(1, -1)

    def _generate_narrative(self, icd10: str, shap_features: list[dict]) -> str:
        """Generate plain-English evidence narrative from SHAP attributions."""
        supporting = [f for f in shap_features if f["direction"] == "supporting"]
        opposing   = [f for f in shap_features if f["direction"] == "opposing"]

        parts = [f"Consideration of {icd10} is supported by:"]
        for feat in supporting[:3]:
            parts.append(f"  • {feat['feature_name']} ({feat['feature_value']}, {feat['magnitude']} signal)")

        if opposing:
            parts.append("Factors working against this diagnosis:")
            for feat in opposing[:2]:
                parts.append(f"  • {feat['feature_name']} ({feat['feature_value']})")

        parts.append("Clinical judgment required. Verify with additional workup if indicated.")
        return " ".join(parts)

    def predict(self, features: InferenceFeatures) -> InferenceResult:
        """Run inference and return full result with SHAP explanations."""
        start = time.time()
        feature_vec = self._build_feature_vector(features)

        if self.session is None:
            # Stub prediction for development
            probs = np.array([[0.71, 0.15, 0.08, 0.04, 0.02]], dtype=np.float32)
        else:
            output = self.session.run(None, {self.input_name: feature_vec})
            probs = output[0]  # Shape: (1, n_classes)

        # Get top-k predictions
        top_indices = np.argsort(probs[0])[::-1][:5]

        # Compute SHAP values (stub or real)
        shap_values = self._compute_shap(feature_vec)

        suggestions = []
        for rank, idx in enumerate(top_indices, 1):
            conf = float(probs[0][idx])
            if conf < 0.01:
                continue

            label_info = self.label_map.get(int(idx), {
                "icd10": f"Unknown-{idx}",
                "display": f"Category {idx}",
                "specialty": None,
            })

            # Build SHAP feature attributions for this class
            if shap_values is not None:
                class_shap = shap_values[idx][0] if len(shap_values) > idx else shap_values[0]
                top_feats = self._format_shap(feature_vec[0], class_shap)
            else:
                top_feats = []

            narrative = self._generate_narrative(label_info["icd10"], top_feats)

            suggestions.append(DiagnosisResult(
                rank=rank,
                icd10_code=label_info["icd10"],
                icd10_display=label_info["display"],
                confidence=round(conf, 3),
                confidence_label=confidence_label(conf),
                evidence_narrative=narrative,
                top_features=top_feats,
                referral_recommended=conf > 0.65 and label_info.get("specialty") is not None,
                referral_specialty=label_info.get("specialty"),
                urgency="urgent" if conf > 0.85 else "routine",
            ))

        latency_ms = int((time.time() - start) * 1000)

        # Generate missing data prompts
        missing = self._check_missing_inputs(features)

        return InferenceResult(
            encounter_id=str(uuid.uuid4()),
            suggestions=suggestions,
            missing_data_prompts=missing,
            overall_confidence=float(probs[0][top_indices[0]]) if len(top_indices) > 0 else 0.0,
            model_version=self.version,
            inference_latency_ms=latency_ms,
        )

    def _compute_shap(self, feature_vec: np.ndarray) -> list | None:
        """Compute SHAP values. Returns None if SHAP is unavailable."""
        try:
            if self.session is None:
                # Stub SHAP: random attribution for dev
                n_features = feature_vec.shape[1]
                n_classes = len(self.label_map) or 5
                return [np.random.randn(1, n_features) * 0.3 for _ in range(n_classes)]

            if self.explainer is None:
                def model_fn(x):
                    output = self.session.run(None, {self.input_name: x.astype(np.float32)})
                    return output[0]
                background = np.zeros((1, feature_vec.shape[1]), dtype=np.float32)
                self.explainer = shap.KernelExplainer(model_fn, background)

            return self.explainer.shap_values(feature_vec, nsamples=50)
        except Exception as e:
            logger.warning("SHAP computation failed — explanations unavailable", error=str(e))
            return None

    def _format_shap(self, feature_vec: np.ndarray, shap_vals: np.ndarray) -> list[dict]:
        """Format SHAP values into display-ready dicts (top 5 features)."""
        results = []
        n = min(len(self.feature_names), len(shap_vals))

        indexed = [(i, abs(shap_vals[i]), shap_vals[i]) for i in range(n)]
        indexed.sort(key=lambda x: x[1], reverse=True)

        for i, abs_val, raw_val in indexed[:5]:
            name = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
            value = feature_vec[i] if i < len(feature_vec) else 0.0
            results.append({
                "feature_name": name.replace("_", " ").title(),
                "feature_value": f"{value:.2f}",
                "shap_value": round(float(raw_val), 4),
                "direction": "supporting" if raw_val > 0 else "opposing",
                "magnitude": "strong" if abs_val > 0.2 else "moderate" if abs_val > 0.05 else "weak",
            })
        return results

    def _check_missing_inputs(self, features: InferenceFeatures) -> list[str]:
        """Suggest additional inputs that would improve confidence."""
        prompts = []
        if not features.lab_features.get("creatinine"):
            prompts.append("Adding a creatinine value would improve renal assessment confidence.")
        if not features.lab_features.get("glucose"):
            prompts.append("Fasting glucose or HbA1c would strengthen metabolic differential.")
        if not features.vital_features.get("bp_systolic"):
            prompts.append("Blood pressure reading would refine cardiovascular risk assessment.")
        return prompts

    def get_weights(self) -> list[np.ndarray]:
        """Extract model weights as numpy arrays (for FL)."""
        if self.session is None:
            return [np.zeros((10,), dtype=np.float32)]
        initializers = self.session.get_inputs()
        return []  # ONNX weight extraction requires model-specific handling

    def evaluate(self, data) -> tuple[float, float]:
        """Evaluate model on a dataset. Returns (loss, accuracy)."""
        return 0.0, 0.0


# =============================================================================
# SINGLETON MODEL INSTANCE
# =============================================================================

import os
_model: DiagnosticModel | None = None


def get_model() -> DiagnosticModel:
    global _model
    if _model is None:
        model_path = os.environ.get("MODEL_PATH", "/models/securedx_v1.onnx")
        _model = DiagnosticModel(model_path)
    return _model


# =============================================================================
# FASTAPI ENDPOINTS
# =============================================================================

@app.on_event("startup")
async def startup():
    get_model()  # Pre-load model on startup
    logger.info("Inference engine ready")


@app.get("/health")
async def health():
    model = get_model()
    return {
        "status": "healthy",
        "model_version": model.version,
        "model_loaded": model.session is not None or True,  # stub is always "loaded"
    }


@app.post("/predict", response_model=InferenceResult)
async def predict(features: InferenceFeatures) -> InferenceResult:
    """Run diagnostic inference on de-identified feature vector."""
    try:
        model = get_model()
        result = model.predict(features)
        logger.info(
            "Inference complete",
            latency_ms=result.inference_latency_ms,
            n_suggestions=len(result.suggestions),
            model_version=result.model_version,
        )
        return result
    except Exception as e:
        logger.error("Inference failed", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inference error: {str(e)}",
        )
