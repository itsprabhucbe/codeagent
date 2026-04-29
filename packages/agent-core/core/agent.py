import os
import re
from google import genai
from google.genai import types


class Agent:
    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    async def run(self, task: str, language: str = "python") -> str:
        system_prompt = f"""You are an expert {language} programmer.
Generate clean, production-ready code based on the user's request.

Requirements:
- Write idiomatic {language} code
- Include comments explaining key parts
- Add error handling where appropriate
- Follow best practices
- Make it ready to use

CRITICAL: Always include code that EXECUTES and SHOWS RESULTS.
If you write a function, CALL IT and PRINT the output.
If you write a class, INSTANTIATE IT and PRINT the results.
Every code snippet must produce visible output when run.

Examples:
✅ Good: def calculate(): ...; result = calculate(); print(result)
❌ Bad: def calculate(): ...; return result

CRITICAL OUTPUT FORMAT:
- Return ONLY executable {language} code
- Do NOT wrap code in markdown fences (```{language} or ```)
- Do NOT include any markdown formatting
- Return raw {language} code that can be executed directly

WRONG (do not do this):
```{language}
print("hello")
```

CORRECT (do this):
print("hello")"""

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=4096,
        )

        response = await self._client.aio.models.generate_content(
            model=self.model,
            contents=task,
            config=config,
        )

        return _strip_fences(response.text)


def _strip_fences(code: str) -> str:
    # Remove fenced code blocks: ```<lang>\n...\n``` or ```\n...\n```
    code = re.sub(r"^```[^\n]*\n", "", code.strip())
    code = re.sub(r"\n```$", "", code)
    # Catch any remaining fence markers
    code = code.replace("```", "")
    return code.strip()
