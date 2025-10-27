#!/usr/bin/env python3
# Add 4 missing endpoints to core/app.py

with open("/home/ubuntu/mrd/core/app.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find line after hacker_endpoint (around line 552)
insert_idx = None
for i, line in enumerate(lines):
    if "import hacker_endpoint" in line:
        # Find the end of this try/except block
        j = i + 1
        while j < len(lines) and not lines[j].strip().startswith("# "):
            j += 1
        insert_idx = j
        break

if insert_idx is None:
    print("ERROR: Could not find insertion point")
    exit(1)

new_code = '''
# 24. INTERNAL (internal tools)
try:
    import internal_endpoint
    app.include_router(internal_endpoint.router)
    print("✓ Internal endpoint     /api/internal/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"⚠ Internal: {e}")

# 25. NLP (natural language processing)
try:
    import nlp_endpoint
    app.include_router(nlp_endpoint.router)
    print("✓ NLP endpoint          /api/nlp/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"⚠ NLP: {e}")

# 26. IMAGE (image processing from core)
try:
    from core import image_endpoint
    app.include_router(image_endpoint.router)
    print("✓ Image endpoint        /api/image/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"⚠ Image: {e}")

# 27. LANG (language detection)
try:
    from core import lang_endpoint
    app.include_router(lang_endpoint.router)
    print("✓ Lang endpoint         /api/lang/*")
except Exception as e:
    if not _SUPPRESS_IMPORT_LOGS:
        print(f"⚠ Lang: {e}")

'''

lines.insert(insert_idx, new_code)

with open("/home/ubuntu/mrd/core/app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print(f"✅ Added 4 endpoints at line {insert_idx}")
