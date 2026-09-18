import { useCallback, useEffect, useRef, useState } from 'react'

export const ReadyState = {
  CONNECTING: 0,
  OPEN: 1,
  CLOSING: 2,
  CLOSED: 3,
}

const MAX_BACKOFF_MS = 10_000

/**
 * A WebSocket that reconnects with exponential backoff.
 * Handlers are read through a ref, so they may change between renders freely.
 * `shouldReconnect(closeEvent)` is consulted after every close.
 */
export function useReconnectingSocket(url, handlers) {
  const [readyState, setReadyState] = useState(ReadyState.CONNECTING)
  const socketRef = useRef(null)
  const handlersRef = useRef(handlers)

  useEffect(() => {
    handlersRef.current = handlers
  })

  useEffect(() => {
    let disposed = false
    let attempt = 0
    let retryTimer

    const connect = () => {
      const socket = new WebSocket(url)
      socketRef.current = socket
      setReadyState(ReadyState.CONNECTING)

      socket.onopen = () => {
        attempt = 0
        setReadyState(ReadyState.OPEN)
        handlersRef.current.onOpen?.()
      }
      socket.onmessage = (event) => handlersRef.current.onMessage?.(event)
      socket.onclose = (event) => {
        if (disposed) return
        setReadyState(ReadyState.CLOSED)
        handlersRef.current.onClose?.(event)
        if (handlersRef.current.shouldReconnect?.(event) ?? true) {
          const delay = Math.min(1000 * 2 ** attempt, MAX_BACKOFF_MS)
          attempt += 1
          retryTimer = setTimeout(connect, delay)
        }
      }
    }

    connect()

    return () => {
      disposed = true
      clearTimeout(retryTimer)
      socketRef.current?.close()
      socketRef.current = null
    }
  }, [url])

  const send = useCallback((data) => {
    const socket = socketRef.current
    if (socket?.readyState !== WebSocket.OPEN) return false
    socket.send(data)
    return true
  }, [])

  return { readyState, send }
}
