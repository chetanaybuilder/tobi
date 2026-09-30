import logging, time, asyncio
from google import genai
from google.genai import types
from .config import settings

log = logging.getLogger("gemini")

if settings.gemini_api_key:
    log.info("GEMINI_API_KEY is set (length=%d)", len(settings.gemini_api_key))
else:
    log.error("GEMINI_API_KEY is NOT set!")

client = genai.Client(api_key=settings.gemini_api_key)
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
        model_health[model] = CircuitBreaker(settings.gemini_model_cooldown_seconds)
    return model_health[model]

def build_contents(history):
    out = []
    for m in history:
        if not m.content or not m.content.strip(): continue
        role = "user" if m.role == "user" else "model"
        if out and out[-1].role == role:
            out[-1].parts[0].text += "\n\n" + m.content.strip()
        else:
            out.append(types.Content(role=role, parts=[types.Part(text=m.content.strip())]))
    if out and out[0].role != "user": out.pop(0)
    while out and out[-1].role != "user": out.pop()
    final_out, total = [], 0
    for c in reversed(out[-MAX_MSGS:]):
        total += len(c.parts[0].text)
        if total > MAX_CHARS and final_out: break
        final_out.append(c)
    final_out = list(reversed(final_out))
    if final_out and final_out[0].role != "user": final_out.pop(0)
    return final_out

def _is_retryable(exc) -> bool:
    status = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
    if isinstance(status, int) and status in RETRYABLE_STATUSES: return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ['429', '500', '502', '503', '504', 'overloaded', 'exhausted', 'deadline', 'timeout'])

async def stream(system_prompt, history):
    if not settings.gemini_api_key: raise ValueError("GEMINI_API_KEY is missing.")
    contents = build_contents(history)
    if not contents: raise ValueError("Empty contents.")

    cfg = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=1024,
        temperature=0.7,
        http_options=types.HttpOptions(timeout=settings.gemini_request_timeout_ms),
    )

    models_to_try = []
    for m in [settings.gemini_model, settings.gemini_fallback_model, settings.gemini_emergency_model]:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    ttft_timeout = settings.gemini_first_token_timeout_ms / 1000.0

    for current_model in models_to_try:
        cb = get_cb(current_model)
        if cb.is_open():
            log.warning("Circuit breaker OPEN for %s. Skipping.", current_model)
            continue
            
        started = False
        try:
            log.info("Gemini request: model=%s", current_model)
            
            if len(contents) > 1:
                chat = client.aio.chats.create(model=current_model, config=cfg, history=contents[:-1])
                response_iter = await chat.send_message_stream(contents[-1])
            else:
                chat = client.aio.chats.create(model=current_model, config=cfg)
                response_iter = await chat.send_message_stream(contents[0])
                
            iterator = response_iter.__aiter__()
            try:
                first_chunk = await asyncio.wait_for(iterator.__anext__(), timeout=ttft_timeout)
            except asyncio.TimeoutError as e:
                log.error("Timeout waiting for first token on %s", current_model)
                raise e
            except StopAsyncIteration:
                first_chunk = None

            cb.record_success()

            if first_chunk and first_chunk.text:
                started = True
                yield first_chunk.text

            async for ch in iterator:
                if ch.text:
                    yield ch.text
                    
            return # success

        except Exception as e:
            status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
            log.error("API Error: model=%s status=%s message=%s", current_model, status, str(e))
            last_error = e

            if started:
                log.warning("Partial response streamed — not retrying.")
                raise

            if isinstance(e, asyncio.TimeoutError) or _is_retryable(e):
                cb.record_failure()
                log.warning("Transient error/timeout on %s. Failing over immediately.", current_model)
                continue # Fast failover to next model
            else:
                log.error("Non-retryable error on %s. Failing over.", current_model)
                continue

    log.error("All models failed.")
    if last_error:
        raise last_error
    raise RuntimeError("All models failed.")
