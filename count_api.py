import json
import sys

with open("/tmp/openapi.json") as f:
    data = json.load(f)
    paths = data.get("paths", {})
    
    print(f"TOTAL API PATHS: {len(paths)}")
    print(f"\nAll {len(paths)} paths:")
    
    # Group by prefix
    grouped = {}
    for p in paths.keys():
        prefix = p.split('/')[1] if len(p.split('/')) > 1 else 'root'
        if prefix not in grouped:
            grouped[prefix] = []
        grouped[prefix].append(p)
    
    for prefix in sorted(grouped.keys()):
        print(f"\n/{prefix}/* ({len(grouped[prefix])} routes):")
        for route in sorted(grouped[prefix]):
            methods = list(paths[route].keys())
            print(f"  {route} [{', '.join(m.upper() for m in methods)}]")
