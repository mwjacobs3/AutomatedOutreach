import EmailCard from './EmailCard'

export default function EmailSequence({ data, onReset }) {
  return (
    <div className="email-sequence">
      <div className="sequence-header">
        <div>
          <h2>Email Cadence for {data.prospect_name}</h2>
          <p className="sequence-subtitle">{data.company}</p>
        </div>
        <button className="reset-btn" onClick={onReset}>
          New Cadence
        </button>
      </div>
      <div className="email-list">
        {data.emails.map((email) => (
          <EmailCard key={email.sequence_number} email={email} />
        ))}
      </div>
    </div>
  )
}
