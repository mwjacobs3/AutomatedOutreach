import { useState } from 'react'
import ProspectForm from './components/ProspectForm'
import EmailSequence from './components/EmailSequence'
import './App.css'

function App() {
  const [emails, setEmails] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleReset = () => {
    setEmails(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AutomatedOutreach</h1>
        <p>Generate personalized email cadences for NetSuite prospects</p>
      </header>

      <main className="app-main">
        {error && (
          <div className="error-banner">
            <span>{error}</span>
            <button onClick={() => setError(null)}>Dismiss</button>
          </div>
        )}

        {loading && (
          <div className="loading-overlay">
            <div className="loading-spinner" />
            <p>Generating your 6-email cadence with AI...</p>
            <p className="loading-sub">This usually takes 15-30 seconds</p>
          </div>
        )}

        {emails ? (
          <EmailSequence data={emails} onReset={handleReset} />
        ) : (
          <ProspectForm
            onSuccess={setEmails}
            loading={loading}
            setLoading={setLoading}
            setError={setError}
          />
        )}
      </main>
    </div>
  )
}

export default App
