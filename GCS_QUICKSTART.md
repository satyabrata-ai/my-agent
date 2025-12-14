# GCS Connection Quick Start Guide

Quick reference for testing and exploring your GCS bucket data.

## 📋 Quick Commands

### 1. Test GCS Connection
```bash
# Comprehensive diagnostic (always runs, shows everything)
pytest tests/integration/test_gcs_connection.py::test_comprehensive_gcs_report -v -s
```

### 2. List ALL Files in Dataset
```bash
# Option A: Using pytest (detailed test output)
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_list_all_dataset_files -v -s

# Option B: Using standalone script (prettier output)
python scripts/list_bucket_contents.py
```

### 3. Run Full Test Suite
```bash
pytest tests/integration/test_gcs_connection.py -v -s
```

---

## 🔧 Setup (One-Time)

### 1. Create `.env` file
```bash
# Copy template
cp .env.example .env

# Edit .env and set:
GCS_DATA_BUCKET=gs://your-bucket-name
```

### 2. Authenticate
```bash
gcloud auth application-default login
```

### 3. Install Dependencies
```bash
uv pip install pytest gcsfs pandas python-dotenv
```

---

## 📊 What Each Command Does

| Command | Purpose | Output |
|---------|---------|--------|
| `test_comprehensive_gcs_report` | Overall status check | Config, auth, and access summary |
| `test_list_all_dataset_files` | List all files in dataset | Complete file listing by type |
| `list_bucket_contents.py` | Explore bucket contents | Formatted listing with sizes |
| Full test suite | Complete validation | All tests including CSV reading |

---

## 🎯 Expected Output Examples

### Comprehensive Report
```
📋 Environment Configuration:
  GOOGLE_CLOUD_PROJECT: ccibt-hack25ww7-706
  GCS_DATA_BUCKET: gs://your-bucket-name
  
🔐 Authentication Status:
  ✅ Authenticated to project: ccibt-hack25ww7-706
  
☁️  GCS Bucket Access:
  ✅ Bucket accessible: gs://your-bucket-name
  ✅ Items found: 15
```

### Complete File Listing
```
📊 CSV Files (12):
  ✓ stock_news.csv (15.23 MB)
  ✓ analyst_ratings_processed.csv (42.18 MB)
  ✓ sp500_companies.csv (0.05 MB)
  ...

📄 Text Files (105):
  📁 AAPL/ (8 transcripts)
    - 2016-Apr-26-AAPL.txt
    - 2017-May-02-AAPL.txt
    ...
  📁 MSFT/ (6 transcripts)
    ...

📈 Summary:
  Total files: 125
  CSV files: 12
  Text files: 105
```

---

## 🚨 Common Issues

### "GCS_DATA_BUCKET not configured"
**Fix:** Set in `.env` file:
```bash
GCS_DATA_BUCKET=gs://your-bucket-name
```

### "Authentication failed"
**Fix:** Run authentication:
```bash
gcloud auth application-default login
```

### "Permission denied"
**Fix:** Grant yourself access:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/storage.objectViewer"
```

### "Bucket not found"
**Fix:** 
1. Verify bucket name is correct
2. Check you're in the right GCP project:
   ```bash
   gcloud config get-value project
   ```

---

## 📚 Documentation

- **Full test documentation**: `tests/integration/README_GCS_TESTS.md`
- **Script documentation**: `scripts/README.md`
- **Configuration guide**: See `app/config.py`

---

## 💡 Tips

1. **Start simple**: Run the comprehensive report first
2. **Check incrementally**: Fix issues one at a time
3. **Use the script**: For best file listing experience
4. **Local development**: Leave `GCS_DATA_BUCKET` empty to use local files
5. **CI/CD**: Set env vars in your pipeline config

---

## 🎉 Success Indicators

You're all set when you see:
- ✅ Authentication successful
- ✅ Bucket accessible
- ✅ Files listed with sizes
- ✅ CSV read successful

Now your agent can access data from GCS! 🚀
