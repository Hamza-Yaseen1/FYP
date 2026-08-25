<div align="center">

# 🤖 Communication AI Platform

*Intelligent communication management powered by AI*

<br/>

## 👨‍💻 **Developed by**

# **[HAMZA YASEEN](https://github.com/Hamza-Yaseen1)**

<br/>

[![Next.js](https://img.shields.io/badge/Next.js-16.3-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow?style=for-the-badge&logo=python)](https://www.python.org/)

</div>

---

## ✨ Features

- 🔐 **Secure Authentication** - JWT-based auth with httpOnly cookies
- 💬 **Message Management** - Intelligent inbox and message routing
- ✅ **Task Tracking** - AI-powered task prioritization and management
- 🎯 **Attention Dashboard** - Focus on what matters most
- 🤝 **Connections** - Manage your communication network
- 🎨 **Modern UI** - Built with Base UI and Tailwind CSS
- ⚡ **Real-time Updates** - Seamless sync between frontend and backend
- 🧠 **AI Analysis** - Powered by Groq for intelligent insights

---

## 🏗️ Tech Stack

### Frontend
- **Framework:** Next.js 16.3 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4.0
- **UI Components:** Base UI + Lucide Icons
- **State Management:** React Hooks
- **Testing:** Vitest + Testing Library

### Backend
- **Framework:** FastAPI
- **Language:** Python 3.11+
- **Database:** MongoDB (via Motor)
- **Authentication:** JWT + bcrypt
- **AI:** Groq API
- **Server:** Uvicorn

---

## 🚀 Getting Started

### Prerequisites

- Node.js 20+ and npm/yarn/pnpm
- Python 3.11+
- MongoDB instance (local or cloud)
- Groq API key

### 1️⃣ Clone the Repository

```bash
git clone <your-repo-url>
cd my-app
```

### 2️⃣ Frontend Setup

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at **[http://localhost:3000](http://localhost:3000)**

### 3️⃣ Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your settings:
# - JWT_SECRET
# - MONGODB_URL
# - GROQ_API_KEY
```

Start the backend server:

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at **[http://localhost:8000](http://localhost:8000)**

---

## 📁 Project Structure

```
my-app/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication pages
│   ├── (dashboard)/       # Dashboard pages
│   └── api/               # API routes
├── backend/               # FastAPI backend
│   ├── models/            # Database models
│   ├── routes/            # API endpoints
│   ├── services/          # Business logic
│   │   └── ai/            # AI analysis services
│   └── tests/             # Backend tests
├── components/            # React components
│   └── ui/                # UI primitives
└── lib/                   # Shared utilities
```

---

## 🔧 Available Scripts

### Frontend

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm start            # Start production server
npm run lint         # Run ESLint
npm test             # Run tests
npm run test:watch   # Run tests in watch mode
```

### Backend

```bash
uvicorn main:app --reload    # Start dev server
pytest                        # Run tests
python -m scripts.assign_legacy_data  # Run migration scripts
```

---

## 🌐 API Documentation

Once the backend is running, visit:
- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🎨 Key Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | User authentication |
| Signup | `/signup` | New user registration |
| Dashboard | `/dashboard` | Main overview |
| Inbox | `/inbox` | Filterable message management with priority tabs and search |
| Tasks | `/tasks` | Task tracking |
| Attention | `/attention` | Priority items |
| Connections | `/connections` | Contact management |
| Settings | `/settings` | User preferences |

---

## 🔐 Environment Variables

### Frontend
Create `.env.local` (optional):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend
Create `backend/.env`:
```env
JWT_SECRET=your-super-secret-key-here
MONGODB_URL=mongodb://localhost:27017/communication_ai
GROQ_API_KEY=your-groq-api-key
```

---

## 🧪 Testing

### Frontend Tests
```bash
npm test                 # Run all tests
npm run test:watch      # Watch mode
```

### Backend Tests
```bash
cd backend
pytest                   # Run all tests
pytest -v               # Verbose output
pytest tests/test_auth.py  # Run specific test file
```

---

## 🚢 Deployment

### Frontend (Vercel)
The easiest way to deploy is using [Vercel](https://vercel.com/new):

```bash
npm run build
```

### Backend (Any Python Host)
Deploy to platforms like:
- Railway
- Render
- DigitalOcean
- AWS/GCP/Azure

Ensure environment variables are set in your hosting platform.

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is private and confidential.

---

## 💬 Support

For questions or issues, please open an issue in the repository.

---

<div align="center">

**Built with ❤️ by Hamza Yaseen using Next.js and FastAPI**

---

### 📧 Contact

**Hamza Yaseen**  
📩 Email: [your.email@example.com](mailto:hamza.sce1@example.com)  
💼 LinkedIn: [linkedin.com/in/hamzayaseen](https://www.linkedin.com/in/hamza-yaseen-3a807b300/)  
🐙 GitHub: [@hamzayaseen](https://github.com/Hamza-Yaseen1)

</div>
