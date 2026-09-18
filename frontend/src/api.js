import { API_URL } from './config'

export const CV_ACCEPT = '.pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp'
export const CV_MAX_BYTES = 5 * 1024 * 1024

/** Upload a CV and return `{ cv_id, profile }`. Throws an Error with a user-facing message. */
export async function uploadCv(file, { signal } = {}) {
  const body = new FormData()
  body.append('file', file)

  let response
  try {
    response = await fetch(`${API_URL}/cv`, { method: 'POST', body, signal })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new Error('Serverə qoşulmaq mümkün olmadı. Backend işləyir?')
  }

  if (!response.ok) {
    let detail = `Xəta baş verdi (${response.status}).`
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') detail = data.detail
    } catch {
      // keep the generic message
    }
    throw new Error(detail)
  }
  return response.json()
}
