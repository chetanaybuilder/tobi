import { useEffect, useRef, useState, useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import { api, streamChat } from './api.js'
const CID = import.meta.env.VITE_GOOGLE_CLIENT_ID
const ORBIT = ['CODING', 'STUDY', 'RESEARCH', 'CREATIVE', 'BUSINESS', 'PLANNING']

function Core() {
  return (<div className="scene" aria-hidden="true"><div className="core"/>
    {ORBIT.map((n, i) => <div key={n} className="ring" style={{ '--a': `${i * 60}deg`, '--d': `${i * -4}s` }}><span className="chip">{n}</span></div>)}</div>)
}
function Login({ onUser }) {
  const [err, setErr] = useState('')
  useEffect(() => {
    const s = document.createElement('script'); s.src = 'https://accounts.google.com/gsi/client'; s.async = true
    s.onload = () => {
      window.google.accounts.id.initialize({ client_id: CID, callback: async r => { try { onUser(await api.google(r.credential)) } catch (e) { setErr(e.message) } } })
      window.google.accounts.id.renderButton(document.getElementById('gbtn'), { theme: 'filled_black', size: 'large', shape: 'pill' })
    }
    document.body.appendChild(s); return () => s.remove()
  }, [])
  return (<main className="login"><Core/><h1>One AI. Many minds.</h1>
    <p>Twenty-eight specialist modes, one workspace. Sign in to enter.</p>
    <div id="gbtn"/>{err && <p role="alert" className="err">{err}</p>}</main>)
}
function Modes({ modes, custom, current, onPick, onClose, favs, toggleFav, onCustom }) {
  const [q, setQ] = useState(''), [cat, setCat] = useState('All')
  const all = useMemo(() => [...modes, ...custom], [modes, custom])
  const cats = ['All', ...new Set(all.map(m => m.category)), 'Favorites']
  const list = all.filter(m => (cat === 'All' || (cat === 'Favorites' ? favs.includes(m.slug) : m.category === cat)) && (m.name + m.description).toLowerCase().includes(q.toLowerCase()))
  return (<div className="overlay" role="dialog" aria-modal="true" aria-label="Choose a mode" onClick={onClose}><div className="panel" onClick={e => e.stopPropagation()}>
    <div className="row"><input autoFocus placeholder="Search modes" value={q} onChange={e => setQ(e.target.value)}/><button onClick={onCustom}>Create mode</button><button onClick={onClose} aria-label="Close">✕</button></div>
    <div className="cats">{cats.map(c => <button key={c} className={c === cat ? 'on' : ''} onClick={() => setCat(c)}>{c}</button>)}</div>
    <div className="grid">{list.map(m => (<div key={m.slug} className={'card' + (m.slug === current ? ' on' : '')}>
      <button className="cardmain" onClick={() => { onPick(m.slug); onClose() }}><b>{m.icon} {m.name}</b><span>{m.description}</span><small>{m.category}{m.suggested_prompts?.[0] ? ` — “${m.suggested_prompts[0]}”` : ''}</small></button>
      <button className="fav" aria-label="Toggle favorite" aria-pressed={favs.includes(m.slug)} onClick={() => toggleFav(m.slug)}>{favs.includes(m.slug) ? '★' : '☆'}</button></div>))}</div></div></div>)
}
function CustomForm({ onSave, onClose, onDelete, existing }) {
  const [f, setF] = useState({ name: '', description: '', instructions: '', response_style: '' }); const set = k => e => setF({ ...f, [k]: e.target.value })
  return (<div className="overlay" role="dialog" aria-modal="true" onClick={onClose}><form className="panel form" onClick={e => e.stopPropagation()} onSubmit={e => { e.preventDefault(); onSave(f) }}>
    <h2>Custom mode</h2><label>Name<input required value={f.name} onChange={set('name')}/></label><label>Description<input value={f.description} onChange={set('description')}/></label>
    <label>Instructions<textarea required rows="5" value={f.instructions} onChange={set('instructions')}/></label><label>Response style<input value={f.response_style} onChange={set('response_style')}/></label>
    <div className="row"><button type="submit">Save mode</button><button type="button" onClick={onClose}>Cancel</button></div>
    {existing.length > 0 && <div className="cm">{existing.map(m => <div key={m.id} className="row"><span>{m.name}</span><button type="button" onClick={() => onDelete(m.id)}>Delete</button></div>)}</div>}</form></div>)
}
export default function App() {
  const [user, setUser] = useState(undefined), [modes, setModes] = useState([]), [custom, setCustom] = useState([])
  const [convs, setConvs] = useState([]), [active, setActive] = useState(null), [msgs, setMsgs] = useState([])
  const [mode, setMode] = useState('general'), [input, setInput] = useState(''), [busy, setBusy] = useState(false), [error, setError] = useState('')
  const [picker, setPicker] = useState(false), [cform, setCform] = useState(false), [drawer, setDrawer] = useState(false), [q, setQ] = useState(''), [hits, setHits] = useState(null), [view, setView] = useState('chat')
  const ctl = useRef(null), end = useRef(null)
  useEffect(() => { api.me().then(setUser).catch(() => setUser(null)) }, [])
  useEffect(() => { if (!user) return; api.modes().then(setModes); api.customModes().then(setCustom); refresh(); setMode(user.preferences?.default_mode || 'general') }, [user?.id])
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [msgs])
  useEffect(() => { if (!q.trim()) return setHits(null); const t = setTimeout(() => api.search(q).then(setHits).catch(() => {}), 250); return () => clearTimeout(t) }, [q])
  const refresh = () => api.convs().then(setConvs)
  const all = [...modes, ...custom], cur = all.find(m => m.slug === mode) || modes[0]
  const favs = user?.preferences?.favorites || []
  const toggleFav = async s => { const f = favs.includes(s) ? favs.filter(x => x !== s) : [...favs, s]; const p = await api.patchPrefs({ favorites: f }); setUser({ ...user, preferences: p }) }
  const open = async c => { setActive(c.id); setMode(c.mode_id); setMsgs(await api.msgs(c.id)); setDrawer(false); setView('chat') }
  const fresh = () => { setActive(null); setMsgs([]); setDrawer(false); setView('chat') }
  async function send(text, regenerate = false) {
    if (busy || (!regenerate && !text.trim())) return
    setError(''); setBusy(true); ctl.current = new AbortController()
    let base = msgs
    if (regenerate) base = msgs.filter((m, i) => !(i === msgs.length - 1 && m.role === 'assistant'))
    else base = [...msgs, { role: 'user', content: text }]
    setMsgs([...base, { role: 'assistant', content: '' }]); setInput('')
    let gotContent = false
    try {
      await streamChat({ conversation_id: active, mode_id: mode, message: text, regenerate }, ctl.current.signal, ev => {
        if (ev.conversation_id) setActive(ev.conversation_id)
        if (ev.text) { gotContent = true; setMsgs(p => { const c = [...p]; c[c.length - 1] = { ...c[c.length - 1], content: c[c.length - 1].content + ev.text }; return c }) }
        if (ev.error) { setError(ev.error); console.error('[chat] Server-side error:', ev.error) }
      })
    } catch (e) {
      if (e.name !== 'AbortError') {
        const errMsg = e.message || "The AI couldn't complete that response. Please try again."
        setError(errMsg)
        console.error('[chat] Stream exception:', e)
      }
    } finally {
      // Remove the empty assistant bubble if no content was ever streamed
      if (!gotContent) setMsgs(p => p.length > 0 && p[p.length - 1].role === 'assistant' && !p[p.length - 1].content ? p.slice(0, -1) : p)
      setBusy(false); refresh()
    }
  }
  const stop = () => ctl.current?.abort()
  const act = async (c, patch) => { await api.patchConv(c.id, patch); refresh() }
  const del = async c => { if (!confirm('Delete this conversation?')) return; await api.delConv(c.id); if (active === c.id) fresh(); refresh() }
  if (user === undefined) return <div className="login"><p>Loading…</p></div>
  if (!user) return <Login onUser={setUser}/>
  const list = (hits || convs); const shown = c => (view === 'archived') === !!c.is_archived
  return (<div className="app">
    <aside className={'side' + (drawer ? ' open' : '')} aria-label="Conversations">
      <button className="primary" onClick={fresh}>New chat</button>
      <input type="search" aria-label="Search conversations" placeholder="Search chats and messages" value={q} onChange={e => setQ(e.target.value)}/>
      <div className="tabs"><button className={view !== 'archived' ? 'on' : ''} onClick={() => setView('chat')}>Chats</button><button className={view === 'archived' ? 'on' : ''} onClick={() => setView('archived')}>Archived</button></div>
      <nav>{list.filter(shown).map(c => (<div key={c.id} className={'conv' + (c.id === active ? ' on' : '')}>
        <button className="ct" onClick={() => open(c)}>{c.is_pinned && '📌 '}{c.title}{c.snippet && <small>{c.snippet}</small>}</button>
        <span className="cactions"><button aria-label="Pin" onClick={() => act(c, { is_pinned: !c.is_pinned })}>📌</button>
          <button aria-label="Rename" onClick={() => { const t = prompt('Rename', c.title); if (t) act(c, { title: t }) }}>✎</button>
          <button aria-label="Archive" onClick={() => act(c, { is_archived: !c.is_archived })}>▣</button><button aria-label="Delete" onClick={() => del(c)}>🗑</button></span></div>))}</nav>
      <div className="me">{user.avatar_url && <img src={user.avatar_url} alt="" referrerPolicy="no-referrer"/>}<span>{user.name}<small>{user.email}</small></span>
        <button onClick={async () => { await api.logout(); setUser(null) }}>Log out</button></div>
    </aside>
    <section className="main">
      <header><button className="burger" aria-label="Menu" onClick={() => setDrawer(!drawer)}>☰</button><b>Tobi</b>
        <button className="modebtn" onClick={() => setPicker(true)}>{cur?.icon} {cur?.name} ▾</button></header>
      <div className="chat" aria-live="polite">{msgs.length === 0 && <div className="empty"><Core/><h2>{cur?.name}</h2><p>{cur?.description}</p>
        <div className="sugg">{(cur?.suggested_prompts || []).map(p => <button key={p} onClick={() => send(p)}>{p}</button>)}</div></div>}
        {msgs.map((m, i) => m.role === 'user' ? <div key={i} className="msg u">{m.content}</div> :
          <div key={i} className="msg a"><div className="who">◉ {cur?.name}</div><ReactMarkdown>{m.content || '…'}</ReactMarkdown>
            {!busy && m.content && <div className="macts"><button onClick={() => navigator.clipboard.writeText(m.content)}>Copy</button>{i === msgs.length - 1 && <button onClick={() => send('', true)}>Regenerate</button>}</div>}</div>)}
        {error && <p role="alert" className="err">{error}</p>}<div ref={end}/></div>
      <form className="composer" onSubmit={e => { e.preventDefault(); send(input) }}>
        <textarea rows="1" aria-label="Message" placeholder={`Message ${cur?.name || ''}…`} value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) } }}/>
        {busy ? <button type="button" onClick={stop}>Stop</button> : <button className="primary" type="submit" disabled={!input.trim()}>Send</button>}</form>
    </section>
    {picker && <Modes modes={modes} custom={custom} current={mode} onPick={setMode} onClose={() => setPicker(false)} favs={favs} toggleFav={toggleFav} onCustom={() => { setPicker(false); setCform(true) }}/>}
    {cform && <CustomForm existing={custom} onClose={() => setCform(false)} onSave={async f => { await api.addCustom(f); setCustom(await api.customModes()); setCform(false) }} onDelete={async id => { await api.delCustom(id); setCustom(await api.customModes()) }}/>}
  </div>)
}
