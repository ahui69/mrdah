#!/usr/bin/env python3
# Fix Self-Reflection block in app.py

with open('app.py', 'r') as f:
    lines = f.readlines()

# Find and fix the Self-Reflection block
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # If we see Self-Reflection print without except before next try
    if i < len(lines) - 2:
        if 'Self-Reflection endpoint /api/reflection' in line and 'except' not in lines[i+1]:
            # Add except block
            new_lines.append('except Exception as e:\n')
            new_lines.append('    if not _SUPPRESS_IMPORT_LOGS:\n')

with open('app.py', 'w') as f:
    f.writelines(new_lines)

print('✓ Fixed Self-Reflection except block')
