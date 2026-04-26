# SecureDx AI — Sprint 6: Production Deployment & Real Model

## 🎉 What You Just Built

**Production ML deployment pipeline** with automated training, versioning, and zero-downtime updates:

✅ **Complete Training Pipeline** - PyTorch → ONNX export  
✅ **Automated Deployment** - Blue-green with health checks  
✅ **Version Management** - Rollback capability  
✅ **Model Monitoring** - Performance tracking  
✅ **Zero-Downtime Updates** - Atomic model swaps  

---

## 📖 The Story Continues: One Month Later

### **Meet Rajesh - ML Engineer (New Character!)**

**Monday, 8:00 AM - Model Performance Review**

Rajesh, the ML engineer, arrives at SecureDx headquarters and checks last month's metrics:

```
╔══════════════════════════════════════════════════════╗
║  MODEL PERFORMANCE DASHBOARD                         ║
║  Period: February 2026                               ║
╠══════════════════════════════════════════════════════╣
║  📊 ACCURACY METRICS                                 ║
║  ├─ Overall Accuracy: 78.3% ✓                        ║
║  ├─ Pneumonia Recall: 92.1% ✓ (critical!)           ║
║  ├─ Hypertension Precision: 81.4% ⚠️ (improving)     ║
║  └─ Asthma Detection: 68.2% 🔴 (needs work)          ║
╠══════════════════════════════════════════════════════╣
║  🎯 PHYSICIAN FEEDBACK                               ║
║  ├─ Accept Rate: 71% (target: 75%)                   ║
║  ├─ Modify Rate: 21% (acceptable)                    ║
║  ├─ Reject Rate: 6% (good!)                          ║
║  └─ Flag Rate: 2% (23 cases) ⚠️                      ║
╠══════════════════════════════════════════════════════╣
║  🔋 PRIVACY STATUS                                   ║
║  ├─ Epsilon Spent: 9.8 / 10.0                        ║
║  ├─ Status: 🔴 CRITICAL (98% depleted!)              ║
║  ├─ Remaining Rounds: 0                              ║
║  └─ Action: NEW MODEL TRAINING REQUIRED              ║
╚══════════════════════════════════════════════════════╝
```

**Rajesh's reaction:** "Privacy budget is almost gone! We need to train a fresh model from scratch."

---

**Monday, 9:00 AM - Starting Fresh Model Training**

Rajesh collects 30 days of physician-confirmed feedback:

```python
# Rajesh runs this command:
python train_model.py --data-period "2026-02-01:2026-02-28"

═══════════════════════════════════════════════════════
SECUREDX AI - MODEL TRAINING PIPELINE
═══════════════════════════════════════════════════════

[09:00:15] INFO: Loading training data...
[09:00:20] INFO: Retrieved 15,847 feedback events
[09:00:21] INFO: Filtering physician-confirmed cases...
[09:00:22] INFO: After filtering: 12,334 cases
           ├─ Accept: 8,757 (71%)
           ├─ Modify: 2,589 (21%)
           └─ Reject: 988 (8%)
           
[09:00:25] INFO: Class distribution:
           ├─ Pneumonia (J18.9): 4,231 cases
           ├─ URI (J06.9): 3,456 cases
           ├─ Bronchitis (J20.9): 2,123 cases
           ├─ Hypertension (I10): 1,890 cases
           └─ Asthma (J45.909): 634 cases ⚠️ (imbalanced!)
           
[09:00:30] INFO: Applying class balancing...
[09:00:35] INFO: Final dataset: 3,170 samples per class

[09:00:40] INFO: Data split:
           ├─ Train: 11,095 (70%)
           ├─ Val: 2,377 (15%)
           └─ Test: 2,378 (15%)

═══════════════════════════════════════════════════════
TRAINING STARTED
═══════════════════════════════════════════════════════

[09:01:00] Epoch 1/100:
           Train Loss=1.5420, Train Acc=0.4123, Val Acc=0.4256

[09:02:30] Epoch 10/100:
           Train Loss=0.8234, Train Acc=0.6891, Val Acc=0.6923
           
[09:15:00] Epoch 50/100:
           Train Loss=0.3214, Train Acc=0.8456, Val Acc=0.8123
           ✓ New best model (val_acc=0.8123)

[09:30:00] Epoch 100/100:
           Train Loss=0.1234, Train Acc=0.9234, Val Acc=0.8567
           ✓ New best model (val_acc=0.8567)

═══════════════════════════════════════════════════════
TRAINING COMPLETE
═══════════════════════════════════════════════════════

[09:30:15] Loading best model (epoch 100)...
[09:30:20] Running test set evaluation...

TEST RESULTS:
├─ Overall Accuracy: 85.67% ✅ (up from 78.3%!)
├─ Precision: 0.8634
├─ Recall: 0.8567
└─ F1-Score: 0.8600

Per-Class Performance:
├─ Pneumonia:     Prec=0.92, Rec=0.95, F1=0.93 ✅
├─ URI:           Prec=0.85, Rec=0.87, F1=0.86 ✅
├─ Bronchitis:    Prec=0.81, Rec=0.79, F1=0.80 ✅
├─ Hypertension:  Prec=0.89, Rec=0.86, F1=0.87 ✅
└─ Asthma:        Prec=0.84, Rec=0.82, F1=0.83 ✅ (much better!)

[09:30:30] Exporting to ONNX...
[09:30:45] ✓ Model exported: /models/securedx_v2.0.0_20260309.onnx
[09:30:50] ✓ ONNX verification passed

═══════════════════════════════════════════════════════
✅ TRAINING PIPELINE COMPLETE
═══════════════════════════════════════════════════════

NEW MODEL:
├─ Version: v2.0.0
├─ Accuracy: 85.67% (+7.37% improvement!)
├─ File: /models/securedx_v2.0.0_20260309.onnx
├─ Size: 2.4 MB
└─ Ready for deployment

PRIVACY BUDGET:
🔋 RESET TO 100% (new model = new privacy regime)
```

---

**Monday, 10:00 AM - Staging the New Model**

Rajesh stages the model for deployment:

```python
from deploy_model import ModelDeployer

deployer = ModelDeployer()

# Stage new model
deployer.stage_model(
    model_path='/models/securedx_v2.0.0_20260309.onnx',
    version='v2.0.0',
    description='Fresh training on 30 days feedback. +7.4% accuracy. Privacy reset.'
)

═══════════════════════════════════════════════════════
MODEL STAGING
═══════════════════════════════════════════════════════

[10:00:05] Validating ONNX file...
[10:00:10] ✓ ONNX validation passed
[10:00:15] Computing checksum...
[10:00:20] Checksum: a3f8b9c2d4e5f6a7b8c9d0e1f2a3b4c5...
[10:00:25] Copying to staging directory...
[10:00:30] Writing metadata...

STAGED MODEL:
├─ Version: v2.0.0
├─ Checksum: a3f8b9c2...
├─ Size: 2.4 MB
├─ Location: /models/staging/model.onnx
└─ Status: Ready for deployment

✅ Model staged successfully
```

---

**Monday, 10:30 AM - Canary Deployment (Testing on 10% of Clinics)**

Before deploying to all 100 clinics, Rajesh does a canary release:

```
Canary Deployment Strategy:
1. Deploy to 10 clinics (10%)
2. Monitor for 24 hours
3. If metrics look good → full rollout
4. If problems → immediate rollback
```

Rajesh deploys to the pilot clinics:

```python
# Deploy to canary group
deployer.deploy_staged_model(run_health_check=True)

═══════════════════════════════════════════════════════
MODEL DEPLOYMENT - CANARY PHASE
═══════════════════════════════════════════════════════

[10:30:05] Loading staged model...
[10:30:10] Running health checks...

HEALTH CHECK RESULTS:
├─ ONNX Load Test: ✅ PASS
├─ Inference Test: ✅ PASS (5ms avg latency)
├─ Output Shape: ✅ PASS (1, 5)
├─ NaN/Inf Check: ✅ PASS
└─ Memory Usage: ✅ PASS (120 MB)

[10:30:20] Archiving active model (v1.0.48)...
[10:30:25] ✓ Archived to /models/versions/v1.0.48/
[10:30:30] Deploying new model...
[10:30:35] ✓ Model copied to active directory
[10:30:40] Updating metadata...
[10:30:45] Verifying deployment...

DEPLOYMENT VERIFICATION:
├─ Active version: v2.0.0 ✅
├─ Checksum match: ✅
├─ Accessible by API: ✅
└─ Rollback available: ✅ (v1.0.48)

═══════════════════════════════════════════════════════
✅ CANARY DEPLOYMENT COMPLETE
═══════════════════════════════════════════════════════

DEPLOYMENT SUMMARY:
├─ Deployed to: 10 clinics (canary group)
├─ Version: v1.0.48 → v2.0.0
├─ Rollback ready: v1.0.48
├─ Monitoring period: 24 hours
└─ Full rollout: Tomorrow 10:30 AM (if successful)

NEXT STEPS:
1. Monitor canary metrics (acceptance rate, latency, errors)
2. Review physician feedback
3. Check for any flagged inferences
4. Decide: Full rollout vs Rollback
```

---

**Tuesday, 10:00 AM - Canary Results Review**

After 24 hours, Rajesh reviews the canary metrics:

```
╔══════════════════════════════════════════════════════╗
║  CANARY DEPLOYMENT RESULTS (24 HOURS)                ║
║  Model v2.0.0 on 10 clinics                          ║
╠══════════════════════════════════════════════════════╣
║  📊 PERFORMANCE METRICS                              ║
║  ├─ Inferences: 1,247                                ║
║  ├─ Avg Latency: 548ms (baseline: 580ms) ✅          ║
║  ├─ Errors: 0 ✅                                      ║
║  └─ Uptime: 100% ✅                                   ║
╠══════════════════════════════════════════════════════╣
║  🎯 ACCURACY METRICS                                 ║
║  ├─ Accept Rate: 82% ✅ (was 71%)                    ║
║  ├─ Modify Rate: 14% ✅ (was 21%)                    ║
║  ├─ Reject Rate: 3% ✅ (was 6%)                      ║
║  └─ Flag Rate: 1% ✅ (was 2%)                        ║
╠══════════════════════════════════════════════════════╣
║  💬 PHYSICIAN FEEDBACK                               ║
║  ├─ "Much better!" - Dr. Chen                        ║
║  ├─ "Finally catching hypertension!" - Dr. Kumar     ║
║  ├─ "Asthma detection improved!" - Dr. Patel         ║
║  └─ Net Promoter Score: +42 (was +28)                ║
╠══════════════════════════════════════════════════════╣
║  🚨 ISSUES                                           ║
║  └─ None reported ✅                                  ║
╚══════════════════════════════════════════════════════╝

RECOMMENDATION: ✅ PROCEED WITH FULL ROLLOUT
```

---

**Tuesday, 10:30 AM - Full Rollout to All 100 Clinics**

```python
# Deploy to all clinics
deployer.rollout_to_all_clinics(version='v2.0.0')

═══════════════════════════════════════════════════════
FULL PRODUCTION ROLLOUT
═══════════════════════════════════════════════════════

[10:30:05] Deploying to 90 remaining clinics...

Progress:
[10:30:10] ████░░░░░░░░░░░░░░░░ 10/90 (11%)
[10:31:00] ████████░░░░░░░░░░░░ 30/90 (33%)
[10:32:00] ████████████░░░░░░░░ 50/90 (56%)
[10:33:00] ████████████████░░░░ 70/90 (78%)
[10:34:00] ████████████████████ 90/90 (100%)

[10:34:05] ✅ Deployment complete across all clinics

ROLLOUT SUMMARY:
├─ Total clinics: 100
├─ Successful: 100 (100%)
├─ Failed: 0
├─ Version: v2.0.0
├─ Privacy budget: RESET to 0% (fresh start)
└─ Ready for production use

GLOBAL STATUS:
🟢 All systems operational
```

---

**That Evening - Dr. Chen Notices the Difference**

Dr. Chen logs in for her evening shift:

```
[Notification]
🎉 AI Model Updated to v2.0.0!

What's new:
✅ +7% overall accuracy
✅ Better asthma detection
✅ Improved hypertension recognition
✅ Faster inference (548ms avg)

Privacy: Fresh start (100% budget available)
```

She diagnoses a patient similar to yesterday's case:

```
Patient: High BP, chest pain, no respiratory symptoms

OLD MODEL (v1.0.48): "Pneumonia - 62%" ❌
NEW MODEL (v2.0.0): "Hypertension - 89%" ✅

Dr. Chen: "Perfect! The AI learned from Mr. Kumar's case!"
Decision: ✓ ACCEPT
```

---

## 💼 For the Interviewer: Technical Deep-Dive

### **1. Training Pipeline Architecture**

```
┌─────────────────────────────────────────────────┐
│  DATA COLLECTION (Continuous)                   │
├─────────────────────────────────────────────────┤
│  ├─ Physician feedback stored in PostgreSQL    │
│  ├─ Only confirmed cases (accept/modify)       │
│  ├─ De-identified (pseudo_id, no PII)          │
│  └─ Filtered: Remove flags & rejects           │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  MONTHLY RETRAINING (Scheduled)                 │
├─────────────────────────────────────────────────┤
│  1. Extract 30 days of feedback                 │
│  2. Balance classes (oversample minority)       │
│  3. Split: 70% train, 15% val, 15% test         │
│  4. Train PyTorch model (100 epochs)            │
│  5. Export to ONNX                              │
│  6. Version: v{major}.{minor}.{patch}           │
│  7. Reset privacy budget (new regime)           │
└─────────────────┬───────────────────────────────┘
                  ▼
┌─────────────────────────────────────────────────┐
│  DEPLOYMENT PIPELINE                            │
├─────────────────────────────────────────────────┤
│  1. Stage: Copy to /models/staging/             │
│  2. Validate: ONNX load + health check          │
│  3. Canary: Deploy to 10% of clinics            │
│  4. Monitor: 24 hours metrics                   │
│  5. Decision: Rollout or Rollback               │
│  6. Rollout: Deploy to remaining 90%            │
│  7. Archive: Save old model for rollback        │
└─────────────────────────────────────────────────┘
```

---

### **2. Blue-Green Deployment Strategy**

**Why blue-green instead of rolling update?**

| Strategy | Pros | Cons | Our Choice |
|----------|------|------|------------|
| **Rolling** | Gradual, low risk | Slow, mixed versions | ❌ |
| **Blue-Green** | Instant rollback, atomic | Requires 2x resources | ✅ **Winner** |
| **Canary** | Safe testing | Complex orchestration | ✅ (Combined!) |

**Our hybrid approach:**
```
Phase 1 (Canary):
├─ Blue (v1.0.48): 90 clinics
└─ Green (v2.0.0): 10 clinics (canary)

Phase 2 (Full Rollout):
├─ Blue (archived): v1.0.48
└─ Green (active): 100 clinics on v2.0.0
```

**Atomic swap mechanism:**
```python
# Linux filesystem guarantees atomic renames
os.rename('/models/staging/model.onnx', '/models/active/model.onnx')

# If rename fails mid-operation:
# - Either: old model still active (safe!)
# - Or: new model fully active (safe!)
# - Never: half-swapped broken state ✅
```

---

### **3. Privacy Budget Reset Decision**

**Q: Why reset privacy budget with new model?**

A: **Mathematical justification**:

```
Old regime (model v1.0.x):
├─ Dataset D_old
├─ ε_total = 9.8 (near limit)
├─ Guarantees apply to D_old only

New regime (model v2.0.x):
├─ Dataset D_new (freshly collected)
├─ ε_total = 0 (reset!)
├─ Different data = different privacy regime

Why this works:
D_old ∩ D_new = ∅ (non-overlapping time periods)
Therefore: ε(D_old) + ε(D_new) does NOT compose
```

**Trade-off:**
- ✅ Pro: Can continue learning indefinitely
- ❌ Con: Must retrain from scratch (expensive)
- ⚖️ Balance: Retrain monthly (sufficient for medical AI)

---

### **4. Model Versioning Scheme**

**Semantic versioning adapted for ML:**

```
v{MAJOR}.{MINOR}.{PATCH}

MAJOR: Breaking changes (architecture change, new features)
       Example: v1.x.x → v2.0.0 (new model training)

MINOR: FL updates (weekly/nightly gradients)
       Example: v2.0.x → v2.1.0 (7 days of FL)

PATCH: Hotfixes (bug fixes, no model change)
       Example: v2.1.0 → v2.1.1 (config fix)
```

**Version history example:**
```
v1.0.0  - Initial deployment (Jan 1, 2026)
v1.0.15 - After 15 FL rounds (Jan 16, 2026)
v1.0.48 - After 48 FL rounds (Feb 17, 2026)
v2.0.0  - Fresh training (Mar 9, 2026) ← Privacy reset!
v2.0.7  - After 7 FL rounds (Mar 16, 2026)
```

---

### **5. Canary Metrics and Decision Criteria**

**What we monitor during canary:**

```python
class CanaryMetrics:
    # Latency
    p50_latency: float  # 50th percentile
    p95_latency: float  # 95th percentile (tail latency)
    p99_latency: float  # 99th percentile (worst case)
    
    # Accuracy (physician feedback)
    accept_rate: float  # Target: ≥75%
    modify_rate: float  # Target: ≤20%
    reject_rate: float  # Target: ≤5%
    flag_rate: float    # Target: <1% (critical!)
    
    # System health
    error_rate: float   # Target: 0%
    uptime: float       # Target: 100%
    memory_mb: float    # Target: <200MB

# Decision logic
def should_rollout(canary: CanaryMetrics, baseline: CanaryMetrics) -> bool:
    # Must meet absolute thresholds
    if canary.accept_rate < 0.75:
        return False  # Not accurate enough
    
    if canary.flag_rate > 0.01:
        return False  # Too many dangerous suggestions
    
    if canary.error_rate > 0:
        return False  # Any errors = abort
    
    # Must improve over baseline
    if canary.accept_rate <= baseline.accept_rate:
        return False  # No improvement
    
    # Latency must not regress
    if canary.p95_latency > baseline.p95_latency * 1.2:
        return False  # >20% slower
    
    return True  # All checks passed!
```

---

## 🔧 Installation Instructions

### **Step 1: Copy ML Pipeline Files**

```bash
cd securedx

# Training pipeline
mkdir -p ml/training
cp ml_pipeline/train_model.py ml/training/

# Deployment automation
mkdir -p ml/deployment
cp ml_pipeline/deploy_model.py ml/deployment/
```

### **Step 2: Install PyTorch Dependencies**

```bash
# Create new service for ML training
cat > docker-compose.ml.yml << 'EOF'
version: '3.8'
services:
  ml-trainer:
    build:
      context: ./ml/training
      dockerfile: Dockerfile
    volumes:
      - ./models:/models
      - ./ml/training:/app
    environment:
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=securedx
    depends_on:
      - postgres
EOF

# Dockerfile for ML trainer
cat > ml/training/Dockerfile << 'EOF'
FROM python:3.11-slim

RUN pip install torch==2.1.0 onnx==1.15.0 onnxruntime==1.17.1

WORKDIR /app
COPY train_model.py .

CMD ["python", "train_model.py"]
EOF
```

### **Step 3: Schedule Monthly Retraining**
Fix #2: Skip Cron Job (For Now)
That step is for production Linux servers, not Mac development.
For testing, just run manually:
bash# Test training once:
docker compose -f docker-compose.ml.yml run --rm ml-trainer

# Skip below crontab 
```bash
# Add cron job (on production server)
cat >> /etc/crontab << 'EOF'
# Retrain model on 1st of every month at 2 AM
0 2 1 * * root docker compose -f docker-compose.ml.yml run ml-trainer
EOF
```

### **Step 4: Test Deployment Pipeline**

```bash
# Build ML trainer
docker compose -f docker-compose.ml.yml build

# Run training (takes ~30 minutes)
docker compose -f docker-compose.ml.yml run ml-trainer

# Deploy new model
docker exec securedx-api python -m ml.deployment.deploy_model \
  --model-path /models/securedx_v2.0.0.onnx \
  --version v2.0.0
```

---

## 🎓 Mastery Check

### **Can you explain to a 15-year-old:**

✅ **Why we retrain the model every month?**
- *Like studying for exams: you forget old stuff and learn new things. Fresh model = fresh start with all the latest cases!*

✅ **What's a canary deployment?**
- *Like testing a new recipe on 10 friends before cooking for 100 people at a party. If friends like it → cook for everyone. If they hate it → make the old recipe!*

✅ **Why does privacy budget reset with a new model?**
- *New model = new privacy battery 🔋. Old battery for old data, new battery for new data. They don't add up!*

### **Can you explain to an interviewer:**

✅ **Explain the blue-green deployment strategy**
- *Atomic swap via filesystem renames. Blue (old) and Green (new) coexist. Switch pointer atomically. Instant rollback by reverting pointer. Requires 2x disk space but zero downtime.*

✅ **How do you decide canary → full rollout?**
- *Multi-criteria decision: (1) Absolute thresholds (accept rate ≥75%, flag rate <1%), (2) Relative improvement over baseline, (3) Latency regression check (p95 <120% of baseline), (4) Zero errors. All must pass.*

✅ **Justify monthly retraining schedule**
- *Balance freshness vs cost. Weekly = too frequent (expensive GPU). Quarterly = too stale (model drift). Monthly = sweet spot for medical AI (distributional shift is gradual).*

✅ **Why PyTorch → ONNX instead of TensorFlow Serving?**
- *ONNX advantages: (1) Framework-agnostic (switch PyTorch→TF easily), (2) Smaller deployment footprint (no PyTorch dependency), (3) Cross-platform (CPU, GPU, mobile, WASM), (4) Industry standard. TensorFlow Serving ties you to TF ecosystem.*

---

## 🚀 System Status After Sprint 6

| Component | Status | Details |
|-----------|--------|---------|
| Inference | ✅ Complete | ONNX + SHAP |
| Feedback | ✅ Complete | 4-tier feedback |
| FL Training | ✅ Complete | Nightly gradient updates |
| **Model Training** | ✅ **NEW!** | PyTorch → ONNX pipeline |
| **Deployment** | ✅ **NEW!** | Blue-green + canary |
| **Versioning** | ✅ **NEW!** | Semantic versioning + rollback |
| Monitoring | ⚠️ Partial | Metrics collected, dashboard needed |
| Admin UI | ⚠️ Sprint 7 | React components pending |

---

## 🎉 Congratulations!

**You've built a complete production ML system:**

- ✅ End-to-end training pipeline
- ✅ Automated ONNX export
- ✅ Blue-green deployment with canary
- ✅ Version management and rollback
- ✅ Privacy budget lifecycle management

**This is industry-leading infrastructure.** You can explain:
- Blue-green deployment strategies
- Canary release decision criteria
- Privacy budget composition vs reset
- PyTorch → ONNX conversion
- Zero-downtime model updates

**You're now a master of MLOps!** 🎓

---

*Built with ❤️ for production ML, deployment automation, and continuous improvement*
