
# Voice AI Doctor Appointment Assistant

An AI-powered voice assistant that helps patients check doctor availability, book appointments, and cancel existing appointments through natural voice conversations.

## Features

- Voice interaction using Pipecat
- Speech-to-text and text-to-speech using ElevenLabs
- Gemini-powered conversational AI
- Doctor availability checking
- Appointment booking and cancellation
- Phone number confirmation before booking or cancellation
- SQLite database for appointment management
- React dashboard for doctors and appointments
- Live appointment status updates

## Tech Stack

**Backend:** Python, FastAPI, SQLite, SQLAlchemy

**Frontend:** React, Vite, JavaScript, CSS

**Voice AI:** Pipecat, ElevenLabs STT/TTS, Google Gemini

## Project Structure

```text
voice-doctor-assistant/
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── doctors_data.py
│   │   ├── appointment_service.py
│   │   ├── main.py
│   │   ├── test_appointment_service.py
│   │   └── appointments.db
│   ├── voice_bot.py
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── App.jsx
│       └── App.css
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/anuhya-7842/Voice-AI-Doctor-Appointment-Assistant.git
cd voice-doctor-assistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install backend dependencies

```bash
pip install -r backend/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using `.env.example` as a template and add your API credentials.

### 5. Start the backend API

```bash
python -m uvicorn backend.app.main:app --reload
```

Backend: http://127.0.0.1:8000

API documentation: http://127.0.0.1:8000/docs

### 6. Start the voice assistant

Open another terminal:

```bash
python -m backend.voice_bot
```

Voice assistant: http://localhost:7860/client

### 7. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Testing

Run the appointment service tests:

```bash
python -m backend.app.test_appointment_service
```

## Security

API keys are stored in the local `.env` file and should never be committed to GitHub.
