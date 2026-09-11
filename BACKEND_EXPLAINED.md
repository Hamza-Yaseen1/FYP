# Backend Architecture - Complete Explanation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Core Files](#core-files)
3. [Data Models](#data-models)
4. [API Routes](#api-routes)
5. [Services Layer](#services-layer)
6. [AI Intelligence](#ai-intelligence)
7. [Flow Diagrams](#flow-diagrams)

---

## 🎯 System Overview

This is a **Communication AI Backend** built with **FastAPI** (Python web framework). The system analyzes messages from different sources (WhatsApp, email, etc.) using AI to:
- **Classify priority** (urgent, important, normal, low)
- **Extract actionable tasks** with deadlines
- **Generate summaries**
- **Recommend next actions**
- **Group related messages into threads**

### Technology Stack
```
Backend Framework: FastAPI (Python async web framework)
Database: MongoDB (NoSQL document database)
Database Driver: Motor (async MongoDB driver)
AI Provider: Groq (LLM API using Qwen model)
Authentication: JWT tokens + bcrypt password hashing
Encryption: AES-256 CBC for sensitive tokens
Testing: pytest + httpx
```

---

## 🔧 Core Files

### 1. `main.py` - Application Entry Point

**Purpose**: The main FastAPI application that starts the web server.

**Line-by-line explanation**:

```python
from contextlib import asynccontextmanager
# asynccontextmanager allows running setup/teardown code when app starts/stops

from fastapi import FastAPI
# FastAPI - the web framework

from fastapi.middleware.cors import CORSMiddleware
# CORS - allows frontend (React) to make requests from different port

from dotenv import load_dotenv
# Loads environment variables from .env file

import logging
# Python's built-in logging system

from database import users_collection, messages_collection, tasks_collection, connections_collection, create_indexes
# Import database collections

from routes.auth import router as auth_router
# Import authentication routes (login/register/logout)

# ... other route imports

load_dotenv()
# Load .env file variables into environment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
# Configure logging format: timestamp, level, name, message

@asynccontextmanager
async def lifespan(app: FastAPI):
    # This runs ONCE when the application starts
    
    # Create database indexes for fast queries
    await users_collection.create_index("email", unique=True)
    # Index on email - ensures no duplicate emails, fast lookup
    
    await messages_collection.create_index([("user_id", 1), ("created_at", -1)])
    # Index for: "get all messages for user X, sorted by newest first"
    
    await messages_collection.create_index(
        [("sender", "text"), ("content", "text"), ("ai_analysis.summary", "text")],
        background=True,
    )
    # Full-text search index - allows searching message content
    
    await messages_collection.create_index(
        [("external_message_id", 1)],
        unique=True,
        partialFilterExpression={"external_message_id": {"$type": "string"}},
    )
    # Prevents duplicate webhook deliveries from WhatsApp
    
    await messages_collection.create_index(
        [("user_id", 1), ("conversationId", 1), ("received_at", -1)]
    )
    # Index for: "get conversation messages, newest first"
    
    await messages_collection.create_index(
        [("user_id", 1), ("threadId", 1), ("received_at", -1)]
    )
    # Index for: "get thread messages, newest first"
    
    await tasks_collection.create_index([("user_id", 1), ("created_at", -1)])
    # Index for: "get user's tasks, newest first"
    
    await connections_collection.create_index(
        [("user_id", 1), ("provider", 1)],
        unique=True
    )
    # Ensures one connection per provider per user (one WhatsApp, one Gmail, etc.)
    
    await connections_collection.create_index([("user_id", 1)])
    # Fast lookup of all user connections
    
    await create_indexes()
    # Additional indexes defined in database.py
    
    yield
    # Application is now running, code after yield runs on shutdown

app = FastAPI(title="Communication AI Backend", lifespan=lifespan)
# Create the FastAPI application with lifecycle management

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:3000",  # Alternative localhost
    ],
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],      # Allow all HTTP methods
    allow_headers=["*"],      # Allow all headers
)
# CORS - lets frontend on port 3000 talk to backend on port 8000

@app.get("/health")
def health_check():
    return {"status": "ok"}
# Health check endpoint - used to verify server is running

app.include_router(auth_router)
app.include_router(messages_router)
app.include_router(webhooks_router)
app.include_router(tasks_router)
app.include_router(connections_router)
# Register all API route groups
```

**Why we created this**:
- Central entry point for the entire backend
- Sets up database indexes for performance
- Configures CORS so frontend can communicate
- Registers all API routes in one place

---

### 2. `database.py` - Database Connection

**Purpose**: Establishes connection to MongoDB and defines collections.

**Line-by-line explanation**:

```python
import os
from motor.motor_asyncio import AsyncIOMotorClient
# Motor - async MongoDB driver (works with FastAPI's async)

from dotenv import load_dotenv
# Load environment variables

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
# Database connection string
# Default: local MongoDB
# Production: MongoDB Atlas cloud (mongodb+srv://...)

DB_NAME = os.getenv("DB_NAME", "communication_ai")
# Database name - default "communication_ai"

client = AsyncIOMotorClient(MONGO_URI, tz_aware=True)
# Create async MongoDB client
# tz_aware=True - handles timezones properly

db = client[DB_NAME]
# Select the database

# Collections (like SQL tables, but for MongoDB documents)
messages_collection = db["messages"]
# Stores all incoming messages with AI analysis

users_collection = db["users"]
# Stores user accounts (name, email, password_hash)

ai_analysis_collection = db["ai_analysis"]
# (Not actively used - analysis stored in messages)

tasks_collection = db["tasks"]
# Stores extracted tasks from messages

connections_collection = db["connections"]
# Stores user's connected accounts (WhatsApp, Gmail, etc.)

# Indexes
async def create_indexes():
    # Tasks indexes for priority-based sorting and snooze queries
    await tasks_collection.create_index([("user_id", 1), ("priority_indicator", 1), ("created_at", -1)])
    # Query: "get user's tasks sorted by priority then date"
    
    await tasks_collection.create_index([("user_id", 1), ("snoozed_until", 1)])
    # Query: "get snoozed tasks that are due to wake up"
```

**Why we created this**:
- Single source of truth for database connection
- All files import collections from here
- Indexes are defined for query performance
- Separation of concerns - database logic isolated

---

### 3. `dependencies.py` - Authentication Dependency

**Purpose**: Validates user authentication for protected routes.

**Line-by-line explanation**:

```python
from bson import ObjectId
# MongoDB uses ObjectId for document IDs

from fastapi import HTTPException, Request
# HTTPException - returns HTTP error responses
# Request - incoming HTTP request object

from database import users_collection
# Import users collection

from services.security import TOKEN_COOKIE_NAME, decode_token
# Import JWT token functions

async def get_current_user(request: Request) -> dict:
    # This function runs BEFORE protected route handlers
    # It validates authentication and returns the user
    
    token = request.cookies.get(TOKEN_COOKIE_NAME)
    # Extract JWT token from cookie (set during login)
    
    user_id = decode_token(token) if token else None
    # Decode JWT to get user ID
    # Returns None if token is invalid/expired
    
    if not user_id or not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=401, detail="Not authenticated.")
    # 401 = Unauthorized - user must login
    
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    # Fetch user from database
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated.")
    # User was deleted after token was issued
    
    return user
    # Return user document to the route handler
```

**Why we created this**:
- Reusable authentication check
- Any route can add `current_user: dict = Depends(get_current_user)` to require login
- Centralizes auth logic - change once, affects all routes
- FastAPI's dependency injection system

---

### 4. `requirements.txt` - Python Dependencies

**Purpose**: Lists all Python packages needed to run the backend.

```txt
fastapi                  # Web framework
uvicorn[standard]        # ASGI server (runs FastAPI)
pydantic                 # Data validation
motor                    # Async MongoDB driver
python-dotenv            # Load .env files
groq                     # Groq LLM API client
bcrypt                   # Password hashing
PyJWT                    # JWT token creation/validation
email-validator          # Validates email addresses

# dev/test
pytest                   # Testing framework
httpx                    # HTTP client for testing
```

**Installation**: `pip install -r requirements.txt`

**Why we created this**:
- Reproducible environment
- Anyone can install exact same packages
- Version control for dependencies

---

## 📊 Data Models

Models define the **shape** of data (validation, types). Built with **Pydantic**.

### 1. `models/user.py` - User Model

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    # Data required to create a new user
    name: str = Field(min_length=1, max_length=100)
    # Name must be 1-100 characters
    
    email: EmailStr
    # Must be valid email format (validated automatically)
    
    password: str = Field(min_length=8, max_length=72)
    # Password 8-72 characters (72 is bcrypt limit)

class UserLogin(BaseModel):
    # Data required to login
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    # Data returned to frontend (no password!)
    id: str
    name: str
    email: str
    created_at: datetime

def user_doc_to_response(doc: dict) -> dict:
    # Converts MongoDB document to UserResponse format
    return {
        "id": str(doc["_id"]),          # Convert ObjectId to string
        "name": doc["name"],
        "email": doc["email"],
        "created_at": doc["created_at"],
    }
```

**Why we created this**:
- **Input validation**: Pydantic automatically validates data
- **Type safety**: Catches errors at runtime
- **Security**: UserResponse excludes password_hash
- **Documentation**: FastAPI auto-generates API docs from models

---

### 2. `models/message.py` - Message Models

```python
class RoutingRecord(BaseModel):
    # Tracks which AI agents processed this message
    agents_run: list[str] = []           # ["priority", "summary", "task_extraction"]
    agents_skipped: list[str] = []       # ["deadline_detection"]
    skip_reason: str = ""                # "trivial" / "no_content"
    triggers: list[str] = []             # ["send", "tomorrow"]
    llm_call_used: bool = False          # Did we call Groq API?
    decided_at: datetime                 # When routing was decided

class AIAnalysis(BaseModel):
    # AI analysis results attached to every message
    priority: str = "pending"                    # "urgent"/"important"/"normal"/"low"
    confidence: float = 0.0                      # 0.0 - 1.0
    explanation: Optional[str] = None            # Why this priority?
    summary: Optional[str] = None                # One-sentence summary
    recommended_action: str = ""                 # "Send the report by 5pm"
    recommended_actions: list[str] = []          # List of actions
    tasks_extracted: list[ExtractedTask] = []    # Parsed tasks
    deadlines: list[str] = []                    # ["tonight", "tomorrow"]
    needs_attention: bool = False                # Flag for attention inbox
    attention_reason: str = ""                   # Why it needs attention
    provider: str = "unknown"                    # "groq" / "rule-based"
    analyzed_at: Optional[datetime] = None       # When analyzed
    status: str = "pending"                      # "completed"/"pending"/"skipped"
    routing: Optional[RoutingRecord] = None      # Routing decision record

class ContextUpdate(BaseModel):
    # Updates to earlier messages based on context
    field: str                    # "deadline" / "priority" / "note"
    value: str                    # "tomorrow" / "urgent"
    source_message_id: str        # Where this info came from
    reason: str                   # Why this update was made
    applied_at: datetime          # When applied

class MessageCreate(BaseModel):
    # Data to create a message (from frontend form)
    sender: str                   # "John Doe"
    content: str                  # "Send me the report by 5pm"
    source: str                   # "email" / "whatsapp" / "simulate"
    status: str = "unread"        # "read" / "unread"

class MessageResponse(BaseModel):
    # Complete message data returned to frontend
    id: str                                    # Message ID
    messageId: Optional[str] = None            # Same as id
    threadId: Optional[str] = None             # Thread this belongs to
    conversationId: Optional[str] = None       # Conversation ID
    sender: str                                # Who sent it
    content: str                               # Message text
    source: str                                # Where from
    status: str                                # Read/unread
    state: str                                 # "active" / "archived"
    ai_analysis: Optional[AIAnalysis] = None   # AI results
    created_at: datetime                       # When created
    updated_at: datetime                       # Last updated
    external_message_id: Optional[str] = None  # WhatsApp message ID
    received_at: Optional[datetime] = None     # When received
```

**Why we created this**:
- **Complex data structure**: Messages have many fields
- **AI integration**: AIAnalysis embedded in message
- **Tracking**: RoutingRecord shows how message was processed
- **Audit trail**: Timestamps, status changes tracked

---

### 3. `models/task.py` - Task Models

```python
class ExtractedTask(BaseModel):
    # Task extracted from message by AI
    description: str                          # "Send the quarterly report"
    deadline: Optional[str] = None            # "tonight" / "by Friday"
    priority_indicator: Optional[str] = None  # "urgent" / "ASAP"
    requires_action: bool = True              # Always true for extracted tasks

class TaskResponse(BaseModel):
    # Complete task data
    id: str                                # Task ID
    description: str                       # Task description
    deadline: Optional[str] = None         # Deadline
    priority_indicator: Optional[str] = None  # Priority
    requires_action: bool = True           # Requires action
    status: str = "pending"                # "pending"/"in_progress"/"completed"
    source_message_id: str                 # Original message ID
    source_message_preview: str            # First 80 chars of message
    created_at: datetime                   # When created
    updated_at: Optional[datetime] = None  # Last updated
    snoozed_until: Optional[datetime] = None  # Snoozed until when
```

**Why we created this**:
- **Task management**: Tracks actionable items
- **Traceability**: Links back to source message
- **Snooze feature**: User can postpone tasks
- **Status tracking**: pending → in_progress → completed

---

### 4. `models/connection.py` - Connection Models

```python
class Provider(str, Enum):
    # Supported integration platforms
    WHATSAPP = "whatsapp"
    GMAIL = "gmail"
    LINKEDIN = "linkedin"

class ConnectionStatus(str, Enum):
    # Connection states
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    COMING_SOON = "coming_soon"

class ConnectionCreate(BaseModel):
    # Data to create connection
    provider: Provider                # Which platform

class ConnectionResponse(BaseModel):
    # Connection data returned to frontend
    id: str
    provider: Provider
    status: ConnectionStatus
    created_at: datetime

class ConnectionInDB(BaseModel):
    # Full connection data in database
    id: Optional[str] = None
    user_id: str                      # Belongs to this user
    provider: Provider
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    access_token: Optional[str] = None      # OAuth token (encrypted)
    refresh_token: Optional[str] = None     # OAuth refresh token (encrypted)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Why we created this**:
- **Multi-platform**: Supports WhatsApp, Gmail, LinkedIn
- **OAuth tokens**: Stores encrypted access tokens
- **Status tracking**: Shows connection health
- **Security**: Tokens encrypted in database

---

### 5. `models/meta_webhook.py` - WhatsApp Webhook Models

```python
# These models parse WhatsApp Business API webhook payloads

class MetaText(BaseModel):
    body: Optional[str] = None              # Message text

class MetaMessage(BaseModel):
    from_: str = Field(alias="from")        # Sender phone number
    id: str                                  # WhatsApp message ID
    timestamp: str                           # When sent
    type: str                                # "text" / "image" / "audio"
    text: Optional[MetaText] = None         # Text content

class MetaContactProfile(BaseModel):
    name: Optional[str] = None              # Sender's name

class MetaContact(BaseModel):
    wa_id: str                              # WhatsApp ID
    profile: Optional[MetaContactProfile] = None

class MetaMetadata(BaseModel):
    display_phone_number: Optional[str] = None  # Business phone number
    phone_number_id: Optional[str] = None       # Phone number ID

class MetaValue(BaseModel):
    messaging_product: Optional[str] = None     # "whatsapp"
    metadata: Optional[MetaMetadata] = None
    contacts: Optional[List[MetaContact]] = None
    messages: Optional[List[MetaMessage]] = None

class MetaChange(BaseModel):
    value: MetaValue
    field: str = ""                         # "messages"

class MetaEntry(BaseModel):
    id: Optional[str] = None
    changes: List[MetaChange]

class MetaWebhookPayload(BaseModel):
    # Top-level webhook payload from Meta
    object: Optional[str] = None            # "whatsapp_business_account"
    entry: Optional[List[MetaEntry]] = None
```

**Why we created this**:
- **WhatsApp integration**: Parses incoming webhooks
- **Type safety**: Validates webhook structure
- **Meta API compliance**: Follows Meta's exact structure
- **Error prevention**: Catches malformed webhooks

---

## 🛣️ API Routes

Routes are the **HTTP endpoints** the frontend calls.

### 1. `routes/auth.py` - Authentication Routes

**Endpoints**:
- `POST /auth/register` - Create new account
- `POST /auth/login` - Login
- `GET /auth/me` - Get current user
- `POST /auth/logout` - Logout

**Line-by-line for `register`**:

```python
@router.post("/register", status_code=201)
async def register(payload: UserCreate, response: Response):
    # POST /auth/register
    # 201 = Created
    # payload validated automatically by Pydantic
    # response - to set cookies
    
    email = payload.email.lower()
    # Normalize email to lowercase (case-insensitive)
    
    existing = await users_collection.find_one({"email": email})
    if existing:
        raise HTTPException(
            status_code=409,  # 409 = Conflict
            detail="An account with this email already exists.",
        )
    # Check if email already registered
    
    doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        # NEVER store plain passwords - always hash
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(doc)
    # Insert new user into database
    
    doc["_id"] = result.inserted_id
    # Get the generated ID
    
    _set_session_cookie(response, create_access_token(str(result.inserted_id)))
    # Create JWT token and set as HTTP-only cookie
    # User is now logged in
    
    return user_doc_to_response(doc)
    # Return user data (without password)
```

**Line-by-line for `login`**:

```python
@router.post("/login")
async def login(payload: UserLogin, response: Response):
    email = payload.email.lower()
    user = await users_collection.find_one({"email": email})
    # Find user by email
    
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    # Check password using bcrypt
    # NEVER reveal whether email or password is wrong (security)
    
    _set_session_cookie(response, create_access_token(str(user["_id"])))
    # Create session
    
    return user_doc_to_response(user)
```

**Why we created this**:
- **User accounts**: Every user has own data
- **Security**: Passwords hashed, JWT tokens, HTTP-only cookies
- **Session management**: Stateless JWT authentication

---

### 2. `routes/messages.py` - Message Management Routes

**Endpoints**:
- `POST /messages` - Create message (with AI analysis)
- `GET /messages` - List messages (with filters)
- `GET /messages/counts` - Get filter counts
- `GET /messages/senders` - Get unique senders
- `GET /messages/sources` - Get unique sources
- `GET /messages/{id}` - Get single message
- `PUT /messages/{id}` - Update message
- `DELETE /messages/{id}` - Delete message
- `PUT /messages/{id}/priority` - Override priority

**Key function: `create_message`**:

```python
@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(
    payload: MessageCreate, 
    current_user: dict = Depends(get_current_user)
):
    # Requires authentication (Depends)
    
    now = datetime.now(timezone.utc)
    uid = str(current_user["_id"])
    
    _id = ObjectId()
    # Pre-generate ID (needed for thread resolution)
    
    thread_id, conversation_id = None, None
    try:
        thread_id, conversation_id = await resolve_and_stamp(
            uid, payload.source, payload.sender, now
        )
        # Try to link to existing thread
        # Same user + source + sender + within 60 minutes = same thread
    except Exception as exc:
        logger.warning("Thread resolution failed; stored standalone: %s", exc)
        # If thread resolution fails, message stored standalone
        # NEVER block message creation
    
    doc = {
        **payload.model_dump(),          # sender, content, source, status
        "_id": _id,
        "messageId": str(_id),
        "user_id": uid,                  # Always user-scoped
        "state": "active",
        "created_at": now,
        "updated_at": now,
        "received_at": now,
    }
    if thread_id:
        doc["threadId"] = thread_id
        doc["conversationId"] = conversation_id
    
    result = await messages_collection.insert_one(doc)
    # Store message FIRST
    
    ai_analysis = await process_message(
        payload.content,
        message_id=str(result.inserted_id),
        user_id=uid,
        thread_id=thread_id,
    )
    # Run AI analysis (single entry point)
    
    await messages_collection.update_one(
        {"_id": result.inserted_id},
        {"$set": {"ai_analysis": ai_analysis}},
    )
    # Update message with analysis
    
    doc["ai_analysis"] = ai_analysis
    return message_doc_to_response(doc)
```

**Key function: `get_messages` (with filters)**:

```python
@router.get("")
async def get_messages(
    current_user: dict = Depends(get_current_user),
    tab: Optional[str] = Query(None),           # "all"/"urgent"/"important"/"normal"/"unread"
    source: Optional[str] = Query(None),        # "whatsapp"/"email"
    priority: Optional[str] = Query(None),      # "urgent"/"important"/"normal"/"low"
    start_date: Optional[str] = Query(None),    # ISO date
    end_date: Optional[str] = Query(None),      # ISO date
    sender: Optional[str] = Query(None),        # Sender name
    search: Optional[str] = Query(None),        # Search text
    limit: int = Query(100, ge=1, le=200),      # Max results
    offset: int = Query(0, ge=0),               # Pagination offset
):
    uid = str(current_user["_id"])
    query = {"user_id": uid}
    # ALWAYS filter by user - security critical
    
    # Tab filter
    if tab and tab != "all":
        if tab == "unread":
            query["status"] = "unread"
        elif tab in ["urgent", "important", "normal"]:
            query["ai_analysis.priority"] = tab
    
    # Source filter
    if source:
        query["source"] = source
    
    # Priority filter
    if priority:
        query["ai_analysis.priority"] = priority
    
    # Date range filter
    if start_date or end_date:
        created_at_filter = {}
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            created_at_filter["$gte"] = start_dt  # Greater than or equal
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            created_at_filter["$lte"] = end_dt    # Less than or equal
        query["created_at"] = created_at_filter
    
    # Sender filter
    if sender:
        query["sender"] = sender
    
    # Search filter - case-insensitive regex
    if search:
        query["$or"] = [
            {"sender": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}},
            {"ai_analysis.summary": {"$regex": search, "$options": "i"}},
        ]
        # Searches sender OR content OR summary
    
    # Get total count
    total = await messages_collection.count_documents(query)
    
    # Get messages with pagination
    cursor = messages_collection.find(query).sort("created_at", -1).skip(offset).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    return {
        "messages": [message_doc_to_response(doc) for doc in docs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
```

**Why we created this**:
- **Message inbox**: Core feature of the app
- **Filtering**: User can filter by priority, source, date, etc.
- **Search**: Full-text search across messages
- **AI integration**: Every message analyzed automatically
- **Thread linking**: Related messages grouped

---

### 3. `routes/webhooks.py` - Webhook Routes

**Endpoints**:
- `GET /webhooks/whatsapp` - WhatsApp webhook verification
- `POST /webhooks/whatsapp` - Receive WhatsApp messages
- `POST /webhooks/simulate` - Test endpoint (manual message creation)

**Key function: Webhook verification**:

```python
@router.get("/webhooks/whatsapp")
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge"),
):
    # WhatsApp sends GET request to verify your webhook
    # You must respond with hub.challenge to complete verification
    
    logger.info("Webhook verification requested: mode=%s", hub_mode)
    
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        # VERIFY_TOKEN from .env - you set this in Meta Dashboard
        logger.info("Webhook verification succeeded")
        return PlainTextResponse(content=hub_challenge)
        # Return challenge as plain text
    
    logger.warning("Webhook verification failed: mode=%s", hub_mode)
    raise HTTPException(status_code=403, detail="Verification token mismatch")
```

**Key function: Receive WhatsApp message**:

```python
@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    raw = await request.body()
    # Get raw request body for signature verification
    
    if not verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=403, detail="Invalid signature")
    # Meta signs every webhook with your app secret
    # This prevents fake webhooks
    
    try:
        payload = MetaWebhookPayload.model_validate_json(raw)
    except ValidationError as exc:
        logger.warning("Webhook rejected: malformed payload (%s)", exc)
        raise HTTPException(status_code=400, detail="Invalid payload")
    # Parse and validate webhook structure
    
    owner_id = await _resolve_owner()
    # Find which user owns the connected WhatsApp account
    
    for entry in payload.entry or []:
        for change in entry.changes:
            if change.field != "messages":
                continue
            
            value = change.value
            if not value.messages:
                continue
            
            phone_number_id = value.metadata.phone_number_id if value.metadata else None
            if phone_number_id != WHATSAPP_PHONE_NUMBER_ID:
                logger.info("Delivery ignored: wrong phone number")
                continue
            # Only process messages for YOUR WhatsApp business number
            
            if owner_id is None:
                logger.info("Delivery ignored: no connected owner")
                continue
            # Only process if someone connected WhatsApp
            
            for msg in value.messages:
                await ingest_message(
                    user_id=owner_id,
                    source="whatsapp",
                    sender=_resolve_sender(value, msg),
                    content=_message_content(msg),
                    external_message_id=msg.id,
                    message_type=_message_type(msg),
                    background_tasks=background_tasks,
                )
                # Store message and analyze in background
    
    logger.info("Webhook delivery acknowledged")
    return {"status": "ok"}
    # Must return 200 OK quickly or Meta retries
```

**Why we created this**:
- **WhatsApp integration**: Receives real messages from WhatsApp Business API
- **Security**: Signature verification prevents fake webhooks
- **Background processing**: AI analysis runs async (doesn't delay webhook response)
- **Duplicate prevention**: external_message_id prevents duplicates

---

### 4. `routes/tasks.py` - Task Management Routes

**Endpoints**:
- `GET /tasks` - List tasks (excludes completed and snoozed)
- `PUT /tasks/{id}/status` - Update task status
- `DELETE /tasks/{id}` - Delete task
- `PUT /tasks/{id}/snooze` - Snooze task
- `GET /tasks/{id}/message` - Get source message for task

**Key function: Get tasks (with priority sorting)**:

```python
@router.get("")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    uid = str(current_user["_id"])
    now = datetime.now(timezone.utc)
    
    # Build query: exclude completed, exclude snoozed
    query = {
        "user_id": uid,
        "status": {"$ne": "completed"},   # Not completed
        "$or": [
            {"snoozed_until": {"$exists": False}},      # No snooze
            {"snoozed_until": {"$lte": now}}            # Snooze expired
        ]
    }
    
    # Aggregation pipeline for priority-based sorting
    pipeline = [
        {"$match": query},
        {"$addFields": {
            "priority_order": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$priority_indicator", "urgent"]}, "then": 1},
                        {"case": {"$eq": ["$priority_indicator", "important"]}, "then": 2},
                        {"case": {"$eq": ["$priority_indicator", "normal"]}, "then": 3}
                    ],
                    "default": 4
                }
            }
        }},
        {"$sort": {"priority_order": 1, "created_at": -1}},
        # Sort by: priority (urgent first), then newest first
        {"$limit": 100}
    ]
    
    cursor = tasks_collection.aggregate(pipeline)
    docs = await cursor.to_list(length=100)
    
    result = []
    for doc in docs:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        doc["is_snoozed"] = doc.get("snoozed_until") and doc["snoozed_until"] > now
        result.append(doc)
    
    return result
```

**Why we created this**:
- **Task tracking**: Users can see actionable items
- **Priority sorting**: Urgent tasks appear first
- **Snooze feature**: Users can postpone tasks
- **Source linking**: Click task to see original message

---

### 5. `routes/connections.py` - Connection Management Routes

**Endpoints**:
- `GET /connections` - List user's connections
- `POST /connections` - Create connection
- `DELETE /connections/{id}` - Delete connection

```python
@router.get("")
async def list_connections(current_user: dict = Depends(get_current_user)):
    service = ConnectionService(db)
    connections = await service.get_user_connections(str(current_user["_id"]))
    return {"connections": connections}

@router.post("", status_code=201)
async def create_connection(
    payload: ConnectionCreate,
    current_user: dict = Depends(get_current_user)
):
    service = ConnectionService(db)
    try:
        connection = await service.create_connection(
            str(current_user["_id"]),
            payload.provider
        )
        return connection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**Why we created this**:
- **Multi-platform**: Users connect WhatsApp, Gmail, LinkedIn
- **OAuth support**: Stores encrypted access tokens
- **Status tracking**: Shows if connection is working

---

## 🔧 Services Layer

Services contain **business logic** (not directly HTTP-related).

### 1. `services/security.py` - Authentication & Encryption

```python
import bcrypt
import jwt

TOKEN_COOKIE_NAME = "cai_token"
TOKEN_EXPIRY_DAYS = 7

JWT_SECRET = os.getenv("JWT_SECRET")
# Secret key for signing JWT tokens
# MUST be strong random string

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    # bcrypt - industry standard password hashing
    # Salt automatically generated
    # Slow by design (prevents brute force)

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        # Constant-time comparison (prevents timing attacks)
    except ValueError:
        return False

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,                              # Subject = user ID
        "iat": now,                                  # Issued at
        "exp": now + timedelta(days=TOKEN_EXPIRY_DAYS),  # Expires
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    # JWT = JSON Web Token
    # Stateless - no database lookup needed
    # Signed with secret - can't be forged

def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("sub")  # Returns user_id
    except jwt.InvalidTokenError:
        return None  # Expired or invalid
```

**Why we created this**:
- **Password security**: Never store plain passwords
- **Stateless auth**: JWT tokens don't require database lookup
- **Expiry**: Tokens auto-expire after 7 days
- **HTTP-only cookies**: JavaScript can't access token (XSS protection)

---

### 2. `services/threads.py` - Message Thread Linking

**Purpose**: Groups related messages into threads (same sender, same channel, within 60 minutes).

```python
LINK_WINDOW_MINUTES = 60  # Configurable

def normalize_sender(sender: str) -> str:
    # Case-insensitive, whitespace-insensitive
    return str(sender).strip().lower()

async def resolve_and_stamp(
    user_id: str,
    source: str,
    sender: str,
    received_at: datetime,
) -> tuple[str | None, str | None]:
    # Find latest message from same user/source/sender within 60 minutes
    
    window_start = received_at - timedelta(minutes=LINK_WINDOW_MINUTES)
    
    candidate = await messages_collection.find_one(
        {
            "user_id": user_id,                              # Same user
            "source": source,                                # Same source (whatsapp/email)
            "sender": _sender_filter(normalize_sender(sender)),  # Same sender (case-insensitive)
            "state": "active",                               # Not deleted
            "received_at": {"$gte": window_start},           # Within 60 minutes
        },
        sort=[("received_at", -1)],                          # Latest first
    )
    
    if candidate is None:
        return None, None
        # No recent message from this sender - new thread
    
    inherited = candidate.get("threadId")
    if inherited:
        # Candidate already has threadId - join that thread
        thread_id = str(inherited)
        return thread_id, thread_id
    
    # Candidate becomes the "anchor" - create new thread
    thread_id = str(candidate["_id"])
    await messages_collection.find_one_and_update(
        {"_id": candidate["_id"], "user_id": user_id},
        {"$set": {"threadId": thread_id, "conversationId": thread_id}},
    )
    logger.info("Anchor stamped: thread=%s (sender=%s)", thread_id, sender)
    
    return thread_id, thread_id
```

**Why we created this**:
- **Conversation grouping**: Related messages grouped together
- **Deterministic**: No AI needed - pure rule-based
- **Time-based**: 60-minute window (configurable)
- **Fast**: Single indexed query

---

### 3. `services/webhook_ingest.py` - Message Ingestion

**Purpose**: Common ingestion path for all message sources.

```python
async def ingest_message(
    user_id: str,
    source: str,
    sender: str,
    content: str,
    external_message_id: Optional[str] = None,
    message_type: str = "text",
    background_tasks: Optional[BackgroundTasks] = None,
) -> str:
    # ALL message ingestion funnels through here:
    # - WhatsApp webhooks
    # - Email webhooks (future)
    # - Manual test messages
    
    now = datetime.now(timezone.utc)
    _id = ObjectId()
    
    # Try to link to thread
    thread_id, conversation_id = None, None
    try:
        thread_id, conversation_id = await resolve_and_stamp(
            user_id, source, sender, now
        )
    except Exception as exc:
        logger.warning("Thread resolution failed; stored standalone: %s", exc)
        # Never block message ingestion
    
    doc = {
        "_id": _id,
        "messageId": str(_id),
        "user_id": user_id,
        "source": source,
        "sender": sender,
        "content": content,
        "message_type": message_type,
        "status": "unread",
        "state": "active",
        "created_at": now,
        "updated_at": now,
        "received_at": now,
    }
    if thread_id:
        doc["threadId"] = thread_id
        doc["conversationId"] = conversation_id
    if external_message_id:
        doc["external_message_id"] = external_message_id
    
    try:
        result = await messages_collection.insert_one(doc)
        message_id = str(result.inserted_id)
    except DuplicateKeyError:
        # WhatsApp sometimes delivers twice - ignore duplicates
        existing = await messages_collection.find_one(
            {"external_message_id": external_message_id}
        )
        logger.info("Duplicate delivery ignored (external_message_id=%s)", external_message_id)
        return str(existing["_id"])
    
    if background_tasks is not None:
        # Run AI analysis in background
        background_tasks.add_task(
            _analyze_and_store, content, message_id, user_id, thread_id
        )
    
    return message_id

async def _analyze_and_store(
    content: str, message_id: str, user_id: str, thread_id: str = None
) -> None:
    # Background task - runs after webhook returns
    try:
        analysis = await process_message(
            content,
            message_id=message_id,
            user_id=user_id,
            thread_id=thread_id,
        )
    except Exception as exc:
        logger.warning("AI analyze task failed for %s: %s", message_id, exc)
        return
    
    try:
        await messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {"$set": {"ai_analysis": analysis}},
        )
    except Exception as exc:
        logger.warning("Failed to persist ai_analysis for %s: %s", message_id, exc)
```

**Why we created this**:
- **Unified ingestion**: All sources use same code path
- **Duplicate prevention**: Handles WhatsApp double-delivery
- **Background processing**: AI analysis doesn't block webhook
- **Error resilience**: Message stored even if AI fails

---

### 4. `services/connection.py` - Connection Service

```python
class ConnectionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db["connections"]
    
    async def get_user_connections(self, user_id: str) -> List[dict]:
        # Get all connections for user
        cursor = self.collection.find({"user_id": user_id})
        connections = []
        async for doc in cursor:
            connections.append({
                "id": str(doc["_id"]),
                "provider": doc["provider"],
                "status": doc["status"],
                "created_at": doc["created_at"],
            })
        return connections
    
    async def create_connection(self, user_id: str, provider: Provider) -> dict:
        # Create new connection
        existing = await self.collection.find_one({
            "user_id": user_id,
            "provider": provider.value
        })
        if existing:
            raise ValueError("This account is already connected")
        
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "provider": provider.value,
            "status": ConnectionStatus.CONNECTED.value,
            "access_token": encrypt("mock_access_token"),      # In production: real OAuth token
            "refresh_token": encrypt("mock_refresh_token"),    # In production: real refresh token
            "created_at": now,
            "updated_at": now,
        }
        
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        
        return {
            "id": str(doc["_id"]),
            "provider": doc["provider"],
            "status": doc["status"],
            "created_at": doc["created_at"],
        }
```

**Why we created this**:
- **Service layer pattern**: Business logic separate from routes
- **Reusability**: Can be called from multiple routes
- **Testing**: Easier to test services than routes

---

## 🤖 AI Intelligence Layer

The AI system has 5 agents that analyze messages:

1. **Priority Classifier** - urgent/important/normal/low
2. **Summary Generator** - One-sentence summary
3. **Task Extractor** - Finds actionable tasks
4. **Deadline Detector** - Extracts deadlines
5. **Action Recommender** - Suggests next action

### Architecture Overview

```
services/ai/
├── orchestrate.py       # Entry point - routing + gating
├── routing.py           # Rule-based agent selection
├── analyzer.py          # Main analysis logic
├── attention.py         # "Needs Attention" rules
├── context.py           # Thread context management
└── providers/
    ├── base.py          # Provider interface
    └── groq.py          # Groq LLM implementation
```

---

### 1. `services/ai/orchestrate.py` - Orchestrator (Entry Point)

**Purpose**: Single entry point for ALL AI analysis. Routes messages to appropriate agents.

```python
async def process_message(
    content: str,
    message_id: str = None,
    user_id: str = None,
    message_type: str = "text",
    thread_id: str = None,
) -> dict:
    # ONLY entry point for AI analysis
    # NEVER call analyze_message directly
    
    # Step 1: Decide routing (rule-based, zero cost)
    routing = decide_routing(content, message_type)
    logger.info(
        "AI routing: reason=%s llm_call=%s agents_run=%s",
        routing.reason,
        routing.needs_llm,
        routing.agents_run(),
    )
    
    # Step 2: Short-circuit cheap paths
    if not routing.needs_analysis or not routing.needs_llm:
        return _deterministic_defaults(routing, message_type, content)
        # Examples:
        # - Empty content -> status="skipped"
        # - "ok" / "thanks" -> priority=normal, no LLM call
    
    # Step 3: Fetch thread context (if available)
    context_messages = await _fetch_context(
        user_id=user_id, 
        thread_id=thread_id, 
        exclude_message_id=message_id
    )
    # Gets last 5 messages from same thread
    
    # Step 4: Run single AI call (with context)
    analysis = await _analyze_with_fallback(
        content,
        message_id=message_id,
        user_id=user_id,
        routing=routing,
        context_messages=context_messages,
    )
    
    # Step 5: Apply context updates to earlier messages
    if message_id and analysis.get("context_updates"):
        await _apply_validated_updates(
            analysis["context_updates"],
            context_messages,
            message_id,
            user_id,
            content,
        )
    
    # Step 6: Attach routing record and return
    analysis.pop("context_updates", None)
    analysis["routing"] = _routing_record(routing, llm_call_used=True)
    return analysis
```

**Key concepts**:

**Routing Decision** - Decides which agents run:
```python
def _routing_record(routing: RoutingDecision, llm_call_used: bool) -> dict:
    if not routing.needs_analysis:
        return {
            "agents_run": [],                    # No agents ran
            "agents_skipped": [],                # All skipped
            "skip_reason": routing.reason,       # "no_content"
            "triggers": [],
            "llm_call_used": False,              # Zero cost
            "decided_at": datetime.now(timezone.utc),
        }
    return {
        "agents_run": routing.agents_run(),           # ["priority", "task_extraction"]
        "agents_skipped": routing.agents_skipped(),   # ["summary", "deadline_detection"]
        "skip_reason": routing.reason,                # "action"
        "triggers": routing.triggers,                 # ["send", "review"]
        "llm_call_used": bool(llm_call_used),         # True if Groq called
        "decided_at": datetime.now(timezone.utc),
    }
```

**Deterministic Defaults** - Zero-cost paths:
```python
def _deterministic_defaults(routing: RoutingDecision, message_type: str, content: str) -> dict:
    if not routing.needs_analysis:
        # No analyzable content (empty / media-only)
        return {
            "priority": "normal",
            "confidence": 0.5,
            "status": "skipped",             # Special status
            "provider": "rule-based",        # No LLM
            # ... rest empty
        }
    
    # Trivial message (ok/thanks/hi)
    return {
        "priority": "normal",
        "confidence": 0.5,
        "explanation": "Trivial message - deep analysis skipped",
        "summary": content,                  # Echo content
        "status": "completed",
        "provider": "rule-based",            # No LLM
        # ... rest empty
    }
```

**Why we created this**:
- **Cost optimization**: Skip LLM for trivial messages
- **Single call**: ONE API call per message (not 5)
- **Routing transparency**: See which agents ran
- **Error resilience**: Degrades gracefully

---

### 2. `services/ai/routing.py` - Rule-Based Routing

**Purpose**: Decides which agents run based on keywords (no AI needed).

```python
# Task keywords (action verbs)
TASK_TRIGGER_KEYWORDS = [
    "send", "call", "review", "submit", "prepare",
    "confirm", "reply", "fix", "finish", "book",
    "pay", "remind", "follow up", "let me know",
    "check", "draft", "create", "email",
]

# Time keywords
TIME_EXPRESSION_KEYWORDS = [
    "tonight", "today", "tomorrow", "asap",
    "right now", "immediately", "this week",
    "next week", "next month", "eod",
    # ... more
]

# Trivial phrases (skip deep analysis)
TRIVIAL_PHRASES = {
    "ok", "okay", "hi", "hello", "hey",
    "yes", "yeah", "yep", "no", "nope",
    "thanks", "thank you", "ty", "thx",
    "sure", "done", "bye", "k", "got it",
    "sounds good", "fine", "good", "great",
}

def decide_routing(content: str, message_type: str = "text") -> RoutingDecision:
    # Decision table:
    
    # 1. No analyzable content / media-only
    if message_type != "text" or not content.strip():
        return RoutingDecision(
            needs_analysis=False,
            needs_llm=False,
            reason="no analyzable content",
        )
    
    task_triggers = has_trigger(content, TASK_TRIGGER_KEYWORDS)
    time_triggers = has_trigger(content, TIME_EXPRESSION_KEYWORDS)
    
    # 2. Non-Latin script (Arabic, Cyrillic, etc.)
    if has_non_latin_script(content):
        return RoutingDecision(
            needs_analysis=True,
            needs_llm=True,
            run_summary=True,
            run_task_extraction=True,
            run_deadline_detection=True,
            run_recommended_action=True,
            reason="non_latin_script",
        )
        # Full analysis - keywords don't work for non-English
    
    # 3. Trivial phrase
    if looks_trivial(content, task_triggers, time_triggers):
        return RoutingDecision(
            needs_analysis=True,
            needs_llm=False,              # No LLM call!
            run_summary=True,
            reason="trivial",
        )
    
    # 4. Has task keywords and/or time keywords
    return RoutingDecision(
        needs_analysis=True,
        needs_llm=True,
        run_summary=True,
        run_task_extraction=bool(task_triggers),        # Only if has task keywords
        run_deadline_detection=bool(time_triggers),     # Only if has time keywords
        run_recommended_action=bool(task_triggers),     # Only if has task keywords
        reason="action" if task_triggers else "deadline",
        triggers=task_triggers + time_triggers,
    )

def looks_trivial(content: str, task_triggers: list, time_triggers: list) -> bool:
    # Exact phrase match in TRIVIAL_PHRASES
    if _tokens(content) in TRIVIAL_PHRASES:
        return True
    
    # Very short (≤20 chars) with no signals
    if len(_normalize(content)) <= 20 and not task_triggers and not time_triggers:
        return True
    
    return False
```

**Examples**:

```python
# Example 1: Trivial
decide_routing("ok", "text")
# Result: needs_llm=False, run_summary=True (deterministic)
# Cost: $0

# Example 2: Task only
decide_routing("Send me the report", "text")
# Result: needs_llm=True, run_task_extraction=True, run_recommended_action=True
# Agents: Priority + Summary + Task Extraction + Action (deadline skipped)

# Example 3: Deadline only
decide_routing("Meeting tomorrow", "text")
# Result: needs_llm=True, run_deadline_detection=True
# Agents: Priority + Summary + Deadline Detection (task skipped)

# Example 4: Full analysis
decide_routing("Send the report by tomorrow", "text")
# Result: needs_llm=True, all agents=True
# Agents: All 5
```

**Why we created this**:
- **Cost optimization**: Skip LLM for 20% of messages
- **Selective analysis**: Only run needed agents
- **Fast**: Pure keyword matching (no AI)
- **Transparent**: Routing recorded in database

---

### 3. `services/ai/analyzer.py` - Analysis Engine

**Purpose**: Calls the LLM provider and processes results.

```python
async def analyze_message(
    message_content: str,
    message_id: str = None,
    user_id: str = None,
    run_tasks: bool = True,
    routing: RoutingDecision | None = None,
    context_messages: list[dict] | None = None,
) -> dict:
    provider = get_provider()  # Groq provider
    
    try:
        logger.info("Starting AI analysis (%d chars)", len(message_content))
        
        # SINGLE LLM call - all agents in one prompt
        if context_messages is None:
            result = await provider.analyze(message_content)
        else:
            result = await provider.analyze(
                message_content,
                context=context_messages,
                current_message_id=message_id
            )
        # ONE API call returns: priority, summary, tasks, deadlines, actions
        
        recommendation = result.recommended_actions[0] if result.recommended_actions else ""
        
        analysis = {
            "priority": result.priority,                    # "urgent"
            "confidence": result.confidence,                # 0.9
            "explanation": result.explanation,              # "Why urgent"
            "summary": result.summary,                      # One sentence
            "recommended_action": recommendation,           # "Send report"
            "recommended_actions": list(result.recommended_actions),
            "tasks_extracted": result.tasks_extracted,      # [{"description": "..."}]
            "deadlines": result.deadlines,                  # ["tomorrow"]
            "context_updates": list(getattr(result, "context_updates", [])),
            "provider": "groq",
            "analyzed_at": datetime.now(timezone.utc),
            "status": "completed",
        }
        
        # Gate skipped agents FIRST
        _gate_outputs(analysis, routing)
        # If routing skipped task_extraction, clear tasks_extracted
        
        # Compute "needs attention" flag
        analysis.update(evaluate_attention(analysis))
        
        logger.info(
            "Analysis complete: priority=%s, tasks=%d, flagged=%s",
            analysis["priority"],
            len(analysis["tasks_extracted"]),
            analysis["needs_attention"],
        )
        
        # Store extracted tasks
        if message_id and run_tasks and result.tasks_extracted:
            if not user_id:
                logger.warning("Skipping task creation: no user_id")
            else:
                preview = message_content[:80] + ("..." if len(message_content) > 80 else "")
                task_docs = []
                for task in result.tasks_extracted:
                    task_docs.append({
                        "user_id": user_id,
                        "description": task["description"],
                        "deadline": task.get("deadline"),
                        "priority_indicator": task.get("priority_indicator"),
                        "requires_action": True,
                        "status": "pending",
                        "source_message_id": message_id,
                        "source_message_preview": preview,
                        "created_at": datetime.now(timezone.utc),
                    })
                if task_docs:
                    await tasks_collection.insert_many(task_docs)
                    logger.info("Stored %d tasks", len(task_docs))
        
        return analysis
        
    except Exception as e:
        # Groq API failed - return fallback
        logger.error("AI analysis FAILED: %s", e, exc_info=True)
        return {
            "priority": "normal",
            "confidence": 0.0,
            "explanation": "Analysis failed, defaulting to normal",
            "summary": None,
            "recommended_action": "",
            "recommended_actions": [],
            "tasks_extracted": [],
            "deadlines": [],
            "context_updates": [],
            "provider": "groq",
            "analyzed_at": None,
            "status": "pending",           # Retry later
        }

def _gate_outputs(analysis: dict, routing: RoutingDecision | None) -> dict:
    # Clear outputs of skipped agents
    if routing is None:
        return analysis
    
    if not routing.run_summary:
        analysis["summary"] = None
    
    if not routing.run_task_extraction:
        analysis["tasks_extracted"] = []
    
    if not routing.run_deadline_detection:
        analysis["deadlines"] = []
    
    if not routing.run_recommended_action:
        analysis["recommended_action"] = ""
        analysis["recommended_actions"] = []
    
    return analysis
```

**Why we created this**:
- **Single call**: All agents in one prompt (cost optimization)
- **Output gating**: Only keep results from selected agents
- **Task creation**: Auto-creates tasks in database
- **Error handling**: Degrades to fallback on failure

---

### 4. `services/ai/attention.py` - Attention Rules

**Purpose**: Determines if message needs immediate attention (pure rules, no AI).

```python
NEAR_TERM_KEYWORDS = [
    "tonight", "today", "tomorrow", "asap",
    "right now", "immediately",
]

R1_REASON = "A task with a near deadline was detected."
R2_REASON = "An urgent message with an actionable task was detected."

def evaluate_attention(analysis: dict) -> dict:
    # Rule 1: Has task + near-term deadline
    has_tasks = bool(analysis.get("tasks_extracted"))
    
    if has_tasks and _near_term_deadline(analysis):
        return {
            "needs_attention": True,
            "attention_reason": R1_REASON
        }
    
    # Rule 2: Urgent priority + has task
    if has_tasks and analysis.get("priority") == "urgent":
        return {
            "needs_attention": True,
            "attention_reason": R2_REASON
        }
    
    return {
        "needs_attention": False,
        "attention_reason": ""
    }

def _near_term_deadline(analysis: dict) -> str | None:
    # Check deadlines from tasks and deadline_detection
    candidates = list(analysis.get("deadlines") or [])
    for task in analysis.get("tasks_extracted") or []:
        deadline = task.get("deadline")
        if deadline:
            candidates.append(deadline)
    
    for candidate in candidates:
        lowered = str(candidate).lower()
        if any(keyword in lowered for keyword in NEAR_TERM_KEYWORDS):
            return str(candidate)
    
    return None
```

**Examples**:

```python
# Example 1: Needs attention (R1)
analysis = {
    "priority": "important",
    "tasks_extracted": [{"description": "Send report", "deadline": "tonight"}],
}
evaluate_attention(analysis)
# Result: needs_attention=True, reason="A task with a near deadline was detected."

# Example 2: Needs attention (R2)
analysis = {
    "priority": "urgent",
    "tasks_extracted": [{"description": "Call client"}],
}
evaluate_attention(analysis)
# Result: needs_attention=True, reason="An urgent message with an actionable task was detected."

# Example 3: No attention
analysis = {
    "priority": "normal",
    "tasks_extracted": [],
}
evaluate_attention(analysis)
# Result: needs_attention=False, reason=""
```

**Why we created this**:
- **Attention inbox**: High-priority items surfaced
- **Pure rules**: Fast, deterministic, no AI
- **Explainable**: Clear reasons logged

---

### 5. `services/ai/context.py` - Thread Context Management

**Purpose**: Provides earlier messages from same thread to AI for better analysis.

```python
async def fetch_thread_context(
    user_id: str,
    thread_id: str,
    exclude_message_id: str | None = None,
    limit: int = 5,
) -> list[dict]:
    # Get last 5 messages from same thread
    # Excludes the message being analyzed
    
    flt = {"user_id": user_id, "threadId": thread_id}
    if exclude_message_id:
        flt["_id"] = {"$ne": ObjectId(exclude_message_id)}
    
    cursor = messages_collection.find(flt).sort([("received_at", -1)]).limit(limit)
    docs = await cursor.to_list(length=limit)
    
    for doc in docs:
        doc["handle"] = str(doc["_id"])[-7:]
        # Short handle for referencing in prompt: "a1b2c3d"
    
    return docs

def build_context_block(
    messages: list[dict] | None, 
    current_message_id: str | None = None
) -> str | None:
    # Render context section for prompt
    
    if not messages:
        return None
    
    lines = [CONTEXT_HEADER]
    for msg in messages:
        received = msg.get("received_at")
        received_iso = received.isoformat() if received else ""
        lines.append(
            f"[{msg['handle']}] {msg.get('sender', '')} ({received_iso}): "
            f"{msg.get('content', '')}"
        )
    
    if current_message_id:
        lines.append(
            f"[{str(current_message_id)[-7:]}] (THIS message being analyzed)"
        )
    
    lines.append(CONTEXT_RULES)
    return "\n".join(lines)

# Example output:
"""
CONTEXT — PREVIOUS MESSAGES IN THIS CONVERSATION:
[a1b2c3d] John (2024-01-15T10:00:00): We need the report
[e4f5g6h] Alice (2024-01-15T10:05:00): What's the deadline?
[i7j8k9l] John (2024-01-15T10:10:00): Tomorrow morning
[m0n1o2p] (THIS message being analyzed)

RULES:
- Use context ONLY to supply missing deadline/urgency
- NEVER override facts in current message
- context_updates must reference handle and value must be verbatim
"""

def validate_context_updates(
    candidates: list[dict],
    thread_messages: list[dict],
    current_message_id: str,
    current_content: str | None = None,
) -> list[dict]:
    # AI can suggest updates to EARLIER messages
    # Example: "John said tomorrow in message [i7j8k9l]"
    
    # STRICT validation:
    # 1. Handle must exist in fetched thread
    # 2. Can't update the message being analyzed
    # 3. Field must be allowed (deadline/priority/note)
    # 4. Source handle must exist
    # 5. Value must appear VERBATIM in source message
    
    valid: list[dict] = []
    for candidate in candidates:
        # ... validation logic ...
        valid.append({
            "target_message_id": target_id,
            "field": field,
            "value": value,
            "source_message_id": source_id,
            "reason": reason,
        })
    return valid

async def apply_context_updates(
    valid_updates: list[dict],
    current_message_id: str,
    user_id: str,
) -> int:
    # Apply validated updates as $push operations
    # Original analysis never changed - only additive
    
    applied = 0
    for update in valid_updates:
        result = await messages_collection.update_one(
            {"_id": ObjectId(update["target_message_id"]), "user_id": user_id},
            {
                "$push": {
                    "ai_analysis.context_updates": {
                        "field": update["field"],
                        "value": update["value"],
                        "source_message_id": update["source_message_id"],
                        "reason": update["reason"],
                        "applied_at": datetime.now(timezone.utc),
                    }
                }
            },
        )
        if result.modified_count:
            applied += 1
    
    return applied
```

**Example flow**:

```
Message 1: "We need the report"
  AI: priority=important, no deadline

Message 2: "What's the deadline?"
  AI: priority=normal, no deadline

Message 3: "Tomorrow morning"
  AI: priority=urgent, deadline="tomorrow morning"
  CONTEXT: Messages 1-2 included
  AI suggests: Update message 1 deadline to "tomorrow morning"
  
  Result: Message 1 updated with context_update:
    {
      field: "deadline",
      value: "tomorrow morning",
      source_message_id: "<Message 3 ID>",
      reason: "Deadline provided in follow-up",
      applied_at: "2024-01-15T10:15:00Z"
    }
```

**Why we created this**:
- **Conversation awareness**: AI sees previous messages
- **Deadline enrichment**: Follow-up message adds deadline to earlier task
- **Strict validation**: Can't invent facts, must prove from source
- **Additive only**: Original analysis preserved

---

### 6. `services/ai/providers/groq.py` - Groq LLM Provider

**Purpose**: Communicates with Groq API (using Qwen model).

```python
MODEL_NAME = "qwen/qwen3.6-27b"

# Single-call analysis prompt (all 5 agents)
ANALYSIS_PROMPT = """You are a communication analysis engine. Analyze the message below and complete ALL FOUR jobs:

1. CLASSIFY PRIORITY
2. EXTRACT ACTIONABLE TASKS WITH DEADLINES
3. WRITE A ONE-SENTENCE SUMMARY
4. RECOMMEND ONE NEXT ACTION FOR THE RECIPIENT

PRIORITY LEVELS:

URGENT - Requires immediate attention within hours.
Evidence needed:
- Explicit time pressure: "right now", "immediately", "ASAP", "urgent"
- OR deadline within 24 hours ("tonight", "today", "right now")
- AND clear consequence of delay

IMPORTANT - Requires attention within 1-3 days.
Evidence needed:
- Deadline within 1-7 days ("tomorrow", "this week", "by Friday")
- OR action required with some consequence of delay

NORMAL - Requires attention but not time-sensitive.
This is the DEFAULT when evidence is ambiguous.
- No explicit deadline
- OR deadline more than 7 days away ("next week", "next month")
- OR action requested but not time-critical

LOW - Minimal or no immediate action needed.
- No action required
- OR automated/system message
- OR informational only

TASK EXTRACTION RULES:
A task is actionable when:
- It contains a clear verb directed at the recipient (send, review, submit, prepare, confirm, call, etc.)
- It's directed at the recipient (not what the sender will do)
- It's specific enough to act on

For each task, extract:
- description: Clear, concise action description
- deadline: The exact time expression from the message, or null if none
- priority_indicator: Words suggesting urgency from the message, or null
- requires_action: Always true

CRITICAL TASK RULES:
- Only extract tasks explicitly mentioned, never invent tasks
- "I'll send you the files tomorrow" is NOT a task for the recipient
- "FYI server down tomorrow" is NOT a task (informational)
- If no clear tasks exist, return empty array
- NEVER invent deadlines. If no deadline is mentioned, deadline MUST be null
- Preserve deadline wording exactly as stated ("Tonight", "ASAP", "next week")
- NEVER convert relative expressions to dates unless explicitly told the current date

[... more rules ...]

MESSAGE TO ANALYZE:
---
{message}
---

Return ONLY a JSON object with exactly these fields:
{{"priority": "urgent", "confidence": 0.9, "explanation": "1-2 sentences", "summary": "one sentence", "tasks_extracted": [{{"description": "...", "deadline": "...", "priority_indicator": "...", "requires_action": true}}], "deadlines": ["..."], "recommended_action": "verb-first sentence"}}"""

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.model = MODEL_NAME
        self.client = AsyncGroq(api_key=api_key)
    
    async def analyze(
        self,
        message: str,
        context: list[dict] | None = None,
        current_message_id: str | None = None,
    ) -> AIAnalysisResult:
        # Build prompt with context
        prompt = ANALYSIS_PROMPT
        block = build_context_block(context, current_message_id) if context else None
        if block:
            prompt = prompt.replace(
                "MESSAGE TO ANALYZE:", 
                block + "\n\nMESSAGE TO ANALYZE:"
            )
        prompt = prompt.replace("{message}", message)
        
        # Single API call
        result = await self._complete(prompt)
        
        # Parse and validate response
        priority = normalize_priority(str(result.get("priority", "normal")))
        confidence = result.get("confidence", 0.5)
        
        tasks_raw = result.get("tasks_extracted", [])
        tasks = []
        for t in tasks_raw:
            if isinstance(t, dict):
                tasks.append({
                    "description": str(t.get("description", "")).strip(),
                    "deadline": t.get("deadline"),
                    "priority_indicator": t.get("priority_indicator"),
                    "requires_action": True,
                })
        
        action = str(result.get("recommended_action") or "").strip()
        
        return AIAnalysisResult(
            priority=priority,
            confidence=confidence,
            explanation=result.get("explanation"),
            summary=result.get("summary"),
            recommended_actions=[action] if action else [],
            tasks_extracted=tasks,
            deadlines=result.get("deadlines", []) or [],
            context_updates=result.get("context_updates", []) or [],
        )
    
    async def _complete(self, prompt: str) -> dict:
        # Call Groq API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt + "\n/no_think"}],
            temperature=0.3,
            max_tokens=4096,
        )
        raw_content = response.choices[0].message.content
        cleaned = clean_response(raw_content)
        return json.loads(cleaned)

def clean_response(text: str) -> str:
    # Remove <think> tags (model reasoning)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove markdown code blocks
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()
    # Extract JSON object
    json_match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if json_match:
        return json_match.group(0)
    return text
```

**Why we created this**:
- **Single call optimization**: All agents in one prompt
- **Context injection**: Thread messages included
- **Structured output**: Returns JSON (easy to parse)
- **Error handling**: Cleans up model response

---

## 🔄 Complete Message Flow

Let me trace a complete example from WhatsApp webhook to Dashboard display:

### Scenario: WhatsApp message received

**Step 1: WhatsApp sends webhook**

```
POST /webhooks/whatsapp
Body: {
  "object": "whatsapp_business_account",
  "entry": [{
    "changes": [{
      "value": {
        "messages": [{
          "from": "1234567890",
          "id": "wamid.ABC123",
          "timestamp": "1234567890",
          "type": "text",
          "text": {"body": "Send me the report by tomorrow morning"}
        }],
        "contacts": [{
          "profile": {"name": "John Doe"},
          "wa_id": "1234567890"
        }]
      }
    }]
  }]
}
```

**Step 2: Webhook handler validates and parses**

```python
# routes/webhooks.py
- Verify X-Hub-Signature-256 (prevent fake webhooks)
- Parse MetaWebhookPayload
- Extract: sender="John Doe", content="Send me the report by tomorrow morning"
- Find owner: user who connected WhatsApp
```

**Step 3: Ingest message**

```python
# services/webhook_ingest.py::ingest_message
- Generate message ID
- Resolve thread: Same sender within 60 minutes?
- Store message in database
- Schedule background task: _analyze_and_store
- Return 200 OK to WhatsApp (fast response)
```

**Step 4: AI analysis (background)**

```python
# services/ai/orchestrate.py::process_message
- Routing decision:
  Keywords found: "send", "tomorrow"
  Result: needs_llm=True, run_task_extraction=True, run_deadline_detection=True

- Fetch thread context: Last 5 messages from John Doe
  
- Call analyzer:
  # services/ai/analyzer.py
  - Build prompt with context
  - Call Groq API (single call)
  - Parse response:
    {
      "priority": "important",
      "confidence": 0.9,
      "explanation": "Contains clear task with near-term deadline",
      "summary": "John requests the report by tomorrow morning",
      "tasks_extracted": [{
        "description": "Send the report",
        "deadline": "tomorrow morning",
        "priority_indicator": "tomorrow",
        "requires_action": true
      }],
      "deadlines": ["tomorrow morning"],
      "recommended_action": "Send the report by tomorrow morning"
    }

- Evaluate attention:
  # services/ai/attention.py
  - Has tasks: Yes
  - Near-term deadline: "tomorrow" detected
  - Result: needs_attention=True

- Store task:
  # tasks_collection
  {
    "description": "Send the report",
    "deadline": "tomorrow morning",
    "priority_indicator": "tomorrow",
    "status": "pending",
    "source_message_id": "<message_id>"
  }

- Update message with analysis
```

**Step 5: Dashboard displays**

```typescript
// Frontend queries:
GET /messages?tab=important
Response: [
  {
    "id": "...",
    "sender": "John Doe",
    "content": "Send me the report by tomorrow morning",
    "source": "whatsapp",
    "status": "unread",
    "ai_analysis": {
      "priority": "important",
      "confidence": 0.9,
      "summary": "John requests the report by tomorrow morning",
      "tasks_extracted": [...],
      "needs_attention": true,
      "attention_reason": "A task with a near deadline was detected.",
      "routing": {
        "agents_run": ["priority", "summary", "task_extraction", "deadline_detection", "recommended_action"],
        "llm_call_used": true,
        "triggers": ["send", "tomorrow"]
      }
    }
  }
]

GET /tasks
Response: [
  {
    "id": "...",
    "description": "Send the report",
    "deadline": "tomorrow morning",
    "priority_indicator": "tomorrow",
    "status": "pending",
    "source_message_id": "..."
  }
]
```

---

## 🎓 Key Concepts Summary

### 1. **Separation of Concerns**
- **Models**: Data structure & validation
- **Routes**: HTTP endpoints
- **Services**: Business logic
- **AI**: Intelligence layer

### 2. **User Isolation**
- Every query filtered by `user_id`
- Users can never see each other's data
- Authentication required for all endpoints (except webhooks)

### 3. **AI Cost Optimization**
- Rule-based routing (20% messages skip LLM)
- Single API call per message (not 5 separate calls)
- Trivial messages handled deterministically

### 4. **Error Resilience**
- Message stored even if AI fails
- Thread resolution errors don't block ingestion
- AI failures degrade to fallback values

### 5. **Async Everything**
- FastAPI async/await
- Motor async MongoDB driver
- Background tasks for AI analysis
- Non-blocking webhook responses

### 6. **Security**
- Passwords hashed with bcrypt
- JWT tokens in HTTP-only cookies
- Webhook signature verification
- OAuth tokens encrypted in database

### 7. **Scalability**
- Database indexes for fast queries
- Background task processing
- Stateless authentication (JWT)
- MongoDB (horizontal scaling)

---

## 📝 Environment Variables

```bash
# Backend/.env

# Database
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME=communication_ai

# Authentication
JWT_SECRET=<strong-random-secret>

# AI Provider
GROQ_API_KEY=<your-groq-api-key>
GROQ_MODEL=qwen/qwen3.6-27b

# WhatsApp
WHATSAPP_VERIFY_TOKEN=<your-verify-token>
WHATSAPP_APP_SECRET=<your-app-secret>
WHATSAPP_PHONE_NUMBER_ID=<your-phone-number-id>

# Encryption
ENCRYPTION_KEY=<base64-encoded-32-byte-key>

# Thread Linking
LINK_WINDOW_MINUTES=60
```

---

## 🚀 Running the Backend

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000

# Run tests
pytest

# Run with specific timeout
pytest --timeout=300
```

---

This documentation explains every line of backend code, why each file exists, and how they all work together. The backend is a sophisticated AI-powered message analysis system with user authentication, multi-platform integration, and intelligent task extraction!
