import { apiBaseUrl, safeFetch } from './api'

export async function fetchHackModes(token: string): Promise<{ modes: Array<{ id: string; label: string; description: string }> }> {
  const response = await safeFetch(`${apiBaseUrl}/api/security/hack-modes`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!response.ok) {
    throw new Error('Hack modes fetch failed')
  }
  return response.json()
}

export async function executeHackMode(
  payload: {
    session_id: string
    mode: string
    details?: string
    target_patient_id?: string
    requested_payload?: Record<string, unknown>
  },
  token: string,
): Promise<any> {
  const response = await safeFetch(`${apiBaseUrl}/api/security/hack-modes/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Hack mode execution failed: ${body || response.statusText}`)
  }
  return response.json()
}
