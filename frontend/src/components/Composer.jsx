import { useState } from 'react'

export function Composer({ disabled, onSend, speech }) {
  const [text, setText] = useState('')

  const submit = () => {
    if (onSend(text)) setText('')
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  const toggleMic = () => {
    if (speech.listening) {
      speech.stopListening()
    } else {
      speech.startListening((transcript) => setText((prev) => (prev ? `${prev} ${transcript}` : transcript)))
    }
  }

  return (
    <form
      className="flex items-end gap-2"
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
    >
      <label htmlFor="answer" className="sr-only">
        Cavabın
      </label>
      <textarea
        id="answer"
        rows={2}
        value={text}
        onChange={(event) => setText(event.target.value)}
        onKeyDown={handleKeyDown}
        maxLength={4000}
        placeholder="Texniki arqumentini yaz və ya mikrofonu aktivləşdir… (Shift+Enter — yeni sətir)"
        className="min-h-14 flex-1 resize-none rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-3 text-neutral-100 transition-colors placeholder:text-neutral-600 focus:border-red-600 focus:outline-none"
      />

      {speech.canListen && (
        <button
          type="button"
          onClick={toggleMic}
          aria-pressed={speech.listening}
          title="Səslə cavab ver"
          className={`h-14 rounded-xl border px-4 text-sm font-semibold transition-colors ${
            speech.listening
              ? 'animate-pulse border-red-400 bg-red-600 text-white'
              : 'border-neutral-800 bg-neutral-900 text-neutral-300 hover:border-neutral-600'
          }`}
        >
          🎤 <span className="hidden sm:inline">{speech.listening ? 'Dinlənilir…' : 'Danış'}</span>
        </button>
      )}

      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="h-14 rounded-xl border border-red-600 bg-red-700 px-6 text-sm font-bold uppercase tracking-wider text-white transition-colors hover:bg-red-600 disabled:cursor-not-allowed disabled:border-neutral-800 disabled:bg-neutral-900 disabled:text-neutral-600"
      >
        Göndər
      </button>
    </form>
  )
}
