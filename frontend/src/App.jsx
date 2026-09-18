import { useState } from 'react'
import { Header } from './components/Header'
import { InterviewScreen } from './components/InterviewScreen'
import { SetupScreen } from './components/SetupScreen'
import { SPEECH_LANGUAGES } from './config'
import { useSpeech } from './hooks/useSpeech'

let sessionCounter = 0

export default function App() {
  const [lang, setLang] = useState(SPEECH_LANGUAGES[0].code)
  const [setup, setSetup] = useState(null) // { id, cvId?, role, lang } once the interview starts
  const speech = useSpeech(lang)

  const headerProps = {
    lang,
    onLangChange: setLang,
    muted: speech.muted,
    speaking: speech.speaking,
    onToggleMute: speech.toggleMute,
  }

  const exit = () => {
    speech.stopSpeaking()
    setSetup(null)
  }

  return (
    <div className="mx-auto flex h-full max-w-5xl flex-col gap-4 p-4 sm:p-6">
      {setup ? (
        <InterviewScreen key={setup.id} setup={setup} headerProps={headerProps} speech={speech} onExit={exit} />
      ) : (
        <>
          <Header {...headerProps} />
          <main className="flex flex-1 items-start justify-center overflow-y-auto py-4 sm:items-center">
            <SetupScreen onStart={(config) => setSetup({ ...config, lang, id: ++sessionCounter })} />
          </main>
        </>
      )}
    </div>
  )
}
