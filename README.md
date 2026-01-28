# Sticky-Net 🕸️

<p align="center">
  <strong>AI-Powered Honeypot System for Scam Detection & Intelligence Extraction</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.109+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Gemini-3.0-purple.svg" alt="Gemini 3.0">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
</p>

---

## 🎯 Overview

**Sticky-Net** is an AI-powered honeypot system that autonomously detects scam messages and engages scammers through multi-turn conversations to extract actionable intelligence. The system uses Google's Gemini 3 models to classify threats and generate believable human responses, wasting scammers' time while gathering evidence for law enforcement.

### Core Capabilities

- 🔍 **Hybrid Scam Detection** — Fast regex pre-filter + AI semantic classification
- 🎭 **Believable Persona** — Maintains a naive, confused victim character
- 🏦 **Intelligence Extraction** — Bank accounts, UPI IDs, phone numbers, phishing links
- ⏱️ **Adaptive Engagement** — Cautious (10 turns) or Aggressive (25 turns) modes
- 🛡️ **Production-Ready** — Docker, Cloud Run deployment, structured logging

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Technology Stack](#-technology-stack)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Intelligence Extraction](#-intelligence-extraction)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Documentation](#-documentation)
- [License](#-license)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│              Incoming Message + Metadata + History                  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 STAGE 0: Regex Pre-Filter (~10ms)                   │
│  • Obvious scam → Skip AI, engage immediately                       │
│  • Obvious safe → Skip AI, return neutral                           │
│  • Uncertain → Continue to AI                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│           STAGE 1: AI Scam Classifier (Gemini 3 Flash)              │
│  • Fast semantic classification (~150ms)                            │
│  • Context-aware (uses conversation history)                        │
│  • Returns: is_scam, confidence, scam_type                          │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
              ┌──────────────────┴──────────────────┐
              │                                     │
      Not Scam (conf < 0.6)              Is Scam (conf ≥ 0.6)
              │                                     │
              ▼                                     ▼
┌─────────────────────────┐     ┌──────────────────────────────────────┐
│  Return neutral         │     │      STAGE 2: Engagement Policy      │
│  Continue monitoring    │     │  • conf 0.6-0.85: CAUTIOUS (10 turns)│
└─────────────────────────┘     │  • conf > 0.85: AGGRESSIVE (25 turns)│
                                └───────────────┬──────────────────────┘
                                                │
                                                ▼
                                ┌─────────────────────────────────────┐
                                │  STAGE 3: AI Engagement Agent       │
                                │  (Gemini 3 Pro)                     │
                                │  • Believable human persona         │
                                │  • Intelligence extraction          │
                                │  • Exit conditions enforced         │
                                └───────────────┬─────────────────────┘
                                                │
                                                ▼
                                ┌─────────────────────────────────────┐
                                │  STAGE 4: Intelligence Extractor    │
                                │  • Bank account regex               │
                                │  • UPI ID patterns                  │
                                │  • Phishing URL detection           │
                                └─────────────────────────────────────┘
```

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Never Reveal Detection** | System always maintains believable human persona |
| **Adaptive Engagement** | Varies tactics based on scammer approach |
| **Natural Extraction** | Asks clarifying questions to prompt intelligence sharing |
| **Monotonic Confidence** | Confidence only increases (prevents false negative oscillation) |
| **Safety Limits** | Max turns, timeout handling, exit conditions |

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.11+ | Core language with type hints |
| **API Framework** | FastAPI | REST API with auto-validation |
| **AI SDK** | `google-genai` v1.51+ | Gemini model access |
| **Primary Models** | Gemini 3 Flash/Pro | Scam detection & engagement |
| **Fallback Models** | Gemini 2.5 Flash/Pro | Reliability fallback |
| **Database** | Google Firestore | Conversation state & intelligence |
| **Validation** | Pydantic v2 | Request/response schemas |
| **Logging** | structlog | Structured JSON logging |
| **Containerization** | Docker | Production deployment |
| **Cloud** | Google Cloud Run | Serverless hosting |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- GCP Service Account with Vertex AI & Firestore access

### Option 1: Local Development (Recommended)

```bash
# Clone the repository
git clone https://github.com/codedbykishore/sticky-net.git
cd sticky-net

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your API key and GCP project

# Place GCP service account key
mkdir -p secrets
cp /path/to/service-account.json secrets/

# Run the server
uvicorn src.main:app --reload --port 8080
```

### Option 2: Docker Compose

```bash
# Build and run with Firestore emulator
docker-compose up --build

# The API will be available at http://localhost:8080
```

### Option 3: Docker Only

```bash
# Build the image
docker build -t sticky-net .

# Run with environment variables
docker run -p 8080:8080 \
  -e API_KEY=your-api-key \
  -e GOOGLE_CLOUD_PROJECT=your-project \
  -v $(pwd)/secrets:/app/secrets:ro \
  sticky-net
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_KEY=your-secure-api-key
PORT=8080
DEBUG=true

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=global
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_APPLICATION_CREDENTIALS=./secrets/service-account.json

# AI Models
FLASH_MODEL=gemini-3-flash-preview      # Fast classification
PRO_MODEL=gemini-3-pro-preview          # Engagement responses
FALLBACK_FLASH_MODEL=gemini-2.5-flash   # Fallback classification
FALLBACK_PRO_MODEL=gemini-2.5-pro       # Fallback engagement
LLM_TEMPERATURE=0.7

# Engagement Policy
MAX_ENGAGEMENT_TURNS_CAUTIOUS=10
MAX_ENGAGEMENT_TURNS_AGGRESSIVE=25
MAX_ENGAGEMENT_DURATION_SECONDS=600
CAUTIOUS_CONFIDENCE_THRESHOLD=0.60
AGGRESSIVE_CONFIDENCE_THRESHOLD=0.85

# Timeouts
API_TIMEOUT_SECONDS=90
GEMINI_MAX_RETRIES=2
```

### GCP Service Account

The service account needs the following roles:
- `roles/aiplatform.user` — Vertex AI access
- `roles/datastore.user` — Firestore access

---

## 📡 API Reference

### Base URL

```
http://localhost:8080/api/v1
```

### Authentication

All requests require an API key header:

```
x-api-key: your-api-key
```

### Endpoints

#### `POST /analyze`

Analyze a message for scam detection and engage if scam is detected.

**Request:**

```json
{
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": "2026-01-21T10:15:30Z"
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Previous message from scammer",
      "timestamp": "2026-01-21T10:10:00Z"
    },
    {
      "sender": "user",
      "text": "Previous response from honeypot",
      "timestamp": "2026-01-21T10:12:00Z"
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

**Response (Scam Detected):**

```json
{
  "status": "success",
  "scamDetected": true,
  "scamType": "banking_fraud",
  "confidence": 0.92,
  "engagementMetrics": {
    "engagementDurationSeconds": 420,
    "totalMessagesExchanged": 18
  },
  "extractedIntelligence": {
    "bankAccounts": ["1234567890123456"],
    "upiIds": ["scammer@paytm"],
    "phoneNumbers": ["+91-9876543210"],
    "beneficiaryNames": ["Rahul Kumar"],
    "phishingLinks": ["http://fake-bank-verify.com"],
    "ifscCodes": ["SBIN0001234"],
    "bankNames": ["State Bank of India"],
    "whatsappNumbers": [],
    "emails": [],
    "other_critical_info": [
      {"label": "TeamViewer ID", "value": "123456789"}
    ]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection",
  "agentResponse": "Oh no! Which account is blocked? I have SBI and HDFC both. Please help me sir, I don't know what to do!"
}
```

**Response (Not a Scam):**

```json
{
  "status": "success",
  "scamDetected": false,
  "scamType": null,
  "confidence": 0.15,
  "engagementMetrics": {
    "engagementDurationSeconds": 0,
    "totalMessagesExchanged": 0
  },
  "extractedIntelligence": {
    "bankAccounts": [],
    "upiIds": [],
    "phoneNumbers": [],
    "beneficiaryNames": [],
    "phishingLinks": [],
    "ifscCodes": [],
    "bankNames": [],
    "whatsappNumbers": [],
    "emails": [],
    "other_critical_info": []
  },
  "agentNotes": "",
  "agentResponse": null
}
```

#### `GET /health`

Health check endpoint.

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### Scam Types

The system classifies scams into the following categories:

| Type | Description |
|------|-------------|
| `banking_fraud` | Fake bank alerts, account blocking threats |
| `job_offer` | Work-from-home scams, fake job offers |
| `lottery_reward` | KBC lottery, prize winning scams |
| `impersonation` | Government official, company impersonation |
| `others` | Other types of scams |

### cURL Example

```bash
curl -X POST http://localhost:8080/api/v1/analyze \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "message": {
      "sender": "scammer",
      "text": "Congratulations! You won ₹50 lakhs in KBC lottery. Send ₹5000 processing fee to claim.",
      "timestamp": "2026-01-21T10:15:30Z"
    },
    "conversationHistory": [],
    "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
  }'
```

---

## 🔍 Intelligence Extraction

Sticky-Net extracts various types of actionable intelligence from scammer messages:

| Type | Pattern Examples | Validation |
|------|------------------|------------|
| **Bank Accounts** | 9-18 digit numbers, formatted with dashes | Length validation, Luhn check |
| **UPI IDs** | `name@paytm`, `phone@upi` | Known provider validation |
| **Phone Numbers** | +91-XXXXX-XXXXX, 10-digit Indian | 6-9 prefix validation |
| **IFSC Codes** | SBIN0001234 | Format: 4 letters + 0 + 6 alphanumeric |
| **Beneficiary Names** | "Account holder: Name" | Pattern matching, NER |
| **Bank Names** | SBI, HDFC, ICICI, etc. | 50+ Indian banks supported |
| **Phishing Links** | Suspicious URLs | Domain reputation, keyword analysis |
| **WhatsApp Numbers** | wa.me links, WhatsApp mentions | Number extraction |
| **Emails** | standard@email.com | RFC 5322 validation |
| **Other Intel** | TeamViewer IDs, Crypto wallets | Flexible key-value extraction |

### Extraction Architecture

The system uses a **hybrid extraction approach**:

1. **Regex Patterns** — Fast, deterministic extraction for known formats
2. **AI Extraction** — LLM-powered extraction for context-dependent values
3. **Validation** — All extracted values are validated before inclusion
4. **Deduplication** — Merged results from both sources, duplicates removed

---

## 📁 Project Structure

```
sticky-net/
├── src/
│   ├── main.py                 # FastAPI application entry point
│   ├── exceptions.py           # Custom exception classes
│   ├── api/
│   │   ├── routes.py           # API endpoint definitions
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── middleware.py       # Auth, timing, error handling
│   ├── detection/
│   │   ├── classifier.py       # AI scam classification (Gemini Flash)
│   │   └── detector.py         # Hybrid detection orchestrator
│   ├── agents/
│   │   ├── honeypot_agent.py   # Main engagement agent
│   │   ├── persona.py          # Victim persona management
│   │   ├── policy.py           # Engagement policy & exit conditions
│   │   ├── prompts.py          # LLM prompt templates
│   │   └── fake_data.py        # Fake data generation for luring
│   └── intelligence/
│       ├── extractor.py        # Hybrid intelligence extraction
│       └── validators.py       # Value validation utilities
├── config/
│   └── settings.py             # Pydantic settings configuration
├── tests/
│   ├── conftest.py             # Pytest fixtures
│   ├── test_api.py             # API endpoint tests
│   ├── test_detection.py       # Scam detection tests
│   ├── test_agent.py           # Engagement agent tests
│   └── test_extractor.py       # Intelligence extraction tests
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architecture documentation
│   ├── COMPLETE_FLOW.md        # End-to-end flow documentation
│   └── DOCUMENTATION.md        # Additional documentation
├── multi-turn-testing/
│   ├── judge_simulator.py      # Multi-turn conversation testing
│   ├── scenarios/              # Test scenario definitions
│   └── logs/                   # Test execution logs
├── secrets/
│   └── service-account.json    # GCP credentials (gitignored)
├── Dockerfile                  # Production Docker image
├── docker-compose.yml          # Local development with Firestore
├── pyproject.toml              # Python project configuration
├── requirements.txt            # Pip requirements (generated)
└── README.md                   # This file
```

---



<p align="center">
  Built with ❤️ for fighting scammers
</p>
