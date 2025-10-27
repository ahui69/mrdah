#!/usr/bin/env python3
import re

with open('core/app.py', 'r') as f:
    lines = f.readlines()

# Usuń wszystkie istniejące AI HACKER bloki
new_lines = []
skip = 0
for i, line in enumerate(lines):
    if skip > 0:
        skip -= 1
        continue
    if '# 23. AI HACKER' in line:
        # Pomiń następne 8 linii
        skip = 8
        continue
    new_lines.append(line)

# Znajdź miejsce po Self-Reflection i dodaj import
final_lines = []
added = False
for i, line in enumerate(new_lines):
    final_lines.append(line)
    if 'Self-Reflection endpoint:' in line and '{e}' in line and not added:
        final_lines.append('\n')
        final_lines.append('# 23. AI HACKER (pentesting & security tools)\n')
        final_lines.append('try:\n')
        final_lines.append('    import hacker_endpoint\n')
        final_lines.append('    app.include_router(hacker_endpoint.router)\n')
        final_lines.append('    if not _SUPPRESS_IMPORT_LOGS:\n')
        final_lines.append('        print("✓ AI Hacker endpoint      /api/hacker/*")\n')
        final_lines.append('except Exception as e:\n')
        final_lines.append('    if not _SUPPRESS_IMPORT_LOGS:\n')
        final_lines.append('        print(f"✗ AI Hacker endpoint: {e}")\n')
        added = True

# Fix line count
with open('core/app.py', 'w') as f:
    f.writelines(final_lines)

# Update count 22 -> 23
with open('core/app.py', 'r') as f:
    content = f.read()
content = content.replace('22 TOTAL', '23 TOTAL')
with open('core/app.py', 'w') as f:
    f.write(content)

print('✓ Fixed app.py - added AI Hacker endpoint')
