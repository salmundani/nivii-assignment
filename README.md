# Text to SQL Application

Decisions:

1. Use Flask for the API
2. Use PostgreSQL for the database
3. Use Docker for containerization
4. Three services: a) app: Flask API, b) db: PostgreSQL, c) ai: AI endpoint
5. ollama for the AI endpoint
6. bartowski/llama-3-sqlcoder-8b-GGUF for the AI model
7. App task's status is saved in memory in the same process as the Flask app
8. ollama has an OpenAI-compatible API, I'm using that instead of the official one as I can just use the openai python client instead of rolling my own.

Some obvious issues of the current design:

- Need a way to throttle requests to the LLM, which will most probably be the bottleneck. A Message Queue between the app and the LLM would help.
- VLLM scales better than ollama. It is designed for concurrent requests. I used ollama as it is easier to install and run.
- Saving task status in the process memory won't work if we have multiple instances of the app + load balancer. We need a database for that. Redis might be a good fit.
- Authentication is not implemented.
