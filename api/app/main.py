from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import logging

from app.services.database_manager import DatabaseManager
from app.services.ollama_service import OllamaService

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db_manager = DatabaseManager()
ai_service = OllamaService()


@app.get("/query")
async def query(question: str):
    async def generate():
        sql_query = ""
        # Generate SQL query
        try:
            schema_info = db_manager.get_schema_info()
            async for chunk in ai_service.text_to_sql(question, schema_info):
                logger.info(f"Received chunk: {chunk}")
                sql_query += chunk
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: Error SQL: '{str(e)}'\n\n"
        yield "data: [DONE SQL]\n\n"

        # Execute SQL query
        sql_query = sql_query.rstrip()
        logger.info(f"SQL query: {sql_query}")
        if sql_query:
            try:
                # 50 rows should be enough
                rows = db_manager.execute_query(
                    sql_query, limit_rows=50, read_only=True
                )
                for row in rows:
                    yield f"data: {row}\n\n"
            except Exception as e:
                yield f"data: Error ROWS: '{str(e)}'\n\n"
        else:
            yield "data: No SQL query generated\n\n"
        yield "data: [DONE ROWS]\n\n"

        # Convert SQL query results to natural language
        try:
            async for chunk in ai_service.rows_to_natural_language(
                question, rows, sql_query
            ):
                logger.info(f"Received chunk: {chunk}")
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: Error TEXT: '{str(e)}'\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
