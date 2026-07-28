import { useRef, useState } from 'react'
import { Bot, MessageCircle, Send, X } from 'lucide-react'
import { api } from '../services/api'

const initialMessages = [
  {
    from: 'bot',
    text: 'Halo! Saya asisten Sistem Penentuan Kelayakan Penerima Bantuan Sosial Desa Citorek Timur. Ada yang dapat saya bantu?',
  },
]

function Chatbot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState(initialMessages)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const conversationId = useRef(
    globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`,
  )

  const handleSubmit = async (event) => {
    event.preventDefault()
    const text = input.trim()
    if (!text || loading) return

    setMessages((previous) => [...previous, { from: 'user', text }])
    setInput('')
    setLoading(true)

    try {
      const response = await api.sendChatMessage(text, conversationId.current)
      setMessages((previous) => [...previous, { from: 'bot', text: response.reply }])
    } catch (error) {
      setMessages((previous) => [
        ...previous,
        { from: 'bot', text: error.message || 'Maaf, chatbot sedang mengalami gangguan. Silakan coba beberapa saat lagi.' },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chatbot">
      {open ? (
        <section className="chat-window">
          <div className="chat-header">
            <div>
              <Bot size={20} />
              <strong>Asisten</strong>
            </div>
            <button type="button" onClick={() => setOpen(false)} aria-label="Tutup asisten">
              <X size={18} />
            </button>
          </div>
          <div className="chat-messages">
            {messages.map((message, index) => (
              <div key={`${message.from}-${index}`} className={`chat-bubble ${message.from}`}>
                {message.text}
              </div>
            ))}
          </div>
          <form className="chat-form" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={loading ? 'Asisten sedang mengetik...' : 'Tulis pesan...'}
              disabled={loading}
            />
            <button type="submit" aria-label="Kirim pesan" disabled={loading}>
              <Send size={18} />
            </button>
          </form>
        </section>
      ) : (
        <button className="chat-landing-trigger" type="button" onClick={() => setOpen(true)}>
          <span>
            <MessageCircle size={34} />
          </span>
          <strong>Asisten</strong>
          <small>Klik untuk membuka asisten.</small>
        </button>
      )}
    </div>
  )
}

export default Chatbot
