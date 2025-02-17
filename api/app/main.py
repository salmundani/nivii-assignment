from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uuid
from typing import Dict
import logging
import asyncio

from app.services.database_manager import DatabaseManager
from app.services.ollama_service import OllamaService

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO use Redis for task storage
# In-memory task storage
tasks: Dict[str, dict] = {}

db_manager = DatabaseManager()
ai_service = OllamaService()


class Query(BaseModel):
    query: str


@app.post("/tasks")
async def create_task(query: Query):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "result": None}

    # Create background task
    asyncio.create_task(process_query(task_id, query.query))

    return {"task_id": task_id, "status": "pending"}


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/stream")
async def stream_query(query: str):
    async def generate():
        try:
            schema_info = db_manager.get_schema_info()
            async for chunk in ai_service.stream_text_to_sql(query, schema_info):
                logger.info(f"Received chunk: {chunk}")
                yield f"data: {chunk}\n\n"

        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
    )


async def process_query(task_id: str, query: str):
    try:
        schema_info = db_manager.get_schema_info()
        response = ai_service.text_to_sql(query, schema_info)

        tasks[task_id] = {"status": "completed", "result": response}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}


app.mount("/", StaticFiles(directory="app/static", html=True), name="static")
