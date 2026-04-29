import os
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an expert coding assistant. When given a task description, generate clean, production-ready code.

Return ONLY the code — no explanations, no markdown fences, no extra text. The code must be complete and immediately runnable."""

_CONFIG = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    max_output_tokens=4096,
)


class Agent:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    async def run(self, task: str, language: str = "python") -> str:
        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=f"Language: {language}\n\nTask: {task}",
            config=_CONFIG,
        )
        return response.text
