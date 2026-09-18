import { SPEECH_LANGUAGES } from '../config'
import { ReadyState } from '../hooks/useReconnectingSocket'

const STATUS = {
  [ReadyState.CONNECTING]: { label: 'Qoşulur…', dot: 'bg-amber-400 animate-pulse' },
  [ReadyState.OPEN]: { label: 'Canlı', dot: 'bg-emerald-400' },
  [ReadyState.CLOSING]: { label: 'Bağlanır…', dot: 'bg-amber-400' },
  [ReadyState.CLOSED]: { label: 'Bağlantı yoxdur', dot: 'bg-red-500' },
}

export function Header({ role, readyState, lang, onLangChange, muted, onToggleMute, canSpeak }) {
  const status = STATUS[readyState] ?? STATUS[ReadyState.CLOSED]

  return (
    <header className="flex flex-wrap items-center justify-between gap-4">
      <div>
        <h1 className="text-xl font-bold uppercase tracking-[0.2em] text-red-500 sm:text-2xl">The Brutal Tech-Lead</h1>
        <p className="mt-1 text-xs text-neutral-500">
          Stress müsahibəsi · <span className="text-neutral-300">{role}</span>
        </p>
      </div>

      <div className="flex items-center gap-2">
        <span
          className="flex items-center gap-2 rounded-full border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-300"
          role="status"
        >
          <span className={`size-2 rounded-full ${status.dot}`} aria-hidden="true" />
          {status.label}
        </span>

        <div className="flex rounded-full border border-neutral-800 bg-neutral-900 p-0.5" role="group" aria-label="Nitq dili">
          {SPEECH_LANGUAGES.map(({ code, label }) => (
            <button
              key={code}
              type="button"
              onClick={() => onLangChange(code)}
              aria-pressed={lang === code}
              className={`rounded-full px-2.5 py-1 text-xs transition-colors ${
                lang === code ? 'bg-red-600 text-white' : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {canSpeak && (
          <button
            type="button"
            onClick={onToggleMute}
            aria-pressed={muted}
            title={muted ? 'Səsi aç' : 'Səsi bağla'}
            className="rounded-full border border-neutral-800 bg-neutral-900 px-3 py-1.5 text-xs text-neutral-300 transition-colors hover:border-neutral-600"
          >
            {muted ? '🔇 Səssiz' : '🔊 Səsli'}
          </button>
        )}
      </div>
    </header>
  )
}
