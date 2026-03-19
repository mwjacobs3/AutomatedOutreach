import { useState } from 'react'

const INITIAL_FORM = {
  // Contact basics
  first_name: '',
  last_name: '',
  email: '',
  title: '',
  company_name: '',
  // LinkedIn context
  linkedin_url: '',
  linkedin_summary: '',
  years_experience: '',
  recent_activity: '',
  // Company context
  company_url: '',
  industry: '',
  company_size: '',
  company_description: '',
  tech_stack: '',
  recent_company_news: '',
  // Pain points
  pain_points_text: '', // one per line, split before sending
  trigger_event: '',
  // Sender info
  sender_name: '',
  sender_title: '',
  sender_company: '',
  sender_email: '',
  calendar_link: '',
}

export default function ProspectForm({ onSuccess, loading, setLoading, setError }) {
  const [form, setForm] = useState(INITIAL_FORM)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const payload = { ...form }
    // Convert pain points text to array
    payload.pain_points = payload.pain_points_text
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
    delete payload.pain_points_text

    // Strip empty optional strings to null
    for (const key of Object.keys(payload)) {
      if (typeof payload[key] === 'string' && payload[key].trim() === '') {
        payload[key] = null
      }
    }

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
      {/* Section: Prospect Contact */}
      <fieldset>
        <legend>Prospect Contact Info</legend>
        <div className="form-row">
          <label>
            First Name *
            <input name="first_name" value={form.first_name} onChange={handleChange} required />
          </label>
          <label>
            Last Name *
            <input name="last_name" value={form.last_name} onChange={handleChange} required />
          </label>
        </div>
        <div className="form-row">
          <label>
            Email *
            <input name="email" type="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Title *
            <input name="title" value={form.title} onChange={handleChange} required placeholder="e.g. VP of Finance" />
          </label>
        </div>
        <label>
          Company Name *
          <input name="company_name" value={form.company_name} onChange={handleChange} required />
        </label>
      </fieldset>

      {/* Section: LinkedIn Context */}
      <fieldset>
        <legend>LinkedIn Profile (paste key details)</legend>
        <label>
          LinkedIn URL
          <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} placeholder="https://linkedin.com/in/..." />
        </label>
        <label>
          LinkedIn Summary / About
          <textarea name="linkedin_summary" value={form.linkedin_summary} onChange={handleChange} rows={4} placeholder="Paste their LinkedIn summary or About section here..." />
        </label>
        <div className="form-row">
          <label>
            Years of Experience
            <input name="years_experience" value={form.years_experience} onChange={handleChange} placeholder="e.g. 15+ years" />
          </label>
        </div>
        <label>
          Recent Activity
          <textarea name="recent_activity" value={form.recent_activity} onChange={handleChange} rows={3} placeholder="Recent posts, comments, job changes, promotions..." />
        </label>
      </fieldset>

      {/* Section: Company Context */}
      <fieldset>
        <legend>Company Info (paste from website)</legend>
        <label>
          Company Website URL
          <input name="company_url" value={form.company_url} onChange={handleChange} placeholder="https://example.com" />
        </label>
        <div className="form-row">
          <label>
            Industry
            <input name="industry" value={form.industry} onChange={handleChange} placeholder="e.g. Manufacturing" />
          </label>
          <label>
            Company Size
            <input name="company_size" value={form.company_size} onChange={handleChange} placeholder="e.g. 200-500 employees" />
          </label>
        </div>
        <label>
          Company Description
          <textarea name="company_description" value={form.company_description} onChange={handleChange} rows={4} placeholder="Paste company description from their website or LinkedIn..." />
        </label>
        <label>
          Tech Stack
          <textarea name="tech_stack" value={form.tech_stack} onChange={handleChange} rows={2} placeholder="Known systems: QuickBooks, Salesforce, Excel..." />
        </label>
        <label>
          Recent Company News
          <textarea name="recent_company_news" value={form.recent_company_news} onChange={handleChange} rows={3} placeholder="Funding rounds, acquisitions, product launches, leadership changes..." />
        </label>
      </fieldset>

      {/* Section: Pain Points */}
      <fieldset>
        <legend>Pain Points & Triggers</legend>
        <label>
          Pain Points (one per line)
          <textarea name="pain_points_text" value={form.pain_points_text} onChange={handleChange} rows={4} placeholder={"Manual reporting processes\nDisconnected systems\nScaling challenges"} />
        </label>
        <label>
          Trigger Event
          <input name="trigger_event" value={form.trigger_event} onChange={handleChange} placeholder="e.g. Just raised Series B, New CFO hired" />
        </label>
      </fieldset>

      {/* Section: Sender Info */}
      <fieldset>
        <legend>Your Info (Sender)</legend>
        <div className="form-row">
          <label>
            Your Name
            <input name="sender_name" value={form.sender_name} onChange={handleChange} />
          </label>
          <label>
            Your Title
            <input name="sender_title" value={form.sender_title} onChange={handleChange} />
          </label>
        </div>
        <div className="form-row">
          <label>
            Your Company
            <input name="sender_company" value={form.sender_company} onChange={handleChange} />
          </label>
          <label>
            Your Email
            <input name="sender_email" type="email" value={form.sender_email} onChange={handleChange} />
          </label>
        </div>
        <label>
          Calendar Link
          <input name="calendar_link" value={form.calendar_link} onChange={handleChange} placeholder="https://calendly.com/..." />
        </label>
      </fieldset>

      <button type="submit" className="submit-btn" disabled={loading}>
        {loading ? 'Generating Cadence...' : 'Generate Email Cadence'}
      </button>
    </form>
  )
}
