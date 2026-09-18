const TONES = {
  good: { text: 'text-emerald-400', bar: 'bg-emerald-500' },
  warn: { text: 'text-amber-400', bar: 'bg-amber-500' },
  bad: { text: 'text-red-500', bar: 'bg-red-600' },
}

export function ScoreCard({ label, value, tone }) {
  const colors = TONES[tone] ?? TONES.warn

  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <h2 className="text-xs uppercase tracking-wider text-neutral-500">{label}</h2>
      <p className={`mt-2 text-4xl font-bold tabular-nums ${colors.text}`}>{value}%</p>
      <div
        className="mt-3 h-1.5 overflow-hidden rounded-full bg-neutral-800"
        role="progressbar"
        aria-label={label}
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={100}
      >
        <div
          className={`h-full rounded-full transition-[width] duration-700 ease-out ${colors.bar}`}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
