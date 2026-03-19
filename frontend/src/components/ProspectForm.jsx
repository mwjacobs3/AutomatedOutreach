import { useState } from 'react'

const INITIAL_FORM = {
  linkedin_url: '',
  company_url: '',
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

    try {
      const res = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
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
      <fieldset>
        <legend>Prospect Research</legend>
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

      <button type="submit" className="submit-btn" disabled={loading}>
        {loading ? 'Researching & Generating...' : 'Generate Email Cadence'}
      </button>
    </form>
  )
}
