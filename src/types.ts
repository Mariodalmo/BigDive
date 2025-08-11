export type Classification = 'Alto Rischio' | 'Medio Rischio' | 'Basso Rischio' | 'Interno'
export type Lifecycle = 'Idea' | 'Sviluppo' | 'Uso' | 'Dismissione'
export type RunStatus = 'Pianificazione' | 'Approvazione' | 'Esecuzione' | 'Esitazione' | 'Chiuso'
export type Outcome = 'Positivo' | 'Negativo' | 'Positivo con Osservazioni'
export type RemediationStatus = 'Aperta' | 'In Corso' | 'Sospesa' | 'Completata' | 'Scaduta'
export type Priority = 'Alta' | 'Media' | 'Bassa'

export interface User { id: string; name: string; role: 'Admin' | 'Compliance' | 'Owner' | 'Viewer' }
export interface AISystem {
  id: string
  name: string
  owner: string
  description: string
  classification: Classification
  lifecycleState: Lifecycle
  createdAt: string
  updatedAt: string
  tags: string[]
  riskLevel: number
  dataCategories: string[]
}
export interface Control { id: string; code: string; title: string; description: string; frequency: string }
export interface ControlRun {
  id: string
  controlId: string
  aiSystemId: string
  plannedDate: string
  status: RunStatus
  approverId?: string | null
  executorId?: string | null
}
export interface ControlResult {
  id: string
  controlRunId: string
  outcome: Outcome
  notes?: { observation?: string }
  evidenceUrl?: string
  submittedAt: string
}
export interface Remediation {
  id: string
  controlResultId: string
  aiSystemId: string
  controlId: string
  description: string
  dueDate: string
  status: RemediationStatus
  assigneeId?: string | null
  updatedAt: string
  priority: Priority
}
