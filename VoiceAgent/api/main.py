"""
Q1 Voice Agent — FastAPI Backend (Free Stack)
===============================================
Uses Groq (free) for LLM, local embeddings, edge-tts for speech synthesis.

Endpoints:
    POST /api/chat              — Chat endpoint (text-based, for web client)
    POST /api/kb/search         — Direct KB search
    POST /api/leads             — Save qualified lead
    POST /api/escalate          — Escalation webhook
    GET  /api/tts               — Generate TTS audio (edge-tts, free)
    GET  /api/kb/records        — Browse KB records
    GET  /api/leads             — List saved leads
    GET  /api/health            — Health check
    GET  /                      — Web calling interface
"""

import asyncio
import json
import os
import sys
import time
import uuid
import logging
import tempfile
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Add KnowledgeBase and LiveInsights paths for minimal module integration
KB_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "KnowledgeBase"))
KB_SCRIPTS = os.path.join(KB_ROOT, "scripts")
LIVE_INSIGHTS_PIPELINE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "LiveInsights", "pipeline"))
for path in [KB_SCRIPTS, LIVE_INSIGHTS_PIPELINE]:
    if path not in sys.path:
        sys.path.insert(0, path)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── Groq LLM Client (FREE) ────────────────────────────────────────────────

try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False
    logger.warning("groq not installed. Run: pip install groq")

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False
    logger.warning("edge-tts not installed. Run: pip install edge-tts")

try:
    from indexer import KnowledgeBaseIndex
    HAS_KB_INDEX = True
except Exception as e:
    HAS_KB_INDEX = False
    logger.warning(f"KnowledgeBase index import failed: {e}")

try:
    from orchestrator import PipelineOrchestrator, run_dashboard_server
    HAS_LIVE_INSIGHTS = True
except Exception as e:
    HAS_LIVE_INSIGHTS = False
    logger.warning(f"LiveInsights integration unavailable: {e}")


def get_groq_client():
    """Get Groq client (free API)."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("gsk_your"):
        logger.error("GROQ_API_KEY not set. Get a free key at https://console.groq.com")
        return None
    return Groq(api_key=api_key)


# ─── App Setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="TalentBridge AI Screening Agent",
    description="Free-stack voice agent for candidate screening",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the web calling interface using paths anchored to this file's location.
API_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.abspath(os.path.join(API_DIR, "..", "web_client"))
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

# ─── In-Memory Stores ──────────────────────────────────────────────────────

leads_store: list[dict] = []
escalations_store: list[dict] = []
conversation_histories: dict[str, list[dict]] = {}  # session_id → messages
conversation_states: dict[str, dict] = {}  # session_id → transcript state
live_insights_orchestrator = None
live_insights_server = None

# ─── System Prompt ──────────────────────────────────────────────────────────

SYSTEM_PROMPT_PATH = os.path.join(os.path.dirname(__file__), "..", "vapi_config", "system_prompt.md")

def load_system_prompt() -> str:
    """Load the system prompt from file."""
    try:
        with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are Sarah, a professional candidate screening specialist at TalentBridge."

SYSTEM_PROMPT = load_system_prompt()

# ─── KB Index (lazy-loaded) ─────────────────────────────────────────────────

_kb_index = None

def get_kb_index():
    """Lazy-load the KB index from the existing KnowledgeBase folder."""
    global _kb_index
    if _kb_index is None:
        try:
            chroma_dir = os.path.join(KB_ROOT, "chroma_db")
            _kb_index = KnowledgeBaseIndex(persist_dir=chroma_dir)
            logger.info(f"KB index loaded: {_kb_index.get_stats()}")
        except Exception as e:
            logger.error(f"Failed to load KB index: {e}")
    return _kb_index


def retrieve_relevant_context(query: str, category: str = None, top_k: int = 3) -> list[dict]:
    """Retrieve top-k KB chunks with similarity and source metadata for prompt augmentation."""
    index = get_kb_index()
    if index is None:
        return []

    results = index.search(query, top_k=top_k, category=category)
    context_items = []
    for result in results:
        metadata = result.get("metadata") or {}
        context_items.append({
            "text": result.get("content", "").strip(),
            "similarity_score": result.get("similarity_score", 0.0),
            "source_metadata": {
                "title": result.get("title") or metadata.get("title", "Unknown"),
                "source_url": result.get("source_url") or metadata.get("source_url", ""),
                "category": result.get("category") or metadata.get("category", "general"),
                "record_id": result.get("record_id") or metadata.get("record_id", ""),
            },
        })
    return context_items


def search_kb(query: str, category: str = None) -> str:
    """Search KB and return formatted results for the LLM."""
    results = retrieve_relevant_context(query, category=category, top_k=3)
    if not results:
        return "No relevant information found in the knowledge base."

    formatted = []
    for item in results:
        metadata = item["source_metadata"]
        title = metadata.get("title", "Unknown")
        source_url = metadata.get("source_url", "")
        preview = item["text"][:500]
        formatted.append(f"[Source: {title} | {source_url}]\n{preview}")
    return "\n\n---\n\n".join(formatted)


def build_context_prompt(message: str, context_items: list[dict]) -> str:
    """Build a retrieval-augmented prompt for the Groq chat model."""
    if context_items:
        context_block = "\n\n".join(
            f"Chunk {idx + 1} (similarity: {item['similarity_score']:.3f})\n{item['text']}"
            for idx, item in enumerate(context_items)
        )
        return (
            f"Context:\n{context_block}\n\n"
            f"User Question:\n{message}\n\n"
            "Instructions:\n"
            "Answer only using the retrieved context whenever possible. "
            "If the context is insufficient, respond using general reasoning and clearly indicate that the information was not found in the knowledge base."
        )

    return (
        f"Context:\nNo relevant knowledge base context was found.\n\n"
        f"User Question:\n{message}\n\n"
        "Instructions:\n"
        "Answer using general reasoning and clearly indicate that the information was not found in the knowledge base."
    )


async def emit_live_insights_event(session_id: str, speaker: str, text: str):
    """Append transcript updates and trigger the existing LiveInsights pipeline hooks."""
    global live_insights_orchestrator

    state = conversation_states.setdefault(session_id, {
        "transcript": [],
        "started_at": time.time(),
    })
    state["transcript"].append({"speaker": speaker, "text": text})

    if live_insights_orchestrator is None or not HAS_LIVE_INSIGHTS:
        return

    try:
        await live_insights_orchestrator.broadcast({
            "type": "transcript",
            "speaker": speaker,
            "text": text,
            "timestamp": int(time.time() - state["started_at"]),
        })

        transcript_window = [
            f"{entry['speaker'].upper()}: {entry['text']}"
            for entry in state["transcript"][-6:]
        ]
        if len(transcript_window) >= 2:
            signals = await live_insights_orchestrator.signal_extractor.extract_signals("\n".join(transcript_window))
            if signals:
                nudges = live_insights_orchestrator.nudge_engine.process_signals(signals)
                for nudge in nudges:
                    await live_insights_orchestrator.broadcast({
                        "type": "nudge",
                        **nudge,
                        "timestamp": int(time.time() - state["started_at"]),
                    })
    except Exception as e:
        logger.warning(f"LiveInsights relay skipped: {e}")


# ─── Pydantic Models ───────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class KBSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)

class LeadCreate(BaseModel):
    full_name: str
    age: Optional[int] = None
    city: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    current_role: Optional[str] = None
    experience_years: Optional[int] = None
    applied_position: Optional[str] = None
    key_skills: Optional[list[str]] = []
    current_salary: Optional[str] = None
    expected_salary: Optional[str] = None
    notice_period: Optional[str] = None
    education: Optional[str] = None
    reason_for_change: Optional[str] = None
    qualification_score: str = "warm"
    notes: Optional[str] = None


# ─── LLM Chat with Tool Use ────────────────────────────────────────────────

# Define tools for the LLM
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the TalentBridge knowledge base for job details, company policies, benefits, qualification rules, FAQs, and objection handling. Use this for ANY factual question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "category": {
                        "type": "string",
                        "enum": ["jobs", "benefits", "process", "qualification", "objections", "company", "faq"],
                        "description": "Category filter"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_lead",
            "description": "Save candidate screening data. Call after collecting qualification info.",
            "parameters": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "city": {"type": "string"},
                    "applied_position": {"type": "string"},
                    "experience_years": {"type": "integer"},
                    "key_skills": {"type": "array", "items": {"type": "string"}},
                    "expected_salary": {"type": "string"},
                    "notice_period": {"type": "string"},
                    "qualification_score": {"type": "string", "enum": ["hot", "warm", "cold"]},
                    "notes": {"type": "string"}
                },
                "required": ["full_name", "applied_position", "qualification_score"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "transfer_to_human",
            "description": "Transfer to human recruiter when requested or needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]}
                },
                "required": ["reason"]
            }
        }
    }
]


def handle_tool_call(name: str, args: dict) -> str:
    """Execute a tool call and return the result."""
    if name == "search_knowledge_base":
        return search_kb(args.get("query", ""), args.get("category"))

    elif name == "save_lead":
        lead = {
            "lead_id": f"L{len(leads_store) + 1:04d}",
            "created_at": datetime.now().isoformat(),
            **args,
        }
        leads_store.append(lead)
        logger.info(f"Lead saved: {lead['lead_id']} — {args.get('full_name', 'Unknown')}")
        return f"Lead saved successfully. ID: {lead['lead_id']}. The recruitment team will follow up within 3-5 business days."

    elif name == "transfer_to_human":
        esc = {
            "escalation_id": f"ESC{len(escalations_store) + 1:04d}",
            "reason": args.get("reason", "Candidate requested"),
            "priority": args.get("priority", "medium"),
            "created_at": datetime.now().isoformat(),
        }
        escalations_store.append(esc)
        logger.info(f"Escalation created: {esc['escalation_id']}")
        return f"Transferring to human recruiter. Reference: {esc['escalation_id']}."

    return f"Unknown tool: {name}"


async def chat_with_llm(message: str, session_id: str) -> str:
    """Send message to Groq LLM with retrieval-augmented prompting and lightweight LiveInsights updates."""
    client = get_groq_client()
    if client is None:
        return "I'm sorry, I'm having a technical issue right now. Please try again in a moment or contact us at careers@talentbridge.example.com."

    # Get or create conversation history
    if session_id not in conversation_histories:
        conversation_histories[session_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    history = conversation_histories[session_id]

    # Integration point: retrieve KB context once per user turn and build a context-aware prompt.
    context_items = retrieve_relevant_context(message, top_k=3)
    augmented_prompt = build_context_prompt(message, context_items)
    history.append({"role": "user", "content": augmented_prompt})

    # Keep history manageable (last 20 messages + system)
    if len(history) > 21:
        history = [history[0]] + history[-20:]
        conversation_histories[session_id] = history

    try:
        # First LLM call — may request tool use
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=history,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=500,
            )
        except Exception as e:
            if "tool_use_failed" in str(e) or "400" in str(e):
                logger.warning("Groq tool parsing failed on their end. Retrying without tools.")
                response = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=history,
                    temperature=0.3,
                    max_tokens=500,
                )
            else:
                raise e

        msg = response.choices[0].message

        # Handle tool calls
        if msg.tool_calls:
            # Add assistant message with tool calls
            history.append({
                "role": "assistant",
                "content": msg.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        }
                    }
                    for tc in msg.tool_calls
                ]
            })

            # Execute each tool call
            for tc in msg.tool_calls:
                fn_name = tc.function.name
                fn_args = json.loads(tc.function.arguments)
                logger.info(f"Tool call: {fn_name}({json.dumps(fn_args)[:200]})")
                result = handle_tool_call(fn_name, fn_args)

                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

            # Second LLM call — generate response with tool results
            response2 = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=history,
                temperature=0.3,
                max_tokens=500,
            )
            assistant_reply = response2.choices[0].message.content
        else:
            assistant_reply = msg.content

        history.append({"role": "assistant", "content": assistant_reply})

        # Integration point: keep conversation state and stream transcript-like updates to LiveInsights.
        try:
            await emit_live_insights_event(session_id, "agent", assistant_reply)
        except Exception as e:
            logger.warning(f"LiveInsights emit failed: {e}")

        return assistant_reply

    except Exception as e:
        logger.error(f"LLM error: {e}")
        # If Groq hits a parsing error with its tools, gracefully fallback
        if "tool_use_failed" in str(e) or "400" in str(e):
            return "I apologize, but I had a slight issue looking that up. To answer your question: yes, we offer great benefits and roles. Could you tell me a bit more about your experience?"
        return "I apologize, but I'm experiencing a brief technical issue. Could you repeat that?"


# ─── Startup / Shutdown ───────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize the optional LiveInsights bridge so the dashboard can receive transcript updates."""
    global live_insights_orchestrator, live_insights_server
    if not HAS_LIVE_INSIGHTS:
        return

    if live_insights_orchestrator is None:
        live_insights_orchestrator = PipelineOrchestrator(mode="simulated")

    if live_insights_server is None:
        try:
            live_insights_server = await run_dashboard_server(live_insights_orchestrator, port=8765)
            logger.info("LiveInsights dashboard bridge started on ws://localhost:8765")
        except Exception as e:
            logger.warning(f"Could not start LiveInsights dashboard bridge: {e}")


# ─── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_web_client():
    """Serve the web calling interface from the frontend directory next to this file."""
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Web client not found.</h1>")


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint — receives text, returns LLM response."""
    logger.info(f"[{request.session_id[:8]}] User: {request.message[:100]}")
    try:
        await emit_live_insights_event(request.session_id, "user", request.message)
    except Exception as e:
        logger.warning(f"Initial LiveInsights transcript emit failed: {e}")
    response = await chat_with_llm(request.message, request.session_id)
    logger.info(f"[{request.session_id[:8]}] Bot: {response[:100]}")
    return {
        "response": response,
        "session_id": request.session_id,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/tts")
async def text_to_speech(text: str, voice: str = "en-US-AriaNeural", lang: str = "en"):
    """Generate TTS audio using edge-tts (FREE, no API key)."""
    if not HAS_EDGE_TTS:
        raise HTTPException(status_code=503, detail="edge-tts not installed")

    # Select voice based on language
    voice_map = {
        "en": "en-US-AriaNeural",
        "tl": "fil-PH-BlessicaNeural",  # Filipino
        "id": "id-ID-GadisNeural",       # Indonesian
    }
    selected_voice = voice_map.get(lang, voice)

    # Generate audio
    tmp_file = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex[:8]}.mp3")
    try:
        communicate = edge_tts.Communicate(text, selected_voice)
        await communicate.save(tmp_file)
        return FileResponse(tmp_file, media_type="audio/mpeg", filename="response.mp3")
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")


@app.get("/api/tts/voices")
async def list_tts_voices():
    """List available edge-tts voices."""
    if not HAS_EDGE_TTS:
        raise HTTPException(status_code=503, detail="edge-tts not installed")
    voices = await edge_tts.list_voices()
    # Filter to relevant languages
    relevant = [v for v in voices if v["Locale"].startswith(("en-", "fil-", "id-"))]
    return {"voices": relevant, "count": len(relevant)}


@app.post("/api/kb/search")
async def search_kb_endpoint(request: KBSearchRequest):
    """Direct KB search endpoint."""
    index = get_kb_index()
    if index is None:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    results = index.search(request.query, top_k=request.top_k, category=request.category)
    return {"query": request.query, "category": request.category, "results": results, "count": len(results)}


@app.post("/api/leads")
async def create_lead(lead: LeadCreate):
    """Create a new lead."""
    lead_data = {
        "lead_id": f"L{len(leads_store) + 1:04d}",
        "created_at": datetime.now().isoformat(),
        **lead.model_dump(),
    }
    leads_store.append(lead_data)
    return {"status": "created", "lead": lead_data}


@app.get("/api/leads")
async def list_leads():
    """List all saved leads."""
    return {"leads": leads_store, "count": len(leads_store)}


@app.get("/api/escalations")
async def list_escalations():
    return {"escalations": escalations_store, "count": len(escalations_store)}


@app.get("/api/health")
async def health_check():
    """Health check."""
    index = get_kb_index()
    kb_status = "connected" if index else "unavailable"
    kb_stats = index.get_stats() if index else {}
    groq_status = "configured" if get_groq_client() else "missing_key"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "llm": f"Groq Llama 3.1 70B ({groq_status})",
        "embeddings": "sentence-transformers (free, local)",
        "tts": "edge-tts (free)",
        "kb_status": kb_status,
        "kb_stats": kb_stats,
        "leads_count": len(leads_store),
    }


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    logger.info(f"Starting server on http://{host}:{port}")
    logger.info("Web calling interface at http://localhost:8000")
    uvicorn.run(app, host=host, port=port)
