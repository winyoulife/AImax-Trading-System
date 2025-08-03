#!/usr/bin/env python3
import sys
import traceback

try:
    print("Testing individual imports...")
    
    print("1. Testing dynamic_error_handler...")
    from src.core.dynamic_error_handler import DynamicErrorHandler, ErrorRecord, ErrorType, ErrorSeverity
    print("   ✓ dynamic_error_handler imported successfully")
    
    print("2. Testing dynamic_trading_config...")
    from src.core.dynamic_trading_config import DynamicTradingConfig
    print("   ✓ dynamic_trading_config imported successfully")
    
    print("3. Testing recovery manager module...")
    import src.core.dynamic_recovery_manager as recovery_module
    print("   ✓ recovery_manager module imported")
    print("   Available attributes:", [attr for attr in dir(recovery_module) if not attr.startswith('_')])
    
    print("4. Testing class import...")
    from src.core.dynamic_recovery_manager import DynamicRecoveryManager
    print("   ✓ DynamicRecoveryManager imported successfully")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()