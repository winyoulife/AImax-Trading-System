#!/usr/bin/env python3
import traceback

try:
    print("Reading file...")
    with open('src/core/dynamic_recovery_manager.py', 'r', encoding='utf-8') as f:
        code = f.read()
    
    print("Compiling code...")
    compiled = compile(code, 'src/core/dynamic_recovery_manager.py', 'exec')
    
    print("Executing code...")
    namespace = {}
    exec(compiled, namespace)
    
    print("Available in namespace:", [k for k in namespace.keys() if not k.startswith('_')])
    
    if 'DynamicRecoveryManager' in namespace:
        print("✓ DynamicRecoveryManager found in namespace")
    else:
        print("✗ DynamicRecoveryManager not found in namespace")
        
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()