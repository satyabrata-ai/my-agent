# Utility Scripts

This directory contains utility scripts for managing and exploring the agent's data sources.

## Scripts

### `list_bucket_contents.py`

Comprehensive explorer for your GCS bucket. Lists all files with sizes, organized by type.

**Usage:**
```bash
# From project root
python scripts/list_bucket_contents.py
```

**What it shows:**
- 📊 All CSV data files with sizes
- 📄 All earnings call transcripts grouped by company
- 📦 ZIP archives
- 📄 Other files
- 📈 Summary statistics and total size

**Requirements:**
- `GCS_DATA_BUCKET` must be set in `.env`
- Google Cloud authentication configured
- `gcsfs` package installed

**Example output:**
```
================================================================================
GCS BUCKET CONTENTS EXPLORER
================================================================================

📦 Bucket: gs://your-bucket-name
📂 Dataset Prefix: datasets/uc4-market-activity-prediction-agent
✅ Connected to GCS

🔍 Scanning: gs://your-bucket-name/datasets/uc4-market-activity-prediction-agent
   (This may take a moment...)

✅ Found 125 files

================================================================================

📊 CSV DATA FILES (12):
--------------------------------------------------------------------------------
  ✓ stock_news.csv                                      15.23 MB
  ✓ analyst_ratings_processed.csv                      42.18 MB
  ✓ sp500_companies.csv                                  0.05 MB
  ...

  Total CSV size: 87.45 MB


📄 EARNINGS CALL TRANSCRIPTS (105):
--------------------------------------------------------------------------------

  📁 AAPL/ (8 transcripts)
     - 2016-Apr-26-AAPL.txt                        45.23 KB
     - 2017-May-02-AAPL.txt                        47.89 KB
     ...

  Total transcripts size: 5.67 MB

================================================================================
SUMMARY
================================================================================
  Total files: 125
  CSV files: 12
  Transcript files: 105
  ZIP files: 3
  Other files: 5

  Total dataset size: 95.34 MB
================================================================================
```

**Troubleshooting:**

If you see "GCS_DATA_BUCKET not configured":
- Make sure you have a `.env` file in project root
- Set `GCS_DATA_BUCKET=gs://your-bucket-name`

If you see "Failed to connect to GCS":
- Run: `gcloud auth application-default login`
- Make sure you have access to the bucket

If you see "Dataset path not found":
- Verify the bucket and prefix are correct
- Check that data actually exists at that location

## Adding More Scripts

Feel free to add more utility scripts here for:
- Data validation
- Sample data generation
- Backup/restore operations
- Data transformations
- etc.
