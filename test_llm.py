import aiohttp, asyncio, json, sys
sys.stdout.reconfigure(encoding='utf-8')
async def test():
    prompt = """You are an expert Vietnamese Career Advisor evaluating jobs.
JOB: Data Analyst at MB Bank, Hanoi. Skills needed: SQL, Python, Power BI.
CANDIDATE: Fresh graduate Finance-Banking, knows Python, SQL, Power BI.

Output ONLY valid JSON: {"score": <0-100>, "rationale": "<2 sentences Vietnamese>", "pros": ["<p1>"], "cons": ["<c1>"]}"""
    payload = {"model": "qwen2.5:14b", "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.1, "num_predict": 512}}
    async with aiohttp.ClientSession() as s:
        async with s.post("http://localhost:11434/api/generate", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as r:
            data = await r.json()
            raw = data.get("response", "")
            print(f"Raw ({len(raw)} chars): {raw[:400]}")
            parsed = json.loads(raw)
            print(f"Score: {parsed.get('score')}")
            print(f"Rationale: {parsed.get('rationale')}")
            print(f"Pros: {parsed.get('pros')}")
            print(f"Cons: {parsed.get('cons')}")
asyncio.run(test())
