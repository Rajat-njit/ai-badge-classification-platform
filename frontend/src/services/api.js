/**
 * api.js — all HTTP calls to the backend, centralised here.
 *
 * All components import from this file only.
 * No direct fetch or axios calls anywhere else.
 */

import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const http = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
})

/** Extract a human-readable error message from an axios error. */
function apiError(err) {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return new Error(detail)
  if (Array.isArray(detail)) return new Error(detail.map(d => d.msg).join('; '))
  return new Error(err.message || 'Unknown API error')
}

/**
 * POST /ingest
 * @param {string} inputType  "obv3_json" | "form" | "free_text"
 * @param {object} payload    Parsed JSON object, form fields object, or {text: string}
 * @returns {Promise<object>} BadgeFactSheet
 */
export async function ingestBadge(inputType, payload) {
  try {
    const { data } = await http.post('/ingest', { input_type: inputType, payload })
    return data
  } catch (err) {
    throw apiError(err)
  }
}

/**
 * POST /classify
 * @param {object} badgeFactSheet  Full BFS object returned by /ingest
 * @returns {Promise<object>}      ClassificationResult
 */
export async function classifyBadge(badgeFactSheet) {
  try {
    const { data } = await http.post('/classify', badgeFactSheet)
    return data
  } catch (err) {
    throw apiError(err)
  }
}

/**
 * POST /review
 * @param {object} reviewPayload  {log_id, reviewer_status, reviewer_id,
 *                                  override_reason, override_category,
 *                                  override_type, override_level}
 * @returns {Promise<object>}     Updated GovernanceLog
 */
export async function submitReview(reviewPayload) {
  try {
    const { data } = await http.post('/review', reviewPayload)
    return data
  } catch (err) {
    throw apiError(err)
  }
}

/**
 * GET /logs
 * @param {number} limit   Records per page (default 20)
 * @param {number} offset  Skip N records (default 0)
 * @returns {Promise<{total:number, offset:number, limit:number, records:object[]}>}
 */
export async function getLogs(limit = 20, offset = 0) {
  try {
    const { data } = await http.get('/logs', { params: { limit, offset } })
    return data
  } catch (err) {
    throw apiError(err)
  }
}

/**
 * GET /logs/{logId}
 * @param {string} logId
 * @returns {Promise<object>} Full GovernanceLog record
 */
export async function getLog(logId) {
  try {
    const { data } = await http.get(`/logs/${logId}`)
    return data
  } catch (err) {
    throw apiError(err)
  }
}

/**
 * GET /health
 * @returns {Promise<{status:string, version:string}>}
 */
export async function getHealth() {
  try {
    const { data } = await http.get('/health')
    return data
  } catch (err) {
    throw apiError(err)
  }
}
