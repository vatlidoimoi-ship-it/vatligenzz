# LMS - Learning Management System (Vật Lý THPT)

## Overview
A web-based Learning Management System for Vietnamese high school students learning Vật Lý in grades 10, 11, and 12. Teachers can create courses, upload documents, manage exercises, and grade essays. Students can enroll in courses, take quizzes, use an AI chatbot (Google Gemini), participate in a forum, and chat.

## Tech Stack
- **Backend:** Flask (Python 3.12)
- **Templating:** Jinja2 + HTML/CSS/Bootstrap + Vanilla JS
- **AI:** Google Generative AI (Gemini) for chatbot, exam analysis, and essay grading
- **Database:** JSON flat-file system in `data/` directory (managed by `utils/database.py`)
- **Auth:** Session-based with werkzeug password hashing (`utils/auth.py`)
- **WSGI (production):** Gunicorn

## Project Structure
```
app.py              # Main Flask app (routes, ~2200 lines)
requirements.txt    # Python dependencies
Procfile            # Heroku-style deployment config
data/               # JSON flat-file database
  users.json        # User accounts (students/teachers)
  courses.json      # Course metadata
  progress.json     # Student progress
  exam_results.json # Exam results
  li.json           # Vật Lý exam bank
static/
  css/style.css
  js/main.js, chatbot.js
templates/          # Jinja2 HTML templates
utils/
  auth.py           # Authentication logic
  database.py       # JSON database CRUD
  gemini_api.py     # Google Gemini AI integration
questions.json      # Global question pool
scores.json         # Scores data
```

## Running the App
- **Development:** `python app.py` (runs on `0.0.0.0:5000`, debug mode)
- **Production:** `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`

## Environment Variables / Secrets
- `GEMINI_API_KEY` — Required. Google Gemini API key for AI features.

## Key Features
- Role-based access (student / teacher / admin)
- AI Chatbot with LaTeX math rendering, SVG, and Mermaid diagram support
- Vật Lý course management for grades 10, 11, and 12 with lesson tracking
- Multiple-choice & essay exercises with AI grading
- Exam analysis with AI feedback
- Forum & chat room
- Leaderboard and quiz game
