import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ingestBadge, classifyBadge } from '../services/api'

// ─── Constants ───────────────────────────────────────────────────────────────

const ISSUERS = ['LDI', 'OSIL', 'Makerspace', 'NCE', 'OGI']
const ASSESSMENT_TYPES = [
  'attendance', 'module_completion', 'final_assessment',
  'knowledge_checks', 'pre_post_assessment', 'project_presentation',
  'practical', 'quiz', 'portfolio',
]
const EVALUATORS = [
  'expert_scored', 'auto_assessed', 'peer_evaluated',
  'self_reported', 'observed',
]
const ACHIEVEMENT_TYPES = [
  'Achievement', 'Competency', 'Certificate Of Completion', 'Micro Credential',
]

const FOLLOWUP_FIELDS = ['issuer', 'assessment_evaluator', 'audience_type']

// ─── Small shared UI components ──────────────────────────────────────────────

function Label({ children }) {
  return <label className="block text-sm font-medium text-gray-700 mb-1">{children}</label>
}

function Input({ error, ...props }) {
  return (
    <input
      className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-njit-red
        ${error ? 'border-red-500' : 'border-gray-300'}`}
      {...props}
    />
  )
}

function Textarea({ error, rows = 4, ...props }) {
  return (
    <textarea
      rows={rows}
      className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-njit-red
        ${error ? 'border-red-500' : 'border-gray-300'}`}
      {...props}
    />
  )
}

function Select({ children, error, ...props }) {
  return (
    <select
      className={`w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-njit-red bg-white
        ${error ? 'border-red-500' : 'border-gray-300'}`}
      {...props}
    >
      {children}
    </select>
  )
}

function FieldGroup({ label, children }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function Spinner() {
  return (
    <div className="flex items-center justify-center py-8">
      <div className="w-8 h-8 border-4 border-njit-red border-t-transparent rounded-full animate-spin" />
    </div>
  )
}

function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <div className="bg-red-50 border border-red-300 text-red-800 rounded p-3 text-sm">
      {message}
    </div>
  )
}

// ─── BFS Confirmation Panel ───────────────────────────────────────────────────

function BfsConfirmPanel({ bfs, onConfirm, onFollowupChange, followupValues, loading }) {
  const missing = bfs.missing_signals || []
  const needsFollowup = bfs.needs_followup_questions

  const keyFields = [
    ['badge_title', 'Badge Title'],
    ['issuer', 'Issuer'],
    ['badge_description', 'Description'],
    ['earning_criteria_text', 'Earning Criteria'],
    ['assessment_required', 'Assessment Required'],
    ['assessment_type', 'Assessment Type'],
    ['assessment_evaluator', 'Assessment Evaluator'],
    ['canvas_course_code', 'Canvas Course Code'],
    ['canvas_sequence_number', 'Sequence Number'],
    ['audience_type', 'Audience Type'],
    ['bloom_level', 'Bloom Level'],
    ['self_declared_level', 'Declared Level'],
  ]

  return (
    <div className="border border-gray-200 rounded-lg p-6 space-y-4">
      <h2 className="text-lg font-semibold text-njit-navy">Extracted Badge Fact Sheet</h2>

      {needsFollowup && (
        <div className="bg-yellow-50 border border-yellow-300 text-yellow-800 rounded p-3 text-sm">
          <strong>Follow-up required:</strong> Some critical signals could not be extracted.
          Please fill in the fields below before classifying.
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {keyFields.map(([field, label]) => {
          const val = bfs[field]
          const isMissing = missing.includes(field)
          const hasVal = val !== null && val !== undefined && val !== ''
          return (
            <div
              key={field}
              className={`rounded p-2 text-sm border
                ${isMissing ? 'bg-yellow-50 border-yellow-300' : 'bg-gray-50 border-gray-200'}`}
            >
              <span className="font-medium text-gray-600">{label}: </span>
              <span className={hasVal ? 'text-gray-900' : 'text-gray-400 italic'}>
                {hasVal ? String(val) : 'not detected'}
              </span>
              {isMissing && <span className="ml-2 text-yellow-700 font-semibold">⚠ missing</span>}
            </div>
          )
        })}
      </div>

      {/* Follow-up form for missing signals */}
      {needsFollowup && (
        <div className="border border-yellow-200 rounded p-4 space-y-3 bg-yellow-50">
          <p className="text-sm font-medium text-yellow-900">
            Fill in missing signals (only the fields below are required):
          </p>
          {missing.includes('issuer') && (
            <FieldGroup label="Issuer *">
              <Select
                value={followupValues.issuer || ''}
                onChange={e => onFollowupChange('issuer', e.target.value)}
              >
                <option value="">— select issuer —</option>
                {ISSUERS.map(i => <option key={i}>{i}</option>)}
              </Select>
            </FieldGroup>
          )}
          {missing.includes('assessment_evaluator') && (
            <FieldGroup label="Assessment Evaluator *">
              <Select
                value={followupValues.assessment_evaluator || ''}
                onChange={e => onFollowupChange('assessment_evaluator', e.target.value)}
              >
                <option value="">— select evaluator —</option>
                {EVALUATORS.map(e => <option key={e}>{e}</option>)}
              </Select>
            </FieldGroup>
          )}
          {missing.includes('audience_type') && (
            <FieldGroup label="Audience Type *">
              <Select
                value={followupValues.audience_type || ''}
                onChange={e => onFollowupChange('audience_type', e.target.value)}
              >
                <option value="">— select audience —</option>
                <option value="njit_employee">NJIT Employee (Faculty/Staff)</option>
                <option value="njit_student">NJIT Student</option>
                <option value="external_professional">External Professional</option>
                <option value="faculty">Faculty</option>
              </Select>
            </FieldGroup>
          )}
        </div>
      )}

      <button
        onClick={onConfirm}
        disabled={loading}
        className="bg-njit-red text-white px-6 py-2 rounded font-medium hover:bg-njit-red-dark disabled:opacity-50"
      >
        {loading ? 'Classifying…' : 'Confirm & Classify →'}
      </button>
    </div>
  )
}

// ─── Tab 1: Proposal Form ─────────────────────────────────────────────────────

function ProposalForm({ onIngested }) {
  const [form, setForm] = useState({
    badge_title: '', badge_description: '', issuer: '',
    intended_audience: '', institutional_context: '',
    earning_criteria_text: '', assessment_required: 'unknown',
    assessment_type: '', assessment_evaluator: '',
    assessment_pass_threshold: '', evidence_required: 'unknown',
    canvas_course_code: '', pathway_name: '', achievement_type: '',
  })
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  function set(field, val) {
    setForm(f => ({ ...f, [field]: val }))
    if (errors[field]) setErrors(e => ({ ...e, [field]: '' }))
  }

  function validate() {
    const e = {}
    if (!form.badge_title.trim()) e.badge_title = 'Required'
    if (!form.badge_description.trim()) e.badge_description = 'Required'
    if (!form.earning_criteria_text.trim()) e.earning_criteria_text = 'Required'
    return e
  }

  async function handleSubmit(ev) {
    ev.preventDefault()
    const e = validate()
    if (Object.keys(e).length) { setErrors(e); return }
    setLoading(true); setApiError('')
    try {
      // Strip empty strings so backend doesn't get empty fields
      const payload = Object.fromEntries(
        Object.entries(form).filter(([, v]) => v !== '')
      )
      const bfs = await ingestBadge('form', payload)
      onIngested(bfs)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorBanner message={apiError} />

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FieldGroup label="Badge Title *">
          <Input value={form.badge_title} error={errors.badge_title}
            onChange={e => set('badge_title', e.target.value)} placeholder="e.g. AI Fundamentals" />
          {errors.badge_title && <p className="text-red-600 text-xs mt-1">{errors.badge_title}</p>}
        </FieldGroup>

        <FieldGroup label="Issuer">
          <Select value={form.issuer} onChange={e => set('issuer', e.target.value)}>
            <option value="">— select —</option>
            {ISSUERS.map(i => <option key={i}>{i}</option>)}
          </Select>
        </FieldGroup>
      </div>

      <FieldGroup label="Badge Description *">
        <Textarea value={form.badge_description} error={errors.badge_description}
          onChange={e => set('badge_description', e.target.value)}
          placeholder="Full badge description…" />
        {errors.badge_description && <p className="text-red-600 text-xs mt-1">{errors.badge_description}</p>}
      </FieldGroup>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FieldGroup label="Intended Audience">
          <Input value={form.intended_audience}
            onChange={e => set('intended_audience', e.target.value)}
            placeholder="e.g. Faculty and instructors" />
        </FieldGroup>
        <FieldGroup label="Institutional Context">
          <Input value={form.institutional_context}
            onChange={e => set('institutional_context', e.target.value)} />
        </FieldGroup>
      </div>

      <FieldGroup label="Earning Criteria *">
        <Textarea value={form.earning_criteria_text} error={errors.earning_criteria_text}
          onChange={e => set('earning_criteria_text', e.target.value)} rows={5}
          placeholder="Full criteria text verbatim…" />
        {errors.earning_criteria_text && <p className="text-red-600 text-xs mt-1">{errors.earning_criteria_text}</p>}
      </FieldGroup>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FieldGroup label="Assessment Required">
          <Select value={form.assessment_required} onChange={e => set('assessment_required', e.target.value)}>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="unknown">Unknown</option>
          </Select>
        </FieldGroup>
        <FieldGroup label="Assessment Type">
          <Select value={form.assessment_type} onChange={e => set('assessment_type', e.target.value)}>
            <option value="">— select —</option>
            {ASSESSMENT_TYPES.map(t => <option key={t}>{t}</option>)}
          </Select>
        </FieldGroup>
        <FieldGroup label="Assessment Evaluator">
          <Select value={form.assessment_evaluator} onChange={e => set('assessment_evaluator', e.target.value)}>
            <option value="">— select —</option>
            {EVALUATORS.map(e => <option key={e}>{e}</option>)}
          </Select>
        </FieldGroup>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <FieldGroup label="Pass Threshold">
          <Input value={form.assessment_pass_threshold}
            onChange={e => set('assessment_pass_threshold', e.target.value)}
            placeholder="e.g. 80%" />
        </FieldGroup>
        <FieldGroup label="Evidence Required">
          <Select value={form.evidence_required} onChange={e => set('evidence_required', e.target.value)}>
            <option value="yes">Yes</option>
            <option value="no">No</option>
            <option value="unknown">Unknown</option>
          </Select>
        </FieldGroup>
        <FieldGroup label="Achievement Type">
          <Select value={form.achievement_type} onChange={e => set('achievement_type', e.target.value)}>
            <option value="">— select —</option>
            {ACHIEVEMENT_TYPES.map(t => <option key={t}>{t}</option>)}
          </Select>
        </FieldGroup>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <FieldGroup label="Canvas Course Code">
          <Input value={form.canvas_course_code}
            onChange={e => set('canvas_course_code', e.target.value)}
            placeholder="e.g. MCAI.002.03" />
        </FieldGroup>
        <FieldGroup label="Pathway Name">
          <Input value={form.pathway_name}
            onChange={e => set('pathway_name', e.target.value)} />
        </FieldGroup>
      </div>

      <button type="submit" disabled={loading}
        className="bg-njit-red text-white px-6 py-2 rounded font-medium hover:bg-njit-red-dark disabled:opacity-50">
        {loading ? 'Submitting…' : 'Extract Badge Fact Sheet →'}
      </button>
    </form>
  )
}

// ─── Tab 2: JSON Paste ────────────────────────────────────────────────────────

function JsonPasteTab({ onIngested }) {
  const [raw, setRaw] = useState('')
  const [parsed, setParsed] = useState(null)
  const [parseError, setParseError] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  function handleParse() {
    setParseError(''); setParsed(null)
    try {
      const obj = JSON.parse(raw)
      setParsed(obj)
    } catch {
      setParseError('Invalid JSON — please check your input.')
    }
  }

  async function handleSubmit() {
    if (!parsed) { setParseError('Parse JSON first.'); return }
    setLoading(true); setApiError('')
    try {
      const bfs = await ingestBadge('obv3_json', parsed)
      onIngested(bfs)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <ErrorBanner message={apiError} />
      <FieldGroup label="Paste OBv3 JSON">
        <Textarea
          value={raw}
          onChange={e => { setRaw(e.target.value); setParsed(null); setParseError('') }}
          rows={12}
          placeholder={'{\n  "@context": "https://purl.imsglobal.org/spec/ob/v3p0/...",\n  "name": "Badge Name",\n  ...\n}'}
          error={!!parseError}
        />
      </FieldGroup>

      {parseError && <p className="text-red-600 text-sm">{parseError}</p>}

      {parsed && (
        <div className="bg-green-50 border border-green-200 rounded p-3 text-sm text-green-800">
          <strong>Valid JSON detected.</strong>{' '}
          Fields found: {Object.keys(parsed).join(', ')}
        </div>
      )}

      <div className="flex gap-3">
        <button onClick={handleParse}
          className="border border-gray-300 px-4 py-2 rounded text-sm hover:bg-gray-50">
          Parse JSON
        </button>
        <button onClick={handleSubmit} disabled={!parsed || loading}
          className="bg-njit-red text-white px-6 py-2 rounded font-medium hover:bg-njit-red-dark disabled:opacity-50">
          {loading ? 'Submitting…' : 'Submit & Extract →'}
        </button>
      </div>
    </div>
  )
}

// ─── Tab 3: Free Text ─────────────────────────────────────────────────────────

function FreeTextTab({ onIngested }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [apiError, setApiError] = useState('')

  async function handleSubmit() {
    if (!text.trim()) return
    setLoading(true); setApiError('')
    try {
      const bfs = await ingestBadge('free_text', { text })
      onIngested(bfs)
    } catch (err) {
      setApiError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <ErrorBanner message={apiError} />
      <FieldGroup label="Describe the badge in plain language">
        <Textarea
          value={text}
          onChange={e => setText(e.target.value)}
          rows={12}
          placeholder="This badge is awarded to faculty who complete the AI for Education course series. Learners must pass the final assessment with 80% or higher…"
        />
      </FieldGroup>
      <button onClick={handleSubmit} disabled={!text.trim() || loading}
        className="bg-njit-red text-white px-6 py-2 rounded font-medium hover:bg-njit-red-dark disabled:opacity-50">
        {loading ? 'Submitting…' : 'Submit & Extract →'}
      </button>
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────────────

const TABS = ['Proposal Form', 'JSON Paste', 'Free Text']

export default function SubmitBadge() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState(0)
  const [bfs, setBfs] = useState(null)
  const [followupValues, setFollowupValues] = useState({})
  const [classifying, setClassifying] = useState(false)
  const [classifyError, setClassifyError] = useState('')

  function handleIngested(bfsData) {
    setBfs(bfsData)
    setFollowupValues({})
    setClassifyError('')
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  }

  function handleFollowupChange(field, val) {
    setFollowupValues(v => ({ ...v, [field]: val }))
  }

  async function handleConfirmClassify() {
    setClassifying(true); setClassifyError('')
    try {
      // Merge follow-up answers into BFS before classifying
      const enrichedBfs = { ...bfs, ...followupValues }
      const result = await classifyBadge(enrichedBfs)
      navigate(`/review/${result.governance.log_id}`, { state: { result, bfs: enrichedBfs } })
    } catch (err) {
      setClassifyError(err.message)
    } finally {
      setClassifying(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-njit-navy">Submit Badge for Classification</h1>
        <p className="text-gray-600 text-sm mt-1">
          Choose an input method below. The system will extract signals and recommend a classification.
        </p>
      </div>

      {/* Tab headers */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-0">
          {TABS.map((tab, i) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(i); setBfs(null) }}
              className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors
                ${activeTab === i
                  ? 'border-njit-red text-njit-red'
                  : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 0 && <ProposalForm onIngested={handleIngested} />}
        {activeTab === 1 && <JsonPasteTab onIngested={handleIngested} />}
        {activeTab === 2 && <FreeTextTab onIngested={handleIngested} />}
      </div>

      {/* BFS confirmation panel */}
      {bfs && (
        <>
          <hr className="border-gray-200" />
          <ErrorBanner message={classifyError} />
          <BfsConfirmPanel
            bfs={bfs}
            onConfirm={handleConfirmClassify}
            onFollowupChange={handleFollowupChange}
            followupValues={followupValues}
            loading={classifying}
          />
        </>
      )}
    </div>
  )
}
