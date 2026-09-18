export function VerdictBanner({ verdict, onRestart }) {
  const hired = verdict === 'hired'

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border px-5 py-4 ${
        hired ? 'border-emerald-700 bg-emerald-950/40' : 'border-red-700 bg-red-950/40'
      }`}
      role="alert"
    >
      <p className={`text-lg font-bold uppercase tracking-widest ${hired ? 'text-emerald-400' : 'text-red-500'}`}>
        {hired ? '✔ Qəbul olundun' : '✖ Rədd edildin'}
      </p>
      <button
        type="button"
        onClick={onRestart}
        className="rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm text-neutral-200 transition-colors hover:border-neutral-500"
      >
        Yenidən başla
      </button>
    </div>
  )
}
