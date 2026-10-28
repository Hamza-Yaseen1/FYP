<div align="center">

# ⚡ Sift (Communication AI Platform)
### *Next-Generation Intelligent Communication Management, Action Item Extraction & Voice Assistant*

<br/>

## 👨‍💻 Developed by
# **[HAMZA YASEEN](https://github.com/Hamza-Yaseen1)**

<br/>

[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.13-yellow?style=for-the-badge&logo=python)](https://www.python.org/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb)](https://www.mongodb.com/)
[![Groq](https://img.shields.io/badge/AI-Groq%20LLM-F55036?style=for-the-badge)](https://groq.com/)

</div>

---

## 📑 Table of Contents

1. [🌟 What is Sift?](#-what-is-sift)
   - [The Problem It Solves](#the-problem-it-solves)
   - [Core Architecture & Capabilities](#core-architecture--capabilities)
   - [Key Highlights](#key-highlights)
2. [🧭 System Map & Key Pages](#-system-map--key-pages)
3. [📖 How to Use Sift (Step-by-Step Guide)](#-how-to-use-sift-step-by-step-guide)
   - [Step 1: Accessing the Executive Dashboard](#step-1-accessing-the-executive-dashboard)
   - [Step 2: Connecting Your Channels (Gmail & WhatsApp)](#step-2-connecting-your-channels-gmail--whatsapp)
   - [Step 3: Navigating the Unified AI Inbox](#step-3-navigating-the-unified-ai-inbox)
   - [Step 4: Triaging with the Attention Cockpit](#step-4-triaging-with-the-attention-cockpit)
   - [Step 5: Managing Tasks & Action Items](#step-5-managing-tasks--action-items)
   - [Step 6: Using the JARVIS / Kestrel Voice & Text Co-Pilot](#step-6-using-the-jarvis--kestrel-voice--text-co-pilot)
   - [Step 7: Analyzing Communication Insights](#step-7-analyzing-communication-insights)
4. [🎙️ JARVIS Voice Command Cheat-Sheet](#-jarvis-voice-command-cheat-sheet)
5. [🔄 Real-World Daily Workflows](#-real-world-daily-workflows)
6. [🛡️ Security, Privacy & Reliability](#-security-privacy--reliability)
7. [💻 Technical Stack Overview](#-technical-stack-overview)
8. [📬 Contact & Connect](#-contact--connect)

---

## 🌟 What is Sift?

**Sift** is an executive-grade, AI-driven communication management platform designed to eliminate inbox anxiety and bring clarity to fragmented digital communications.

Modern professionals, executives, and teams receive hundreds of messages every day across disconnected platforms like **Gmail** and **WhatsApp**. Important requests get buried, deadlines are overlooked, and contextual follow-ups become nearly impossible. 

Sift solves this by aggregating multi-channel communications into a single intelligent stream, analyzing incoming messages in real-time, isolating actionable tasks, scoring urgency, and providing an always-ready **voice and conversational co-pilot (JARVIS / Kestrel)** that lets you query, triage, and control your inbox hands-free.

---

### The Problem It Solves

```
❌ The Chaos:
   [Gmail Inbox]     ──> 150+ unread emails, marketing noise, scattered requests
   [WhatsApp Chats]  ──> Critical client updates mixed with casual chatter
   [Action Tracking] ──> Manual copying of deadlines into to-do lists
   [Search Friction] ──> "Where did they send that contract? Was it email or WhatsApp?"

              ⬇  TRANSFORMED BY SIFT  ⬇

✅ The Solution:
   [Unified Stream]  ──> All channels ingested into one real-time inbox
   [AI Triage]       ──> Instant priority scoring: Urgent, Important, Normal, Low
   [Auto-Tasks]      ──> AI extracts action items & due dates automatically
   [Attention Hub]   ──> Isolates items requiring immediate human intervention
   [Voice Co-Pilot]  ──> "What came in today? What needs my attention?"
```

---

### Core Architecture & Capabilities

- 📬 **Cross-Platform Aggregation**: Direct Google OAuth 2.0 integration for Gmail plus automated webhook ingestion for WhatsApp, normalizing all incoming messages into a single consistent data schema.
- 🧠 **AI Intelligence Pipeline**: Powered by high-speed Groq models. Each incoming message is analyzed for:
  - **Priority Scoring**: Classified into `Urgent`, `Important`, `Normal`, or `Low`.
  - **Executive Summary**: A concise 1–2 sentence breakdown of message contents.
  - **Sentiment & Intent**: Detection of tone, deadlines, and urgency indicators.
  - **Task Extraction**: Automatically isolates to-do items, deadlines, and requests into actionable records.
  - **Suggested Replies**: Pre-formulates contextual, professional responses ready for one-click review.
- 🎙️ **JARVIS / Kestrel Voice & Text Assistant**:
  - **Real-Time Voice Interaction**: Web Speech API integration with hands-free microphone control.
  - **Speech Barge-In**: Interrupt the assistant mid-sentence, and it immediately pauses speech and seamlessly processes your new thought.
  - **Sentence-Chunked TTS**: Prevents speech truncation by streaming sequential, natural-sounding audio chunks.
  - **Multi-Turn Memory**: Follow up naturally (e.g., *"Show yesterday's emails"*, then *"Which ones are urgent?"*, then *"Summarize them"*).
  - **Deterministic Safety Fallback**: If external AI services face rate limits or network issues, JARVIS operates deterministically from your database without interruption or crashes.
- 🎯 **Attention Cockpit**: A dedicated triage view highlighting urgent unread messages and critical pending tasks so you never drop high-stakes communication.
- 📊 **Executive Analytics**: Visual breakdowns of message throughput, channel distributions, response velocity, and priority trends over 7-day, 30-day, and 90-day horizons.
- 🔐 **Zero-Trust Multi-Tenant Security**: Every query is strictly scoped to the authenticated user ID. Tokens are protected with cryptographic encryption (Fernet) and stored via secure httpOnly session cookies.

---

## 🧭 System Map & Key Pages

| Area | Route | Primary Purpose |
|------|-------|-----------------|
| **Executive Dashboard** | `/dashboard` | High-level birds-eye view: unread volume, attention alerts, recent messages, and quick tasks. |
| **Unified Inbox** | `/inbox` | Multi-channel inbox with priority filters, search, full thread history, and AI analysis drawers. |
| **Attention Center** | `/attention` | Triage center displaying strictly high-urgency items, overdue threads, and critical messages. |
| **Tasks & Actions** | `/tasks` | Dedicated task tracker displaying AI-extracted action items alongside manual tasks. |
| **Analytics** | `/analytics` | Interactive charts showing communication volume, priority splits, and channel breakdowns. |
| **Connections** | `/connections` | Integration hub to connect Gmail OAuth, monitor WhatsApp webhooks, and test message pipelines. |
| **Settings** | `/settings` | User profile management, appearance preferences (dark/light themes), and application settings. |
| **JARVIS Orb** | *Everywhere* | Always-available floating assistant widget in the bottom-right corner for voice and text commands. |

---

## 📖 How to Use Sift (Step-by-Step Guide)

### Step 1: Accessing the Executive Dashboard

1. **Sign In**: Navigate to `/login` or `/signup` to access your workspace.
2. **Dashboard Overview**:
   - The top metrics cards show your **Unread Messages**, **Urgent Items**, **Pending Tasks**, and **Connected Channels**.
   - The **Needs Attention** section highlights items flagged by AI as requiring immediate response.
   - The **Recent Communications** feed shows live updates with colored priority badges (`Urgent`, `Important`, `Normal`, `Low`).

---

### Step 2: Connecting Your Channels (Gmail & WhatsApp)

To let Sift manage your incoming communications, link your channels via the **Connections** page (`/connections`):

#### ✉️ Connecting Gmail
1. Navigate to **Connections** from the left sidebar.
2. Find the **Gmail** card and click **Connect**.
3. You will be redirected to the official Google OAuth consent screen. Sign in and grant read-only message permissions (`gmail.readonly`).
4. Once authenticated, Sift securely encrypts your credentials using Fernet encryption and starts a background poller that automatically ingests and analyzes incoming emails.

#### 💬 Connecting WhatsApp
1. On the **Connections** page, view the **WhatsApp** integration card.
2. Sift supports real-time WhatsApp Webhook ingestion.
3. Use the **Simulate Message** or **Bulk Test** tools right from the dashboard to simulate real-world messages, verify webhook reception, and inspect the real-time AI classification pipeline.

---

### Step 3: Navigating the Unified AI Inbox

Open the **Inbox** (`/inbox`) to manage all communication across email and messaging in one unified workspace:

1. **Filtering by Priority**:
   - Use the top tab bar to filter messages instantly:
     - **All**: Complete stream across all sources.
     - **Urgent**: High-risk, immediate-attention communications.
     - **Important**: High-value items, inquiries, and scheduled meetings.
     - **Normal & Low**: Routine updates, notifications, and newsletters.
     - **Unread**: Only messages that have not yet been marked as read.
2. **Instant Search**:
   - Use the search bar to query by sender name, email address, subject line, or message keywords.
3. **Deep AI Analysis Drawer**:
   - Click on any message to view its contents and full AI breakdown:
     - **Summary**: Concise executive briefing of the communication.
     - **Priority Score**: Explanation of why the AI assigned that priority.
     - **Extracted Action Items**: Checkboxes representing tasks found inside the message.
     - **Suggested Reply**: A drafted contextual response you can use to reply rapidly.

---

### Step 4: Triaging with the Attention Cockpit

When you have limited time and cannot read every message, navigate to **Attention** (`/attention`):

1. **Focused Triage**: This view filters out noise, newsletters, and routine chatter.
2. **Critical Highlights**: Displays only items marked as `Urgent` or requiring an immediate decision.
3. **Resolution**: Mark items as resolved, jump directly into the source thread, or trigger task creation with a single click.

---

### Step 5: Managing Tasks & Action Items

Navigate to **Tasks** (`/tasks`) to stay on top of commitments made across conversations:

1. **Automated Extraction**: When someone sends an email saying *"Please send the revised proposal by Thursday 3 PM"*, Sift's AI automatically generates a task with the deadline.
2. **Task Views**:
   - View pending, in-progress, and completed tasks.
   - Filter by priority or due date.
3. **Traceability**: Each auto-generated task contains a reference link to the original email or message it was extracted from.
4. **Manual Creation**: Click **Add Task** to manually record to-dos and assign custom priority levels.

---

### Step 6: Using the JARVIS / Kestrel Voice & Text Co-Pilot

The intelligent assistant is accessible across all dashboard pages through the glowing **Orb** in the lower-right corner.

#### 🎤 Interacting by Voice
1. **Activate**: Click the microphone icon or tap the Orb to open the assistant.
2. **Speak Naturally**: Speak your command into your microphone (e.g., *"What messages came in today?"*).
3. **Visual Feedback**:
   - 🔵 **Idle**: Waiting for input.
   - 🟢 **Listening**: Listening to your voice in real time.
   - 🟣 **Thinking**: Processing data or routing queries.
   - 🟠 **Speaking**: Playing back voice response with chunked TTS.
4. **Natural Voice Barge-In**:
   - If JARVIS is speaking and you want to ask another question or stop the response, simply **start speaking**.
   - JARVIS immediately halts audio playback, switches to listening mode, and responds to your new instruction.

#### 💬 Interacting by Text
- If your microphone is muted or unsupported, simply type commands or questions into the input field inside the JARVIS panel.

#### 🧠 What JARVIS Can Do
- **Message Queries**: Ask about message counts, today's messages, yesterday's updates, or date spans.
- **Priority Triage**: Request urgent or important messages specifically.
- **Summarization**: Ask for high-level summaries of recent communications.
- **Task Inquiries**: Check pending tasks or items needing your immediate attention.
- **Voice Navigation**: Direct the app hands-free (e.g., *"Take me to analytics"*).
- **Conversational Q&A**: Ask general questions or discuss your workflow.

---

### Step 7: Analyzing Communication Insights

Navigate to **Analytics** (`/analytics`) to monitor your communication habits and team responsiveness:

1. **Timeframe Selection**: Toggle between **7 Days**, **30 Days**, and **90 Days**.
2. **Volume Trends**: See day-by-day charts of inbound messages and peak communication days.
3. **Channel Split**: Compare volume coming from Gmail versus WhatsApp.
4. **Priority Distribution**: Visual donut/bar charts displaying the ratio of Urgent vs Normal communications.
5. **Action Completion Rate**: Track how quickly extracted tasks are completed over time.

---

## 🎙️ JARVIS Voice Command Cheat-Sheet

You can speak or type these commands directly to JARVIS:

### 📩 Message & Inbox Queries
| What you say | What JARVIS does |
|---|---|
| *"What messages came in today?"* | Fetches and recites all messages received since midnight UTC. |
| *"Show me yesterday's messages"* | Summarizes emails and chats received on the previous calendar day. |
| *"Which messages are urgent?"* | Filters and lists high-urgency communications needing immediate action. |
| *"How many unread messages do I have?"* | Returns the exact count of unread items across all channels. |
| *"Summarize my recent messages"* | Uses AI to generate a unified digest of recent communications. |
| *"Show me messages from this week"* | Lists all communications received within the current calendar week. |

### 🎯 Tasks & Attention Queries
| What you say | What JARVIS does |
|---|---|
| *"What needs my attention?"* | Reviews urgent threads, unread priorities, and pending action items. |
| *"Do I have any pending tasks?"* | Reads your active to-do list extracted by the AI pipeline. |
| *"How many tasks are completed?"* | Reports your task completion statistics. |

### 🚀 Hands-Free Screen Navigation
| What you say | Where JARVIS takes you |
|---|---|
| *"Go to inbox"* or *"Open messages"* | Navigates to `/inbox` |
| *"Show analytics"* or *"Open dashboard"* | Navigates to `/analytics` or `/dashboard` |
| *"Open tasks"* or *"Take me to to-do"* | Navigates to `/tasks` |
| *"Go to attention"* | Navigates to `/attention` |
| *"Open connections"* | Navigates to `/connections` |
| *"Go to settings"* | Navigates to `/settings` |

### 🔁 Multi-Turn Context Follow-Ups
| First Command | Follow-Up Command | Outcome |
|---|---|---|
| *"Show my messages from yesterday"* | *"Which ones are urgent?"* | Filters yesterday's result set down to urgent items. |
| *"How many messages do I have?"* | *"Summarize them"* | Generates an executive digest of those messages. |
| *"Show my messages"* | *"Actually, I mean tasks"* | Gracefully pivots context to show pending tasks. |

---

## 🔄 Real-World Daily Workflows

### ☀️ The Morning Executive Briefing
1. Open Sift on your browser or tablet.
2. Tap the **JARVIS** orb and ask: *"What needs my attention today?"*
3. JARVIS verbally highlights critical emails and urgent WhatsApp messages received overnight.
4. Review auto-generated tasks extracted from those messages.
5. You are briefed and ready in under 60 seconds without scrolling through hundreds of emails.

### ⏱️ Mid-Day Triage & Inbox Zero
1. Navigate to the **Attention** tab (`/attention`).
2. Triage high-priority items first.
3. Click any message to inspect the **AI Suggested Reply**.
4. Check off completed action items as you reply.
5. All completed items automatically update the **Analytics** progress metrics.

### 📊 End-of-Week Review
1. Open the **Analytics** tab (`/analytics`).
2. Review the 7-day throughput chart to identify communication bottlenecks.
3. Verify your channel split between Gmail and WhatsApp.
4. Ensure all extracted tasks for the week are completed.

---

## 🛡️ Security, Privacy & Reliability

- **🔒 Token Encryption**: OAuth access and refresh tokens for Gmail are encrypted at rest using **Fernet symmetric encryption** (`cryptography` library) before storing in MongoDB.
- **🍪 Secure Cookie Authentication**: JWT access tokens are stored in `httpOnly`, `SameSite=Lax` cookies, preventing unauthorized access via cross-site scripting (XSS).
- **🛡️ Strict Multi-Tenant Isolation**: Every database read, write, query, and aggregation includes the authenticated user's ID (`user_id`). Users can never access or query another user's messages or tasks.
- **⚡ AI Circuit Breaker & Fallback**: Sift includes an intelligent circuit breaker. If Groq API rate limits (OTPM/TPD) are reached, the system gracefully falls back to deterministic data retrieval. Messages are safely queued and retried without application downtime.
- **🔇 Privacy-First Assistant Context**: Prompts sent to LLM providers strictly contain conversation history and query text. Internal database IDs, sensitive authentication keys, and foreign user records are never exposed to external models.

---

## 💻 Technical Stack Overview

```
Frontend Architecture (Next.js 16 App Router)
├── Framework: Next.js 16.3.1 (React 19, TypeScript 5)
├── Styling: Tailwind CSS 4.0 + Shadcn/UI primitives
├── Audio & Speech: Web Speech API (Recognition + Chunked Synthesis)
├── Charts: Recharts
└── State & Realtime: Custom Hooks + WebSocket Client

Backend Architecture (FastAPI + Python 3.13)
├── API Server: FastAPI + Uvicorn
├── Database: MongoDB Atlas (Async via Motor)
├── AI Engine: Groq LLM API (Qwen 3.8 27B / Llama 3)
├── Security: Fernet Encryption, PyJWT, bcrypt
└── Ingestion: Google OAuth 2.0 REST API & WhatsApp Webhook Engine
```

---

## 📬 Contact & Connect

**Hamza Yaseen**  
- 💼 LinkedIn: [linkedin.com/in/hamza-yaseen-3a807b300](https://www.linkedin.com/in/hamza-yaseen-3a807b300/)  
- 🐙 GitHub: [@Hamza-Yaseen1](https://github.com/Hamza-Yaseen1)  
- ✉️ Email: [hamza.sce1@gmail.com](mailto:hamza.sce1@gmail.com)

<br/>

<div align="center">
  <sub>Designed & engineered with modern AI architecture by <b>Hamza Yaseen</b>.</sub>
</div>
