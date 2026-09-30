async function req(path, opts = {}) {
  const r = await fetch('/api' + path, { credentials: 'include', headers: { 'Content-Type': 'application/json' }, ...opts, body: opts.body ? JSON.stringify(opts.body) : undefined })
  if (!r.ok) { const e = new Error((await r.json().catch(() => ({}))).detail || 'Request failed'); e.status = r.status; throw e }
  return r.json()
}
export const api = {
  me: () => req('/auth/me'), google: c => req('/auth/google', { method: 'POST', body: { credential: c } }), logout: () => req('/auth/logout', { method: 'POST' }),
  modes: () => req('/modes'), customModes: () => req('/custom-modes'),
  addCustom: b => req('/custom-modes', { method: 'POST', body: b }), delCustom: id => req('/custom-modes/' + id, { method: 'DELETE' }),
  convs: () => req('/conversations'), msgs: id => req(`/conversations/${id}/messages`),
  patchConv: (id, b) => req('/conversations/' + id, { method: 'PATCH', body: b }), delConv: id => req('/conversations/' + id, { method: 'DELETE' }),
  search: q => req('/search?q=' + encodeURIComponent(q)), patchPrefs: b => req('/preferences', { method: 'PATCH', body: b }),
}
export async function streamChat(body, signal, onEvent) {
  const r = await fetch('/api/chat/stream', { method: 'POST', credentials: 'include', signal, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!r.ok) { const detail = (await r.json().catch(() => ({}))).detail || 'Request failed'; console.error('[streamChat] HTTP error:', r.status, detail); throw new Error(detail) }
  const rd = r.body.getReader(), dec = new TextDecoder(); let buf = ''
  for (;;) {
    const { done, value } = await rd.read(); if (done) break
    buf += dec.decode(value, { stream: true }); const parts = buf.split('\n\n'); buf = parts.pop()
    for (const p of parts) {
      if (p.startsWith('data: ')) {
        const ev = JSON.parse(p.slice(6))
        if (ev.error) console.error('[streamChat] Server error event:', ev.error)
        onEvent(ev)
      } else if (p.startsWith('event: error\ndata: ')) {
        const ev = JSON.parse(p.slice(19))
        console.error('[streamChat] Structured error event:', ev)
        onEvent({ error: ev.message || 'An error occurred' })
      }
    }
  }
}
