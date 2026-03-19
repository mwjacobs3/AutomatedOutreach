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
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const text = `Subject: ${email.subject}\n\n${email.body}`
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="email-card">
      <div className="email-card-header">
        <span className="email-number">Email {email.sequence_number}</span>
        <span className="email-day">{DAY_LABELS[email.send_day] || `Day ${email.send_day}`}</span>
        <span className="email-purpose">{email.purpose}</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <div className="email-subject">
        <strong>Subject:</strong> {email.subject}
      </div>
      <div className="email-body">{email.body}</div>
    </div>
  )
}
