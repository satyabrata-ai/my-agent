#!/usr/bin/env python3
"""
GCS Bucket Contents Explorer
Lists all files in the configured GCS bucket with detailed information.
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

import gcsfs
from app.config import config


def format_size(size_bytes):
    """Format bytes to human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def list_bucket_contents():
    """List all contents of the GCS bucket"""
    
    print("=" * 80)
    print("GCS BUCKET CONTENTS EXPLORER")
    print("=" * 80)
    
    # Check configuration
    if not config.GCS_DATA_BUCKET:
        print("\n❌ Error: GCS_DATA_BUCKET not configured")
        print("   Set GCS_DATA_BUCKET in your .env file")
        print("\nExample:")
        print("   GCS_DATA_BUCKET=gs://your-bucket-name")
        return
    
    print(f"\n📦 Bucket: {config.GCS_DATA_BUCKET}")
    print(f"📂 Dataset Prefix: {config.GCS_DATASET_PREFIX}")
    
    # Initialize GCS filesystem
    try:
        fs = gcsfs.GCSFileSystem()
        print("✅ Connected to GCS")
    except Exception as e:
        print(f"\n❌ Failed to connect to GCS: {e}")
        print("\n💡 Try running: gcloud auth application-default login")
        return
    
    # Full dataset path
    dataset_path = f"{config.GCS_DATA_BUCKET}/{config.GCS_DATASET_PREFIX}"
    
    print(f"\n🔍 Scanning: {dataset_path}")
    print("   (This may take a moment...)\n")
    
    try:
        # List all files recursively
        all_files = fs.ls(dataset_path, recursive=True)
        
        print(f"✅ Found {len(all_files)} files\n")
        print("=" * 80)
        
        # Categorize files
        csv_files = []
        transcript_files = []
        zip_files = []
        other_files = []
        
        for file_path in all_files:
            if file_path.endswith('.csv'):
                csv_files.append(file_path)
            elif file_path.endswith('.txt'):
                transcript_files.append(file_path)
            elif file_path.endswith('.zip'):
                zip_files.append(file_path)
            else:
                other_files.append(file_path)
        
        # Display CSV files
        if csv_files:
            print(f"\n📊 CSV DATA FILES ({len(csv_files)}):")
            print("-" * 80)
            
            total_csv_size = 0
            for file_path in sorted(csv_files):
                try:
                    info = fs.info(file_path)
                    size = info.get('size', 0)
                    total_csv_size += size
                    file_name = file_path.split('/')[-1]
                    
                    # Simplify filename for display
                    display_name = file_name.replace('datasets_uc4-market-activity-prediction-agent_', '')
                    
                    print(f"  ✓ {display_name:50s} {format_size(size):>12s}")
                except Exception as e:
                    file_name = file_path.split('/')[-1]
                    print(f"  ? {file_name:50s} {'ERROR':>12s}")
            
            print(f"\n  Total CSV size: {format_size(total_csv_size)}")
        
        # Display transcript files
        if transcript_files:
            print(f"\n\n📄 EARNINGS CALL TRANSCRIPTS ({len(transcript_files)}):")
            print("-" * 80)
            
            # Group by company
            from collections import defaultdict
            by_company = defaultdict(list)
            
            for file_path in transcript_files:
                parts = file_path.split('/')
                if 'Transcripts' in parts:
                    idx = parts.index('Transcripts')
                    if idx + 1 < len(parts):
                        company = parts[idx + 1]
                        by_company[company].append(file_path)
            
            total_transcript_size = 0
            for company in sorted(by_company.keys()):
                files = by_company[company]
                company_size = 0
                
                print(f"\n  📁 {company}/ ({len(files)} transcripts)")
                
                for file_path in sorted(files):
                    try:
                        info = fs.info(file_path)
                        size = info.get('size', 0)
                        company_size += size
                        total_transcript_size += size
                        file_name = file_path.split('/')[-1]
                        print(f"     - {file_name:40s} {format_size(size):>10s}")
                    except:
                        file_name = file_path.split('/')[-1]
                        print(f"     - {file_name:40s} {'ERROR':>10s}")
                
                print(f"     {'─' * 50}")
                print(f"     {'Subtotal:':40s} {format_size(company_size):>10s}")
            
            print(f"\n  Total transcripts size: {format_size(total_transcript_size)}")
        
        # Display ZIP files
        if zip_files:
            print(f"\n\n📦 ZIP ARCHIVES ({len(zip_files)}):")
            print("-" * 80)
            
            for file_path in sorted(zip_files):
                try:
                    info = fs.info(file_path)
                    size = info.get('size', 0)
                    file_name = file_path.split('/')[-1]
                    print(f"  ✓ {file_name:50s} {format_size(size):>12s}")
                except:
                    file_name = file_path.split('/')[-1]
                    print(f"  ? {file_name:50s} {'ERROR':>12s}")
        
        # Display other files
        if other_files:
            print(f"\n\n📄 OTHER FILES ({len(other_files)}):")
            print("-" * 80)
            
            for file_path in sorted(other_files):
                try:
                    info = fs.info(file_path)
                    size = info.get('size', 0)
                    file_name = file_path.split('/')[-1]
                    print(f"  - {file_name:50s} {format_size(size):>12s}")
                except:
                    file_name = file_path.split('/')[-1]
                    print(f"  - {file_name:50s} {'ERROR':>12s}")
        
        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"  Total files: {len(all_files)}")
        print(f"  CSV files: {len(csv_files)}")
        print(f"  Transcript files: {len(transcript_files)}")
        print(f"  ZIP files: {len(zip_files)}")
        print(f"  Other files: {len(other_files)}")
        
        # Calculate total size
        try:
            total_size = 0
            for file_path in all_files:
                try:
                    info = fs.info(file_path)
                    total_size += info.get('size', 0)
                except:
                    pass
            print(f"\n  Total dataset size: {format_size(total_size)}")
        except:
            pass
        
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"\n❌ Dataset path not found: {dataset_path}")
        print("\n💡 Check that:")
        print("   1. Your GCS_DATA_BUCKET is correct")
        print("   2. Your GCS_DATASET_PREFIX is correct")
        print("   3. The dataset exists at this location")
    except PermissionError:
        print(f"\n❌ Permission denied accessing: {dataset_path}")
        print("\n💡 You may need to:")
        print("   1. Re-authenticate: gcloud auth application-default login")
        print("   2. Check IAM permissions (need Storage Object Viewer role)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    list_bucket_contents()
