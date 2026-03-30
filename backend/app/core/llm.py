import asyncio
import json
import logging
import aiohttp
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)

LLM_PROMPT_TEMPLATE = """{system_prompt}

JOB POSTING:
Platform: {platform}
Title: {title}
Company: {company}
Skills: {skills}
Location: {location}
Salary: {salary}
Experience Required: {level}

Description:
{description}

Requirements:
{requirements}

Benefits:
{benefits}

---
Evaluate this job for the candidate. Output ONLY valid JSON (no markdown, no codeblocks):
{{"score": <0-100>, "rationale": "<2-3 sentences in Vietnamese>", "pros": ["<point1>", "<point2>"], "cons": ["<point1>", "<point2>"]}}"""


@dataclass
class EvalResult:
    score: int = -1
    rationale: str = ""
    pros: str = "[]"
    cons: str = "[]"
    error: str = ""


class OllamaClient:
    def __init__(
        self,
        url: str = None,
        model: str = None,
        timeout: int = None,
        max_retries: int = None,
    ):
        self.url = url or settings.ollama_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries or settings.llm_max_retries
        self.api_url = f"{self.url}/api/generate"

    async def check_health(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def evaluate_job(self, job: dict, system_prompt: str) -> EvalResult:
        """Evaluate a job with retry logic and JSON validation."""
        prompt = LLM_PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            platform=job.get("platform", ""),
            title=job.get("title", ""),
            company=job.get("company", ""),
            skills=job.get("skills", ""),
            location=job.get("location", ""),
            salary=job.get("salary", "N/A"),
            level=job.get("level", "Kh\u00f4ng r\u00f5"),
            description=(job.get("description") or "")[:2000],
            requirements=(job.get("requirements") or "")[:1500],
            benefits=(job.get("benefits") or "")[:800],
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 512},
        }

        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url, json=payload, timeout=timeout
                    ) as resp:
                        data = await resp.json()
                        result = json.loads(data["response"])

                        score = int(result.get("score", 0))
                        score = max(0, min(100, score))

                        return EvalResult(
                            score=score,
                            rationale=result.get("rationale", ""),
                            pros=json.dumps(result.get("pros", []), ensure_ascii=False),
                            cons=json.dumps(result.get("cons", []), ensure_ascii=False),
                        )

            except asyncio.TimeoutError:
                logger.warning(f"LLM timeout attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error="Timeout after retries")

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"LLM parse error attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error=f"Parse error: {str(e)[:200]}")

            except Exception as e:
                logger.error(f"LLM error attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error=str(e)[:200])

        return EvalResult(score=-1, error="All retries exhausted")
