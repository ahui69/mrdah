#!/usr/bin/env python3

import sys

def add_autorouter():
    with open("/home/ubuntu/EHH/core/app.py", "r") as f:
        lines = f.readlines()

    # Znajdź linię z pierwszym endpointem (AUTH)
    for i, line in enumerate(lines):
        if "# 0. AUTH (login/register/JWT)" in line:
            # Wstaw AutoRouter przed AUTH
            autorouter_code = [
                "# 0. FRONTEND AUTOROUTER (intelligent routing)\n",
                "try:\n",
                "    from core import frontend_autorouter\n", 
                "    app.include_router(frontend_autorouter.router)\n",
                "    if not _SUPPRESS_IMPORT_LOGS:\n",
                "        print(\"✓ AutoRouter endpoint     /api/autoroute/*\")\n",
                "except Exception as e:\n",
                "    if not _SUPPRESS_IMPORT_LOGS:\n",
                "        print(f\"✗ AutoRouter endpoint: {e}\")\n",
                "\n"
            ]
            
            # Zmień numerację AUTH na 0.1
            lines[i] = "# 0.1. AUTH (login/register/JWT)\n"
            
            # Wstaw AutoRouter
            lines = lines[:i] + autorouter_code + lines[i:]
            break

    with open("/home/ubuntu/EHH/core/app.py", "w") as f:
        f.writelines(lines)

    print("AutoRouter dodany do core/app.py")

if __name__ == "__main__":
    add_autorouter()