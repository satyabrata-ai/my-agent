#!/usr/bin/env python3
"""
Diagnostic script to verify memory persistence configuration.
Run this locally or in Agent Engine to see exact configuration.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 80)
    print("🔍 AGENT MEMORY PERSISTENCE DIAGNOSTIC")
    print("=" * 80)
    
    # Step 1: Check environment variables
    print("\n📋 STEP 1: Environment Variables")
    print("-" * 80)
    
    critical_vars = {
        "GCS_DATA_BUCKET": os.getenv("GCS_DATA_BUCKET"),
        "GCS_MEMORY_PATH": os.getenv("GCS_MEMORY_PATH"),
        "GOOGLE_CLOUD_PROJECT": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT"),
    }
    
    for key, value in critical_vars.items():
        status = "✅" if value else "❌ NOT SET"
        print(f"  {status} {key}: {value if value else '(none)'}")
    
    # Step 2: Load config
    print("\n📦 STEP 2: Loading Config Module")
    print("-" * 80)
    
    try:
        from app.config import config
        print("✅ Config loaded successfully\n")
        
        print("Configuration values:")
        print(f"  GCS_DATA_BUCKET: {config.GCS_DATA_BUCKET}")
        print(f"  GCS_MEMORY_PATH: {config.GCS_MEMORY_PATH}")
        print(f"  ENVIRONMENT: {config.ENVIRONMENT}")
        
        # Determine if persistence is enabled
        if config.GCS_DATA_BUCKET and config.GCS_DATA_BUCKET != "":
            memory_path = f"{config.GCS_DATA_BUCKET}/{config.GCS_MEMORY_PATH}/session_memory.json"
            print(f"\n✅ PERSISTENCE ENABLED")
            print(f"  Memory will be saved to: {memory_path}")
        else:
            print(f"\n❌ PERSISTENCE DISABLED")
            print(f"  GCS_DATA_BUCKET is not set or empty")
            
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Test memory store
    print("\n🧪 STEP 3: Testing PersistentMemoryStore")
    print("-" * 80)
    
    try:
        from app.sub_agents.news_sentiment_agent.tools import PersistentMemoryStore
        
        print("Creating memory store instance...\n")
        memory = PersistentMemoryStore()
        
        print("\n📊 Memory Store Status:")
        print(f"  Filesystem initialized: {'✅ Yes' if memory.fs else '❌ No'}")
        print(f"  Memory file path: {memory.memory_file if memory.memory_file else '❌ Not set'}")
        print(f"  Tickers in memory: {len(memory.memory.get('analyzed_tickers', {}))}")
        print(f"  Cached queries: {len(memory.memory.get('query_cache', {}))}")
        print(f"  Total queries: {memory.memory.get('statistics', {}).get('total_queries', 0)}")
        
        # Test save capability
        if memory.fs and memory.memory_file:
            print("\n🧪 Testing save capability...")
            try:
                # Mark as dirty and try to save
                memory._dirty = True
                memory.save_memory(force=True)
                print("✅ Save test PASSED - memory can be persisted!")
            except Exception as e:
                print(f"❌ Save test FAILED: {e}")
                print("\n💡 Possible issues:")
                print("  1. IAM permissions - service account needs 'Storage Object Admin'")
                print("  2. Bucket doesn't exist")
                print("  3. Network connectivity issues")
        else:
            print("\n❌ Cannot test save - GCS not configured")
            
    except Exception as e:
        print(f"❌ Failed to initialize memory store: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 4: Check GCS bucket
    print("\n🪣 STEP 4: Checking GCS Bucket")
    print("-" * 80)
    
    if config.GCS_DATA_BUCKET:
        try:
            import gcsfs
            fs = gcsfs.GCSFileSystem()
            
            # Try to list bucket
            bucket = config.GCS_DATA_BUCKET.replace("gs://", "")
            print(f"Checking bucket: {bucket}")
            
            try:
                files = fs.ls(bucket, detail=False)
                print(f"✅ Bucket accessible - contains {len(files)} items")
                
                # Check for memory folder
                memory_folder = f"{bucket}/{config.GCS_MEMORY_PATH}"
                if fs.exists(memory_folder):
                    memory_files = fs.ls(memory_folder, detail=False)
                    print(f"✅ Memory folder exists - contains {len(memory_files)} items")
                    for f in memory_files:
                        print(f"  - {f}")
                else:
                    print(f"📝 Memory folder will be created on first save")
                    
            except Exception as e:
                print(f"❌ Cannot access bucket: {e}")
                print("💡 Possible issues:")
                print("  1. Bucket doesn't exist")
                print("  2. IAM permissions missing")
                print("  3. Service account credentials not configured")
                
        except Exception as e:
            print(f"❌ GCS filesystem error: {e}")
    else:
        print("⚠️  GCS_DATA_BUCKET not configured - skipping bucket check")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    issues = []
    if not config.GCS_DATA_BUCKET or config.GCS_DATA_BUCKET == "":
        issues.append("GCS_DATA_BUCKET not set")
    
    if issues:
        print("\n❌ ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        
        print("\n💡 TO FIX:")
        print("  1. Ensure .env file contains:")
        print("     GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706")
        print("\n  2. Redeploy to Agent Engine:")
        print("     make deploy")
        print("\n  3. Check Agent Engine logs for:")
        print("     '✅ Loaded persistent memory from GCS'")
        print("     or")
        print("     '⚠️ WARNING: NO GCS PERSISTENCE CONFIGURED!'")
    else:
        print("\n✅ ALL CHECKS PASSED!")
        print("  Memory persistence is configured correctly.")
        print("\n  Verify in Agent Engine logs:")
        print("  - Look for '💾 Memory persisted to GCS' messages")
        print("  - Check GCS bucket for session_memory.json file")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
