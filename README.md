# WhatsApp RAG Agent

An AI agent that runs a local restaurant's WhatsApp line end to end: takes table reservations and answers menu/policy questions, deciding on its own, message by message, which one applies. Built in 7 days (August 2026) as a real client engagement — not a tutorial project.

## What it does

Before this, any reservation or question depended on someone answering the phone or WhatsApp by hand. This agent covers that first contact automatically, 24/7, without making the customer wait on a human for something as simple as confirming an opening time.

## Architecture

```
Customer (WhatsApp) → Meta WhatsApp Cloud API → n8n → FastAPI → Claude API (tool use)
                                                          ├─→ Voyage AI (RAG)   → FAQ answers
                                                          └─→ Google Sheets     → reservations
```

Seven independent pieces, each with one responsibility. No layer knows how the one two steps away works — FastAPI doesn't know anything about WhatsApp or Meta, it just receives `{numero, texto}` and returns `{respuesta}`. That's what lets the same pattern get reused for a different channel or client without touching the business logic.

## Key technical decisions

**Two tools, not one tool with a `type` field.** Claude has two tools available on every message: `crear_reserva` (extracts reservation data) and `consultar_faq` (empty input schema, used purely as a classification signal). The obvious alternative — one tool with a `tipo: "reserva" | "faq"` field — was rejected because it mixes two different responsibilities into one schema and lets the model second-guess a field it doesn't need to. Whichever tool Claude picks *is* the classification; there's no extra field to get wrong.

**Three-way routing solved with tool absence, not keyword matching.** The naive approach ("no tool_use → it's a FAQ question") breaks the moment a reservation is missing a required field — Claude also doesn't call a tool in that case, so it would incorrectly fall into the FAQ path. The routing checks for tool absence *and* an incomplete-data signal from the conversation state, not just presence/absence of a tool call.

**The system prompt is rebuilt every request, never cached.** Today's date gets computed fresh on each call so relative expressions ("tomorrow", "Saturday") resolve against the real current date — not the date the server happened to boot, which matters for a process that can stay up for days.

**Fail-fast for deploy errors, graceful degradation for runtime errors.** An empty FAQ file or a missing API key stops the server from starting at all, on purpose — better to never come up than to come up broken and fail silently on the first real customer. A transient failure calling Claude or the embeddings API, on the other hand, returns a safe fallback message instead of crashing the request.

**The similarity threshold for FAQ matching (0.45) was measured, not guessed.** A small calibration script ran real and out-of-scope questions through the embedding model; 0.45 sits at the midpoint between the lowest real-match score and the highest false-match score observed.

## Stack

Python · FastAPI · Claude API (tool use) · Voyage AI (embeddings) · n8n · WhatsApp Cloud API · Google Sheets (persistence)

## Status

This is a working prototype (PMV), not a production system yet — and that's a deliberate, documented boundary, not an oversight. What's still missing before it could run unsupervised for a real client: a permanent WhatsApp system token (currently uses a 24h development token), a real server instead of a local machine + tunnel, and persistent conversation state instead of in-memory.

## Running it locally

```bash
git clone https://github.com/nachixxs/whatsapp-rag-agent.git
cd whatsapp-rag-agent
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
# copy .env.example to .env and fill in ANTHROPIC_API_KEY, VOYAGE_API_KEY, WHATSAPP_TOKEN, WHATSAPP_PHONE_ID
uvicorn app.main:app --reload
```

Also requires a published n8n workflow (Webhook → IF → Respond to Webhook) and a Meta app with WhatsApp configured.
