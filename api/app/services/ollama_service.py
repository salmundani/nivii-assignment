from openai import OpenAI, AsyncOpenAI
import os

# TODO this is the suggested prompt and temperature for llama-3-sqlcoder-8b, might not be the best for other models
USER_PROMPT = """
    Generate a SQL query to answer this question: `%s`
    Use PostgreSQL syntax.

    DDL statements:
    %s
    """

ASSISTANT_PROMPT = """
    The following SQL query best answers the question `%s`:
    ```sql
    """
TEMPERATURE = 0.0


class OllamaService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OLLAMA_HOST") + "/v1",
            api_key="ollama",
        )
        self.async_client = AsyncOpenAI(
            base_url=os.getenv("OLLAMA_HOST") + "/v1",
            api_key="ollama",
        )
        self.model_name = os.getenv("OLLAMA_MODEL_NAME")

    def text_to_sql(self, query, schema):
        return (
            self.client.chat.completions.create(
                model=self.model_name,
                temperature=TEMPERATURE,
                stop=[
                    "<|end_of_text|>"
                ],  # model doesn't seem to work that well with ollama, we need this or it will output gibberish
                messages=[
                    {"role": "user", "content": USER_PROMPT % (query, schema)},
                    {"role": "assistant", "content": ASSISTANT_PROMPT % query},
                ],
            )
            .choices[0]
            .message.content
        )

    async def stream_text_to_sql(self, query, schema):
        stream = await self.async_client.chat.completions.create(
            model=self.model_name,
            temperature=TEMPERATURE,
            stop=[
                "<|end_of_text|>"
            ],  # model doesn't seem to work that well with ollama, we need this or it will output gibberish
            messages=[
                {"role": "user", "content": USER_PROMPT % (query, schema)},
                {"role": "assistant", "content": ASSISTANT_PROMPT % query},
            ],
            stream=True,
        )
        async with stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
