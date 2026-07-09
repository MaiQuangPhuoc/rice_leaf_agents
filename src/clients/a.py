
from openai import OpenAI
from types import SimpleNamespace


class OpenAIAdapter:
    def __init__(self, client, model):
        self.client = client
        self.model = model

    def invoke(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        content = response.choices[0].message.content or ""

        return SimpleNamespace(
            content=content,
            response_metadata={
                "id": response.id,
                "model": response.model,
                "usage": (
                    response.usage.model_dump()
                    if response.usage
                    else {}
                ),
            },
            additional_kwargs={},
        )


class DeepSeekClient:
    def __init__(self):
        self.client = OpenAI(
            api_key="sk-",
            base_url="https://api.deepseek.com",
        )

        # Giữ tương thích với code cũ
        self._llm = OpenAIAdapter(
            client=self.client,
            model="deepseek-v4-flash",
        )