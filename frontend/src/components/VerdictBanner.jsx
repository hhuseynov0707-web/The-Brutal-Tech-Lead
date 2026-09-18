const VARIANTS = {
  hired: { label: '✔ Qəbul olundun', box: 'border-emerald-700 bg-emerald-950/40', text: 'text-emerald-400' },
  rejected: { label: '✖ Rədd edildin', box: 'border-red-700 bg-red-950/40', text: 'text-red-500' },
  interrupted: { label: 'Müsahibə dayandı', box: 'border-amber-700 bg-amber-950/40', text: 'text-amber-400' },
}

export function VerdictBanner({ verdict, onRestart, onExit }) {
  const variant = VARIANTS[verdict] ?? VARIANTS.interrupted

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border px-5 py-4 ${variant.box}`}
      role="alert"
    >
      <p className={`text-lg font-bold uppercase tracking-widest ${variant.text}`}>{variant.label}</p>
      <div className="flex gap-2">
        {verdict && (
          <button
            type="button"
            onClick={onRestart}
            className="rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm text-neutral-200 transition-colors hover:border-neutral-500"
          >
            Yenidən başla
          </button>
        )}
        <button
          type="button"
          onClick={onExit}
          className="rounded-lg border border-neutral-700 bg-neutral-900 px-4 py-2 text-sm text-neutral-200 transition-colors hover:border-neutral-500"
        >
          Yeni CV
        </button>
      </div>
    </div>
  )
}
