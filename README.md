# Campus Customs: Shop + AI Shopping Assistant (MGT 409, HW 4)

A quiet-luxury storefront for officially licensed Yale apparel, with a PydanticAI shopping assistant that answers price and stock questions from a local SQLite database, updates the page with search results, remembers logged-in customers, and logs every agent loop to an audit trail.

- **Frontend:** React 19 + Vite + TypeScript (`frontend/`)
- **Backend:** FastAPI + PydanticAI agent (`backend/`), model `gpt-5.6-luna` via Portkey
- **Docs:** `output/`, including the harness, design notes, usability notes, a live app check, and the audit trail

## Project layout

```
hw4/
├── AI_prompts.md           # log of the prompts used to build this project
├── requirements.txt        # backend Python dependencies
├── .env.example            # copy to .env and add your key
├── .gitignore
├── README.md
├── frontend/               # Vite React TypeScript app
├── backend/
│   ├── main.py             # FastAPI app: run with `uvicorn main:app --reload --port 8000`
│   ├── agent.py            # agent wiring: prompt file, Portkey model, instructions, validator, audit hook
│   ├── models.py           # Pydantic / PydanticAI structured types
│   ├── tools.py            # tools the agent calls (catalogue, stock, snapshot, memory)
│   ├── prompts/prompt.md   # system prompt: voice, tool rules, safety rules
│   ├── auth.py             # password hashing, sessions, login rate limit
│   ├── memory.py           # saved chat history + customer profile
│   └── audit.py            # append-only audit trail writer
└── output/
    ├── harness.md          # full engineering reference (models, tools, safety, specs)
    ├── design.md
    ├── usability.md
    ├── app_check.html      # open with a double-click
    ├── app_check_images/   # screenshots linked from app_check.html
    └── audit_trail.json    # append-only log of agent loops
```

The agent is the four core backend files: `main.py`, `agent.py`, `models.py`, `tools.py` (plus `prompts/prompt.md`). `auth.py`, `memory.py`, and `audit.py` are small helper modules they import.

## 1. Place the data pack (not in git)

The database and product images are **not** in this repository. Put the data pack inside `hw4/` so it looks like this:

```
hw4/
└── data/
    ├── campus_customs.db
    └── products/           # images referenced by the catalogue
```

The backend reads `data/campus_customs.db` and serves `data/products/` at `/media/products/`. On first start it adds a `sessions` table and a `page_results_json` column to `chat_messages` if they're missing. Existing data isn't changed.

## 2. Configure the environment

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Edit `.env` and set `PORTKEY_API_KEY`. `MODEL_NAME` defaults to `gpt-5.6-luna`. The site, product pages, and accounts work without a key; only the chat assistant needs it.

## 3. Run the backend (terminal 1)

Requires Python 3.11+.

```bash
cd backend
python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

Check it: <http://localhost:8000/api/health> returns `{"status":"ok"}`. API docs are at <http://localhost:8000/docs>.

## 4. Run the frontend (terminal 2)

Requires Node.js 20+.

```bash
cd frontend
npm install
npm run dev
```

Open **<http://localhost:5173>**. Vite proxies `/api` and `/media` to the backend on port 8000, so both must be running.

Test account (from the data pack): `test@campuscustoms.yale.edu` / `password`, or create your own on **Create Account**.

## 5. Try it

- **Products:** browse, filter, and click any card to open the product pop-up (your scroll position is kept).
- **Chat** (bottom-right bubble):
  - "Is the Ice Hockey Left Chest Hoodie in stock in a medium?" returns live stock and price from the database.
  - "What t-shirts do you have?" fills the Products page with matching cards; use **Return to Full Menu** to go back.
  - Open a product, then ask "Do you have this in red?". The assistant knows which item you're viewing.
- **Log in** to have your chat saved and restored on your next visit. Guest chats are not stored.
- Every chat message appends one record to `output/audit_trail.json`.

## Checks

```bash
cd frontend && npx tsc -b && npm run lint
cd backend && python -c "import main"
```

## Notes

- Model calls go through Portkey (`https://api.portkey.ai/v1`) using PydanticAI's `OpenAIChatModel`.
- Passwords are stored as salted PBKDF2-SHA256 hashes; the session cookie is `HttpOnly` and `SameSite=Lax`.
- Lifestyle banner photos in `frontend/public/images/` are used for a class project only.
- See `output/harness.md` for the full reference: model fields, tools, safety rules, loop limits, and result caps.
