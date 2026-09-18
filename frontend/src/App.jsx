import { useState } from 'react'
import { ChatWindow } from './components/ChatWindow'
import { Composer } from './components/Composer'
import { Header } from './components/Header'
import { ProgressCard } from './components/ProgressCard'
import { ScoreCard } from './components/ScoreCard'
import { VerdictBanner } from './components/VerdictBanner'
import { INTERVIEW_ROLE, SPEECH_LANGUAGES } from './config'
import { useInterview } from './hooks/useInterview'
import { useSpeech } from './hooks/useSpeech'

const techTone = (score) => (score >= 70 ? 'good' : score >= 40 ? 'warn' : 'bad')
const stressTone = (score) => (score <= 40 ? 'good' : score <= 70 ? 'warn' : 'bad')

export default function App() {
  const [lang, setLang] = useState(SPEECH_LANGUAGES[0].code)
  const speech = useSpeech(lang)
  const interview = useInterview({ onAgentReply: speech.speak })
  const { scores, progress } = interview

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col gap-4 p-4 sm:p-6">
      <Header
        role={INTERVIEW_ROLE}
        readyState={interview.readyState}
        lang={lang}
        onLangChange={setLang}
        muted={speech.muted}
        onToggleMute={speech.toggleMute}
        canSpeak={speech.canSpeak}
      />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <ScoreCard label="Texniki dəqiqlik" value={scores.tech} tone={techTone(scores.tech)} />
        <ScoreCard label="Stres səviyyəsi" value={scores.stress} tone={stressTone(scores.stress)} />
        <ProgressCard turn={progress.turn} maxTurns={progress.maxTurns} />
      </div>

      <ChatWindow messages={interview.messages} typing={interview.awaitingReply && interview.isConnected} />

      {interview.verdict ? (
        <VerdictBanner verdict={interview.verdict} onRestart={interview.restart} />
      ) : (
        <Composer disabled={!interview.canAnswer} onSend={interview.sendAnswer} speech={speech} />
      )}
    </div>
  )
}
