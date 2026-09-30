import json, logging
from fastapi import FastAPI, Depends, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from google.oauth2 import id_token
from google.auth.transport import requests as greq
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from . import gemini_service
from .auth import current_user, make_token, MAX_AGE
from .config import settings
from .database import get_db, SessionLocal
from .models import User, Conversation, Message, CustomMode, UserPreference
from .modes import MODES, public_modes
logging.basicConfig(level=logging.INFO); log = logging.getLogger("app")
app = FastAPI(title="Tobi API")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
@app.middleware("http")
async def headers(request: Request, call_next):
    r = await call_next(request)
    r.headers.update({"X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "same-origin"})
    return r
@app.exception_handler(Exception)
async def boom(request, exc):
    log.exception("unhandled"); return JSONResponse({"detail": "Something went wrong. Please try again."}, 500)

def conv_out(c): return dict(id=c.id, mode_id=c.mode_id, title=c.title, is_pinned=c.is_pinned, is_archived=c.is_archived, updated_at=c.updated_at.isoformat() if c.updated_at else None)
def own_conv(db, user, cid):
    c = db.get(Conversation, cid)
    if not c or c.user_id != user.id: raise HTTPException(404, "Conversation not found")
    return c
def cm_out(m): return dict(id=m.id, slug=f"custom:{m.id}", name=m.name, description=m.description, instructions=m.instructions, response_style=m.response_style, category="Custom", icon="✚", suggested_prompts=[])

# ---- auth
class GoogleIn(BaseModel): credential: str
@app.post("/api/auth/google")
def google_login(b: GoogleIn, resp: Response, db: Session = Depends(get_db)):
    try: info = id_token.verify_oauth2_token(b.credential, greq.Request(), settings.google_client_id)
    except Exception: raise HTTPException(401, "Google sign-in could not be verified")
    if not info.get("email_verified"): raise HTTPException(401, "Email not verified")
    u = db.scalar(select(User).where(User.google_id == info["sub"]))
    if not u: u = User(google_id=info["sub"], email=info["email"]); db.add(u); db.flush(); db.add(UserPreference(user_id=u.id))
    u.name, u.avatar_url, u.email = info.get("name", ""), info.get("picture"), info["email"]
    db.commit()
    resp.set_cookie("session", make_token(u.id), max_age=MAX_AGE, httponly=True, samesite="lax", secure=settings.cookie_secure)
    return me(u, db)
@app.get("/api/auth/me")
def me(u: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.scalar(select(UserPreference).where(UserPreference.user_id == u.id))
    return dict(id=u.id, name=u.name, email=u.email, avatar_url=u.avatar_url, created_at=u.created_at.isoformat(),
                preferences=dict(default_mode=p.default_mode, response_style=p.response_style, favorites=p.favorites or []) if p else {})
@app.post("/api/auth/logout")
def logout(resp: Response): resp.delete_cookie("session"); return {"ok": True}

# ---- modes
@app.get("/api/modes")
def modes(u: User = Depends(current_user)): return public_modes()
class CMIn(BaseModel):
    name: str = Field(min_length=1, max_length=80); description: str = Field("", max_length=300)
    instructions: str = Field(min_length=1, max_length=6000); response_style: str = Field("", max_length=300)
@app.get("/api/custom-modes")
def cm_list(u: User = Depends(current_user), db: Session = Depends(get_db)):
    return [cm_out(m) for m in db.scalars(select(CustomMode).where(CustomMode.user_id == u.id))]
@app.post("/api/custom-modes")
def cm_new(b: CMIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    m = CustomMode(user_id=u.id, **b.model_dump()); db.add(m); db.commit(); return cm_out(m)
def own_cm(db, u, mid):
    m = db.get(CustomMode, mid)
    if not m or m.user_id != u.id: raise HTTPException(404, "Mode not found")
    return m
@app.patch("/api/custom-modes/{mid}")
def cm_edit(mid: str, b: CMIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    m = own_cm(db, u, mid)
    for k, v in b.model_dump().items(): setattr(m, k, v)
    db.commit(); return cm_out(m)
@app.delete("/api/custom-modes/{mid}")
def cm_del(mid: str, u: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(own_cm(db, u, mid)); db.commit(); return {"ok": True}

# ---- preferences
class PrefIn(BaseModel):
    default_mode: str | None = Field(None, max_length=80); response_style: str | None = Field(None, max_length=300); favorites: list[str] | None = None
@app.get("/api/preferences")
def pref_get(u: User = Depends(current_user), db: Session = Depends(get_db)): return me(u, db)["preferences"]
@app.patch("/api/preferences")
def pref_set(b: PrefIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    p = db.scalar(select(UserPreference).where(UserPreference.user_id == u.id))
    for k, v in b.model_dump(exclude_none=True).items(): setattr(p, k, v)
    db.commit(); return me(u, db)["preferences"]

# ---- conversations
class ConvIn(BaseModel): mode_id: str = "general"; title: str = "New chat"
class ConvPatch(BaseModel):
    title: str | None = Field(None, max_length=200); is_pinned: bool | None = None; is_archived: bool | None = None; mode_id: str | None = None
@app.get("/api/conversations")
def conv_list(u: User = Depends(current_user), db: Session = Depends(get_db)):
    q = select(Conversation).where(Conversation.user_id == u.id).order_by(Conversation.is_pinned.desc(), Conversation.updated_at.desc()).limit(200)
    return [conv_out(c) for c in db.scalars(q)]
@app.post("/api/conversations")
def conv_new(b: ConvIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = Conversation(user_id=u.id, mode_id=b.mode_id, title=b.title); db.add(c); db.commit(); return conv_out(c)
@app.get("/api/conversations/{cid}")
def conv_get(cid: str, u: User = Depends(current_user), db: Session = Depends(get_db)): return conv_out(own_conv(db, u, cid))
@app.patch("/api/conversations/{cid}")
def conv_patch(cid: str, b: ConvPatch, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = own_conv(db, u, cid)
    for k, v in b.model_dump(exclude_none=True).items(): setattr(c, k, v)
    db.commit(); return conv_out(c)
@app.delete("/api/conversations/{cid}")
def conv_del(cid: str, u: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(own_conv(db, u, cid)); db.commit(); return {"ok": True}
@app.get("/api/conversations/{cid}/messages")
def msgs(cid: str, u: User = Depends(current_user), db: Session = Depends(get_db)):
    c = own_conv(db, u, cid); return [dict(id=m.id, role=m.role, content=m.content, created_at=m.created_at.isoformat()) for m in c.messages]
@app.get("/api/search")
def search(q: str, u: User = Depends(current_user), db: Session = Depends(get_db)):
    q = q.strip()[:100]
    if not q: return []
    like = f"%{q.replace('%', '').replace('_', '')}%"
    rows = db.execute(select(Conversation, Message).outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == u.id, or_(Conversation.title.ilike(like), Conversation.mode_id.ilike(like), Message.content.ilike(like)))
        .order_by(Conversation.updated_at.desc()).limit(60)).all()
    seen, out = set(), []
    for c, m in rows:
        if c.id in seen: continue
        seen.add(c.id); out.append(dict(**conv_out(c), snippet=(m.content[:160] if m else None), date=c.updated_at.isoformat()))
    return out

# ---- chat
class ChatIn(BaseModel):
    conversation_id: str | None = None; mode_id: str = "general"
    message: str = Field("", max_length=12000); regenerate: bool = False
def resolve_prompt(db, u, mode_id, style):
    if mode_id.startswith("custom:"):
        m = own_cm(db, u, mode_id[7:])
        p = f"You are a custom AI mode named {m.name}.\n{m.instructions}\nResponse style: {m.response_style}"
    elif mode_id in MODES: p = MODES[mode_id]["system_prompt"]
    else: raise HTTPException(400, "Unknown mode")
    return p + (f"\nUser's preferred response style: {style}" if style else "")
@app.post("/api/chat/stream")
def chat_stream(b: ChatIn, u: User = Depends(current_user), db: Session = Depends(get_db)):
    if b.conversation_id: c = own_conv(db, u, b.conversation_id); c.mode_id = b.mode_id
    else:
        if not b.message.strip(): raise HTTPException(400, "Message is empty")
        c = Conversation(user_id=u.id, mode_id=b.mode_id, title=b.message.strip()[:60]); db.add(c); db.flush()
    pref = db.scalar(select(UserPreference).where(UserPreference.user_id == u.id))
    system = resolve_prompt(db, u, b.mode_id, pref.response_style if pref else "")
    if b.regenerate:
        last = c.messages[-1] if c.messages else None
        if last and last.role == "assistant": db.delete(last); db.flush(); db.refresh(c)
    elif b.message.strip(): db.add(Message(conversation_id=c.id, role="user", content=b.message.strip(), meta={"mode": b.mode_id}))
    else: raise HTTPException(400, "Message is empty")
    db.commit(); cid, mode = c.id, b.mode_id
    log.info("chat_stream: user=%s cid=%s mode=%s regenerate=%s msg_len=%d", u.id, cid, mode, b.regenerate, len(b.message))
    def gen():
        s = SessionLocal(); buf = []
        try:
            hist = list(s.scalars(select(Message).where(Message.conversation_id == cid).order_by(Message.created_at)))
            log.info("chat_stream gen: %d messages in history for cid=%s", len(hist), cid)
            yield f"data: {json.dumps({'conversation_id': cid})}\n\n"
            for t in gemini_service.stream(system, hist):
                buf.append(t); yield f"data: {json.dumps({'text': t})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
            body = getattr(e, 'body', None) or getattr(e, 'message', str(e))
            log.error("Chat stream failed: type=%s status=%s message=%s", type(e).__name__, status, body)
            log.exception("stream exception details:")
            msg = "The API is currently experiencing high demand. Please try again later." if "503" in str(e) else "The AI couldn't complete that response. Please try again."
            yield f"data: {json.dumps({'error': msg})}\n\n"
        finally:  # also runs when the client hits Stop -> partial reply is kept
            if buf:
                s.add(Message(conversation_id=cid, role="assistant", content="".join(buf), meta={"mode": mode}))
                conv = s.get(Conversation, cid); conv.mode_id = mode; s.commit()
            s.close()
    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"})
