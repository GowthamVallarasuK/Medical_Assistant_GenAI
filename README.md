# 🤖 Agentic AI Medical Diagnosis Assistant

A production-level multi-agent AI system for medical diagnosis assistance that demonstrates true agentic behavior with collaborative AI agents.

## 🏗️ System Architecture

### Frontend (React + Vite + Tailwind)
- Chatbot-style interface
- Symptom input (text + voice)
- Medical report upload (PDF/image)
- Real-time diagnosis results
- Risk level indicators

### Backend (Node.js + Express)
- API routing and authentication
- Agent orchestration
- Session management
- Database integration

### Multi-Agent AI System (Python + FastAPI)
1. **Symptom Analyzer** - NLP-based symptom extraction
2. **Diagnosis Generator** - ML-based disease prediction
3. **Report Analyzer** - OCR + NLP for medical reports
4. **Recommendation Agent** - Treatment suggestions
5. **Orchestrator Agent** - Central coordinator

### Database & Storage
- **MongoDB** - User data, history, diagnoses
- **Vector DB (FAISS)** - Medical knowledge RAG system

## 🚀 Quick Start

```bash
# Frontend
cd frontend
npm install
npm run dev

# Backend
cd backend
npm install
npm run dev

# AI Services
cd ai-services
pip install -r requirements.txt
python main.py
```

## 📁 Project Structure

```
Gen_AI_Project/
├── frontend/                 # React + Vite + Tailwind
├── backend/                  # Node.js + Express
├── ai-services/             # Python FastAPI Agents
├── database/                # MongoDB schemas
├── docs/                    # Documentation
└── docker-compose.yml       # Container orchestration
```

## 🔧 Tech Stack

- **Frontend**: React, Vite, Tailwind CSS, Lucide Icons
- **Backend**: Node.js, Express, JWT, Socket.io
- **AI Services**: Python, FastAPI, OpenAI, Tesseract, Scikit-learn
- **Database**: MongoDB, FAISS/Pinecone
- **Deployment**: Docker, Docker Compose

## ⚠️ Medical Disclaimer

This system is for educational purposes only and is NOT a replacement for professional medical advice. Always consult with qualified healthcare providers.

## 📊 Features

- ✅ Multi-agent collaborative AI
- ✅ Real-time symptom analysis
- ✅ Medical report processing
- ✅ RAG-enhanced diagnosis
- ✅ Risk assessment
- ✅ Doctor recommendations
- ✅ JWT authentication
- ✅ Responsive UI/UX
