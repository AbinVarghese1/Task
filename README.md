# 🤖 GenAPAC Workspace AI Assistant

An intelligent **multi-agent AI workspace assistant** that helps users manage tasks, notes, calendar events, and reminders using natural language.

Built for **Gen AI Academy APAC Hackathon (Google Cloud × H2S)** 🚀

---

## 🚀 Features

* 💬 Natural language interaction
* 📋 Task management (add, update, delete, list)
* 📝 Notes creation with tagging & retrieval
* 📅 Calendar scheduling & event tracking
* 🔔 Smart reminders system
* 🗂️ Workspace summary dashboard
* ⚡ Real-time cloud data storage
* 🤖 Multi-agent architecture (ADK-based)
* 🧠 Action-based AI (not just chat responses)

---

## 🧠 How It Works

* User sends a natural language request
* Root agent routes the request
* Workspace agent detects intent
* Relevant tool is executed
* Data stored/retrieved from Datastore
* Response returned to user

---

## 🏗️ Architecture Overview

* **Root Agent** → Handles routing
* **Workflow Agent** → Manages flow & state
* **Workspace Agent** → Executes tasks

### Tools Layer:

* Tasks Tool
* Notes Tool
* Calendar Tool
* Reminders Tool

### Storage:

* Google Cloud Datastore (persistent storage)

---

## 🛠️ Tech Stack

* 🐍 Python
* ⚡ FastAPI
* 🤖 Google ADK (Agent Development Kit)
* 🧠 Gemini 2.5 Flash
* ☁️ Google Cloud Datastore
* 📊 Google Cloud Logging
* 🚀 Cloud Run (deployment)

---

## 📂 Project Structure

```
.
├── agent.py
├── __init__.py
├── requirements.txt
├── .env
└── README.md
```

---

## ⚙️ Installation

```bash
git clone https://github.com/AbinVarghese1/Task.git
cd Task
pip install -r requirements.txt
```

---

## ▶️ Run Locally

```bash
uvicorn main:app --reload
```

---

## ☁️ Deploy to Google Cloud Run

```bash
uvx --from google-adk==1.14.0 \
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --service_name=genapac-ai-assistant \
  --with_ui \
  . \
  -- \
  --service-account=$SERVICE_ACCOUNT
```

---

## 🔐 Environment Variables

Create a `.env` file:

```
PROJECT_ID=your-project-id
GOOGLE_API_KEY=your-api-key
```

---

## 📌 Usage

* Start the server
* Open the provided UI
* Interact using natural language
* Manage tasks, notes, calendar & reminders

---

## 🌟 Key Highlights

* Multi-agent AI system using Google ADK
* Tool-driven execution (real actions, not just responses)
* Modular architecture for easy scalability
* Real-time cloud-backed workspace
* Designed for real-world productivity use cases

---

## 🤝 Contributing

Pull requests are welcome.
For major changes, please open an issue first.

---

## 📄 License

MIT License

---

⭐ If you like this project, consider giving it a star!
