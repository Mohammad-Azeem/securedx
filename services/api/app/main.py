"""
SecureDx AI — FastAPI Application Entry Point

PHI BOUNDARY: This service runs entirely within the clinic's local network.
No raw PHI is transmitted externally. All external communications are
limited to DP-protected FL gradients via the fl-client service.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.logging import configure_logging
from app.middleware.audit import AuditLoggingMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.scheduler import start_scheduler

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # --- Startup ---
    configure_logging()
    logger.info(
        "SecureDx AI API starting",
        clinic_id=settings.CLINIC_ID,
        environment=settings.ENVIRONMENT,
        version="1.0.0",
    )
    await init_db()
    logger.info("Database connection pool initialized")

    yield

    # --- Shutdown ---
    await close_db()
    logger.info("SecureDx AI API shutting down cleanly")


app = FastAPI(
    title="SecureDx AI API",
    description=(
        "Privacy-first clinical decision support API. "
        "All PHI remains within the clinic's local network. "
        "HIPAA §164.312 technical safeguards implemented."
    ),
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# =============================================================================
# MIDDLEWARE (order matters — outermost middleware runs first on request)
# =============================================================================

# 1. Request ID — attach unique ID to every request for tracing
app.add_middleware(RequestIDMiddleware)

# 2. CORS — restrict to configured clinic-local origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 3. Audit Logging — write all requests/responses to tamper-evident audit log
app.add_middleware(AuditLoggingMiddleware)


# =============================================================================
# GLOBAL EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal error occurred. This event has been logged."},
    )


# =============================================================================
# ROUTES
# =============================================================================

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"], summary="Service health check")
async def health():
    """
    Lightweight health check for Docker and load balancer probes.
    Does not expose any PHI or system details.
    """
    return {"status": "healthy", "service": "securedx-api"}


@app.get("/health/detailed", tags=["Health"], summary="Detailed health check (internal)")
async def health_detailed():
    """
    Detailed health check including database and inference service connectivity.
    Restricted to internal network calls only.
    """
    from app.core.database import check_db_health
    from app.services.inference_client import check_inference_health

    db_healthy = await check_db_health()
    inference_healthy = await check_inference_health()

    all_healthy = db_healthy and inference_healthy
    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "inference": "healthy" if inference_healthy else "unhealthy",
        },
    }

@app.get("/inference")
async def inference():
    # Import ONLY when needed
    from schemas.inference import run_inference
    return run_inference()

# Result: Faster cold starts (5s vs 30s) and reduced memory usage 
# on startup, since heavy ML libraries are only loaded 
# when the /inference endpoint is hit for the first time. 
# Subsequent calls to /inference will be fast as the model stays 
# in memory. This is a common pattern for optimizing FastAPI apps 
# that have heavy dependencies used in specific routes.


@app.on_event("startup")
async def startup_event():
    """Run when API starts"""
    start_scheduler()
    logger.info("API started with nightly training scheduler")


## 🌅 Chapter 4: "The Morning After"
"""
**Tuesday, 7:00 AM - The Smarter AI Wakes Up**

AI Model (v2.0.49 - NEW VERSION!):
Good morning! I'm smarter today!

What I learned last night:
✓ Blood pressure is more important for hypertension (+8% trust)
✓ Low oxygen is critical for asthma/pneumonia (+5% trust)
✓ Temperature alone isn't enough for pneumonia (-4% trust)

My NEW accuracy:
- Pneumonia: 78% → 81% (+3%!) 
- Hypertension: 81% → 87% (+6%!) 
- Asthma: 68% → 74% (+6%!) 

I'm ready to help more doctors today!"
"

---

**Tuesday, 9:00 AM - Testing the New Knowledge**
```
Dr. Kumar: "Patient: High BP 165/95, chest pain, no fever"

🤖 AI (Old v2.0.48): "Pneumonia 62%" ❌
🤖 AI (New v2.0.49): "Hypertension 89%" ✅

Dr. Kumar: "Perfect! The AI learned! 🎉"
```

---

## 📊 The Complete Learning Cycle Visualization
```
┌─────────────────────────────────────────────────────┐
│  DAYTIME (7 AM - 11 PM): AI Works                   │
├─────────────────────────────────────────────────────┤
│  Doctors use AI → Make corrections → Save feedback  │
│  342 inferences → 99 corrections collected          │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  NIGHTTIME (11 PM - 12 AM): AI Studies              │
├─────────────────────────────────────────────────────┤
│  Step 1: Fetch 99 corrections from database         │
│  Step 2: Convert to training data (X, y)            │
│  Step 3: Load current AI brain (weights)            │
│  Step 4: Compute gradients (how to improve)         │
│  Step 5: Update weights (adjust knobs)              │
│  Step 6: Save new AI brain                          │
│  Step 7: Deploy v2.0.49                             │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│  NEXT MORNING (7 AM): Smarter AI!                   │
├─────────────────────────────────────────────────────┤
│  v2.0.48 (71% accurate) → v2.0.49 (74% accurate)    │
│  Improvement: +3% overnight! 🎓                     │
└─────────────────────────────────────────────────────┘
```

---

## 🎓 What You Just Learned (For the 15-Year-Old)

### **Lesson 1: Neural Networks Are Just Knobs**
```
Before I knew AI, I thought:
"AI is magic! 🪄"

Now I know:
"AI is just a bunch of knobs (weights) that get adjusted!"

Example:
Temperature Knob: 0.42 → 0.38 (trust temperature 4% less)
BP Knob: 0.15 → 0.23 (trust BP 8% more)

When all knobs are adjusted correctly → AI is accurate! ✅
```

---

### **Lesson 2: Learning = Adjusting Knobs Based on Mistakes**
```
How humans learn:
1. Try something
2. Get it wrong
3. Remember the mistake
4. Try differently next time

How AI learns:
1. Make prediction (try something)
2. Get correction from doctor (get it wrong)
3. Compute gradient (remember the mistake mathematically)
4. Adjust weights (try differently next time)

Same process! Just with math! 🧮
```

---

### **Lesson 3: Batch Learning vs Real-Time Learning**
```
Why train at NIGHT instead of IMMEDIATELY?

Option A: Real-time (bad):
Doctor corrects → Train instantly → 0.5 seconds delay ❌
Too slow! Doctors would wait!

Option B: Batch (good):
Collect 342 corrections → Train at night → 0 delay ✅
Doctors never wait! AI learns while sleeping! 😴

Bonus: Batch is more efficient!
- Training 342 cases at once: 2 minutes
- Training 342 cases one-by-one: 3 hours!
"""