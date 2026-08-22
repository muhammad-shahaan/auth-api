import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    HTTPException,
    Header,
    Depends,
    Response
)
from supabase import create_client, Client
from pydantic import BaseModel


# =========================================================
# ENVIRONMENT SETUP
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "Supabase environment variables are missing"
    )


# =========================================================
# SUPABASE CLIENT
# =========================================================

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# FASTAPI APP
# =========================================================

app = FastAPI(
    title="Auth Practice API",
    version="1.0.0"
)


# =========================================================
# MODELS
# =========================================================

class AuthRequest(BaseModel):
    email: str
    password: str


# =========================================================
# REUSABLE AUTH DEPENDENCY
# =========================================================

def get_current_user(
    authorization: Optional[str] = Header(default=None)
):

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Access token required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Access token required"
        )

    token = authorization.replace(
        "Bearer ",
        "",
        1
    ).strip()

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
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token
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
        "message": "Protected profile accessed successfully",
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
        "message": "Welcome to your protected dashboard",
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