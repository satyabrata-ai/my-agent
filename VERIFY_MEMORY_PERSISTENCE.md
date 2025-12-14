# Quick Verification Guide: Memory Persistence in Agent Engine

## 🎯 What Was Fixed

The agent now:
1. ✅ Has a default GCS bucket configured (`gs://datasets-ccibt-hack25ww7-706`)
2. ✅ Provides detailed diagnostic logging
3. ✅ Saves memory every 3 operations automatically
4. ✅ Shows clear messages about configuration status

## 🚀 How to Verify the Fix

### Step 1: Run Diagnostic (Optional)

```bash
cd my-agent
uv run python diagnose_memory.py
```

**Expected output:**
```
✅ GCS_DATA_BUCKET: gs://datasets-ccibt-hack25ww7-706
✅ PERSISTENCE ENABLED
✅ Save test PASSED
```

### Step 2: Deploy to Agent Engine

```bash
make deploy
```

### Step 3: Check Deployment Logs

Look for these **SUCCESS** messages in Agent Engine logs:

```
🔧 Initializing PersistentMemoryStore...
   GCS_DATA_BUCKET: gs://datasets-ccibt-hack25ww7-706
   GCS_MEMORY_PATH: agent_memory
   Memory file: gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json

✅ Loaded persistent memory from GCS
```

Or on first run:
```
📝 No existing memory found - initializing new store
   Will create: gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json
```

### Step 4: Run Test Queries

In Agent Engine, run 3-4 queries:
```
User: "What's the sentiment for AAPL?"
User: "Analyze MSFT sentiment"
User: "Tell me about GOOGL"
```

### Step 5: Check for Save Messages

Look for in logs:
```
💾 Saving memory to GCS: gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json
✅ Memory persisted successfully (3 tickers)
```

### Step 6: Verify File in GCS

```bash
# Check if memory file was created
gsutil ls gs://datasets-ccibt-hack25ww7-706/agent_memory/

# Expected output:
# gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json

# View the content
gsutil cat gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json
```

**Expected content:**
```json
{
  "version": "1.0",
  "analyzed_tickers": {
    "AAPL": [...],
    "MSFT": [...],
    "GOOGL": [...]
  },
  "statistics": {
    "total_queries": 3,
    "unique_tickers_analyzed": 3
  }
}
```

### Step 7: Test Persistence Across Restarts

1. **Restart the agent** (or wait for new session)

2. **Check logs for:**
   ```
   ✅ Loaded persistent memory from GCS
      Tickers analyzed: 3
      Total queries: 3
   ```

3. **Run a query about previously analyzed ticker:**
   ```
   User: "Have we analyzed AAPL before?"
   ```

4. **Agent should recall previous analysis** ✅

## ❌ Warning Signs

If you see these messages, something is wrong:

### Warning 1: No GCS Configured
```
======================================================================
⚠️  WARNING: NO GCS PERSISTENCE CONFIGURED!
======================================================================
```

**Fix:** Ensure `.env` file has `GCS_DATA_BUCKET` or code has default (already done)

### Warning 2: Permission Denied
```
⚠️  Permission denied saving to GCS
   Service account needs 'Storage Object Admin' on bucket
```

**Fix:** Grant IAM permissions:
```bash
# Get service account email from logs or:
gcloud run services describe YOUR-SERVICE \
  --region us-central1 \
  --format="value(spec.template.spec.serviceAccountName)"

# Grant permissions
gsutil iam ch serviceAccount:SERVICE-ACCOUNT-EMAIL:roles/storage.objectAdmin \
  gs://datasets-ccibt-hack25ww7-706
```

### Warning 3: Cannot Save
```
⚠️  Cannot persist N operations (no GCS configured)
```

**Fix:** Check config.py has correct default bucket (already done)

## 📊 Success Criteria

✅ **Memory persistence is working if:**

1. Logs show: `✅ Memory persisted successfully`
2. GCS file exists: `session_memory.json`
3. File contains analyzed tickers
4. On restart: `✅ Loaded persistent memory from GCS`
5. Agent recalls previous analyses

## 🔧 Quick Commands Reference

```bash
# 1. Run diagnostic
uv run python diagnose_memory.py

# 2. Deploy
make deploy

# 3. Check GCS
gsutil ls gs://datasets-ccibt-hack25ww7-706/agent_memory/
gsutil cat gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json

# 4. View Agent Engine logs
gcloud logging read "resource.type=cloud_run_revision" --limit=100

# 5. Check service account
gcloud run services describe YOUR-SERVICE \
  --region us-central1 \
  --format="value(spec.template.spec.serviceAccountName)"

# 6. Grant permissions (if needed)
gsutil iam ch serviceAccount:EMAIL:roles/storage.objectAdmin \
  gs://datasets-ccibt-hack25ww7-706
```

## 💡 Pro Tips

1. **Check logs immediately after deployment** to see initialization messages

2. **Run 3 queries first** to trigger the first save (saves every 3 operations)

3. **Look for file timestamp** in GCS to confirm recent saves

4. **Use diagnose_memory.py** locally to test configuration before deploying

5. **Keep Agent Engine logs open** while testing to see real-time persistence

## 🎉 Expected Timeline

1. **Deploy:** ~2-3 minutes
2. **First queries:** Immediate
3. **First save:** After 3rd operation
4. **GCS file appears:** Within seconds
5. **Restart test:** Immediate on next session

Total verification time: **< 5 minutes**

## 📚 Related Documentation

- `AGENT_ENGINE_MEMORY_FIX.md` - Detailed fix documentation
- `diagnose_memory.py` - Diagnostic script
- `FINAL_MEMORY_FIX_SUMMARY.md` - Complete memory fix history

---

**Memory persistence in Agent Engine should now be working!** 🚀

If you still see issues after following this guide, check the troubleshooting section in `AGENT_ENGINE_MEMORY_FIX.md`.
