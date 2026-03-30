import aiohttp, asyncio, sys, json
sys.stdout.reconfigure(encoding='utf-8')
async def check():
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get("http://localhost:11434/api/tags", timeout=aiohttp.ClientTimeout(total=3)) as r:
                data = await r.json()
                models = data.get('models', [])
                print(f"Ollama running: {len(models)} models")
                for m in models:
                    size_gb = m.get('size', 0) / 1024 / 1024 / 1024
                    print(f"  {m['name']:40} {size_gb:.1f}GB")
    except Exception as e:
        print(f"Ollama not reachable: {e}")
asyncio.run(check())
