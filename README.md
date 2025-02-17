# Text to SQL Application

## Setup

To create the .sql file with the INSERT statements cd to misc and run `python3 generate_insert_statements.py`. This will create the `02-populate-data.sql` file in the db/init folder. This folder is used by the docker compose file to populate the database.

The rest of the setup is just running `docker compose up` and waiting for the services to start. After that, the app will be available at `http://0.0.0.0/`.

## Decisions

1. Use FastAPI for the API
2. Use PostgreSQL for the database
3. Use Docker for containerization
4. Three services, orchestrated by docker compose: a) app: FastAPI API and services, b) db: PostgreSQL, c) ai: Ollama server
5. ollama for the AI endpoint
6. Quantized version of llama-3-sqlcoder-8b-GGUF for the text-to-sql step
7. Quantized version of llama3.2-3b for the rows-to-text step
8. ollama has an OpenAI-compatible API, I'm using that instead of the official one as I can just use the openai python client instead of rolling my own.
9. Endpoint is implemented using SSE. It's more convoluted than just having a POST endpoint to create a task and another GET endpoint to poll it, but it significantly reduces the time to first token. Doing so, we don't have to keep track of the task status, simplifying the architecture significantly. It also allows the frontend to update the UI as soon as the first token is available.
10. I'm limiting the input length to 500 characters. Besides 500 characters being more than enough to make a question, the smaller context window will help reduce the stress on the LLM and will keep the GET requests URLs from being too long (SSE only works for GET endpoints).

## Issues

- We need a way to throttle requests to the LLM, which will most probably be the bottleneck. A Message Queue between the app and the LLM would be the first step. Later on, adding a reverse proxy that load balances requests between multiple instances of ollama in different machines would help if we want to scale horizontally. Once we scale the LLM server, the second bottleneck is most likely the database. Using pgpool or similar might help in that scenario.
- VLLM scales better than ollama. It is designed for concurrent requests. I used ollama as it is easier to install and run.
- Authentication and rate limiting is not implemented.
- The UI is just a PoC.
- There are no tests.
- If deploying for the first time, PostgreSQL and Ollama take some time to start, but the app will start right away. I added some checks to the docker compose file to wait for the services to be ready before starting the app, but they are being ignored for now.
- I did some prompt engineering so that the model is more likely to output the top 10 rows when asked about superlatives (e.g. most, least, highest, lowest, etc.), but most of the time it just outputs just the top row. I'm using quantized versions of the models to run it on my hardware, so they might not be as "smart" as the full versions.
- When asked a question regarding information that is not available in the database, the model will create an irrelevant query. Sometimes, the last model recognizes that the query is irrelevant and says so in the final answer, but a more robust mechanism is needed.
