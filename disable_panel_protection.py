import asyncio, json, sys
from pathlib import Path
from bscpylgtv import WebOsClient

prof = json.load(open(Path.home() / "Library/Application Support/AuroraVision/av-frameworks/daemon/lg-tv/brightness.json"))

async def main():
    c = await WebOsClient.create(prof["host"], client_key=prof["client_key"], states=[], connect_retry_attempts=1, timeout_connect=15)
    await asyncio.wait_for(c.connect(), 20)
    try:
        info = await c.get_system_info()
        model = info.get("modelName")
        print("model:", model)
        if not prof["model"].startswith(model or "?"):
            sys.exit(f"model mismatch: {model} vs {prof['model']}")
        for algo in ("tpc", "gsr"):
            r = await c.enable_tpc_or_gsr(algo, False)
            print(algo, "->", r)
    finally:
        await c.disconnect()

asyncio.run(main())
