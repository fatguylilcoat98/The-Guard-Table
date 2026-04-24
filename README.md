# The Guard Table

**Every company has a system. Now so do you.**

Built by Christopher Hughes, Sacramento CA, The Good Neighbor Guard  
Truth · Safety · We Got Your Back

## What It Is

A system that takes a regular person's raw anger and fear about something being done to them — and turns it into the exact words, the exact law, and the exact next steps that make the other side take them seriously.

## Tech Stack

- **Frontend**: React (mobile-first, dark theme)
- **Backend**: Python Flask
- **AI**: Claude API (claude-sonnet-4-20250514)
- **Deploy**: Render (monorepo)

## Local Development

### Backend
```bash
cd backend
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## Deployment

Deploy both services on Render as a monorepo:
- Backend: Python service pointing to `/backend`
- Frontend: Static site pointing to `/frontend`

Environment variable required: `ANTHROPIC_API_KEY`

## The Experience

1. **Landing**: "Every company has a system. Now so do you."
2. **Category**: Choose what they're doing to you
3. **Input**: Tell your story, raw and unfiltered
4. **Results**: Get your WAIT, LEVERAGE, and GUARD response

This is not a portfolio project. This is a tool that sits in front of people on the worst days of their lives and gives them something they have never had before — a system that fights back for them.

---

*The Good Neighbor Guard — Truth · Safety · We Got Your Back*