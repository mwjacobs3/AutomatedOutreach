import { useState } from 'react'

const DAY_LABELS = {
  1: 'Day 1',
  3: 'Day 3',
  7: 'Day 7',
  10: 'Day 10',
  14: 'Day 14',
  21: 'Day 21',
}

export default function EmailCard({ email }) {
  const [copiedSubject, setCopiedSubject] = useState(false)
  const [copiedBody, setCopiedBody] = useState(false)

  const handleCopySubject = async () => {
    await navigator.clipboard.writeText(email.subject)
    setCopiedSubject(true)
    setTimeout(() => setCopiedSubject(false), 2000)
  }

  const handleCopyBody = async () => {
    await navigator.clipboard.writeText(email.body)
    setCopiedBody(true)
    setTimeout(() => setCopiedBody(false), 2000)
  }

  return (
    <div className="email-card">
      <div className="email-card-header">
        <span className="email-number">Email {email.sequence_number}</span>
        <span className="email-day">{DAY_LABELS[email.send_day] || `Day ${email.send_day}`}</span>
        <span className="email-purpose">{email.purpose}</span>
      </div>
      <div className="email-subject">
        <div className="email-field-row">
          <strong>Subject:</strong> {email.subject}
          <button className="copy-btn" onClick={handleCopySubject}>
            {copiedSubject ? 'Copied!' : 'Copy Subject'}
          </button>
        </div>
      </div>
      <div className="email-body">{email.body}</div>
      <button className="copy-btn copy-body-btn" onClick={handleCopyBody}>
        {copiedBody ? 'Copied!' : 'Copy Email Body'}
      </button>
    </div>
  )
}
