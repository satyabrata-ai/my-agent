# 🚀 Agent Engine Deployment Guide

## ✅ Changes Made for Deployment

Your agent is now configured to properly deploy to Google Agent Engine with all necessary environment variables.

---

## 📝 What Was Fixed

### 1. **Makefile Updated**
The `make deploy` command now includes:

```makefile
deploy:
	@uv export ... > app/app_utils/.requirements.txt
	@uv run -m app.app_utils.deploy \
		--source-packages=./app \
		--entrypoint-module=app.agent_engine_app \
		--entrypoint-object=agent_engine \
		--requirements-file=app/app_utils/.requirements.txt \
		--env-file=.env \                          # ← NEW: Uses root .env file
		--set-env-vars="ENVIRONMENT=production"    # ← NEW: Sets production mode
```

### 2. **Environment Variables That Will Deploy**

From your `.env` file (lines 6-11):
- ✅ `GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706`
- ✅ `GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent`
- ✅ `AGENT_MODEL=gemini-2.5-flash`
- ✅ `ENVIRONMENT=production` (overridden for deployment)

---

## 🎯 How to Deploy

### Step 1: Verify Your `.env` File

Make sure your root `.env` file contains:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=ccibt-hack25ww7-706
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
LOGS_BUCKET_NAME=gs://ccibt-agent-logs

# GCS Data Bucket Configuration
GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent

# Agent Memory Settings
GCS_MEMORY_PATH=agent_memory

# Model Configuration
AGENT_MODEL=gemini-2.5-flash

# Environment (overridden to 'production' during deployment)
ENVIRONMENT=development
```

### Step 2: Deploy the Agent

```bash
make deploy
```

### Step 3: Verify Deployment

Check the deployment logs for:

```
🌍 Environment Variables:
  GCS_DATA_BUCKET: gs://datasets-ccibt-hack25ww7-706
  GCS_DATASET_PREFIX: datasets/uc4-market-activity-prediction-agent
  AGENT_MODEL: gemini-2.5-flash
  ENVIRONMENT: production
  GOOGLE_CLOUD_REGION: us-central1
  ...
```

---

## 🔐 Required IAM Permissions

Your Agent Engine service account needs these permissions:

### GCS Bucket Access

```bash
# Get your service account email from deployment logs
# It will look like: PROJECT_NUMBER-compute@developer.gserviceaccount.com

# Grant read/write access to your GCS bucket
gcloud storage buckets add-iam-policy-binding gs://datasets-ccibt-hack25ww7-706 \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@developer.gserviceaccount.com" \
    --role="roles/storage.objectUser"
```

### Required Roles:
- **`roles/storage.objectUser`** - Read/write access to GCS objects
- **`roles/storage.legacyBucketReader`** - List bucket contents
- **`roles/aiplatform.user`** - Access Vertex AI models

---

## 🔍 Troubleshooting

### Issue: Environment Variables Not Loading

**Symptom:**
```
⚠️  Configuration warning: GCS_DATA_BUCKET is required but not set.
```

**Solution:**
1. Verify `.env` file exists in project root
2. Check Makefile includes `--env-file=.env`
3. Redeploy: `make deploy`

### Issue: GCS Access Denied

**Symptom:**
```
403 Forbidden: Permission denied on resource 'gs://datasets-ccibt-hack25ww7-706'
```

**Solution:**
```bash
# Find your service account
gcloud run services describe my-agent --region=us-central1 --format="value(spec.template.spec.serviceAccountName)"

# Grant permissions
gcloud storage buckets add-iam-policy-binding gs://datasets-ccibt-hack25ww7-706 \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT" \
    --role="roles/storage.objectUser"
```

### Issue: Model Not Available

**Symptom:**
```
Model 'gemini-2.5-flash' not found or not available
```

**Solution:**
Update `.env` to use a different model:
```bash
AGENT_MODEL=gemini-1.5-pro  # Stable production model
```

Then redeploy: `make deploy`

---

## 📊 Deployment Verification Checklist

After deployment, verify:

- [ ] Deployment completed without errors
- [ ] Environment variables appear in deployment logs
- [ ] Agent responds to test queries
- [ ] GCS data is accessible (check agent logs)
- [ ] Persistent memory works (queries are cached)
- [ ] Model is working correctly

### Test Queries

```bash
# Get the agent endpoint from deployment output
curl -X POST "https://YOUR-AGENT-ENDPOINT/invoke" \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze sentiment for Apple (AAPL)"}'
```

Or use the Agent Engine console to send test messages.

---

## 🎯 Production Best Practices

### 1. **Use Stable Models**
```bash
AGENT_MODEL=gemini-1.5-pro  # ✅ Production-ready
# Not: gemini-3-pro-preview  # ❌ Preview/experimental
```

### 2. **Set Environment Correctly**
```bash
ENVIRONMENT=production  # Automatically set during deployment
```

### 3. **Monitor GCS Usage**
```bash
# Check GCS object count
gsutil ls -r gs://datasets-ccibt-hack25ww7-706/agent_memory/ | wc -l

# Check storage size
gsutil du -sh gs://datasets-ccibt-hack25ww7-706/agent_memory/
```

### 4. **Set Up Logging**
```bash
# View agent logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=my-agent" \
    --limit=50 \
    --format=json
```

---

## 🔄 Updating Configuration

### To Change Model

1. Update `.env`:
   ```bash
   AGENT_MODEL=gemini-1.5-flash
   ```

2. Redeploy:
   ```bash
   make deploy
   ```

### To Change GCS Bucket

1. Update `.env`:
   ```bash
   GCS_DATA_BUCKET=gs://new-bucket-name
   ```

2. Grant permissions to new bucket
3. Redeploy

### To Add New Environment Variables

1. Add to `.env`:
   ```bash
   MY_NEW_VAR=some_value
   ```

2. Use in code:
   ```python
   from app.config import config
   my_var = os.getenv("MY_NEW_VAR")
   ```

3. Redeploy

---

## 📚 Additional Resources

- **Agent Engine Docs:** https://cloud.google.com/vertex-ai/docs/agent-engine
- **GCS IAM:** https://cloud.google.com/storage/docs/access-control/iam
- **Vertex AI Models:** https://cloud.google.com/vertex-ai/docs/generative-ai/models

---

## ✅ Summary

**What's Working Now:**
- ✅ `.env` variables deploy correctly
- ✅ GCS data bucket configuration included
- ✅ Model configuration from environment
- ✅ Production environment set automatically
- ✅ Persistent memory configuration

**Deployment Command:**
```bash
make deploy
```

**Verification:**
Check logs for environment variables after deployment completes.

---

**Status:** ✅ Ready to deploy with proper environment configuration!
