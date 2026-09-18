import { useInterview } from '../hooks/useInterview'
import { ChatWindow } from './ChatWindow'
import { Composer } from './Composer'
import { Header } from './Header'
import { ProgressCard } from './ProgressCard'
import { ScoreCard } from './ScoreCard'
import { VerdictBanner } from './VerdictBanner'

const techTone = (score) => (score >= 70 ? 'good' : score >= 40 ? 'warn' : 'bad')
const stressTone = (score) => (score <= 40 ? 'good' : score <= 70 ? 'warn' : 'bad')

export function InterviewScreen({ setup, headerProps, speech, onExit }) {
  const interview = useInterview({ setup, onAgentReply: speech.speak })
  const { scores, progress } = interview

  return (
    <>
      <Header {...headerProps} role={setup.role} readyState={interview.readyState} onExit={onExit} />

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <ScoreCard label="Texniki dəqiqlik" value={scores.tech} tone={techTone(scores.tech)} />
        <ScoreCard label="Stres səviyyəsi" value={scores.stress} tone={stressTone(scores.stress)} />
        <ProgressCard turn={progress.turn} maxTurns={progress.maxTurns} />
      </div>

      <ChatWindow messages={interview.messages} typing={interview.awaitingReply && interview.isConnected} />

      {interview.verdict || interview.fatal ? (
        <VerdictBanner verdict={interview.verdict} onRestart={interview.restart} onExit={onExit} />
      ) : (
        <Composer
          disabled={!interview.canAnswer}
          onSend={(text) => interview.sendAnswer(text, headerProps.lang)}
          speech={speech}
        />
      )}
    </>
  )
}
