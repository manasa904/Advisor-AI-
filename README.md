# Advisor-AI  
## Intelligent Agent for Financial Advisors

Advisor AI is an AI-powered concierge platform designed for financial advisors at broker-dealer firms.  
The system combines Retrieval-Augmented Generation (RAG), Large Language Models (LLMs), real-time Kafka streaming, and role-based access control to deliver intelligent financial assistance and operational automation.

---

# Features

| Feature | Description |
|---|---|
| **RAG Chat** | Ask questions about portfolios, research, and compliance using natural language |
| **Portfolio Dashboard** | View real-time holdings, P&L, sector allocation, and risk flags |
| **Compliance Engine** | Pre-trade validation using suitability, concentration, restricted-list, watchlist, and position-size rules |
| **Kafka Streaming** | Live alerts streamed to the UI using Kafka and WebSockets |
| **NBA / Revenue Intelligence** | Next-best-action recommendations, life-event detection, cross-sell and upsell suggestions |
| **Scenario Simulation** | Simulate market crashes, interest rate hikes, and sector rotations |
| **Role-Based Access Control** | Separate dashboards for Advisors, Compliance Officers, and Operations teams |
| **Anomaly Detection** | Detect concentration risk, abnormal losses, and profile mismatches |
| **Observability** | AI model metrics, system monitoring, and audit trail tracking |
| **Knowledge Graph** | Client-product relationship mapping with suitability insights |
| **Human-in-the-Loop (HITL)** | Approval workflows for sensitive AI-driven decisions |
| **NER Engine** | Financial entity extraction for clients, tickers, amounts, and intents |
| **Voice Input** | Hands-free interaction using Web Speech API voice-to-text |

---

# Tech Stack

| Component | Technology |
|---|---|
| **LLM** | Groq (Llama 3) / Ollama |
| **Vector Database** | ChromaDB |
| **Backend** | FastAPI + Python 3.11 |
| **Frontend** | React + TypeScript |
| **Streaming** | Apache Kafka |
| **Database** | SQLite |
| **Authentication** | JWT (`python-jose`) |
| **Orchestration** | LangChain |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |

---

# System Architecture

```text
localhost:3000  → React Frontend
localhost:8000  → FastAPI Backend
localhost:8090  → Kafka UI Dashboard
localhost:9092  → Kafka Broker
```

---

# Setup and Installation

## Prerequisites

Make sure the following are installed:

- Python 3.11
- Node.js
- Docker Desktop
- Git

---

# Backend Setup

```bash
cd backend

python -m venv venv

# Windows
.\venv\Scripts\activate

pip install -r requirements.txt

uvicorn main:app --reload --port 8000
```

---

# Frontend Setup

```bash
cd frontend

npm install

npm start
```

---

# Infrastructure Setup

```bash
cd docker

docker compose up -d
```

---

# Load Sample Data

```bash
cd ..

python scripts/load_structured_data.py
```

---

# Test Credentials

| Username | Password | Role |
|---|---|---|
| `advisor1` | `advisor123` | Financial Advisor |
| `compliance1` | `compliance123` | Compliance Officer |
| `ops1` | `ops123` | Operations Team |

---

# Project Structure

```text
advisor-ai/
│
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   └── services/     # Business logic
│   ├── requirements.txt
│   └── main.py
│
├── frontend/
│   └── src/
│       └── App.tsx       # React application
│
├── data/                 # Sample CSV datasets
├── docker/               # Docker Compose configuration
└── scripts/              # Data ingestion scripts
```

---

# Problem Statement

Financial advisors often work across fragmented systems where client data, portfolios, research insights, and compliance policies are distributed across multiple platforms.

This fragmentation leads to:

- Delayed advisor responses
- Inconsistent compliance monitoring
- Operational inefficiencies
- Missed revenue opportunities

Advisor AI addresses these challenges through a unified conversational platform powered by RAG and LLM technologies.

---

## KPIs

- Advisor productivity: 30%+ time saved
- Client response time: under 2 minutes
- Compliance violations: 80% reduction
- AUM per advisor: 15%+ growth target
---
