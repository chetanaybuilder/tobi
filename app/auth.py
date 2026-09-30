from fastapi import Cookie, Depends, HTTPException
from itsdangerous import URLSafeTimedSerializer, BadSignature
from sqlalchemy.orm import Session
from .config import settings
from .database import get_db
from .models import User
ser = URLSafeTimedSerializer(settings.session_secret, salt="session")
MAX_AGE = 60*60*24*14
def make_token(user_id): return ser.dumps(user_id)
def current_user(session: str | None = Cookie(default=None), db: Session = Depends(get_db)) -> User:
    if not session: raise HTTPException(401, "Not signed in")
    try: uid = ser.loads(session, max_age=MAX_AGE)
    except BadSignature: raise HTTPException(401, "Session expired")
    u = db.get(User, uid)
    if not u: raise HTTPException(401, "Unknown user")
    return u
