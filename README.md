# Vibe JS 😭

AI-native developer CLI for debugging, code analysis, scaffolding, and workflow automation directly from the terminal.

---

## ✨ Features

### 🧠 AI Code Explanation
Explain confusing files in plain English.

```bash
vibe explain main.py
```

---

### 🔥 AI Roast
Get brutally honest (but useful) feedback on your code.

```bash
vibe roast app.py
```

---

### 🛠️ AI Code Fixing
Preview safer fixes or apply them directly.

```bash
vibe fix app.py
vibe fix app.py --write
```

---

### 😭 Contextual Debugging Workflow

Vibe JS can now debug progressively:

```bash
vibe complain "my flask app runs but the page is blank"
vibe check app.py
vibe fix --last-check --write
```

This workflow:
- remembers the complaint
- analyzes likely files
- checks the verified file
- applies contextual fixes

---

### 🩺 Project Doctor

Analyze project health and detect frameworks.

```bash
vibe doctor
```

Detects:
- React
- Vite
- Next.js
- Express
- missing dependencies
- missing `.env`
- Git setup

---

### 📝 AI Commit Messages

Generate commit messages from staged Git diffs.

```bash
vibe commit
```

---

### 🏗️ Structure Generation

Materialize folder structures from text files.

```bash
vibe structure structure.txt
```

Example:

```txt
my-app/
├── backend/
│   ├── routes/
│   └── app.py
├── frontend/
│   └── src/
└── README.md
```

---

### ⚡ Project Scaffolding

Generate starter project templates.

```bash
vibe create flask-api my-api
```

---

## 🚀 Installation

Clone the repo:

```bash
git clone https://github.com/Rikawesome/vibe-js.git
cd vibe-js
```

Create virtual environment:

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

### Git Bash

```bash
source venv/Scripts/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Install Vibe JS locally:

```bash
pip install -e .
```

---

## 🔑 Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_api_key_here
```

Get Gemini API key:

https://aistudio.google.com/app/apikey

---

## 🧪 Example Commands

```bash
vibe doctor

vibe explain main.py

vibe roast app.py

vibe complain "my app crashes on login"

vibe check auth.py

vibe fix --last-check

vibe structure examples/flask_structure.txt
```

---

## 📦 Tech Stack

- Python
- Typer
- Rich
- Gemini API
- pathlib
- Git

---

## 🛣️ Roadmap

- [ ] AI project scanning
- [ ] Multi-file contextual debugging
- [ ] `vibe sync`
- [ ] Smarter scaffolding
- [ ] AI-powered project generation
- [ ] Provider switching
- [ ] Offline-safe fallbacks

---

## ⚠️ Disclaimer

Vibe JS can modify files directly.

Always review generated fixes before writing changes 😭

---

## 📜 License

MIT License

---

Built with vibes 😭