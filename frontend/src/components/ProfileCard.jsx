const SENIORITY_LABELS = {
  intern: 'Intern',
  junior: 'Junior',
  middle: 'Middle',
  senior: 'Senior',
  lead: 'Lead',
}

function Section({ title, children }) {
  return (
    <div>
      <h3 className="mb-2 text-[11px] uppercase tracking-wider text-neutral-500">{title}</h3>
      {children}
    </div>
  )
}

export function ProfileCard({ profile, fileName, onReset }) {
  const seniority = SENIORITY_LABELS[profile.seniority?.toLowerCase()] ?? profile.seniority

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-neutral-800 bg-neutral-900/60 p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-wider text-neutral-500">
            {profile.name ? `${profile.name} · ` : ''}
            {fileName}
          </p>
          <h2 className="mt-1 text-xl font-bold text-neutral-100">{profile.target_role}</h2>
          <p className="mt-1 text-sm text-red-400">
            {seniority}
            {profile.years_experience != null && ` · ~${profile.years_experience} il təcrübə`}
          </p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="rounded-lg border border-neutral-700 px-3 py-1.5 text-xs text-neutral-300 transition-colors hover:border-neutral-500"
        >
          Başqa CV
        </button>
      </div>

      {profile.summary && <p className="text-sm leading-relaxed text-neutral-300">{profile.summary}</p>}

      {profile.skills.length > 0 && (
        <Section title="Bacarıqlar">
          <ul className="flex flex-wrap gap-1.5">
            {profile.skills.map((skill) => (
              <li key={skill} className="rounded-md border border-neutral-700 bg-neutral-950 px-2 py-1 text-xs text-neutral-300">
                {skill}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {profile.focus_areas.length > 0 && (
        <Section title="Tech-Lead bunları yoxlayacaq">
          <ul className="flex flex-col gap-1.5 text-sm text-neutral-300">
            {profile.focus_areas.map((area) => (
              <li key={area} className="flex gap-2">
                <span className="text-red-500" aria-hidden="true">
                  ▸
                </span>
                {area}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  )
}
