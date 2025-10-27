# Add chat status endpoint to app.py

with open("/home/ubuntu/mrd/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add status endpoint after health endpoint
status_endpoint = '''

@app.get("/api/chat/assistant/status")
async def chat_status():
    """Chat assistant status endpoint"""
    return {
        "status": "online",
        "model": "gpt-4-turbo-preview",
        "features": ["memory", "research", "learning", "proactive"],
        "endpoints": {
            "chat": "/api/chat/assistant",
            "stream": "/api/chat/assistant/stream"
        }
    }
'''

# Insert after health function
if '@app.get("/health")' in content and '@app.get("/api/chat/assistant/status")' not in content:
    # Find the end of health function
    parts = content.split('async def health():')
    if len(parts) == 2:
        # Find next function definition
        after_health = parts[1]
        next_func = after_health.find('\n@app.')
        if next_func > 0:
            new_content = parts[0] + 'async def health():' + after_health[:next_func] + status_endpoint + after_health[next_func:]
            with open("/home/ubuntu/mrd/app.py", "w", encoding="utf-8") as f:
                f.write(new_content)
            print("✓ Added /api/chat/assistant/status endpoint")
        else:
            print("✗ Could not find next function")
    else:
        print("✗ Could not split by health function")
else:
    if '@app.get("/api/chat/assistant/status")' in content:
        print("⚠ Status endpoint already exists")
    else:
        print("✗ Could not find health endpoint")
