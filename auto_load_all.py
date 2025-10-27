#!/usr/bin/env python3
"""Auto-load ALL endpoints from mrd directory"""

import os
from pathlib import Path

app_py = Path("/home/ubuntu/mrd/app.py")

with open(app_py, "r", encoding="utf-8") as f:
    content = f.read()

# Find where endpoints are loaded (after imports, before if __name__)
marker = '# ENDPOINT LOADING SECTION'

if marker not in content:
    # Add marker after imports
    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('app = FastAPI('):
            insert_idx = i + 1
            break
    
    if insert_idx == 0:
        print("❌ Could not find app = FastAPI")
        exit(1)
    
    # Insert auto-loader
    auto_load_code = '''
# ENDPOINT LOADING SECTION - AUTO-GENERATED
import importlib
import sys
from pathlib import Path

def auto_load_endpoints():
    """Automatically load ALL *_endpoint.py files"""
    loaded = 0
    base = Path("/home/ubuntu/mrd")
    
    # Scan main dir and core/
    for pattern in ["*_endpoint.py", "core/*_endpoint.py"]:
        for endpoint_file in base.glob(pattern):
            module_name = endpoint_file.stem
            
            # Skip if already imported
            if module_name in sys.modules:
                continue
            
            try:
                # Import from correct location
                if "core/" in str(endpoint_file):
                    module = importlib.import_module(f"core.{module_name}")
                else:
                    module = importlib.import_module(module_name)
                
                # Try to register router
                if hasattr(module, 'router'):
                    app.include_router(module.router)
                    loaded += 1
                    print(f"✓ Loaded {module_name}")
                elif hasattr(module, 'app'):
                    # Some endpoints export app instead
                    app.mount(f"/api/{module_name.replace('_endpoint', '')}", module.app)
                    loaded += 1
                    print(f"✓ Mounted {module_name}")
                    
            except Exception as e:
                print(f"⚠ {module_name}: {e}")
                continue
    
    return loaded

print("\\n" + "="*70)
print("AUTO-LOADING ALL ENDPOINTS")
print("="*70)
total_loaded = auto_load_endpoints()
print(f"\\n🔥 LOADED {total_loaded} ENDPOINTS AUTOMATICALLY 🔥\\n")

'''
    
    lines.insert(insert_idx, auto_load_code)
    
    with open(app_py, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Added auto-loader at line {insert_idx}")
    print("✅ Will load ALL endpoint files automatically")
else:
    print("⚠ Auto-loader already exists")
