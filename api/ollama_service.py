from openai import OpenAI
import os


class OllamaService:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("OLLAMA_HOST") + "/v1",
            api_key="ollama",
        )
        self.model_name = os.getenv("OLLAMA_MODEL_NAME")

    # TODO add streaming support if we are implementing UI
    def text_to_sql(self, query, schema):
        # TODO this is the suggested prompt and temperature for llama-3-sqlcoder-8b, might not be the best for other models
        user_prompt = f"""
        Generate a SQL query to answer this question: `{query}`
        Use PostgreSQL syntax.

        DDL statements:
        {schema}
        """
        assistant_prompt = f"""
        The following SQL query best answers the question `{query}`:
        ```sql
        """
        return (
            self.client.chat.completions.create(
                model=self.model_name,
                temperature=0.0,
                stop=[
                    "<|end_of_text|>"
                ],  # model doesn't seem to work that well with ollama, we need this or it will output gibberish
                messages=[
                    {"role": "user", "content": user_prompt},
                    {"role": "assistant", "content": assistant_prompt},
                ],
            )
            .choices[0]
            .message.content
        )
