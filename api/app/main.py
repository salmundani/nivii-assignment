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


def error_event(error_message: str):
    return f"event: error\ndata: {error_message}\n\n"


def done_event(event_type: str):
    return f"event: done\ndata: {event_type}\n\n"


def data_event(data: str):
    return f"data: {data}\n\n"


@app.get("/query")
async def query(question: str):
    async def generate():
        # parameter validation
        if question.strip() == "":
            yield error_event("Question cannot be empty")
        if len(question) > 500:
            yield error_event("Question cannot be longer than 500 characters")
        sql_query = ""

        # Generate SQL query
        try:
            schema_info = db_manager.get_schema_info()
            async for chunk in ai_service.text_to_sql(question, schema_info):
                logger.info(f"Received chunk: {chunk}")
                sql_query += chunk
                yield data_event(chunk)
        except Exception as e:
            yield error_event(
                f"There was an error generating the SQL query: '{str(e)}'"
            )
        yield done_event("SQL")

        # Execute SQL query
        sql_query = sql_query.rstrip()
        logger.info(f"SQL query: {sql_query}")
        if sql_query:
            try:
                # 50 rows should be more than enough
                rows = db_manager.execute_query(
                    sql_query, limit_rows=50, read_only=True
                )
                for row in rows:
                    yield data_event(row)
            except Exception as e:
                yield error_event(f"There was an error fetching the rows: '{str(e)}'")
        else:
            yield data_event("No SQL query generated")
        yield done_event("ROWS")

        # Convert SQL query results to natural language
        try:
            async for chunk in ai_service.rows_to_natural_language(
                question, rows, sql_query
            ):
                logger.info(f"Received chunk: {chunk}")
                yield data_event(chunk)
        except Exception as e:
            yield error_event(
                f"There was an error converting the rows to natural language: '{str(e)}'"
            )
        yield done_event("ALL")

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
