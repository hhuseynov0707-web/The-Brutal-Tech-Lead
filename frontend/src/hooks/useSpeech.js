import { useCallback, useEffect, useRef, useState } from 'react'
import { API_URL } from '../config'

const SpeechRecognition =
  typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : undefined

const canBrowserSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

const TTS_URL = `${API_URL}/tts`
const MAX_TTS_LENGTH = 2000

/**
 * Speech-to-text (browser) and text-to-speech with a shared language setting.
 * TTS uses the backend's neural voices (edge-tts) and falls back to the
 * browser's speechSynthesis if the backend cannot produce audio.
 */
export function useSpeech(lang) {
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [muted, setMuted] = useState(false)
  const recognitionRef = useRef(null)
  const audioRef = useRef(null)
  const requestRef = useRef(null)
  const mutedRef = useRef(muted)

  useEffect(() => {
    mutedRef.current = muted
  }, [muted])

  const stopSpeaking = useCallback(() => {
    requestRef.current?.abort()
    requestRef.current = null
    const audio = audioRef.current
    if (audio) {
      audio.pause()
      URL.revokeObjectURL(audio.src)
      audioRef.current = null
    }
    if (canBrowserSpeak) window.speechSynthesis.cancel()
    setSpeaking(false)
  }, [])

  const speakWithBrowser = useCallback(
    (text) => {
      if (!canBrowserSpeak) {
        setSpeaking(false)
        return
      }
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang
      utterance.pitch = 0.8
      utterance.onend = () => setSpeaking(false)
      utterance.onerror = () => setSpeaking(false)
      window.speechSynthesis.speak(utterance)
    },
    [lang],
  )

  const speak = useCallback(
    async (text) => {
      if (mutedRef.current || !text) return
      stopSpeaking()

      const controller = new AbortController()
      requestRef.current = controller
      setSpeaking(true)

      try {
        const response = await fetch(TTS_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text.slice(0, MAX_TTS_LENGTH), lang }),
          signal: controller.signal,
        })
        if (!response.ok) throw new Error(`TTS request failed with ${response.status}`)

        const blob = await response.blob()
        if (controller.signal.aborted) return

        const audio = new Audio(URL.createObjectURL(blob))
        audio.onended = () => {
          if (audioRef.current === audio) stopSpeaking()
        }
        audioRef.current = audio
        requestRef.current = null
        await audio.play()
      } catch (error) {
        if (controller.signal.aborted || error.name === 'AbortError') return
        // Autoplay was blocked (no user interaction yet) — stay quiet rather than retry.
        if (error.name === 'NotAllowedError') {
          setSpeaking(false)
          return
        }
        speakWithBrowser(text)
      }
    },
    [lang, speakWithBrowser, stopSpeaking],
  )

  const toggleMute = useCallback(() => {
    setMuted((value) => !value)
    stopSpeaking()
  }, [stopSpeaking])

  const stopListening = useCallback(() => recognitionRef.current?.stop(), [])

  const startListening = useCallback(
    (onTranscript) => {
      if (!SpeechRecognition || recognitionRef.current) return
      stopSpeaking()

      const recognition = new SpeechRecognition()
      recognition.lang = lang
      recognition.interimResults = false
      recognition.onstart = () => setListening(true)
      recognition.onend = () => {
        setListening(false)
        recognitionRef.current = null
      }
      recognition.onerror = () => recognition.stop()
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results, (result) => result[0].transcript).join(' ')
        onTranscript(transcript)
      }

      recognitionRef.current = recognition
      recognition.start()
    },
    [lang, stopSpeaking],
  )

  useEffect(
    () => () => {
      recognitionRef.current?.abort()
      stopSpeaking()
    },
    [stopSpeaking],
  )

  return {
    canListen: Boolean(SpeechRecognition),
    listening,
    speaking,
    muted,
    speak,
    stopSpeaking,
    toggleMute,
    startListening,
    stopListening,
  }
}
