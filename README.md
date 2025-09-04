# Vet Voice AI - AI Receptionist for Veterinary Clinics

An intelligent voice-based receptionist system for veterinary clinics that can handle appointment scheduling, answer common questions, and provide 24/7 customer service.

## Features

- **Voice Call Handling**: Automated reception via Twilio Voice API
- **Speech Recognition**: OpenAI Whisper for speech-to-text
- **Natural Language Processing**: GPT-4/Claude for intelligent conversations
- **Text-to-Speech**: ElevenLabs for natural voice responses
- **Appointment Management**: Automated scheduling and management
- **Real-time Communication**: WebSocket support for live updates
- **Admin Dashboard**: Web interface for clinic management

## Tech Stack

- **Backend**: Python + FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **Voice Processing**: OpenAI Whisper (STT) + ElevenLabs (TTS)
- **LLM**: OpenAI GPT-4 or Claude
- **Voice Infrastructure**: Twilio Voice API
- **Real-time**: WebSockets for live audio streaming
- **Deployment**: Docker + AWS/Google Cloud

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone <repository-url>
   cd vet-voice-ai
   pip install -r requirements.txt
   ```

2. **Environment Setup**:
   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

3. **Database Setup**:
   ```bash
   docker-compose up -d postgres
   alembic upgrade head
   ```

4. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Endpoints

- `POST /api/voice/webhook` - Twilio voice webhook
- `GET /api/appointments` - List appointments
- `POST /api/appointments` - Create appointment
- `WebSocket /ws/audio` - Real-time audio streaming

## Configuration

All configuration is handled through environment variables. See `.env.example` for required variables.

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Deployment

```bash
# Build and run with Docker
docker-compose up --build

# Or deploy to cloud
# See deployment/ directory for cloud-specific configurations
```

## License

MIT License
