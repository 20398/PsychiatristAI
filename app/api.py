from fastapi import FastAPI, Depends, HTTPException, status, Form, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import os
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timedelta
import time
import secrets
from typing import Optional

# Auth imports
from passlib.context import CryptContext
from jose import JWTError, jwt

from .database import (
    get_db, init_db, User, UserProfile, Gender, Session as DBSession,
    ShortTermMemory, SessionLog, CrisisEvent, ConversationMetrics
)
from .therapy_agent import classify_message, select_strategy, generate_response

app = FastAPI()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ============================================================================
# AUTHENTICATION SETUP
# ============================================================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# ============================================================================
# AUTH UTILITIES
# ============================================================================
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(security), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

async def get_current_user_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalars().first()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
    return profile

@app.on_event("startup")
async def on_startup():
    pass  # Remove init_db call for now

# ============================================================================
# PYDANTIC MODELS
# ============================================================================
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    gender_id: int

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default_session"

class ChatResponse(BaseModel):
    answer: str

class GenderResponse(BaseModel):
    id: int
    name: str
    description: str

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================
@app.post("/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Check if user exists
        result = await db.execute(select(User).where(User.email == user_data.email))
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Validate password length
        if len(user_data.password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            email=user_data.email,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone=user_data.phone,
            gender_id=user_data.gender_id
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        # Store session
        session = DBSession(
            user_id=user.id,
            token=access_token,
            expires_at=datetime.utcnow() + access_token_expires
        )
        db.add(session)
        await db.commit()
        
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        # Log the actual error and return a meaningful message
        print(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalars().first()
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    # Store session
    session = DBSession(
        user_id=user.id,
        token=access_token,
        expires_at=datetime.utcnow() + access_token_expires
    )
    db.add(session)
    await db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/genders")
async def get_genders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Gender))
    genders = result.scalars().all()
    return [GenderResponse(id=g.id, name=g.name, description=g.description) for g in genders]

@app.get("/auth/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    return {"user": {"id": current_user.id, "email": current_user.email, "first_name": current_user.first_name}}

# ============================================================================
# FRONTEND ENDPOINTS
# ============================================================================
@app.get("/", response_class=HTMLResponse)
async def landing_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Therapy Chat - Login</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="auth-container">
            <div class="auth-card">
                <h1>Welcome to Therapy Chat</h1>
                <p>Your AI-powered therapy assistant</p>
                
                <div class="auth-buttons">
                    <button onclick="showLogin()" class="btn-primary">Login</button>
                    <button onclick="showRegister()" class="btn-secondary">Create Account</button>
                </div>
                
                <div class="google-auth">
                    <button onclick="googleLogin()" class="btn-google">
                        Continue with Google
                    </button>
                </div>
            </div>
        </div>
        
        <script src="/static/auth.js"></script>
    </body>
    </html>
    """

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(current_user: User = Depends(get_current_user)):
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Therapy Chat</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="app-container">
            <header class="chat-header">
                <div class="logo">
                    <div class="logo-icon"></div>
                    <h1>Therapy Chat</h1>
                </div>
                <div class="user-info">
                    <span>Welcome, {current_user.first_name}</span>
                    <button onclick="logout()" class="btn-logout">Logout</button>
                </div>
            </header>

            <main class="chat-container">
                <div id="chat-messages" class="chat-messages">
                    <div class="message assistant-message initial-message">
                        <div class="avatar assistant-avatar">T</div>
                        <div class="message-content">
                            Hello {current_user.first_name}! I'm your therapy assistant. How are you feeling today?
                        </div>
                    </div>
                </div>
                
                <div class="typing-indicator" id="typing-indicator" style="display: none;">
                    <span></span><span></span><span></span>
                </div>
            </main>

            <footer class="input-area">
                <form id="chat-form">
                    <div class="input-wrapper">
                        <input type="text" id="user-input" placeholder="Share what's on your mind..." autocomplete="off">
                        <button type="submit" id="send-button" disabled>
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M22 2L11 13M22 2L15 22L11 13M11 13L2 9L22 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    </div>
                </form>
            </footer>
        </div>
        
        <script src="/static/script.js"></script>
    </body>
    </html>
    """

# ============================================================================
# CHAT ENDPOINT
# ============================================================================
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest, 
    user_profile: UserProfile = Depends(get_current_user_profile),
    db: AsyncSession = Depends(get_db)
):
    """Main chat endpoint - handles conversation, crisis detection, and data persistence"""
    start_time = time.time()
    
    try:
        # ========== STEP 1: User profile is already fetched ==========
        user = user_profile
        
        # ========== STEP 2: Fetch or create session (short-term memory) ==========
        result = await db.execute(select(ShortTermMemory).where(ShortTermMemory.session_id == request.session_id))
        session = result.scalars().first()
        
        if not session:
            session = ShortTermMemory(
                session_id=request.session_id,
                user_profile_id=user.id,  # user is UserProfile, id is profile id
                messages=[],
                stage="exploration"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        
        # ========== STEP 3: Format conversation history ==========
        history_str = " | ".join([f"{msg['role']}: {msg['content']}" for msg in session.messages[-4:]])
        if not history_str:
            history_str = "No prior context."

        # ========== STEP 4: NLP Pipeline Execution ==========
        
        # A. Classify emotion & intent
        db_latency_start = time.time()
        classification = await classify_message(request.query)
        db_latency = (time.time() - db_latency_start) * 1000
        
        # B. Select therapeutic strategy
        strategy = await select_strategy(
            emotion=classification.primary_emotion,
            intent=classification.intent,
            stage=session.stage
        )
        
        # C. Generate response
        response_start = time.time()
        response_text = await generate_response(
            user_input=request.query,
            classification=classification,
            stage=session.stage,
            strategy=strategy,
            short_term_memory=history_str
        )
        response_time = (time.time() - response_start) * 1000
        
        # ========== STEP 5: Crisis Event Logging ==========
        if classification.crisis_risk_level in ["Medium", "High"]:
            crisis_event = CrisisEvent(
                user_profile_id=user.id,
                session_id=request.session_id,
                risk_level=classification.crisis_risk_level,
                trigger_message=request.query,
                confidence_score=0.95,  # Can be enhanced with actual confidence from LLM
                crisis_indicators=[classification.primary_emotion],
                response_given=response_text,
                response_strategy="immediate_escalation",
                resources_provided=["988", "crisis_text_line"],
                follow_up_recommended=True,
                follow_up_status="pending"
            )
            db.add(crisis_event)
            
            # Update user's crisis tracking
            user.total_crisis_events += 1
            user.last_crisis_event_at = datetime.utcnow()
            user.last_assessed_risk = classification.crisis_risk_level
            
            await db.commit()
        
        # ========== STEP 6: Update Session Memory ==========
        # Add messages to conversation history
        new_messages = list(session.messages) if session.messages else []
        new_messages.append({
            "role": "user",
            "content": request.query,
            "timestamp": datetime.utcnow().isoformat(),
            "emotion": classification.primary_emotion
        })
        new_messages.append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": strategy
        })
        
        session.messages = new_messages
        session.turn_count += 1
        session.last_emotion_detected = classification.primary_emotion
        session.last_crisis_risk_level = classification.crisis_risk_level
        session.updated_at = datetime.utcnow()
        
        # ========== STEP 7: Update Conversation Stage ==========
        if session.turn_count > 3 and session.stage == "exploration":
            session.stage = "understanding"
        elif session.turn_count > 6 and session.stage == "understanding":
            session.stage = "guidance"
        
        db.add(session)
        await db.commit()
        
        # ========== STEP 8: Log Conversation Metrics ==========
        total_latency = (time.time() - start_time) * 1000
        
        metrics = ConversationMetrics(
            user_profile_id=user.id,
            session_id=request.session_id,
            response_generation_time_ms=int(response_time),
            database_latency_ms=int(db_latency),
            total_latency_ms=int(total_latency),
            user_message_length=len(request.query),
            assistant_response_length=len(response_text),
            emotion_intensity_before=classification.intensity,
            emotion_intensity_after=classification.intensity,  # Can be enhanced to track changes
            lm_model_name="gemini-2.5-flash",
            lm_temperature=0.6,
            strategy_applied=strategy,
            conversation_turn=session.turn_count,
            stage_at_turn=session.stage,
            rag_was_used=False  # Can be set to True if RAG was used
        )
        db.add(metrics)
        await db.commit()
        
        # ========== STEP 9: Update User Profile Statistics ==========
        user.total_messages += 2  # User message + assistant response
        user.total_sessions = len((await db.execute(
            select(ShortTermMemory).where(ShortTermMemory.user_profile_id == user.id)
        )).scalars().all())
        user.last_session_at = datetime.utcnow()
        db.add(user)
        await db.commit()
        
        return ChatResponse(answer=response_text)
    
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Index HTML not found. Please create app/static/index.html</h1>")
