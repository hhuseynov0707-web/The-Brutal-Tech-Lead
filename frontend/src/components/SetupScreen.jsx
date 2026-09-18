import { useEffect, useRef, useState } from 'react'
import { CV_ACCEPT, CV_MAX_BYTES, uploadCv } from '../api'
import { ProfileCard } from './ProfileCard'

function Dropzone({ onFile, busy }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleDrop = (event) => {
    event.preventDefault()
    setDragging(false)
    const file = event.dataTransfer.files?.[0]
    if (file) onFile(file)
  }

  return (
    <button
      type="button"
      disabled={busy}
      onClick={() => inputRef.current?.click()}
      onDragOver={(event) => {
        event.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`flex w-full flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed px-6 py-12 text-center transition-colors disabled:cursor-wait ${
        dragging ? 'border-red-500 bg-red-950/20' : 'border-neutral-700 bg-neutral-900/40 hover:border-neutral-500'
      }`}
    >
      {busy ? (
        <>
          <span className="size-6 animate-spin rounded-full border-2 border-neutral-700 border-t-red-500" aria-hidden="true" />
          <span className="text-sm text-neutral-300">Tech-Lead CV-ni oxuyur…</span>
        </>
      ) : (
        <>
          <span className="text-3xl" aria-hidden="true">
            📄
          </span>
          <span className="text-sm font-semibold text-neutral-200">CV-ni bura at və ya seçmək üçün kliklə</span>
          <span className="text-xs text-neutral-500">PDF (skan da olar), DOCX, TXT, şəkil · maksimum 5 MB</span>
        </>
      )}
      <input
        ref={inputRef}
        type="file"
        accept={CV_ACCEPT}
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0]
          event.target.value = ''
          if (file) onFile(file)
        }}
      />
    </button>
  )
}

export function SetupScreen({ onStart }) {
  const [status, setStatus] = useState('idle') // idle | uploading | ready
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null) // { cvId, profile, fileName }
  const [role, setRole] = useState('')
  const abortRef = useRef(null)

  useEffect(() => () => abortRef.current?.abort(), [])

  const handleFile = async (file) => {
    setError(null)
    if (file.size > CV_MAX_BYTES) {
      setError('Fayl 5 MB-dan böyük ola bilməz.')
      return
    }

    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setStatus('uploading')
    try {
      const data = await uploadCv(file, { signal: controller.signal })
      setResult({ cvId: data.cv_id, profile: data.profile, fileName: file.name })
      setStatus('ready')
    } catch (err) {
      if (err.name === 'AbortError') return
      setError(err.message)
      setStatus('idle')
    }
  }

  const reset = () => {
    setResult(null)
    setStatus('idle')
    setError(null)
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-5">
      <div>
        <h2 className="text-lg font-bold text-neutral-100">Müsahibəyə hazırlıq</h2>
        <p className="mt-1 text-sm text-neutral-400">
          CV-ni yüklə — Tech-Lead sahəni, səviyyəni və layihələrini analiz edib suallarını ona uyğun quracaq.
        </p>
      </div>

      {result ? (
        <ProfileCard profile={result.profile} fileName={result.fileName} onReset={reset} />
      ) : (
        <Dropzone onFile={handleFile} busy={status === 'uploading'} />
      )}

      {error && (
        <p className="rounded-lg border border-red-900 bg-red-950/40 px-4 py-3 text-sm text-red-300" role="alert">
          {error}
        </p>
      )}

      {result ? (
        <button
          type="button"
          onClick={() => onStart({ cvId: result.cvId, role: result.profile.target_role })}
          className="h-14 rounded-xl border border-red-600 bg-red-700 text-sm font-bold uppercase tracking-wider text-white transition-colors hover:bg-red-600"
        >
          Müsahibəyə başla
        </button>
      ) : (
        <form
          className="flex flex-col gap-2 border-t border-neutral-800 pt-5"
          onSubmit={(event) => {
            event.preventDefault()
            if (role.trim()) onStart({ role: role.trim() })
          }}
        >
          <label htmlFor="role" className="text-xs uppercase tracking-wider text-neutral-500">
            və ya CV-siz, rol seçərək başla
          </label>
          <div className="flex gap-2">
            <input
              id="role"
              value={role}
              onChange={(event) => setRole(event.target.value)}
              maxLength={120}
              placeholder="məs. Frontend Engineer (React), DevOps, Data Analyst"
              className="h-12 flex-1 rounded-xl border border-neutral-800 bg-neutral-900 px-4 text-sm text-neutral-100 placeholder:text-neutral-600 focus:border-red-600 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!role.trim() || status === 'uploading'}
              className="h-12 rounded-xl border border-neutral-700 bg-neutral-900 px-5 text-sm text-neutral-200 transition-colors hover:border-neutral-500 disabled:cursor-not-allowed disabled:text-neutral-600"
            >
              Başla
            </button>
          </div>
        </form>
      )}

      <p className="text-xs leading-relaxed text-neutral-600">
        CV mətni analiz üçün Groq API-yə göndərilir. Serverdə fayl saxlanılmır — yalnız çıxarılmış profil 2 saat müddətinə
        yaddaşda qalır.
      </p>
    </div>
  )
}
