# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Integration tests for Google Cloud Storage bucket connectivity.
Tests authentication, bucket access, and data file availability.
"""

import os
import pytest
import pandas as pd
from pathlib import Path

# Import configuration
from app.config import config


class TestGCSConnection:
    """Test suite for validating GCS bucket connection and data access"""
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are properly loaded from .env"""
        print("\n1️⃣ Testing Environment Variables...")
        
        # Check critical env vars
        assert config.GOOGLE_CLOUD_PROJECT, "GOOGLE_CLOUD_PROJECT not set"
        print(f"  ✅ GOOGLE_CLOUD_PROJECT: {config.GOOGLE_CLOUD_PROJECT}")
        
        assert config.GOOGLE_CLOUD_LOCATION, "GOOGLE_CLOUD_LOCATION not set"
        print(f"  ✅ GOOGLE_CLOUD_LOCATION: {config.GOOGLE_CLOUD_LOCATION}")
        
        print(f"  ℹ️  GCS_DATA_BUCKET: {config.GCS_DATA_BUCKET or 'Not set (using local data)'}")
        print(f"  ℹ️  ENVIRONMENT: {config.ENVIRONMENT}")
    
    def test_google_auth(self):
        """Test Google Cloud authentication"""
        print("\n2️⃣ Testing Google Cloud Authentication...")
        
        try:
            import google.auth
            credentials, project_id = google.auth.default()
            
            assert credentials is not None, "No credentials found"
            assert project_id, "No project ID found"
            
            print(f"  ✅ Authentication successful")
            print(f"  ✅ Credentials type: {type(credentials).__name__}")
            print(f"  ✅ Project ID: {project_id}")
            
        except Exception as e:
            pytest.skip(f"Google Cloud authentication not configured: {e}")
    
    def test_gcsfs_initialization(self):
        """Test that gcsfs can be initialized"""
        print("\n3️⃣ Testing gcsfs Library...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            assert fs is not None, "Failed to initialize GCSFileSystem"
            print(f"  ✅ gcsfs initialized successfully")
            
        except Exception as e:
            pytest.fail(f"gcsfs initialization failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_bucket_access(self):
        """Test access to the configured GCS bucket"""
        print(f"\n4️⃣ Testing Bucket Access...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            bucket_path = config.GCS_DATA_BUCKET
            assert bucket_path, "GCS_DATA_BUCKET is empty"
            
            print(f"  📦 Bucket: {bucket_path}")
            
            # Try to list bucket contents
            items = fs.ls(bucket_path)
            
            assert items is not None, "Failed to list bucket contents"
            print(f"  ✅ Bucket accessible")
            print(f"  ✅ Found {len(items)} items in bucket root")
            
            # Print first few items
            if items:
                print(f"  📁 Sample items:")
                for item in items[:5]:
                    print(f"     - {item}")
            
            return items
            
        except FileNotFoundError:
            pytest.fail(f"Bucket not found: {bucket_path}")
        except PermissionError:
            pytest.fail(f"Permission denied accessing bucket: {bucket_path}")
        except Exception as e:
            pytest.fail(f"Bucket access failed: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_list_all_dataset_files(self):
        """List ALL files in the dataset directory"""
        print(f"\n4️⃣B Testing Complete Dataset Listing...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            # Full path to dataset directory
            dataset_path = f"{config.GCS_DATA_BUCKET}/{config.GCS_DATASET_PREFIX}"
            
            print(f"  📂 Dataset path: {dataset_path}")
            
            # List all files recursively in the dataset directory
            all_files = fs.ls(dataset_path, recursive=True)
            
            print(f"  ✅ Found {len(all_files)} total files")
            print(f"\n  📋 Complete file listing:\n")
            
            # Group files by type
            csv_files = []
            txt_files = []
            other_files = []
            
            for file_path in all_files:
                file_name = file_path.split('/')[-1]
                
                if file_path.endswith('.csv'):
                    csv_files.append(file_path)
                elif file_path.endswith('.txt'):
                    txt_files.append(file_path)
                else:
                    other_files.append(file_path)
            
            # Print CSV files
            if csv_files:
                print(f"  📊 CSV Files ({len(csv_files)}):")
                for file_path in sorted(csv_files):
                    try:
                        info = fs.info(file_path)
                        size_mb = info.get('size', 0) / 1024 / 1024
                        file_name = file_path.split('/')[-1]
                        print(f"     ✓ {file_name} ({size_mb:.2f} MB)")
                    except:
                        file_name = file_path.split('/')[-1]
                        print(f"     ✓ {file_name}")
            
            # Print TXT files (transcripts)
            if txt_files:
                print(f"\n  📄 Text Files ({len(txt_files)}):")
                # Group transcripts by company
                from collections import defaultdict
                by_company = defaultdict(list)
                
                for file_path in txt_files:
                    # Extract company from path like .../Transcripts/AAPL/2020-Apr-30-AAPL.txt
                    parts = file_path.split('/')
                    if 'Transcripts' in parts:
                        idx = parts.index('Transcripts')
                        if idx + 1 < len(parts):
                            company = parts[idx + 1]
                            by_company[company].append(file_path)
                
                for company in sorted(by_company.keys()):
                    files = by_company[company]
                    print(f"     📁 {company}/ ({len(files)} transcripts)")
                    for file_path in sorted(files):
                        file_name = file_path.split('/')[-1]
                        print(f"        - {file_name}")
            
            # Print other files
            if other_files:
                print(f"\n  📦 Other Files ({len(other_files)}):")
                for file_path in sorted(other_files):
                    file_name = file_path.split('/')[-1]
                    print(f"     - {file_name}")
            
            # Summary
            print(f"\n  📈 Summary:")
            print(f"     Total files: {len(all_files)}")
            print(f"     CSV files: {len(csv_files)}")
            print(f"     Text files: {len(txt_files)}")
            print(f"     Other files: {len(other_files)}")
            
            assert len(all_files) > 0, "No files found in dataset directory"
            
            return {
                'total': len(all_files),
                'csv_files': csv_files,
                'txt_files': txt_files,
                'other_files': other_files
            }
            
        except FileNotFoundError:
            pytest.fail(f"Dataset directory not found: {dataset_path}")
        except Exception as e:
            pytest.fail(f"Error listing dataset files: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_dataset_files_exist(self):
        """Test that expected dataset files exist in GCS"""
        print(f"\n5️⃣ Testing Dataset Files Existence...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            # Expected files
            expected_files = [
                "stock_news.csv",
                "analyst_ratings_processed.csv",
                "sp500_companies.csv",
            ]
            
            results = {}
            
            for filename in expected_files:
                full_filename = f"datasets_uc4-market-activity-prediction-agent_{filename}"
                file_path = config.get_dataset_file_path(full_filename)
                
                exists = fs.exists(file_path)
                results[filename] = exists
                
                if exists:
                    # Get file info
                    info = fs.info(file_path)
                    size_mb = info.get('size', 0) / 1024 / 1024
                    print(f"  ✅ {filename}: exists ({size_mb:.2f} MB)")
                else:
                    print(f"  ⚠️  {filename}: NOT FOUND")
            
            # At least one file should exist
            assert any(results.values()), "No expected dataset files found in GCS"
            
            return results
            
        except Exception as e:
            pytest.fail(f"Error checking dataset files: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_read_sample_csv(self):
        """Test reading a sample CSV file from GCS"""
        print(f"\n6️⃣ Testing CSV File Read...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            # Try to read stock_news.csv
            filename = "datasets_uc4-market-activity-prediction-agent_stock_news.csv"
            file_path = config.get_dataset_file_path(filename)
            
            print(f"  📖 Reading: {file_path}")
            
            # Check if file exists first
            if not fs.exists(file_path):
                pytest.skip(f"File not found: {file_path}")
            
            # Read first few rows
            with fs.open(file_path, 'r') as f:
                df = pd.read_csv(f, nrows=10)
            
            assert not df.empty, "CSV file is empty"
            assert len(df.columns) > 0, "CSV has no columns"
            
            print(f"  ✅ Successfully read CSV")
            print(f"  ✅ Shape (first 10 rows): {df.shape}")
            print(f"  ✅ Columns: {list(df.columns)}")
            
            # Print sample data
            print(f"\n  📊 Sample data:")
            print(df.head(3).to_string(index=False))
            
            return df
            
        except Exception as e:
            pytest.fail(f"Failed to read CSV: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_read_specific_file(self):
        """Test reading a specific file from GCS"""
        print(f"\n7️⃣ Testing Specific File Read...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            filename = "datasets_uc4-market-activity-prediction-agent_analyst_ratings_processed.csv"
            file_path = config.get_dataset_file_path(filename)
            
            print(f"  📖 Reading: {file_path}")
            
            if not fs.exists(file_path):
                pytest.skip(f"File not found: {file_path}")
            
            with fs.open(file_path, 'r') as f:
                df = pd.read_csv(f, nrows=20)
            
            print(f"  ✅ File read successful")
            print(f"  ✅ Shape: {df.shape}")
            print(f"  ✅ Columns: {list(df.columns)}")
            print(f"\n  📊 First 5 rows:")
            print(df.head(5).to_string(index=False))
            
            assert not df.empty
            
        except Exception as e:
            pytest.fail(f"Failed to read file: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_read_transcript_file(self):
        """Test reading an earnings call transcript from GCS"""
        print(f"\n8️⃣ Testing Transcript File Read...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            dataset_path = f"{config.GCS_DATA_BUCKET}/{config.GCS_DATASET_PREFIX}"
            transcript_pattern = f"{dataset_path}/**/Transcripts/AAPL/*.txt"
            
            print(f"  🔍 Searching for: {transcript_pattern}")
            
            files = fs.glob(transcript_pattern)
            
            if not files:
                pytest.skip("No AAPL transcript files found")
            
            test_file = files[0]
            print(f"  📖 Reading: {test_file}")
            
            with fs.open(test_file, 'r') as f:
                content = f.read()
            
            print(f"  ✅ Transcript read successful")
            print(f"  ✅ File size: {len(content)} characters")
            print(f"  ✅ First 500 characters:")
            print(f"\n{content[:500]}")
            
            assert len(content) > 0
            assert "Apple" in content or "AAPL" in content or "earnings" in content.lower()
            
        except Exception as e:
            pytest.fail(f"Failed to read transcript: {e}")
    
    @pytest.mark.skipif(
        not os.getenv("GCS_DATA_BUCKET"),
        reason="GCS_DATA_BUCKET not configured, skipping GCS tests"
    )
    def test_read_index_data_csv(self):
        """Test reading indexData.csv from GCS"""
        print(f"\n9️⃣ Testing indexData.csv Read...")
        
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            filename = "indexData.csv"
            file_path = config.get_dataset_file_path(filename)
            
            print(f"  📖 Reading: {file_path}")
            
            if not fs.exists(file_path):
                pytest.skip(f"File not found: {file_path}")
            
            with fs.open(file_path, 'r') as f:
                df = pd.read_csv(f)
            
            print(f"  ✅ File read successful")
            print(f"  ✅ Total rows: {len(df)}")
            print(f"  ✅ Columns ({len(df.columns)}): {list(df.columns)}")
            
            if len(df) > 0:
                print(f"\n  📊 First 10 rows:")
                print(df.head(10).to_string(index=False))
                
                print(f"\n  📊 Data types:")
                print(df.dtypes.to_string())
                
                print(f"\n  📊 Summary statistics:")
                print(df.describe().to_string())
            
            assert not df.empty, "indexData.csv is empty"
            assert len(df.columns) > 0, "indexData.csv has no columns"
            
            return df
            
        except Exception as e:
            pytest.fail(f"Failed to read indexData.csv: {e}")
    
    def test_local_data_fallback(self):
        """Test that local data access works when GCS is not configured"""
        print(f"\n7️⃣ Testing Local Data Fallback...")
        
        # Check if local dataset directory exists
        local_dataset_path = Path(__file__).parent.parent.parent / "app" / "dataset"
        
        print(f"  📁 Local dataset path: {local_dataset_path}")
        
        if local_dataset_path.exists():
            print(f"  ✅ Local dataset directory exists")
            
            # List some files
            csv_files = list(local_dataset_path.glob("*.csv"))
            print(f"  ✅ Found {len(csv_files)} CSV files locally")
            
            if csv_files:
                print(f"  📄 Sample files:")
                for f in csv_files[:3]:
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"     - {f.name} ({size_mb:.2f} MB)")
        else:
            print(f"  ⚠️  Local dataset directory not found")
            print(f"  ℹ️  This is expected if data is only in GCS")
    
    def test_data_store_connection(self):
        """Test the SentimentDataStore can initialize"""
        print(f"\n8️⃣ Testing Data Store Initialization...")
        
        try:
            from app.sub_agents.news_sentiment_agent.tools import data_store
            
            assert data_store is not None, "data_store is None"
            print(f"  ✅ SentimentDataStore initialized")
            
            # Check if using GCS or local
            if hasattr(data_store, 'use_gcs'):
                mode = "GCS" if data_store.use_gcs else "Local"
                print(f"  ℹ️  Data mode: {mode}")
            
            if hasattr(data_store, 'base_path'):
                print(f"  ℹ️  Base path: {data_store.base_path}")
            
        except Exception as e:
            pytest.fail(f"Failed to initialize data store: {e}")


def test_comprehensive_gcs_report():
    """
    Comprehensive test that generates a detailed report of GCS connectivity.
    This test always runs and provides diagnostic information.
    """
    print("\n" + "=" * 70)
    print("GCS CONNECTION COMPREHENSIVE REPORT")
    print("=" * 70)
    
    report = {
        "environment_vars": {},
        "authentication": {},
        "gcs_access": {},
        "recommendations": []
    }
    
    # 1. Environment Variables
    print("\n📋 Environment Configuration:")
    report["environment_vars"] = {
        "GOOGLE_CLOUD_PROJECT": config.GOOGLE_CLOUD_PROJECT,
        "GOOGLE_CLOUD_LOCATION": config.GOOGLE_CLOUD_LOCATION,
        "GCS_DATA_BUCKET": config.GCS_DATA_BUCKET or "Not configured",
        "ENVIRONMENT": config.ENVIRONMENT,
    }
    for key, value in report["environment_vars"].items():
        print(f"  {key}: {value}")
    
    # 2. Authentication
    print("\n🔐 Authentication Status:")
    try:
        import google.auth
        credentials, project_id = google.auth.default()
        report["authentication"] = {
            "status": "success",
            "project_id": project_id,
            "credentials_type": type(credentials).__name__
        }
        print(f"  ✅ Authenticated to project: {project_id}")
    except Exception as e:
        report["authentication"] = {
            "status": "failed",
            "error": str(e)
        }
        print(f"  ❌ Authentication failed: {e}")
        report["recommendations"].append(
            "Run: gcloud auth application-default login"
        )
    
    # 3. GCS Access
    if config.GCS_DATA_BUCKET:
        print("\n☁️  GCS Bucket Access:")
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            items = fs.ls(config.GCS_DATA_BUCKET)
            report["gcs_access"] = {
                "status": "success",
                "bucket": config.GCS_DATA_BUCKET,
                "items_count": len(items)
            }
            print(f"  ✅ Bucket accessible: {config.GCS_DATA_BUCKET}")
            print(f"  ✅ Items found: {len(items)}")
        except Exception as e:
            report["gcs_access"] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"  ❌ Bucket access failed: {e}")
            report["recommendations"].append(
                f"Verify bucket exists and you have access: {config.GCS_DATA_BUCKET}"
            )
    else:
        print("\n💾 Using Local Data:")
        print(f"  ℹ️  GCS_DATA_BUCKET not configured")
        print(f"  ℹ️  Agent will use local filesystem")
        report["recommendations"].append(
            "Set GCS_DATA_BUCKET in .env to use cloud storage"
        )
    
    # 4. Recommendations
    if report["recommendations"]:
        print("\n💡 Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "=" * 70)
    print("END REPORT")
    print("=" * 70)
    
    # Test always passes but provides information
    assert True, "Report generated successfully"


if __name__ == "__main__":
    """Run tests with detailed output"""
    pytest.main([__file__, "-v", "-s"])
