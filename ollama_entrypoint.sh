#!/bin/bash

ollama serve &
# Record Process ID.
pid=$!

sleep 5

ollama pull "${OLLAMA_MODEL_NAME}"

# Wait for Ollama process to finish.
wait $pid
