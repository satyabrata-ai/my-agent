# GCS Connection Integration Tests

This directory contains integration tests for validating Google Cloud Storage (GCS) bucket connectivity.

## Test File: `test_gcs_connection.py`

Comprehensive test suite that validates:
- ✅ Environment variables configuration
- ✅ Google Cloud authentication
- ✅ GCS bucket accessibility
- ✅ Dataset files existence
- ✅ CSV file reading capabilities
- ✅ Local data fallback

## Setup

### 1. Create `.env` File

Copy the example and fill in your values:

```bash
# In project root directory
cp .env.example .env
```

Edit `.env`:
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=True
LOGS_BUCKET_NAME=gs://your-logs-bucket

# GCS Data Bucket Configuration
GCS_DATA_BUCKET=gs://your-data-bucket
GCS_DATASET_PREFIX=datasets/uc4-market-activity-prediction-agent

# Environment
ENVIRONMENT=development
```

### 2. Authenticate with Google Cloud

```bash
# Install gcloud CLI if not already installed
# Then authenticate:
gcloud auth application-default login

# Verify authentication
gcloud auth list
```

### 3. Install Dependencies

```bash
# Make sure you have the required packages
uv pip install pytest pandas gcsfs python-dotenv
```

## Running Tests

### Run All GCS Tests

```bash
# From project root
pytest tests/integration/test_gcs_connection.py -v -s
```

### Run Specific Test

```bash
# Test authentication only
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_google_auth -v -s

# Test bucket access
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_bucket_access -v -s

# List ALL files in dataset (comprehensive)
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_list_all_dataset_files -v -s

# Test CSV reading
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_read_sample_csv -v -s
```

### Run Comprehensive Report

```bash
# This test always runs and provides detailed diagnostic info
pytest tests/integration/test_gcs_connection.py::test_comprehensive_gcs_report -v -s
```

## Test Scenarios

### Scenario 1: GCS Configured (Production-like)

**Setup:**
- `GCS_DATA_BUCKET` is set in `.env`
- Google Cloud authentication is configured
- Data files are in GCS bucket

**Expected:**
- ✅ All tests pass
- ✅ Data is read from GCS
- ✅ Bucket access succeeds

### Scenario 2: Local Development (No GCS)

**Setup:**
- `GCS_DATA_BUCKET` is empty or not set in `.env`
- Data files are in `app/dataset/` directory

**Expected:**
- ✅ Basic tests pass
- ⚠️ GCS tests are skipped
- ✅ Local fallback works

### Scenario 3: Authentication Issues

**Setup:**
- `GCS_DATA_BUCKET` is set
- Google Cloud authentication not configured

**Expected:**
- ❌ Authentication test fails with helpful error
- 💡 Recommendation to run `gcloud auth application-default login`

## Understanding Test Results

### All Green (✅)
```
✅ Environment variables loaded
✅ Authentication successful  
✅ Bucket accessible
✅ Dataset files exist
✅ CSV read successful
```
**Meaning:** GCS is fully configured and working!

### Mixed Results (⚠️)
```
✅ Environment variables loaded
⚠️  GCS_DATA_BUCKET not configured
✅ Local data fallback working
```
**Meaning:** Running in local development mode, which is fine for testing.

### Failures (❌)
```
✅ Environment variables loaded
❌ Authentication failed
❌ Bucket access failed
```
**Meaning:** Configuration issue. Follow recommendations in test output.

## Troubleshooting

### Problem: "Authentication failed"

**Solution:**
```bash
gcloud auth application-default login
```

### Problem: "Bucket not found"

**Solutions:**
1. Verify bucket name in `.env` is correct
2. Check bucket exists:
   ```bash
   gsutil ls gs://your-bucket-name
   ```
3. Verify you're in the right GCP project:
   ```bash
   gcloud config get-value project
   ```

### Problem: "Permission denied"

**Solution:**
```bash
# Grant yourself Storage Object Viewer role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:your-email@example.com" \
  --role="roles/storage.objectViewer"
```

### Problem: "File not found in bucket"

**Solution:**
1. Check what's actually in your bucket:
   ```bash
   gsutil ls -r gs://your-bucket-name/
   ```
2. Verify the `GCS_DATASET_PREFIX` matches your bucket structure
3. Ensure files are named correctly:
   - `datasets_uc4-market-activity-prediction-agent_stock_news.csv`
   - `datasets_uc4-market-activity-prediction-agent_analyst_ratings_processed.csv`

## Comprehensive File Listing

### Using the Test

To see ALL files in your dataset directory:

```bash
pytest tests/integration/test_gcs_connection.py::TestGCSConnection::test_list_all_dataset_files -v -s
```

This will show:
- ✅ All CSV files with sizes
- ✅ All transcript files grouped by company
- ✅ Summary statistics
- ✅ Total file counts

### Using the Standalone Script

For a more detailed view with better formatting:

```bash
python scripts/list_bucket_contents.py
```

This script provides:
- 📊 All CSV data files
- 📄 Transcripts organized by company
- 📦 ZIP archives
- 📈 Total dataset size
- 🎨 Better formatting and colors

See `scripts/README.md` for details.

## Integration with CI/CD

These tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run GCS Integration Tests
  env:
    GCS_DATA_BUCKET: ${{ secrets.GCS_DATA_BUCKET }}
    GOOGLE_APPLICATION_CREDENTIALS: ${{ secrets.GCP_SA_KEY }}
  run: |
    pytest tests/integration/test_gcs_connection.py -v
```

## Local Development Best Practices

1. **Don't commit `.env`** - It contains sensitive credentials
2. **Use `.env.example`** - Template for other developers
3. **Local data fallback** - Keep sample data in `app/dataset/` for offline development
4. **Test both modes** - Run tests with and without GCS configured

## Support

If tests fail:
1. Check the comprehensive report output
2. Follow recommendations in test output
3. Verify all prerequisites are met
4. Check GCP console for bucket permissions
