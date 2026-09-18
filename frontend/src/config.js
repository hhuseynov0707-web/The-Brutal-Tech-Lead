export const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://127.0.0.1:8000/ws/interview'
export const INTERVIEW_ROLE = import.meta.env.VITE_INTERVIEW_ROLE ?? 'AI Engineer'

export const SPEECH_LANGUAGES = [
  { code: 'en-US', label: 'EN' },
  { code: 'az-AZ', label: 'AZ' },
  { code: 'tr-TR', label: 'TR' },
]
