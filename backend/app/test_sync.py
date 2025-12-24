# test_sync.py (put this in your project root)
"""
Test script to manually run permission sync.
Run this from your project root directory.
"""

import sys
import os

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import logging configuration first
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main test function."""
    try:
        logger.info("🚀 Starting permission sync test...")
        
        # Import the sync functions
        from app.core.permission_sync import sync_permissions, get_permission_sync_status
        
        # Step 1: Get current status
        logger.info("📊 Getting current sync status...")
        status_before = get_permission_sync_status()
        
        print("\n" + "="*50)
        print("BEFORE SYNC STATUS:")
        print("="*50)
        print(f"Permissions in code: {status_before['code']['total']}")
        print(f"Active in DB: {status_before['database']['active']}")
        print(f"Deleted in DB: {status_before['database']['deleted']}")
        
        if status_before['drift']['missing_in_db']:
            print(f"\n⚠️  Missing in DB: {len(status_before['drift']['missing_in_db'])} permissions")
            for perm in status_before['drift']['missing_in_db']:
                print(f"   - {perm}")
        
        if status_before['drift']['extra_in_db']:
            print(f"\n⚠️  Extra in DB: {len(status_before['drift']['extra_in_db'])} permissions")
            for perm in status_before['drift']['extra_in_db']:
                print(f"   - {perm}")
        
        # Step 2: Run the sync
        print("\n" + "="*50)
        print("RUNNING SYNC...")
        print("="*50)
        
        sync_result = sync_permissions()
        
        # Step 3: Get status after sync
        status_after = get_permission_sync_status()
        
        print("\n" + "="*50)
        print("SYNC RESULTS:")
        print("="*50)
        print(f"✅ Inserted: {len(sync_result['inserted'])}")
        if sync_result['inserted']:
            for perm in sync_result['inserted']:
                print(f"   - {perm}")
        
        print(f"\n🔄 Reactivated: {len(sync_result['reactivated'])}")
        if sync_result['reactivated']:
            for perm in sync_result['reactivated']:
                print(f"   - {perm}")
        
        print(f"\n🗑️  Soft-deleted: {len(sync_result['soft_deleted'])}")
        if sync_result['soft_deleted']:
            for perm in sync_result['soft_deleted']:
                print(f"   - {perm}")
        
        print(f"\n📋 Unchanged: {len(sync_result['unchanged'])}")
        
        print("\n" + "="*50)
        print("AFTER SYNC STATUS:")
        print("="*50)
        print(f"Permissions in code: {status_after['code']['total']}")
        print(f"Active in DB: {status_after['database']['active']}")
        print(f"Deleted in DB: {status_after['database']['deleted']}")
        print(f"In sync: {'✅ YES' if status_after['summary']['in_sync'] else '❌ NO'}")
        
        # Check if any drift remains
        if status_after['drift']['missing_in_db'] or status_after['drift']['extra_in_db']:
            print("\n⚠️  DRIFT STILL EXISTS:")
            if status_after['drift']['missing_in_db']:
                print(f"   Missing in DB: {status_after['drift']['missing_in_db']}")
            if status_after['drift']['extra_in_db']:
                print(f"   Extra in DB: {status_after['drift']['extra_in_db']}")
        
        logger.info("✅ Permission sync test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Permission sync test failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()