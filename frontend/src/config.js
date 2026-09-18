export const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://127.0.0.1:8003/ws/interview'
export const INTERVIEW_ROLE = import.meta.env.VITE_INTERVIEW_ROLE ?? 'AI Engineer'

// HTTP base of the backend; derived from WS_URL unless set explicitly.
function httpOrigin(wsUrl) {
  const url = new URL(wsUrl)
  return `${url.protocol === 'wss:' ? 'https:' : 'http:'}//${url.host}`
}
export const API_URL = import.meta.env.VITE_API_URL ?? httpOrigin(WS_URL)

export const SPEECH_LANGUAGES = [
  { code: 'en-US', label: 'EN' },
  { code: 'az-AZ', label: 'AZ' },
  { code: 'tr-TR', label: 'TR' },
]
