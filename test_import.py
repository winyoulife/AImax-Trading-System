#!/usr/bin/env python3
try:
    import src.core.dynamic_recovery_manager
    print("Module imported successfully")
    print("Available attributes:", [attr for attr in dir(src.core.dynamic_recovery_manager) if not attr.startswith('_')])
    
    try:
        from src.core.dynamic_recovery_manager import DynamicRecoveryManager
        print("DynamicRecoveryManager imported successfully")
    except ImportError as e:
        print(f"Failed to import DynamicRecoveryManager: {e}")
        
except Exception as e:
    print(f"Failed to import module: {e}")
    import traceback
    traceback.print_exc()