import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage

from database import get_db, init_db
from models import Conversation
from agent.graph import agent_app


# ── Pydantic schemas ─────────────────────────────────────────────────

class MessageRequest(BaseModel):
    """Request body for sending a guest message."""
    message: str


class MessageResponse(BaseModel):
    """Response body after the agent processes a message."""
    response: str
    escalated: bool


class ChatMessage(BaseModel):
    """A single message in conversation history."""
    role: str
    content: str
    timestamp: str


class HistoryResponse(BaseModel):
    """Response body for conversation history."""
    conversation_id: str
    messages: list[ChatMessage]


# ── App lifecycle ────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="StayEase AI Agent",
    description="AI-powered booking assistant for short-term accommodation in Bangladesh.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Endpoints ────────────────────────────────────────────────────────

@app.post(
    "/api/chat/{conversation_id}/message",
    response_model=MessageResponse,
    summary="Send a guest message",
)
async def send_message(
    conversation_id: uuid.UUID,
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """
    Send a guest message to the StayEase AI agent.
    The agent will classify the intent and respond accordingly.
    """
    # Load or create conversation
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        conversation = Conversation(id=conversation_id, state={"messages": []})
        db.add(conversation)

    # Build message list from stored state
    stored_messages: list[dict[str, Any]] = conversation.state.get("messages", [])

    # Invoke the LangGraph agent
    agent_input = {
        "messages": [HumanMessage(content=request.message)],
        "escalate": False,
    }
    agent_output = await agent_app.ainvoke(agent_input)

    # Extract the final assistant response
    response_messages = agent_output.get("messages", [])
    final_message = response_messages[-1] if response_messages else None
    response_text = final_message.content if final_message else "I'm sorry, something went wrong."
    escalated = agent_output.get("escalate", False)

    # Persist updated conversation state
    conversation.state = {"messages": stored_messages + [
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": response_text},
    ]}
    await db.commit()

    return MessageResponse(response=response_text, escalated=escalated)


@app.get(
    "/api/chat/{conversation_id}/history",
    response_model=HistoryResponse,
    summary="Get conversation history",
)
async def get_history(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> HistoryResponse:
    """
    Retrieve the full conversation history for a given session.
    """
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    stored_messages: list[dict[str, Any]] = conversation.state.get("messages", [])

    chat_messages = [
        ChatMessage(
            role=msg.get("role", "unknown"),
            content=msg.get("content", ""),
            timestamp=msg.get("timestamp", conversation.updated_at.isoformat()),
        )
        for msg in stored_messages
    ]

    return HistoryResponse(
        conversation_id=str(conversation_id),
        messages=chat_messages,
    )
