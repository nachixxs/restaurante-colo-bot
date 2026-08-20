# WhatsApp RAG Agent

An AI agent that runs a local restaurant's WhatsApp line end to end: it takes
table reservations and answers menu and policy questions, deciding on its own,
message by message, which one applies. Built in 7 days (August 2026) as a real
client engagement.

The routing is not a keyword match. Claude gets two tools on every message and
**whichever one it picks _is_ the classification** — there is no `if` looking
for the word "reservar" anywhere in the codebase.

```
Customer (WhatsApp) → Meta Cloud API → n8n ──→ FastAPI → Claude API (tool use)
                                        │                      │
                                        │                      └→ Voyage AI (RAG)
                                        └──────→ Google Sheets
                                                 (reservations)
```

**Stack:** Python 3.11+ · FastAPI · Claude API (tool use) · Voyage AI
(embeddings) · n8n · WhatsApp Cloud API · Google Sheets

Note the shape of that diagram: **FastAPI never touches Google Sheets.** It
returns the reservation as JSON and n8n writes the row. That keeps the API layer
free of any knowledge about where reservations end up — it receives
`{numero, texto}` and returns `{respuesta}`, and would work the same behind a
web widget or a different spreadsheet.

---

## What it does

Three paths, decided in a single Claude call per message:

| The customer writes | The agent |
|---|---|
| "mesa para 4 el sábado a las 21" | calls `crear_reserva`, returns the confirmed booking |
| "tenés wifi?" | calls `consultar_faq`, then answers from the FAQ via RAG |
| "quiero reservar una mesa" | calls no tool: asks for the missing field and waits |

Before this, every reservation and every question depended on someone picking up
the phone. The agent covers that first contact 24/7, without making a customer
wait on a human to find out what time the place closes.

---

## Key technical decisions

**Two tools, not one tool with a `type` field.** The obvious alternative — a
single tool with `tipo: "reserva" | "faq"` — was rejected because it merges two
unrelated responsibilities into one schema and gives the model a field it can
get wrong independently of the decision it already made. With two tools, the
choice and the classification are the same act.

`consultar_faq` takes this to its conclusion: its input schema is **empty on
purpose**. The tool returns nothing and receives nothing. It exists purely as a
signal that the message is a question, and the search runs on the customer's
original text.

```python
"input_schema": {"type": "object", "properties": {}}
```

**Three-way routing solved with tool absence — but tool absence alone isn't
enough.** The naive rule ("no `tool_use` → it's a FAQ question") breaks
immediately, because Claude *also* calls no tool when a reservation is missing a
required field. Both cases look identical at the API level. The router checks
for `crear_reserva` first, then explicitly for `consultar_faq`, and treats
anything left over as the incomplete-reservation path — so a missing field can
never be silently answered as if it were a question about the menu.

**The system prompt is rebuilt on every request, never cached.** Today's date is
computed inside the request handler so that "mañana" and "el sábado" resolve
against the real current date, not the date uvicorn happened to boot. For a
process that stays up for days, a frozen date is a bug that only shows up on day
two.

This came out of a real failure: the `fecha` field was reaching Google Sheets as
the literal string `"mañana"`, which is useless to whoever reads the sheet three
days later. The prompt now instructs the model to resolve relative dates to
`DD/MM/AAAA` — **and to leave the customer's own words alone when the expression
is genuinely ambiguous** rather than invent a date. "El sábado que viene" is
ambiguous even to a person, and a wrong date in the sheet is worse than a
follow-up question.

**Fail fast on deploy errors, degrade gracefully on runtime errors.** These are
different failures and they get different treatment:

| Failure | Behaviour | Why |
|---|---|---|
| Empty FAQ file | server refuses to start | it would come up looking healthy and break on the first real customer |
| Missing / empty API key | server refuses to start | an empty key raises `TypeError`, which is *not* an `anthropic.APIError`, so it escapes the router's `except` and 500s with the bot silent |
| Claude API error | fallback message | transient, and the customer is mid-conversation |
| Voyage embedding error | different fallback message | same, but distinguishable in logs |

The distinction is enforced by the type system, not by convention:
`BusquedaFallidaError` exists specifically so that "no relevant results" (a valid
empty list) can't be confused with "the search never ran" (a real failure that
the caller must handle differently).

**The similarity threshold was measured, not guessed.** `UMBRAL_SIMILITUD = 0.45`
comes from running 8 real questions through the embedding model
(`scripts/check_scores.py`): the worst true match scored **0.5635**, the best
false match scored **0.3278**. The threshold sits at the midpoint. The constant
in the code carries that measurement in a comment, so the next person to touch it
knows what would have to be re-measured.

**Conversation memory is a dict in RAM, and that's a deliberate trade.** Keyed by
phone number, no database. It's what lets a reservation arrive across three
messages ("quiero reservar" → "para 6, el domingo" → "a las 20:30"). The cost is
stated in the limitations below rather than hidden.

One detail worth naming: **the history for a number is cleared the moment a
reservation is confirmed.** Without that, the next booking from the same customer
inherits the previous party size. It also causes a known gap — see below.

---

## How it's built

```
app/
├── main.py            # the only endpoint: POST /webhook, and the 3-way routing
├── claude_client.py   # system prompt, both tool schemas, response parsing
├── conversaciones.py  # in-memory history, keyed by phone number
├── models.py          # the incoming payload (Pydantic)
└── rag/
    ├── embeddings.py  # generates and stores the FAQ vectors
    └── search.py      # cosine similarity, top-k, the measured threshold
scripts/
├── check_scores.py    # the calibration run behind the 0.45 threshold
└── correr_guiones.py  # runs the test scripts against a live server
docs/                  # build log, testing scripts, architecture diagram
n8n/workflow-dia2.json # sanitized snapshot of the workflow
```

Roughly 650 lines of Python. The FAQ path costs **two** Claude calls, not one:
the first classifies and the second answers using only the retrieved fragments,
with a system prompt that forbids answering from memory.

---

## Testing

**18 end-to-end scripts plus 3 degenerate-input cases**, documented with input,
expected behaviour and the actual result obtained — in
[`docs/guiones_testing.md`](docs/guiones_testing.md).

They're written the way customers actually type: lowercase, no accents, typos,
emoji, and information arriving in pieces.

> `che tenes algo pa comer si soy celiaco?`
> `llevo a mi perrita, hay problema?`
> `🍕😋`

The rule for verifying them is the important part: **structurally, never by
whether the reply sounds right.** Exact comparison against the fallback constants
imported from `app.claude_client`, and presence or absence of the `"reserva"` key
in the JSON to know which tool Claude picked. A reply that "reads well" is not a
passing test.

Two details that make the scripts trustworthy rather than decorative:

- Each script uses **its own phone number**, because conversation memory is keyed
  by number — reusing one would leak history between scripts and quietly
  invalidate the result.
- Runs are spaced 20–25s apart on the FAQ path. Voyage's free tier allows 3
  requests per minute, and without the spacing the rate limit surfaces as a
  fallback message in scripts where nothing is actually wrong.

The scripts are also where the known limitations below came from. They are
recorded with their status — corrected, accepted, or open — not quietly dropped.

---

## Known limitations

This is a working prototype, and the boundary is deliberate and documented rather
than discovered later.

**Conversation state is in memory.** A server restart wipes every in-flight
conversation. Fine for the volume of a single restaurant during a build; the
first thing to change for unattended operation.

**A confirmed reservation can't be modified.** Because the history is cleared on
confirmation, "che, en realidad somos 5" arrives with no context and is read as a
brand-new booking. Fixing it properly means a modification tool that can find the
existing row — a feature, not a patch.

**Ambiguous messages route inconsistently.** "Tienen mesa para cumpleaños, somos
re grupo grande?" biases toward the reservation path even though it's a question.
Across runs it goes both ways. Documented as unstable rather than declared fixed,
because a single passing run wouldn't prove anything.

**The FAQ shipped here is sample data.** `data/faq_embeddings.json` holds six
example entries, not the restaurant's real FAQ, which wasn't ready during the
build. Swapping it is a one-line change to the list in `app/rag/embeddings.py`
followed by regenerating the vectors — no other code changes.

**Not production-ready, specifically:** the WhatsApp token is a 24-hour
development token rather than a permanent system-user token; it runs on a local
machine behind a tunnel instead of a real server; and the webhook signature Meta
sends (`X-Hub-Signature-256`) is not verified.

---

## Running it locally

```bash
git clone https://github.com/nachixxs/whatsapp-rag-agent.git
cd whatsapp-rag-agent
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt

cp .env.example .env    # fill in ANTHROPIC_API_KEY and VOYAGE_API_KEY

python -m app.rag.embeddings    # generates data/faq_embeddings.json
uvicorn app.main:app --reload
```

Those are the only two keys the Python side needs. **The WhatsApp token and
phone ID live in n8n, not in `.env`** — FastAPI never talks to Meta.

The API is usable on its own, without WhatsApp or n8n in the picture:

```bash
curl -X POST localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"numero":"549260000001","texto":"mesa para 4 el sábado a las 21"}'
```

For the full path you also need a published n8n workflow (a sanitized export is
in `n8n/`) and a Meta app with WhatsApp configured.

---

## Project docs

| Document | What's in it |
|---|---|
| [`docs/guiones_testing.md`](docs/guiones_testing.md) | the 18 test scripts, their results, and every finding with its status |
| [`docs/explicacion-tecnica-dias-1-2.md`](docs/explicacion-tecnica-dias-1-2.md) | technical walkthrough of the first two days |
| `docs/bitacora-completa-seccion-*.md` | the build log, including what broke |
| `docs/diagrama-arquitectura-secciones-1-3.svg` | architecture diagram |

The build log and the testing document are in Spanish; they were written while
building, not translated afterwards.
