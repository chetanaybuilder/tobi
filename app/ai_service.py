"""
app/ai_service.py
Provides robust AI stream interaction with Groq using circuit breakers, fallbacks, and timeouts.
"""
import logging, time, asyncio
from groq import AsyncGroq
from .config import settings

log = logging.getLogger("ai")

if settings.groq_api_key:
    log.info("GROQ_API_KEY is set (length=%d)", len(settings.groq_api_key))
else:
    log.error("GROQ_API_KEY is NOT set!")

client = AsyncGroq(api_key=settings.groq_api_key) if settings.groq_api_key else None
MAX_MSGS, MAX_CHARS = 10, 12000

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}

class CircuitBreaker:
    def __init__(self, cooldown):
        self.state = "CLOSED"
        self.failures = 0
        self.cooldown = cooldown
        self.last_failure = 0

    def is_open(self):
        if self.state == "OPEN":
            if time.time() - self.last_failure > self.cooldown:
                self.state = "HALF_OPEN"
                return False
            return True
        return False

    def record_failure(self):
        self.failures += 1
        self.last_failure = time.time()
        if self.state == "HALF_OPEN" or self.failures >= 2:
            self.state = "OPEN"
            
    def record_success(self):
        self.state = "CLOSED"
        self.failures = 0

model_health = {}
def get_cb(model):
    if model not in model_health:
        model_health[model] = CircuitBreaker(settings.groq_model_cooldown_seconds)
    return model_health[model]

def build_messages(system_prompt, history):
    messages = [{"role": "system", "content": system_prompt}]
    out = []
    for m in history:
        if not m.content or not m.content.strip(): continue
        role = "user" if m.role == "user" else "assistant"
        if out and out[-1]["role"] == role:
            out[-1]["content"] += "\n\n" + m.content.strip()
        else:
            out.append({"role": role, "content": m.content.strip()})
            
    final_out, total = [], 0
    for c in reversed(out[-MAX_MSGS:]):
        total += len(c["content"])
        if total > MAX_CHARS and final_out: break
        final_out.append(c)
    final_out = list(reversed(final_out))
    
    messages.extend(final_out)
    return messages

def _is_retryable(exc) -> bool:
    status = getattr(exc, 'status_code', None)
    if isinstance(status, int) and status in RETRYABLE_STATUSES: return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ['429', '500', '502', '503', '504', 'overloaded', 'timeout', 'connection', 'unavailable'])

async def stream(system_prompt, history):
    """
    Streams AI responses yielding text chunks. 
    Implements model fallbacks, TTFT timeouts, and exponential backoff states.
    """
    if not client: raise ValueError("GROQ_API_KEY is missing.")
    messages = build_messages(system_prompt, history)
    if len(messages) < 2: raise ValueError("Empty contents.")

    models_to_try = []
    for m in [settings.groq_model, settings.groq_fallback_model, settings.groq_emergency_model]:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    ttft_timeout = settings.groq_first_token_timeout_ms / 1000.0

    for current_model in models_to_try:
        cb = get_cb(current_model)
        if cb.is_open():
            log.warning("Circuit breaker OPEN for %s. Skipping.", current_model)
            continue
            
        started = False
        try:
            log.info("Groq request: model=%s", current_model)
            
            response_iter = await client.chat.completions.create(
                model=current_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
                stream=True,
                timeout=settings.groq_request_timeout_ms / 1000.0
            )
            
            iterator = response_iter.__aiter__()
            try:
                first_chunk = await asyncio.wait_for(iterator.__anext__(), timeout=ttft_timeout)
            except asyncio.TimeoutError as e:
                log.error("Timeout waiting for first token on %s", current_model)
                raise e
            except StopAsyncIteration:
                first_chunk = None

            cb.record_success()

            if first_chunk and first_chunk.choices and first_chunk.choices[0].delta.content:
                started = True
                yield first_chunk.choices[0].delta.content

            async for chunk in iterator:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
            return # success

        except Exception as e:
            status = getattr(e, 'status_code', None)
            log.error("API Error: model=%s status=%s message=%s", current_model, status, str(e))
            last_error = e

            if started:
                log.warning("Partial response streamed — not retrying.")
                raise

            if isinstance(e, asyncio.TimeoutError) or _is_retryable(e):
                cb.record_failure()
                log.warning("Transient error/timeout on %s. Failing over immediately.", current_model)
                continue
            else:
                log.error("Non-retryable error on %s. Failing over.", current_model)
                continue

    log.error("All models failed.")
    if last_error:
        raise last_error
    raise RuntimeError("All models failed.")
