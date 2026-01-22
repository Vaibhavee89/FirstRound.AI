# FirstRound.AI

FirstRound.AI is an AI-powered automated interview platform designed to streamline the preliminary screening process. It uses advanced voice AI to conduct real-time, interactive interviews with candidates via web or phone, providing instant transcripts and scoring to recruiters.

## 🚀 Features

*   **AI Voice Agent**: Conducts natural, conversational interviews using state-of-the-art LLMs and voice technologies.
*   **Dual Modes**:
    *   **Web Interview**: Interactive video/audio interview interface powered by Daily.co.
    *   **Phone Interview**: Automated outbound calling to candidates via Twilio.
*   **Job Portal**: A modern Next.js frontend for candidates to browse jobs and apply.
*   **Real-time Processing**: Low-latency speech-to-text (Deepgram), LLM processing (OpenAI), and text-to-speech (Cartesia/OpenAI).
*   **Automated Scoring**: (Future) Analyzes interview responses to screen candidates effectively.

## 🛠️ Tech Stack

### Frontend
*   **Framework**: [Next.js](https://nextjs.org/) (React)
*   **Styling**: [Tailwind CSS](https://tailwindcss.com/)
*   **UI Components**: [Shadcn UI](https://ui.shadcn.com/) / Lucide React
*   **Real-time Video/Audio**: [Daily.co SDK](https://www.daily.co/)

### Backend / Agent
*   **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python)
*   **Voice Pipeline**: [Pipecat AI](https://docs.pipecat.ai/)
*   **ASR (Speech-to-Text)**: Deepgram
*   **LLM (Intelligence)**: OpenAI (GPT-4o/GPT-4o-mini)
*   **TTS (Text-to-Speech)**: Cartesia / OpenAI
*   **Telephony**: Twilio

## 📋 Prerequisites

Before running the project, ensure you have the following installed:
*   [Node.js](https://nodejs.org/) (v18+)
*   [Python](https://www.python.org/) (v3.10+)
*   [Docker](https://www.docker.com/) (Optional, for containerized run)

You will also need API keys for the following services:
*   Daily.co
*   OpenAI
*   Deepgram
*   Cartesia (Optional, defaults to OpenAI TTS if not configured)
*   Twilio (Account SID, Auth Token, and proper Phone Number configuration)

## ⚙️ Configuration

1.  Clone the repository:
    ```bash
    git clone https://github.com/Vaibhavee89/FirstRound.AI.git
    cd FirstRound.AI
    ```

2.  Create a `.env` file in the root directory based on the example:
    ```bash
    cp .env.example .env
    ```

3.  Fill in your API keys in `.env`:
    ```env
    # Daily.co API Key
    DAILY_API_KEY=your_daily_key
    
    # OpenAI API Key
    OPENAI_API_KEY=sk-...
    
    # Deepgram API Key
    DEEPGRAM_API_KEY=your_deepgram_key
    
    # Cartesia API Key (Optional)
    CARTESIA_API_KEY=your_cartesia_key
    
    # Twilio Credentials
    TWILIO_ACCOUNT_SID=your_sid
    TWILIO_AUTH_TOKEN=your_token
    TWILIO_PHONE_NUMBER=your_number
    ```

## 🏃‍♂️ How to Run

### Option 1: Using Docker (Recommended)

The easiest way to get everything running is with Docker Compose.

```bash
docker-compose up --build
```
*   **Frontend**: http://localhost:3000
*   **Agent API**: http://localhost:7860

### Option 2: Manual Setup

You can run the services individually using the provided helper script or manually.

**Using `start.sh`**:
```bash
./start.sh
```

**Manual Individual Setup**:

1.  **Backend (Agent)**:
    ```bash
    cd agent
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn bot:app --host 0.0.0.0 --port 7860 --reload
    ```

2.  **Frontend**:
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## 📁 Project Structure

```
├── agent/               # Python/FastAPI Service (Voice Bot)
│   ├── audio/           # Static audio assets
│   ├── logs/            # Interview transcripts and logs
│   ├── bot.py           # Main application entry point
│   └── requirements.txt # Python dependencies
├── frontend/            # Next.js Application
│   ├── src/             # Source code
│   └── package.json     # Node dependencies
├── jobs.json            # Database mock for job listings
├── applications.json    # Database mock for submitted applications
├── docker-compose.yml   # Docker orchestration
└── start.sh             # Local startup script
```
