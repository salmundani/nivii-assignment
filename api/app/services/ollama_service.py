from openai import AsyncOpenAI
import os


class OllamaService:
    def __init__(self):
        self.async_client = AsyncOpenAI(
            base_url=os.getenv("OLLAMA_HOST") + "/v1",
            api_key="ollama",
        )
        self.sql_model_name = os.getenv("OLLAMA_SQL_MODEL_NAME")
        self.model_name = os.getenv("OLLAMA_MODEL_NAME")

    async def text_to_sql(self, question, schema):
        # TODO this is the suggested prompt and temperature for llama-3-sqlcoder-8b, might not be the best for other models
        user_prompt = f"""
            Generate a SQL query to answer this question: `{question}`
            Use PostgreSQL syntax. Unless specified, prefer selecting more descriptive columns instead of serial identifiers when possible.

            DDL statements:
            {schema}
        """
        assistant_prompt = f"""
            The following SQL query best answers the question `{question}`:
            ```sql
        """
        stream = await self.async_client.chat.completions.create(
            model=self.sql_model_name,
            temperature=0.0,
            stop=[
                "<|end_of_text|>"
            ],  # model doesn't seem to work that well with ollama, we need this or it will output gibberish
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_prompt},
            ],
            stream=True,
        )
        async with stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
    
    async def rows_to_natural_language(self, question, rows, sql_query):
        system_prompt = """
            You are a helpful assistant that can convert SQL query results into natural language.
            You are given a question related to the contents of the database, its generated SQL query, and its row results, and you need to convert the results into a natural language response.
            Rows are formatted as a comma-separated list of values, with the first row being the column names and the following rows being the data.
            Only output the specified natural language response, no other text.
        """
        user_prompt = f"""
            The following question was asked: `{question}`.
            
            The model generated the following SQL query:
            ```sql
            {sql_query}
            ```

            After running the query, the following rows were returned:
            ```
            {rows}
            ```
        """
        stream = await self.async_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
        )
        async with stream:
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
