import logging, time, random
from google import genai
from google.genai import types
from .config import settings

log = logging.getLogger("gemini")

# ---- Startup validation ----
if settings.gemini_api_key:
    log.info("GEMINI_API_KEY is set (length=%d, starts=%s…)", len(settings.gemini_api_key), settings.gemini_api_key[:6])
else:
    log.error("GEMINI_API_KEY is NOT set — all chat requests will fail!")

log.info("Using model: %s", settings.gemini_model)

client = genai.Client(api_key=settings.gemini_api_key)
MAX_MSGS, MAX_CHARS = 30, 24000

# Status codes that are safe to retry
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def build_contents(history):
    """
    Build a clean contents array from message history.
    Ensures:
      1. No blank/empty messages
      2. Proper alternation (user -> model -> user -> model)
      3. First message is always from 'user'
      4. Capped at MAX_MSGS and MAX_CHARS
    """
    out = []
    for m in history:
        if not m.content or not m.content.strip():
            continue
        role = "user" if m.role == "user" else "model"
        # Merge consecutive same-role messages
        if out and out[-1].role == role:
            out[-1].parts[0].text += "\n\n" + m.content.strip()
        else:
            out.append(types.Content(role=role, parts=[types.Part(text=m.content.strip())]))

    # Ensure first message is from user
    if out and out[0].role != "user":
        out.pop(0)

    # Ensure last message is from user (Gemini requires this)
    while out and out[-1].role != "user":
        out.pop()

    # Cap by count and character budget
    final_out, total = [], 0
    for c in reversed(out[-MAX_MSGS:]):
        total += len(c.parts[0].text)
        if total > MAX_CHARS and final_out:
            break
        final_out.append(c)

    final_out = list(reversed(final_out))

    # Re-enforce: first message must be user
    if final_out and final_out[0].role != "user":
        final_out.pop(0)

    return final_out


def _is_retryable(exc) -> bool:
    """Check if an exception is retryable based on status code or message."""
    status = getattr(exc, 'status_code', None) or getattr(exc, 'code', None)
    if isinstance(status, int) and status in RETRYABLE_STATUSES:
        return True
    msg = str(exc).lower()
    return any(kw in msg for kw in ['429', '500', '502', '503', '504', 'overloaded', 'resource exhausted', 'deadline', 'timeout'])


async def stream(system_prompt, history):
    """Yield text chunks. Retries only before the first chunk arrives."""
    if not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is missing or undefined.")

    contents = build_contents(history)

    # Guard: Gemini rejects an empty contents array with a 400
    if not contents:
        log.error("build_contents() produced an empty list — history had %d messages", len(history))
        raise ValueError("Cannot call Gemini with an empty contents array. The conversation history may be corrupt or empty.")

    cfg = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=1024,
        temperature=0.7,
        http_options=types.HttpOptions(timeout=30_000),
    )

    log.info(
        "Gemini request: model=%s, system_prompt_len=%d, contents_len=%d, first_role=%s, last_role=%s",
        settings.gemini_model, len(system_prompt), len(contents),
        contents[0].role if contents else "N/A",
        contents[-1].role if contents else "N/A",
    )

    import asyncio
    
    models_to_try = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model != settings.gemini_model:
        models_to_try.append(settings.gemini_fallback_model)

    last_error = None
    for m_idx, current_model in enumerate(models_to_try):
        max_retries = 3
        for attempt in range(max_retries):
            started = False
            try:
                log.info("Gemini request: model=%s attempt=%d", current_model, attempt + 1)
                response = await client.aio.models.generate_content_stream(
                    model=current_model,
                    contents=contents,
                    config=cfg,
                )
                async for ch in response:
                    if ch.text:
                        started = True
                        yield ch.text
                return  # success

            except Exception as e:
                status = getattr(e, 'status_code', None) or getattr(e, 'code', None)
                body = getattr(e, 'body', None) or getattr(e, 'message', str(e))
                log.error(
                    "Gemini API Error: model=%s attempt=%d status=%s message=%s",
                    current_model, attempt + 1, status, body
                )
                last_error = e

                # If we already streamed some content, don't retry (partial response is saved)
                if started:
                    log.warning("Partial response was already streamed — not retrying.")
                    raise

                # Check if error is retryable
                is_transient = _is_retryable(e)
                if not is_transient:
                    log.error("Non-retryable error on %s. Moving to fallback if available.", current_model)
                    break  # Move to next model immediately

                if attempt == max_retries - 1:
                    log.warning("Exhausted %d attempts for %s.", max_retries, current_model)
                    break  # Move to next model

                # Exponential backoff with jitter
                delay = min(2.0 * (2 ** attempt) + random.uniform(0, 1), 10.0)
                log.info("Retrying %s in %.1fs…", current_model, delay)
                await asyncio.sleep(delay)

    # If we get here, all models failed
    log.error("All models failed. Raising final error.")
    if last_error is not None:
        raise last_error
    raise RuntimeError("All models failed, but no specific error was captured.")
