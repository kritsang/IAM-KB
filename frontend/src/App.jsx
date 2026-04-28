import { useState, useRef, useEffect } from 'react'
import './App.css'

const API_URL = 'https://web-production-13995.up.railway.app/query'

function getStoredAuth() {
  try { return sessionStorage.getItem('kb_auth') } catch { return null }
}

function LoginOverlay({ onLogin }) {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!user || !pass) return
    setLoading(true)
    setError('')
    const token = btoa(`${user}:${pass}`)
    try {
      const res = await fetch(API_URL.replace('/query', '/auth'), {
        headers: { Authorization: `Basic ${token}` },
      })
      if (res.ok) {
        sessionStorage.setItem('kb_auth', token)
        onLogin(token)
      } else {
        setError('Username หรือ Password ไม่ถูกต้อง')
      }
    } catch {
      setError('เชื่อมต่อ server ไม่ได้')
    }
    setLoading(false)
  }

  return (
    <div className="login-overlay">
      <div className="login-card">
        <div className="login-logo">🧠</div>
        <h2>IAM AMS Knowledge Base</h2>
        <p className="login-sub">กรุณาเข้าสู่ระบบก่อนใช้งาน</p>
        <form onSubmit={handleSubmit} className="login-form">
          <input
            type="text"
            placeholder="Username"
            value={user}
            onChange={(e) => setUser(e.target.value)}
            autoFocus
            disabled={loading}
          />
          <input
            type="password"
            placeholder="Password"
            value={pass}
            onChange={(e) => setPass(e.target.value)}
            disabled={loading}
          />
          {error && <p className="login-error">{error}</p>}
          <button type="submit" disabled={!user || !pass || loading}>
            {loading ? 'กำลังตรวจสอบ...' : 'เข้าสู่ระบบ'}
          </button>
        </form>
      </div>
    </div>
  )
}

const SUGGESTED = [
  'SAP posting error CORM month close solution',
  'EWM delivery note error solution',
  'วิธีแก้ปัญหา short dump ใน SAP',
  'REQ authorization check PR PO',
]

export default function App() {
  const [auth, setAuth] = useState(() => getStoredAuth())
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [sources, setSources] = useState([])
  const [status, setStatus] = useState('idle') // idle | searching | streaming | done | error
  const abortRef = useRef(null)

  if (!auth) return <LoginOverlay onLogin={setAuth} />

  const handleSubmit = async (e) => {
    e.preventDefault()
    const q = question.trim()
    if (!q || status === 'searching' || status === 'streaming') return

    setAnswer('')
    setSources([])
    setStatus('searching')

    abortRef.current = new AbortController()

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${auth}`,
        },
        body: JSON.stringify({ question: q }),
        signal: abortRef.current.signal,
      })

      if (res.status === 401) {
        sessionStorage.removeItem('kb_auth')
        setAuth(null)
        return
      }
      if (!res.ok) throw new Error(`Server error: ${res.status}`)

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))

          if (data.type === 'token') {
            setStatus('streaming')
            setAnswer((prev) => prev + data.content)
          } else if (data.type === 'sources') {
            setSources(data.content)
          } else if (data.type === 'done') {
            setStatus('done')
          } else if (data.type === 'error') {
            setAnswer(data.content)
            setStatus('error')
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        setAnswer('เกิดข้อผิดพลาด: ' + err.message)
        setStatus('error')
      }
    }
  }

  const handleSuggestion = (s) => {
    setQuestion(s)
  }

  const handleReset = () => {
    abortRef.current?.abort()
    setQuestion('')
    setAnswer('')
    setSources([])
    setStatus('idle')
  }

  const isLoading = status === 'searching' || status === 'streaming'

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-icon">🧠</span>
            <div>
              <h1>IAM AMS Knowledge Base</h1>
              <p>ค้นหาคำตอบจาก Solution Docs และ Tickets</p>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        <form className="search-form" onSubmit={handleSubmit}>
          <div className="search-row">
            <input
              className="search-input"
              type="text"
              placeholder="ถามคำถามเกี่ยวกับ SAP, Incidents, Solutions..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={isLoading}
            />
            <button
              className="search-btn"
              type="submit"
              disabled={!question.trim() || isLoading}
            >
              {isLoading ? '⏳' : '🔍 ค้นหา'}
            </button>
            {(answer || isLoading) && (
              <button className="reset-btn" type="button" onClick={handleReset}>
                ✕
              </button>
            )}
          </div>
        </form>

        {status === 'idle' && !answer && (
          <div className="suggestions">
            <p className="suggestions-label">ตัวอย่างคำถาม:</p>
            <div className="suggestion-chips">
              {SUGGESTED.map((s) => (
                <button
                  key={s}
                  className="chip"
                  onClick={() => handleSuggestion(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {status === 'searching' && (
          <div className="status-bar">
            <span className="spinner" /> กำลังค้นหาเอกสารที่เกี่ยวข้อง...
          </div>
        )}

        {answer && (
          <div className={`answer-card ${status === 'error' ? 'error' : ''}`}>
            <div className="answer-header">
              <span>💬 คำตอบ</span>
              {status === 'streaming' && <span className="streaming-badge">กำลังพิมพ์...</span>}
            </div>
            <div className="answer-text">
              {answer}
              {status === 'streaming' && <span className="cursor" />}
            </div>
          </div>
        )}

        {sources.length > 0 && (
          <div className="sources">
            <h3 className="sources-title">📄 แหล่งอ้างอิง ({sources.length})</h3>
            <div className="source-list">
              {sources.map((s) => (
                <div key={s.index} className="source-item">
                  <span className="source-index">[{s.index}]</span>
                  <div className="source-detail">
                    <span className="source-name">{s.source}</span>
                    <div className="source-meta">
                      {s.ticket && <span className="tag">{s.ticket}</span>}
                      {s.type && <span className="tag tag-type">{s.type}</span>}
                      <span className="similarity">
                        similarity: {s.similarity}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
