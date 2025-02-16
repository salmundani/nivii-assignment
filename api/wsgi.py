from flask import Flask, request, jsonify
from celery import Celery, Task, shared_task
from celery.result import AsyncResult
import os
from database_manager import DatabaseManager
from ollama_service import OllamaService


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        result_backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        task_ignore_result=False,
    ),
)

celery_app = celery_init_app(app)
db_manager = DatabaseManager()
ai_service = OllamaService()


@shared_task(ignore_result=False)
def process_query(query: str) -> dict:
    try:
        schema_info = db_manager.get_schema_info()
        response = ai_service.text_to_sql(query, schema_info)
        return response
    except Exception as e:
        error_msg = f"Error processing query: {query}"
        raise Exception(error_msg) from e


@app.route("/tasks", methods=["POST"])
def create_task():
    if not request.json or "query" not in request.json:
        return jsonify({"error": "Missing query"}), 400
    task = process_query.delay(request.json["query"])
    return jsonify({"task_id": task.id, "status": "pending"}), 202


@app.route("/tasks/<task_id>", methods=["GET"])
def get_task_status(task_id):
    result = AsyncResult(task_id)

    # TODO this returns pending even if no task with that id exists. In that case, we should return 404
    if not result.ready():
        return jsonify({"task_id": task_id, "status": "pending"})

    if result.successful():
        return jsonify(
            {"task_id": task_id, "status": "completed", "result": result.get()}
        )

    return jsonify(
        {"task_id": task_id, "status": "failed", "error": str(result.result)}
    ), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
