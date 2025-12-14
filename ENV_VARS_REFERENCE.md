# 🔧 Environment Variables Reference

## Quick Reference for Agent Deployment

---

## ✅ Required Variables (Must Be Set)

| Variable | Value | Purpose |
|----------|-------|---------|
| `GCS_DATA_BUCKET` | `gs://datasets-ccibt-hack25ww7-706` | GCS bucket for datasets |
| `GCS_DATASET_PREFIX` | `datasets/uc4-market-activity-prediction-agent` | Dataset path within bucket |
| `AGENT_MODEL` | `gemini-2.5-flash` | LLM model to use |

---

## 📋 Standard Variables (Pre-configured)

| Variable | Value | Purpose |
|----------|-------|---------|
| `GOOGLE_CLOUD_PROJECT` | `ccibt-hack25ww7-706` | GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | `global` | Default location |
| `GOOGLE_GENAI_USE_VERTEXAI` | `True` | Use Vertex AI |
| `LOGS_BUCKET_NAME` | `gs://ccibt-agent-logs` | Logs bucket |

---

## 🎯 Deployment-Specific Variables

| Variable | Local Value | Deployment Value | Auto-Set? |
|----------|-------------|------------------|-----------|
| `ENVIRONMENT` | `development` | `production` | ✅ Yes (via `--set-env-vars`) |
| `GOOGLE_CLOUD_REGION` | `global` | `us-central1` | ✅ Yes (auto) |
| `NUM_WORKERS` | - | `1` | ✅ Yes (auto) |

---

## 🚀 Where Variables Are Read From

### Local Development (`make playground`)
```
Root .env file
  └─> Loaded by python-dotenv
      └─> Available to app via config.py
```

### Deployment (`make deploy`)
```
Root .env file
  └─> Loaded by deploy script (--env-file=.env)
      └─> Merged with --set-env-vars
          └─> Deployed as container environment variables
              └─> Available to app via os.getenv()
```

---

## 📝 Your Current Configuration

### Root `.env` File
```bash
# Lines 6-11 (Critical for deployment)
GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent
AGENT_MODEL=gemini-2.5-flash
```

### How It's Used in Code

```python
# app/config.py
class Config:
    GCS_DATA_BUCKET: str = os.getenv(
        "GCS_DATA_BUCKET",
        ""  # No default
    )
    
    AGENT_MODEL: str = os.getenv(
        "AGENT_MODEL", 
        "gemini-2.5-flash"  # Default
    )
```

---

## 🔍 Verification Commands

### Check Local Variables
```bash
# Windows PowerShell
Get-Content .env | Select-String "GCS_DATA_BUCKET|AGENT_MODEL"

# Linux/Mac
grep -E "GCS_DATA_BUCKET|AGENT_MODEL" .env
```

### Check Deployed Variables
```bash
# View environment variables in deployed agent
gcloud run services describe my-agent \
    --region=us-central1 \
    --format="value(spec.template.spec.containers[0].env)"
```

---

## ⚠️ Common Issues & Fixes

### Issue 1: Variables Not Loading in Deployment

**Symptom:**
```
⚠️  Configuration warning: GCS_DATA_BUCKET is required but not set.
```

**Fix:**
- Verify `.env` exists in project root ✅
- Check Makefile has `--env-file=.env` ✅ (Already added!)
- Redeploy: `make deploy`

### Issue 2: Wrong Model Deployed

**Symptom:**
```
Model 'gemini-3-pro-preview' not found
```

**Fix:**
Update `.env`:
```bash
AGENT_MODEL=gemini-2.5-flash  # ✅ Stable
```
Redeploy: `make deploy`

### Issue 3: GCS Access Issues

**Symptom:**
```
403 Forbidden: gs://datasets-ccibt-hack25ww7-706
```

**Fix:**
Grant service account permissions:
```bash
gcloud storage buckets add-iam-policy-binding \
    gs://datasets-ccibt-hack25ww7-706 \
    --member="serviceAccount:YOUR_SA@developer.gserviceaccount.com" \
    --role="roles/storage.objectUser"
```

---

## 🎯 Testing Locally vs Deployment

### Local Testing
```bash
# Uses root .env file
make playground

# Variables loaded via python-dotenv
# GCS access via your personal credentials
```

### Deployment
```bash
# Uses root .env file via --env-file flag
make deploy

# Variables set as container env vars
# GCS access via service account
```

---

## 📊 Variable Priority (Highest to Lowest)

1. **`--set-env-vars`** (Command line) - Highest priority
2. **`.env` file** (via --env-file flag)
3. **Default values** (in config.py) - Lowest priority

Example:
```bash
# In .env file:
AGENT_MODEL=gemini-2.5-flash

# Makefile override:
--set-env-vars="ENVIRONMENT=production"

# Final result in deployment:
AGENT_MODEL=gemini-2.5-flash (from .env)
ENVIRONMENT=production (from --set-env-vars)
```

---

## ✅ Deployment Checklist

Before running `make deploy`:

- [ ] `.env` file exists in project root
- [ ] `GCS_DATA_BUCKET` is set in `.env`
- [ ] `GCS_DATASET_PREFIX` is set in `.env`
- [ ] `AGENT_MODEL` is set to stable model (e.g., `gemini-2.5-flash`)
- [ ] Makefile includes `--env-file=.env` ✅ (Done!)
- [ ] Service account has GCS permissions
- [ ] You're authenticated: `gcloud auth list`

---

## 🔄 Quick Updates

### Change Model
```bash
# Edit .env
AGENT_MODEL=gemini-1.5-pro

# Redeploy
make deploy
```

### Change GCS Bucket
```bash
# Edit .env
GCS_DATA_BUCKET=gs://new-bucket-name

# Grant permissions
gcloud storage buckets add-iam-policy-binding gs://new-bucket-name ...

# Redeploy
make deploy
```

### Add New Variable
```bash
# 1. Add to .env
MY_NEW_VAR=value

# 2. Use in code
from app.config import config
value = os.getenv("MY_NEW_VAR")

# 3. Redeploy
make deploy
```

---

## 📚 Summary

**Key Points:**
- ✅ Root `.env` file is used for both local and deployment
- ✅ Makefile updated to include `--env-file=.env`
- ✅ `ENVIRONMENT=production` automatically set during deployment
- ✅ All required variables are in your `.env` file
- ✅ Ready to deploy with: `make deploy`

**Current Model:** `gemini-2.5-flash` (Stable, production-ready)

**GCS Bucket:** `gs://datasets-ccibt-hack25ww7-706`

**Status:** ✅ Configuration complete and deployment-ready!
