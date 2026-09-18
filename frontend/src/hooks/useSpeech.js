import { useCallback, useEffect, useRef, useState } from 'react'

const SpeechRecognition =
  typeof window !== 'undefined' ? window.SpeechRecognition || window.webkitSpeechRecognition : undefined

const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window

/** Browser speech-to-text and text-to-speech with a shared language setting. */
export function useSpeech(lang) {
  const [listening, setListening] = useState(false)
  const [muted, setMuted] = useState(false)
  const recognitionRef = useRef(null)
  const mutedRef = useRef(muted)
  useEffect(() => {
    mutedRef.current = muted
  }, [muted])

  const speak = useCallback(
    (text) => {
      if (!canSpeak || mutedRef.current || !text) return
      window.speechSynthesis.cancel()
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = lang
      utterance.rate = 1.05
      utterance.pitch = 0.8 // a deeper, harsher tone
      window.speechSynthesis.speak(utterance)
    },
    [lang],
  )

  const toggleMute = useCallback(() => {
    setMuted((value) => {
      if (!value && canSpeak) window.speechSynthesis.cancel()
      return !value
    })
  }, [])

  const stopListening = useCallback(() => recognitionRef.current?.stop(), [])

  const startListening = useCallback(
    (onTranscript) => {
      if (!SpeechRecognition || recognitionRef.current) return
      if (canSpeak) window.speechSynthesis.cancel()

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
    [lang],
  )

  useEffect(
    () => () => {
      recognitionRef.current?.abort()
      if (canSpeak) window.speechSynthesis.cancel()
    },
    [],
  )

  return {
    canListen: Boolean(SpeechRecognition),
    canSpeak,
    listening,
    muted,
    speak,
    toggleMute,
    startListening,
    stopListening,
  }
}
