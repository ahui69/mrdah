#!/usr/bin/env python3
# Disable auth requirement for chat endpoint

with open("/home/ubuntu/mrd/core/security_mw.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find guard function and add /api/chat/assistant to bypass list
for i, line in enumerate(lines):
    if "async def guard(" in line or "def guard(" in line:
        # Look for the function body
        # Add bypass for chat endpoint at start of function
        indent_idx = i + 1
        while indent_idx < len(lines) and lines[indent_idx].strip() and not lines[indent_idx].strip().startswith("def "):
            if 'req.url.path' in lines[indent_idx] or 'Request' in lines[indent_idx]:
                # Insert bypass before any checks
                bypass_code = '''    # Bypass auth for chat endpoint
    if req.url.path.startswith("/api/chat/assistant") or req.url.path == "/":
        return
    
'''
                lines.insert(i + 1, bypass_code)
                print(f"✓ Added chat endpoint bypass at line {i+2}")
                break
            indent_idx += 1
        break

with open("/home/ubuntu/mrd/core/security_mw.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("✓ Security bypass added for /api/chat/assistant")
