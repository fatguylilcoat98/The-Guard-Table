<!--
  PathBack — The Good Neighbor Guard
  Built by Christopher Hughes · Sacramento, CA
  Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
  Truth · Safety · We Got Your Back
-->

# PathBack

**When someone knocks you off course, PathBack helps you stand your ground and get back on your path.**

Built by Christopher Hughes, Sacramento CA, The Good Neighbor Guard
Truth · Safety · We Got Your Back

## What It Is

A system that takes a regular person's raw anger and fear about something being done to them — and turns it into the exact words, the exact law, and the exact next steps that make the other side take them seriously.

> PathBack provides information and drafting help, not legal advice. For legal advice, consult a licensed attorney.

## Tech Stack

- **Frontend**: React (mobile-first, dark theme)
- **Backend**: Python Flask + gunicorn
- **Storage**: SQLite (usage counters, access passes, usage log, admin tokens — survives restarts, safe across gunicorn workers)
- **AI**: Multi-provider via `backend/gng_inference.py` — Groq (free tier), Ollama (local backup), Claude (paid tier, with prompt caching)
- **Payments**: Stripe Checkout (7-Day Pass + subscriptions)
- **Deploy**: Docker + docker-compose on a home server behind a Cloudflare Tunnel (Render config kept as an alternative)

## Pricing

| Product | Price | What you get |
|---|---|---|
| Free | $0 | 3 responses/day per person (global daily cap protects capacity) |
| 7-Day Pass | $6.99 one-time | Unlimited responses for 7 days |
| Subscription | $11.99/mo or $99/yr | Unlimited responses, strongest model |

## Inference Lanes & Cost Profile

All model calls go through `backend/gng_inference.py`. Every response records `served_by` (`groq` / `local` / `claude`) in the SQLite usage log.

| Lane | Model | Cost | Used for |
|---|---|---|---|
| `groq` | `llama-3.3-70b-versatile` | **$0** (Groq free tier: ~30 req/min, ~6K tokens/min, ~1K req/day — tokens/min is the binding cap) | Free-tier main responses, citation verification |
| `local` | Ollama `qwen2.5:7b` (configurable) | **$0** (your electricity) | Backup when Groq is rate-limited. Responses carry a caution banner and tier label — a 7B model is less reliable on citations |
| `claude` | `claude-sonnet-4-20250514` | ~ $3/$15 per Mtok, reduced by prompt caching on the big system prompt | Paid-tier main responses only |

**Routing policy** (env-overridable):
- Free main response: `groq → local →` honest "at capacity, try again shortly" message. **Free users never touch Claude** — the free tier costs ≈ $0.
- Paid main response: `claude → groq` (a fallback is flagged `downgraded` in the response metadata and UI).
- Citation verification: `groq → local →` skip with a logged warning. Verification never blocks a response.
- 429s get one retry with backoff, then fall down the chain. The 3/day/IP limit and the 200/day global cap now protect the Groq quota instead of Anthropic spend.

### Getting a free Groq key

1. Go to https://console.groq.com and sign up (free, no card).
2. Left sidebar → **API Keys** → **Create API Key**.
3. Copy the key (starts with `gsk_`) into `GROQ_API_KEY` in your `.env`.

## Environment Variables

See `.env.example` for the full commented template.

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | for free tier | Groq lane (free-tier responses + verification) |
| `ANTHROPIC_API_KEY` | for paid tier | Claude lane (paid responses, prompt-cached) |
| `OLLAMA_URL` / `OLLAMA_MODEL` | optional | Local lane (defaults `http://localhost:11434` / `qwen2.5:7b`) |
| `PATHBACK_FREE_CHAIN` / `PATHBACK_PAID_CHAIN` / `PATHBACK_VERIFY_CHAIN` | optional | Routing overrides (comma-separated lanes) |
| `STRIPE_SECRET_KEY` | for payments | Stripe API key (`sk_…`) |
| `STRIPE_WEBHOOK_SECRET` | for payments | Webhook signing secret (`whsec_…`) |
| `PRICE_ID_PASS_7DAY` / `PRICE_ID_SUB_MONTHLY` / `PRICE_ID_SUB_YEARLY` | for payments | Stripe Price IDs (`price_…`) |
| `PUBLIC_BASE_URL` | for payments | Public https URL used in Stripe redirects (your tunnel hostname) |
| `PATHBACK_DB` | optional | SQLite path (default `backend/data/pathback.db`; `/data/pathback.db` in Docker) |
| `GUARD_ADMIN_KEY` / `GUARD_ADMIN_PASSWORD` | recommended | Protect `/admin/*` endpoints |
| `ADMIN_TOKENS` | optional | Legacy comma-separated admin tokens (SQLite `admin_tokens` table preferred) |

## Stripe Dashboard Setup (manual steps)

Do these once in https://dashboard.stripe.com (start in **Test mode**, repeat in Live mode when ready):

1. **Create the 7-Day Pass product**
   - **Products** → **+ Add product**
   - Name: `PathBack 7-Day Pass`, Description: `Unlimited PathBack responses for 7 days`
   - Pricing: **One-off**, `6.99` USD → **Save**
   - Copy the Price ID (`price_…`) → `PRICE_ID_PASS_7DAY`
2. **Create the subscription product**
   - **Products** → **+ Add product**
   - Name: `PathBack Unlimited`
   - Pricing #1: **Recurring**, `11.99` USD, **Monthly** → save → copy Price ID → `PRICE_ID_SUB_MONTHLY`
   - **+ Add another price**: **Recurring**, `99` USD, **Yearly** → save → copy Price ID → `PRICE_ID_SUB_YEARLY`
3. **Get your API key**
   - **Developers** → **API keys** → reveal the **Secret key** (`sk_…`) → `STRIPE_SECRET_KEY`
4. **Create the webhook endpoint**
   - **Developers** → **Webhooks** → **+ Add endpoint**
   - Endpoint URL: `https://YOUR-TUNNEL-HOSTNAME/api/stripe/webhook`
   - Select events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`
   - **Add endpoint**, then copy the **Signing secret** (`whsec_…`) → `STRIPE_WEBHOOK_SECRET`
5. Put all five values in `.env`, restart the app, and run a test checkout with card `4242 4242 4242 4242`.

After checkout, the webhook issues an **access code** (`pb_…`) stored in SQLite; the success page shows it and unlocks the device automatically. The code can be pasted on any device.

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY=gsk_your_key          # free lane
# export ANTHROPIC_API_KEY=sk-ant-...     # paid lane (optional)
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

### Tests
```bash
pip install pytest requests
python -m pytest tests/test_pathback.py -v      # new-feature suite (no network needed)
PATHBACK_BASE_URL=http://localhost:8787 python tests/test_guard_table.py   # 17-test E2E baseline
```

## Deployment — Home Server + Cloudflare Tunnel

### 1. Build and run

```bash
cp .env.example .env       # fill in keys (see tables above)
docker compose build
docker compose up -d
curl http://localhost:8787/health   # → {"status": "healthy", "service": "PathBack", ...}
```

SQLite lives on the `pathback-data` volume — counters and access passes survive restarts and image rebuilds. The container runs 2 gunicorn workers; all counters are transactional in SQLite, so that's safe.

### 2. Cloudflare Tunnel hostname mapping

On the home server (one-time):

```bash
# Install cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
cloudflared tunnel login
cloudflared tunnel create pathback
cloudflared tunnel route dns pathback pathback.yourdomain.com
```

`~/.cloudflared/config.yml`:

```yaml
tunnel: pathback
credentials-file: /home/YOU/.cloudflared/<TUNNEL-ID>.json
ingress:
  - hostname: pathback.yourdomain.com
    service: http://localhost:8787
  - service: http_status:404
```

```bash
cloudflared tunnel run pathback     # or: sudo cloudflared service install
```

### 3. Wire Stripe to the tunnel

- Set `PUBLIC_BASE_URL=https://pathback.yourdomain.com` in `.env` and `docker compose up -d` again.
- In the Stripe webhook you created above, make sure the endpoint URL is `https://pathback.yourdomain.com/api/stripe/webhook`.
- Test end-to-end: buy a 7-Day Pass in Test mode; the success page at `https://pathback.yourdomain.com/success?...` should show your `pb_…` access code within a few seconds.

## API Endpoints

| Route | Method | Purpose |
|---|---|---|
| `/api/guard` | POST | Main response (SSE stream; `access_token` unlocks paid tier) |
| `/api/thought-partner` | POST | Thought Partner conversation |
| `/api/stripe/create-checkout` | POST | `{product: pass_7day \| sub_monthly \| sub_yearly}` → Checkout URL |
| `/api/stripe/webhook` | POST | Stripe events (signature-verified) |
| `/api/stripe/session-pass` | GET | Success page: session id → access code |
| `/api/stripe/status` | GET | Pass validity check |
| `/api/stripe/cancel` | POST | Cancel subscription at period end |
| `/health`, `/api/test` | GET | Monitoring |
| `/admin/status`, `/admin/usage`, `/admin/emergency-stop/<on\|off>` | — | Admin (SQLite-backed, key-protected) |

## The Experience

1. **Landing**: PathBack — get back on your path.
2. **Category**: Choose what they're doing to you
3. **Input**: Tell your story, raw and unfiltered (with an honest note about what PathBack is and isn't)
4. **Results**: Get your WAIT, LEVERAGE, and GUARD response — with the disclaimer footer and the lane that served you
5. **Upgrade**: 7-Day Pass or subscription via Stripe when you need more than 3/day

This is not a portfolio project. This is a tool that sits in front of people on the worst days of their lives and gives them something they have never had before — a system that fights back for them.

---

*PathBack — The Good Neighbor Guard — Truth · Safety · We Got Your Back*
