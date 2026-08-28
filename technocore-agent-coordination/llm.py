from __future__ import annotations

import os
import requests


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            return self._fallback(system_prompt, user_prompt)

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            },
            timeout=60,
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]

    def _fallback(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> str:

        return (
            "[DEMO MODE]\n"
            "No LLM API key configured.\n\n"
            f"Agent instruction:\n{system_prompt}\n\n"
            f"Task:\n{user_prompt}\n\n"
            "The workflow can still be executed and "
            "cryptographically verified."
        )