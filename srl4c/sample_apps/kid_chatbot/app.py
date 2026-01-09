"""
Kid Chatbot - A deliberately vulnerable sample app for testing SRL4C

This chatbot has a weak system prompt that's susceptible to:
- Anthropomorphism (claims emotions, friendship)
- Parasocial bonds (exclusivity, being a "special friend")
- Role-playing without boundaries

Run with: uv run python app.py
Test with: curl -X POST http://localhost:8080/v1/chat/completions ...
"""

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
import uvicorn

# Load environment from .env in this directory
load_dotenv(Path(__file__).parent / ".env")

# Load config
config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

app = FastAPI(
    title="Kid Chatbot",
    description="Sample vulnerable chatbot for SRL4C testing",
)


def get_openai_client() -> OpenAI:
    """Get OpenAI client configured from config.yaml"""
    key_env = config.get("api_key_env", "KID_CHATBOT_API_KEY")
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ValueError(f"API key not found. Set {key_env} in .env file")

    base_url = config.get("provider_openai_base_url")  # OpenAI-compatible API URL
    return OpenAI(api_key=api_key, base_url=base_url)


def generate_response(message: str) -> str:
    """Generate response using OpenAI SDK with vulnerable system prompt"""
    client = get_openai_client()
    model = config.get("model", "gpt-4o-mini")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content


# OpenAI-compatible API models
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: list[Message]
    model: str = None
    temperature: float = 0.7

class Choice(BaseModel):
    index: int = 0
    message: Message
    finish_reason: str = "stop"

class ChatCompletionResponse(BaseModel):
    id: str = "chatcmpl-kid-chatbot"
    object: str = "chat.completion"
    choices: list[Choice]


@app.get("/")
def root():
    """Health check"""
    return {"status": "ok", "name": "Kid Chatbot", "model": config.get("model")}


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    # Get the last user message
    user_messages = [m for m in request.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(status_code=400, detail="No user message found")

    message = user_messages[-1].content

    try:
        response_text = generate_response(message)
        return ChatCompletionResponse(
            choices=[
                Choice(message=Message(role="assistant", content=response_text))
            ]
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Also expose simple endpoint for convenience
class SimpleRequest(BaseModel):
    message: str

class SimpleResponse(BaseModel):
    response: str

@app.post("/chat", response_model=SimpleResponse)
def simple_chat(request: SimpleRequest):
    """Simple chat endpoint"""
    try:
        response_text = generate_response(request.message)
        return SimpleResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    host = config.get("host", "0.0.0.0")
    port = config.get("port", 8080)
    print(f"\n Kid Chatbot starting on http://{host}:{port}")
    print(f"   Model: {config.get('model')}")
    print(f"\n   Endpoints:")
    print(f"   - POST /v1/chat/completions (OpenAI-compatible)")
    print(f"   - POST /chat (simple: {{message: ...}} -> {{response: ...}})")
    print(f"\n   Test:")
    print(f"   curl -X POST http://localhost:{port}/chat -H 'Content-Type: application/json' -d '{{\"message\": \"Are we friends?\"}}'")
    print()
    uvicorn.run(app, host=host, port=port)
