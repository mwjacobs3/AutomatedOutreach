import { useState } from 'react'

const INITIAL_FORM = {
  linkedin_url: '',
  company_url: '',
  pain_points: '',
  tone: '',
  call_to_action: '',
  additional_context: '',
}

const TONE_OPTIONS = [
  { value: '', label: 'Default (Professional)' },
  { value: 'casual', label: 'Casual & Friendly' },
  { value: 'formal', label: 'Formal & Corporate' },
  { value: 'consultative', label: 'Consultative' },
  { value: 'urgent', label: 'Urgent & Direct' },
]

const CTA_OPTIONS = [
  { value: '', label: 'Default (Book a meeting)' },
  { value: 'demo', label: 'Schedule a Demo' },
  { value: 'call', label: 'Book a Discovery Call' },
  { value: 'reply', label: 'Reply to Email' },
  { value: 'resource', label: 'Download a Resource' },
]

export default function ProspectForm({ onSuccess, loading, setLoading, setError }) {
  const [form, setForm] = useState(INITIAL_FORM)
  const [showOptions, setShowOptions] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const payload = {
      linkedin_url: form.linkedin_url,
      company_url: form.company_url,
    }

    if (form.pain_points) payload.pain_points = form.pain_points
    if (form.tone) payload.tone = form.tone
    if (form.call_to_action) payload.call_to_action = form.call_to_action
    if (form.additional_context) payload.additional_context = form.additional_context

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `Request failed (${res.status})`)
      }

      const data = await res.json()
      onSuccess(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="prospect-form">
      <fieldset className="required-fields">
        <legend>Prospect Info</legend>
        <label>
          LinkedIn Profile URL *
          <input
            name="linkedin_url"
            value={form.linkedin_url}
            onChange={handleChange}
            required
            placeholder="https://linkedin.com/in/john-smith"
          />
        </label>
        <label>
          Company Website URL *
          <input
            name="company_url"
            value={form.company_url}
            onChange={handleChange}
            required
            placeholder="https://example.com"
          />
        </label>
      </fieldset>

      <div className="optional-section">
        <button
          type="button"
          className="optional-toggle"
          onClick={() => setShowOptions(!showOptions)}
        >
          <span className={`toggle-arrow ${showOptions ? 'open' : ''}`}>&#9656;</span>
          Personalization Options
          <span className="optional-badge">Optional</span>
        </button>

        {showOptions && (
          <div className="optional-fields">
            <label>
              Tone
              <select name="tone" value={form.tone} onChange={handleChange}>
                {TONE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Call to Action
              <select name="call_to_action" value={form.call_to_action} onChange={handleChange}>
                {CTA_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Pain Points
              <textarea
                name="pain_points"
                value={form.pain_points}
                onChange={handleChange}
                placeholder="e.g., Manual processes, disconnected systems, lack of visibility..."
                rows={2}
              />
            </label>

            <label>
              Additional Context
              <textarea
                name="additional_context"
                value={form.additional_context}
                onChange={handleChange}
                placeholder="e.g., Recently acquired a competitor, expanding into new markets..."
                rows={2}
              />
            </label>
          </div>
        )}
      </div>

      <button type="submit" className="submit-btn" disabled={loading}>
        {loading ? 'Researching & Generating...' : 'Generate Email Cadence'}
      </button>
    </form>
  )
}
