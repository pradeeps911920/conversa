# Conversa 🧠

### The AI strategist for conversations where you need to convince someone.

Conversa is a persistent, stateful AI agent for convincing, negotiating, and navigating conversations toward a desired outcome.

It doesn't just generate replies. Conversa understands the situation, tracks the other person's position and reactions, and continuously adapts its strategy to help you figure out **what to say, when to say it, and how to respond when they push back.**

## Architecture

This project is currently optimized for rapid local testing with zero heavy dependencies:
- **Backend:** Python + FastAPI
- **Database:** SQLite (Zero-install, local `conversa.db` file) + SQLAlchemy
- **AI Engine:** Google Gemini (3.1 Pro for Strategy Planning, 3.6 Flash for Drafting/Critique)
- **Frontend:** Vanilla JS + Tailwind CSS (Served natively by FastAPI, no Node.js required)

---

## How to Run (Windows Guide)

You don't need Docker, PostgreSQL, or a separate frontend server. Everything runs through a single Python command.

### 1. Setup the Environment
Open PowerShell and navigate to the `backend` folder:
```powershell
cd backend
python -m venv venv
```

### 2. Install Dependencies
*(Note: We use the executable directly to bypass strict Windows PowerShell script execution policies).*
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Set your API Key
You need a Google Gemini API key to power the strategy engines.
```powershell
$env:GEMINI_API_KEY="your-real-gemini-key-here"
```

### 4. Start the Application
```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### 5. Open the App
Open your web browser and go to:
**http://localhost:8000**

You will see the Conversa UI. Click **+ New Strategy Session** in the sidebar to begin!

---

## Features
- **Stateless AI Generation:** You can tweak context and regenerate AI responses infinitely without corrupting your database history.
- **Mid-Conversation Pivots:** Update your objective in the sidebar at any time, and the Strategy Agent will immediately pivot its approach.
- **Editable Drafts:** You always have the final say. Edit the AI's drafted response before clicking "Accept & Advance" to permanently commit it to the canonical memory state.
