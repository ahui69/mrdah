#!/usr/bin/env python3
with open("/home/ubuntu/mrd/app.py", "r") as f:
    lines = f.readlines()

# Fix health endpoint - add missing decorator
for i, line in enumerate(lines):
    if "async def health():" in line:
        if i > 0 and "@app" not in lines[i-1]:
            lines[i] = '@app.get("/health")\n' + line
            print(f"Fixed health endpoint decorator at line {i+1}")
        break

# Add status endpoint after health
for i, line in enumerate(lines):
    if "async def health():" in line:
        end_idx = i + 1
        while end_idx < len(lines) and not lines[end_idx].startswith(("@app", "def ", "class ")):
            end_idx += 1
        
        status = '''
@app.get("/api/chat/assistant/status")
async def chat_status():
    return {"status": "online", "model": "gpt-4", "features": ["memory", "research"]}

'''
        lines.insert(end_idx, status)
        print(f"Added chat status endpoint at line {end_idx+1}")
        break

with open("/home/ubuntu/mrd/app.py", "w") as f:
    f.writelines(lines)

print("Done!")
