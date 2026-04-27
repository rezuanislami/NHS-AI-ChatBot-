# NHS Scotland Careers — AI Chat Assistant

A retrieval-augmented chat assistant for the NHS Scotland Careers website.
The user-facing widget answers questions about NHS Scotland career paths,
entry requirements, salaries, applications and training, using only
content scraped from `careers.nhs.scot`.

This project was built as a Napier University assignment.

---

## Project status (April 2026)

| Feature                                  | Status                                                |
| ---------------------------------------- | ----------------------------------------------------- |
| Static frontend (chat widget + modal)    | Working                                               |
| FastAPI backend (`/chat`)                | Working                                               |
| RAG over scraped NHS Scotland Careers    | Working (1k+ chunks)                                  |
| Multi-turn conversation memory           | Working (in-memory, 30-min TTL)                       |
| Off-topic redirect / NHS-only answers    | Working (enforced by system prompt)                   |
| FAQ themes file (`faq_themes.json`)      | Working (only file written to disk)                   |
| JIRA support-ticket integration          | Working — needs `JIRA_*` env vars (see below)         |
| Real JIRA file attachments               | Not yet — see Roadmap                                 |
| Admin endpoint authentication            | Not yet — see Roadmap                                 |

### Quickstart

If you just cloned the repo and want to see it run:

```bash
# 1. Python deps
python -m venv .venv
.venv\Scripts\activate                      # Windows
# source .venv/bin/activate                  # macOS / Linux
pip install -r requirements.txt

# 2. Local LLM
ollama pull llama3
ollama pull nomic-embed-text

# 3. Backend (terminal 1)
uvicorn app.main:app --reload --port 8000

# 4. Frontend (terminal 2)
python -m http.server 5500
```

Then visit <http://localhost:5500>. The chat works without any
configuration. JIRA ticket submission needs the env vars in
[JIRA support-ticket setup](#jira-support-ticket-setup); without them,
the chat still works and the ticket form shows a clear "JIRA not
configured" error.

---

## Table of contents

1. [What's in the box](#whats-in-the-box)
2. [Architecture at a glance](#architecture-at-a-glance)
3. [Data and privacy](#data-and-privacy)
4. [FAQ themes file](#faq-themes-file)
5. [Local setup](#local-setup)
6. [Running the project](#running-the-project)
7. [Project layout](#project-layout)
8. [API reference](#api-reference)
9. [Regenerating the knowledge base](#regenerating-the-knowledge-base)
10. [JIRA support-ticket setup](#jira-support-ticket-setup)
11. [Embedding the widget into the live NHS Scotland Careers site](#embedding-the-widget-into-the-live-nhs-scotland-careers-site)
12. [Roadmap / TODO](#roadmap--todo)

---

## What's in the box

A FastAPI backend (`app/`) that exposes a single `/chat` endpoint. The
endpoint runs RAG (retrieval-augmented generation) on top of a local
[Ollama](https://ollama.com) instance using the `llama3` chat model and
`nomic-embed-text` embedding model.

A small static frontend (`index.html`, `css/`, `js/`) that mimics the
NHS Scotland Careers landing page and embeds a chat widget that talks to
the backend.

A scraper / chunker / embedder pipeline (`app/scraper.py`,
`app/chunker.py`, `generate_embeddings.py`) used to build
`embedded_chunks.json` from the official NHS Scotland Careers website.

A "FAQ themes" generator (`app/services/faq_themes.py`) that clusters
common user questions into themes and writes a single
`app/data/faq_themes.json`. This is the only file the application
writes to disk.

A support-ticket modal in the chat widget that submits to a real JIRA
Cloud project via the `/api/jira-ticket` endpoint. See
[JIRA support-ticket setup](#jira-support-ticket-setup) for the
required configuration.

---

## Architecture at a glance

```
 ┌──────────────┐    POST /chat    ┌──────────────────┐    HTTP    ┌────────────┐
 │  Browser     │ ───────────────► │  FastAPI         │ ─────────► │  Ollama    │
 │  (index.html │                  │  (app/main.py)   │            │  llama3    │
 │   + script.  │ ◄─────────────── │                  │ ◄───────── │  + nomic   │
 │   js)        │   reply + sources│                  │            │            │
 └──────────────┘                  └─────────┬────────┘            └────────────┘
                                             │
                                             │ cosine similarity over
                                             ▼ embedded_chunks.json
                                   ┌──────────────────┐
                                   │  RAG retriever   │
                                   │  (numpy)         │
                                   └──────────────────┘
```

For each user message the backend (a) retrieves the top NHS Scotland
Careers chunks by cosine similarity, (b) injects them into the system
prompt, (c) sends the full conversation history to Ollama, (d) returns
the reply plus the source documents to the browser.

---

## Data and privacy

**Nothing is persisted to disk except `app/data/faq_themes.json`.**

- Conversations are kept in a Python `dict` in the running process and
  expire after 30 minutes of inactivity (see
  `_CONVERSATION_TTL_SECONDS` in `app/models.py`). A server restart
  wipes everything.
- The browser keeps the `conversation_id` in a JavaScript variable for
  the lifetime of the tab. Closing or reloading the tab forgets it.
- No cookies, no `localStorage`, no analytics calls.
- User questions are mirrored into a fixed-size in-memory ring buffer
  (200 entries, see `_QUESTION_BUFFER_SIZE` in `app/models.py`) only so
  the FAQ themes job can spot trends. The buffer is overwritten as new
  questions arrive and is lost on restart.
- The only piece of content that ever touches disk is the clustered
  themes summary in `app/data/faq_themes.json`, and it never contains
  full chat transcripts.

**Information sources.** The chat assistant is constrained by its
system prompt to only use the NHS CONTEXT block (retrieved from
`embedded_chunks.json`) and to recommend
<https://www.careers.nhs.scot> if the answer isn't covered. Off-topic
questions trigger a polite redirect.

---

## FAQ themes file

Location: `app/data/faq_themes.json`

The file is rewritten end-to-end whenever someone hits
`POST /admin/faq-themes/refresh`. Example shape:

```json
{
  "generated_at": "2026-04-27T13:50:00+00:00",
  "buffer_size": 42,
  "themes": [
    {
      "theme": "nurse + training",
      "frequency": 7,
      "top_keywords": ["nurse", "training", "qualifications", "degree", "apply"],
      "example_questions": [
        "how do i become a nurse",
        "what training do nurses need",
        "nursing qualifications scotland"
      ]
    }
  ]
}
```

You can also fetch the current themes without writing anything via
`GET /admin/faq-themes`.

> The `/admin/*` endpoints are intentionally simple and unauthenticated
> for the prototype. In production they should sit behind basic auth or
> be reachable only from an internal network.

---

## Local setup

### Prerequisites

- Python 3.10 or newer (tested with 3.10 / 3.13).
- [Ollama](https://ollama.com/download) installed and running.
- Models pulled once:

  ```bash
  ollama pull llama3
  ollama pull nomic-embed-text
  ```

  Confirm Ollama is up by visiting <http://localhost:11434> — you
  should see `Ollama is running`.

### Install

```bash
git clone https://github.com/<your-org>/NHS-AI-ChatBot.git
cd NHS-AI-ChatBot
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env   # optional, only needed once you wire up JIRA
```

---

## Running the project

You need **two terminals** open, both with the virtualenv activated.

**Terminal 1 — backend API (port 8000):**

```bash
cd <project root>
.venv\Scripts\activate          # or source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

You should see `[RAG] Loaded N chunks` followed by
`Uvicorn running on http://127.0.0.1:8000`.

**Terminal 2 — static frontend (port 5500):**

```bash
cd <project root>
python -m http.server 5500
```

Then open <http://localhost:5500> in your browser. The first reply will
be slow because Ollama loads the model into memory; subsequent replies
are quick.

Quick health check:

```bash
curl http://localhost:8000/healthz
# {"status":"ok"}
```

---

## Project layout

```
NHS-AI-ChatBot/
├── app/
│   ├── main.py              # FastAPI app (chat + admin endpoints)
│   ├── models.py            # In-memory conversation + question buffer
│   ├── schemas.py           # Pydantic request/response models
│   ├── config.py            # Env-driven settings
│   ├── chunker.py           # Splits cleaned pages into RAG chunks
│   ├── scraper.py           # Pulls and cleans careers.nhs.scot pages
│   ├── cleaned_pages/       # Output of scraper.py (committed)
│   ├── chunked_pages/       # Output of chunker.py (committed)
│   ├── data/
│   │   └── faq_themes.json  # The ONLY runtime-written file
│   └── services/
│       ├── ollama_service.py  # RAG + Ollama call
│       ├── faq_themes.py      # Clusters question buffer -> themes
│       ├── rag_engine.py      # Lower-level RAG helper (re-usable)
│       └── security.py        # Lightweight input filter
├── css/style.css
├── js/script.js             # Chat widget + ticket modal
├── index.html               # Demo NHS careers landing page + widget
├── embedded_chunks.json     # Vector store consumed by ollama_service
├── generate_embeddings.py   # Rebuilds embedded_chunks.json via Ollama
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md                # this file
```

---

## API reference

### `POST /chat`

Send a single chat turn.

```jsonc
// request
{
  "message": "How do I become a nurse?",
  "conversation_id": "8f3c..."   // optional; omit on first turn
}

// response
{
  "reply": "To become a registered nurse in NHS Scotland...",
  "sources": [
    { "title": "Nursing", "url": "https://www.careers.nhs.scot/explore-careers/nursing/" }
  ],
  "conversation_id": "8f3c..."
}
```

### `GET /healthz`

Simple liveness check.

### `POST /v1/conversations`

Manually start a new conversation. Rarely needed — `/chat` will create
one for you when `conversation_id` is omitted.

### `GET /admin/faq-themes`

Returns the current in-memory themes without writing to disk.

### `POST /admin/faq-themes/refresh?min_count=2`

Clusters the current question buffer and rewrites
`app/data/faq_themes.json`. `min_count` controls the minimum number of
questions required for a cluster to count as a theme.

### `POST /api/jira-ticket`

Submit the chat-widget support form to JIRA Cloud.

```jsonc
// request
{
  "name": "Pablo Yague",
  "email": "pablo@example.com",
  "issueType": "Bug",
  "priority": "High",
  "subject": "Cannot find midwifery vacancies",
  "description": "Long description here...",
  "source": "NHS Careers Chatbot Frontend",
  "attachment": null
}

// success response (201 from JIRA -> 200 here)
{
  "success": true,
  "ticketKey": "NHS-42",
  "url": "https://your-team.atlassian.net/browse/NHS-42",
  "message": "Ticket created successfully."
}
```

Returns HTTP 503 if JIRA is not configured on the server, or 502 if
JIRA rejected the request. See
[JIRA support-ticket setup](#jira-support-ticket-setup) for setup
instructions.

---

## Regenerating the knowledge base

The chat assistant only knows what is inside `embedded_chunks.json`.
To refresh that knowledge:

1. Run the scraper to pull the latest pages from `careers.nhs.scot`:

   ```bash
   python -m app.scraper
   ```

   This populates `app/cleaned_pages/`.

2. Split the pages into RAG-friendly chunks:

   ```bash
   python -m app.chunker
   ```

   Output goes to `app/chunked_pages/`.

3. Embed the chunks (requires Ollama running with `nomic-embed-text`):

   ```bash
   python generate_embeddings.py
   ```

   This rewrites `embedded_chunks.json` at the project root.

4. Restart `uvicorn` so the new embeddings are picked up.

---

## JIRA support-ticket setup

The "Submit a support ticket" button in the chat widget posts to
`POST /api/jira-ticket`, which forwards the form to a real JIRA Cloud
project. Setup is a one-off:

**1. Create an Atlassian API token.** In your Atlassian account, go to
*Account Settings → Security → API tokens → Create API token*. Give it
a name like `NHS Careers Chatbot` and copy the token immediately —
Atlassian will not show it again.

**2. Note four values you'll need:**

  - Your Atlassian **site URL**, e.g. `https://your-team.atlassian.net`
  - The **email address** on your Atlassian account
  - The **API token** from step 1
  - The **project key** of the JIRA project where tickets should land
    (e.g. `NHS`). You can find this on your JIRA project's URL or
    settings page.

**3. Add them to `.env`** at the project root (copy `.env.example`
first if you haven't already):

```env
JIRA_BASE_URL=https://your-team.atlassian.net
JIRA_EMAIL=you@example.com
JIRA_API_TOKEN=ATATT3xFf...your-token-here
JIRA_PROJECT_KEY=NHS
JIRA_DEFAULT_ISSUE_TYPE=Task
```

`JIRA_DEFAULT_ISSUE_TYPE` should match an issue type that exists in
your project — `Task` works for most projects; `Story` or `Bug` are
also fine.

**4. Restart uvicorn** so the new environment variables are loaded.

**5. Test the endpoint** with curl before clicking the form:

```bash
curl -X POST http://localhost:8000/api/jira-ticket \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "issueType": "Bug",
    "priority": "Medium",
    "subject": "Test ticket from chatbot",
    "description": "This is a test ticket submitted from the local dev environment.",
    "source": "curl"
  }'
```

A success response looks like
`{"success": true, "ticketKey": "NHS-42", "url": "https://.../browse/NHS-42"}`.
Open the URL — the ticket should appear on your JIRA board.

### Behaviour without JIRA configured

If any of the four required `JIRA_*` variables are blank, the endpoint
returns HTTP 503 with a clear message and the frontend displays it in
the modal. The rest of the application (chat, FAQ themes) is
unaffected.

### What is sent to JIRA

The user's name, email, requested category, requested priority,
subject and free-text description are forwarded. The category becomes
a JIRA label so support staff can filter by it. The user's name and
email are appended to the ticket body so support can reply. Attachment
**filenames** are mentioned in the body, but the file bytes themselves
are not uploaded in this version (see [Roadmap](#roadmap--todo)).

### What is NOT sent or stored

Nothing about the ticket is logged on the server. Once `create_jira_ticket`
returns the JIRA key it is sent straight back to the browser and the
backend forgets about it. There is no local copy of the ticket.

---

## Embedding the widget into the live NHS Scotland Careers site

The frontend in this repo is a self-contained demonstration page, but
the moving parts that make the chat work are isolated and can be
dropped into the production site with minimal changes.

**1. Host the backend.** Deploy `app/` (plus `embedded_chunks.json`)
behind any Python WSGI/ASGI host. A typical NHS-friendly setup would
be:

- A container running `uvicorn app.main:app --host 0.0.0.0 --port 8000`,
  fronted by an internal reverse proxy (NGINX / Apache).
- An Ollama instance reachable from the container, or — if local
  hosting is not viable — swap `ollama_service.py` to call a managed
  LLM provider that meets NHS data-handling requirements.
- HTTPS termination at the proxy. The chat client only needs to reach
  the API origin (e.g. `https://chat-api.careers.nhs.scot`).

**2. Tighten CORS.** In `app/main.py`, change
`allow_origins=["*"]` to the production origin(s) of the live site,
e.g. `allow_origins=["https://www.careers.nhs.scot"]`.

**3. Lift the chat widget into the live page.** The widget is just
two pieces:

- The HTML block in `index.html` between
  `<div id="chat-widget">…</div>` and the matching ticket modal
  (`<div id="ticket-modal">`).
- The two stylesheet rules and the single `<script src="js/script.js">`
  reference.

Copy the markup into the live NHS Scotland Careers template, ship
`css/style.css` (or merge the `#chat-widget` rules into the existing
stylesheet), and ship `js/script.js`. At the top of `script.js`,
change:

```js
const API_BASE = 'http://localhost:8000';
```

to the production API origin, e.g.:

```js
const API_BASE = 'https://chat-api.careers.nhs.scot';
```

**4. Authenticate the admin endpoints.** Put `/admin/*` behind basic
auth or restrict the route on the reverse proxy so only the content
team / internal network can read or refresh the FAQ themes file.

**5. Configure JIRA credentials.** The `/api/jira-ticket` endpoint and
its frontend wiring already exist; production just needs a real JIRA
project and the four `JIRA_*` environment variables on the server (see
[JIRA support-ticket setup](#jira-support-ticket-setup)).

**6. Rebuild the knowledge base on a schedule.** Run the
scraper → chunker → embedder pipeline (see
[Regenerating the knowledge base](#regenerating-the-knowledge-base))
on a cron / scheduled task — once a month is enough — so the assistant
stays in sync with the live careers content.

---

## Contributing / pushing changes back

The canonical repository lives at
<https://github.com/rezuanislami/NHS-AI-ChatBot-> on the `main` branch.
If you have write access:

```bash
git clone https://github.com/rezuanislami/NHS-AI-ChatBot-.git
cd NHS-AI-ChatBot-
# ...make changes, follow Quickstart to test...
git add -A
git commit -m "Short description of what you changed"
git push origin main
```

If you do not have write access, fork the repo on GitHub, push to your
fork, then open a pull request back to `main`.

A few hygiene rules:

- Never commit `.env` (it is gitignored). Update `.env.example` instead
  if you add new settings.
- Never commit `.venv/`, `venv/`, or `__pycache__/` (all gitignored).
- `embedded_chunks.json` IS committed — it is the data the bot reads.
  Re-run the scrape → chunk → embed pipeline if NHS Scotland updates
  their site significantly.

---

## Roadmap / TODO

- **Real JIRA file attachments.** The form currently sends only the
  filename. Real upload requires switching the frontend to `FormData`,
  changing the endpoint to accept `UploadFile`, creating the issue
  first, then `POST`ing the file bytes to
  `/rest/api/3/issue/{key}/attachments` with the
  `X-Atlassian-Token: no-check` header.
- **Auth on `/admin/*`.** Basic auth or an internal-only route is
  required before deploying anywhere public.
- **Pin dependency versions.** `requirements.txt` is currently
  unpinned. For reproducibility, pin to known-good versions before any
  production rollout.
- **Optional Markdown rendering** for assistant replies (currently
  rendered as plain paragraphs to keep the dependency footprint and
  XSS surface small).
