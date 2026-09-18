import { useEffect, useRef } from 'react'

const STYLES = {
  agent: 'self-start border-red-900/60 bg-red-950/30 text-red-100',
  candidate: 'self-end border-sky-900/60 bg-sky-950/30 text-sky-100',
  system: 'self-center border-amber-900/60 bg-amber-950/30 text-sm text-amber-200',
}

const AUTHORS = { agent: 'Tech-Lead', candidate: 'Sən', system: 'Sistem' }

function TypingIndicator() {
  return (
    <div
      className="flex items-center gap-1.5 self-start rounded-xl border border-neutral-800 px-4 py-3"
      aria-label="Tech-Lead yazır"
    >
      {[0, 150, 300].map((delay) => (
        <span
          key={delay}
          className="size-1.5 animate-bounce rounded-full bg-red-500"
          style={{ animationDelay: `${delay}ms` }}
        />
      ))}
    </div>
  )
}

export function ChatWindow({ messages, typing }) {
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, typing])

  return (
    <section
      className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto rounded-xl border border-neutral-800 bg-black/60 p-4 shadow-[0_0_40px_-10px_rgba(220,38,38,0.25)]"
      aria-live="polite"
      aria-label="Müsahibə söhbəti"
    >
      {messages.length === 0 && !typing && (
        <p className="m-auto text-center text-sm text-neutral-600">Tech-Lead otağa daxil olur…</p>
      )}

      {messages.map((msg) => (
        <article key={msg.id} className={`max-w-[85%] rounded-xl border px-4 py-3 leading-relaxed ${STYLES[msg.role]}`}>
          <header className="mb-1 text-[11px] uppercase tracking-wider opacity-60">{AUTHORS[msg.role]}</header>
          <p className="whitespace-pre-wrap break-words">{msg.text}</p>
        </article>
      ))}

      {typing && <TypingIndicator />}
      <div ref={endRef} />
    </section>
  )
}
