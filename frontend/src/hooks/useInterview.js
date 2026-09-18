import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { INTERVIEW_ROLE, WS_URL } from '../config'
import { ReadyState, useReconnectingSocket } from './useReconnectingSocket'

const INITIAL_SCORES = { tech: 100, stress: 0 }

let messageId = 0
const nextId = () => ++messageId

/**
 * Owns the interview WebSocket and all conversation state.
 * `onAgentReply` is called with the text of every Tech-Lead message (used for TTS).
 */
export function useInterview({ onAgentReply } = {}) {
  const [messages, setMessages] = useState([])
  const [scores, setScores] = useState(INITIAL_SCORES)
  const [progress, setProgress] = useState({ turn: 0, maxTurns: 0 })
  const [awaitingReply, setAwaitingReply] = useState(false)
  const [verdict, setVerdict] = useState(null)
  const [sessionKey, setSessionKey] = useState(0)

  const finishedRef = useRef(false)
  const onAgentReplyRef = useRef(onAgentReply)
  useEffect(() => {
    onAgentReplyRef.current = onAgentReply
  }, [onAgentReply])

  const url = useMemo(() => {
    const params = new URLSearchParams({ role: INTERVIEW_ROLE, s: String(sessionKey) })
    return `${WS_URL}?${params}`
  }, [sessionKey])

  const handleMessage = useCallback((event) => {
    let data
    try {
      data = JSON.parse(event.data)
    } catch {
      return
    }

    const type = data.type ?? 'evaluation'
    setAwaitingReply(false)
    setMessages((prev) => [...prev, { id: nextId(), role: type === 'error' ? 'system' : 'agent', type, text: data.ai_reply }])

    if (type === 'error') return

    if (data.tech_accuracy_score != null && data.stress_level_score != null) {
      setScores({ tech: data.tech_accuracy_score, stress: data.stress_level_score })
    }
    if (data.max_turns) setProgress({ turn: data.turn ?? 0, maxTurns: data.max_turns })
    if (type === 'end') {
      finishedRef.current = true
      setVerdict(data.verdict)
    }
    onAgentReplyRef.current?.(data.ai_reply)
  }, [])

  const { send, readyState } = useReconnectingSocket(url, {
    onOpen: () => {
      finishedRef.current = false
      setMessages([])
      setScores(INITIAL_SCORES)
      setProgress({ turn: 0, maxTurns: 0 })
      setVerdict(null)
      setAwaitingReply(true)
    },
    onMessage: handleMessage,
    onClose: () => setAwaitingReply(false),
    shouldReconnect: () => !finishedRef.current,
  })

  const isConnected = readyState === ReadyState.OPEN
  const canAnswer = isConnected && !awaitingReply && !verdict

  const sendAnswer = useCallback(
    (text) => {
      const trimmed = text.trim()
      if (!trimmed || !canAnswer) return false
      if (!send(JSON.stringify({ type: 'answer', text: trimmed }))) return false
      setMessages((prev) => [...prev, { id: nextId(), role: 'candidate', type: 'answer', text: trimmed }])
      setAwaitingReply(true)
      return true
    },
    [canAnswer, send],
  )

  const restart = useCallback(() => setSessionKey((key) => key + 1), [])

  return {
    messages,
    scores,
    progress,
    verdict,
    awaitingReply,
    readyState,
    isConnected,
    canAnswer,
    sendAnswer,
    restart,
  }
}
