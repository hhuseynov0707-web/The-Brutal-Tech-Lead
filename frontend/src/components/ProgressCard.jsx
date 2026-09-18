export function ProgressCard({ turn, maxTurns }) {
  return (
    <div className="rounded-xl border border-neutral-800 bg-neutral-900/60 p-4">
      <h2 className="text-xs uppercase tracking-wider text-neutral-500">Raund</h2>
      <p className="mt-2 text-4xl font-bold tabular-nums text-neutral-100">
        {turn}
        <span className="text-lg text-neutral-600">/{maxTurns || '–'}</span>
      </p>
      <div className="mt-3 flex gap-1" aria-hidden="true">
        {Array.from({ length: maxTurns }, (_, i) => (
          <span key={i} className={`h-1.5 flex-1 rounded-full ${i < turn ? 'bg-red-600' : 'bg-neutral-800'}`} />
        ))}
      </div>
    </div>
  )
}
