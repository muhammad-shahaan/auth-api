import os
import json
import time
from typing import Literal

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    Response
)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, ValidationError
from supabase import create_client, Client
from groq import Groq


# =========================================================
# ENVIRONMENT SETUP
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
AI_ENABLED = os.getenv("AI_ENABLED", "true").lower() == "true"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase environment variables are missing"
    )


# =========================================================
# CLIENTS
# =========================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

groq_client = None

if GROQ_API_KEY:
    groq_client = Groq(
        api_key=GROQ_API_KEY,
        timeout=10.0,
        max_retries=0
    )


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Auth Practice API",
    version="2.0.0"
)


# =========================================================
# SWAGGER BEARER AUTH
# =========================================================

security = HTTPBearer()


# =========================================================
# MODELS
# =========================================================

class AuthRequest(BaseModel):
    email: str
    password: str


class MessageRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000
    )


class AIJudgement(BaseModel):
    category: Literal[
        "internship",
        "job",
        "support",
        "general"
    ]

    priority: Literal[
        "low",
        "medium",
        "high"
    ]

    summary: str = Field(
        ...,
        min_length=1,
        max_length=300
    )


# =========================================================
# REUSABLE AUTH DEPENDENCY
# =========================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Access token required"
        )

    try:
        response = supabase.auth.get_user(token)

        if not response.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token"
            )

        return response.user

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


# =========================================================
# AI CLASSIFICATION FUNCTION
# =========================================================

def classify_with_ai(message: str) -> AIJudgement:

    if not AI_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="AI feature is currently disabled"
        )

    if not groq_client:
        raise HTTPException(
            status_code=503,
            detail="AI service is not configured"
        )

    prompt = f"""
You classify incoming messages.

Return ONLY valid JSON.

Allowed categories:
- internship
- job
- support
- general

Allowed priorities:
- low
- medium
- high

Required JSON format:

{{
  "category": "internship",
  "priority": "medium",
  "summary": "Short summary here"
}}

Message:
{message}
"""

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:
            response = groq_client.chat.completions.create(
               model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a message classification API. "
                            "Return only valid JSON."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0
            )

            raw_output = response.choices[0].message.content

            if not raw_output:
                raise ValueError(
                    "AI returned an empty response"
                )

            parsed_json = json.loads(raw_output)

            judgement = AIJudgement.parse_obj(
                parsed_json
            )

            return judgement

        except (
            json.JSONDecodeError,
            ValidationError,
            ValueError
        ) as error:

            print(
                f"Invalid AI output on attempt "
                f"{attempt}: {error}"
            )

            # Invalid structured output is unlikely
            # to improve forever, so retry only once.
            if attempt >= 2:
                raise HTTPException(
                    status_code=502,
                    detail=(
                        "AI returned an invalid "
                        "structured response"
                    )
                )

        except Exception as error:

            print(
                f"AI request failed on attempt "
                f"{attempt}: {error}"
            )

            if attempt == max_attempts:
                raise HTTPException(
                    status_code=503,
                    detail="AI service unavailable"
                )

            # Small backoff before retrying
            time.sleep(attempt)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Auth Practice API is running"
    }


# =========================================================
# PUBLIC ROUTE
# =========================================================

@app.get("/public/info")
def public_info():
    return {
        "message": "Welcome stranger! This info is public."
    }


# =========================================================
# AI JUDGEMENT ENDPOINT
# =========================================================

@app.post(
    "/ai/classify-message",
    response_model=AIJudgement
)
def classify_message(data: MessageRequest):

    return classify_with_ai(
        data.message.strip()
    )


# =========================================================
# SIGN UP
# =========================================================

@app.post("/auth/signup", status_code=201)
def signup(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password
        })

        return {
            "message": "User created successfully",
            "user": response.user
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =========================================================
# LOG IN
# =========================================================

@app.post("/auth/login")
def login(data: AuthRequest):

    if not data.email.strip() or not data.password.strip():
        raise HTTPException(
            status_code=400,
            detail="Email and password are required"
        )

    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if not response.session:
            raise HTTPException(
                status_code=401,
                detail="Invalid login credentials"
            )

        return {
            "access_token":
                response.session.access_token,

            "refresh_token":
                response.session.refresh_token
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid login credentials"
        )


# =========================================================
# PROTECTED PROFILE
# =========================================================

@app.get("/protected/profile")
def protected_profile(
    user=Depends(get_current_user)
):

    return {
        "message":
            "Protected profile accessed successfully",

        "user_id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }


# =========================================================
# PROTECTED DASHBOARD
# =========================================================

@app.get("/protected/dashboard")
def protected_dashboard(
    user=Depends(get_current_user)
):

    return {
        "message":
            "Welcome to your protected dashboard",

        "user_id": user.id,
        "email": user.email
    }


# =========================================================
# LOG OUT
# =========================================================

@app.post(
    "/auth/logout",
    status_code=204
)
def logout(
    user=Depends(get_current_user)
):

    try:
        supabase.auth.sign_out()

        return Response(
            status_code=204
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Logout failed"
        )