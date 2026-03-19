# -*- coding: utf-8 -*-
"""Test if node table initialization and backfill works"""
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG, BOTNET_CONFIG
from log_processor.db_writer import BotnetDBWriter
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_initialization():
    """Test database initialization for one botnet type"""
    
    # Test with asruex
    botnet_type = 'asruex'
    
    print("=" * 70)
    print(f"Testing initialization for {botnet_type}")
    print("=" * 70)
    
    try:
        # Create writer instance (this should trigger _initialize_database)
        print(f"\nCreating BotnetDBWriter for {botnet_type}...")
        writer = BotnetDBWriter(
            botnet_type=botnet_type,
            db_config=DB_CONFIG,
            batch_size=100,
            use_connection_pool=False,  # Disable pool for testing
            enable_monitoring=False      # Disable monitoring for testing
        )
        
        print(f"\nWriter created successfully!")
        print(f"Table created: {writer.table_created}")
        print(f"Fields checked: {writer.fields_checked}")
        
        print("\n" + "=" * 70)
        print("Initialization test completed!")
        print("=" * 70)
        
        # Check if fields were added
        print("\nNow run: python check_data_in_fields.py")
        print("to verify if data was backfilled")
        
    except Exception as e:
        print(f"\nError during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_initialization()
