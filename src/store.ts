import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { AISystem, Control, ControlRun, ControlResult, Remediation, Outcome, RunStatus, RemediationStatus, User } from './types'
import { now, addDaysISO, uuid } from './utils'

// Normalized state
interface Entities<T> { byId: Record<string, T>; allIds: string[] }
const empty = <T,>(): Entities<T> => ({ byId: {}, allIds: [] })

interface State {
  currentUser: User
  systems: Entities<AISystem>
  controls: Entities<Control>
  runs: Entities<ControlRun>
  results: Entities<ControlResult>
  remediations: Entities<Remediation>
  // actions
  addSystem: (s: Omit<AISystem, 'id'|'createdAt'|'updatedAt'>) => void
  updateSystem: (id: string, patch: Partial<AISystem>) => void
  scheduleRun: (input: { controlId: string; aiSystemId: string; plannedDate: string }) => void
  progressRun: (id: string, to: RunStatus) => void
  submitResult: (runId: string, outcome: Outcome, notes?: string, evidenceUrl?: string) => void
  updateRemediation: (id: string, patch: Partial<Remediation>) => void
}

const seed = (): Pick<State, 'systems'|'controls'|'runs'|'results'|'remediations'> => {
  // minimal seed with 5 systems and 4 controls
  const s1: AISystem = { id: uuid(), name: 'AI Risk Analyzer', owner: 'Owner 1', description: 'Analisi predittiva rischi', classification: 'Alto Rischio', lifecycleState: 'Uso', createdAt: now(), updatedAt: now(), tags: ['ML'], riskLevel: 5, dataCategories: ['Personali'] }
  const s2: AISystem = { id: uuid(), name: 'ChatAudit', owner: 'Owner 2', description: 'Audit NLP', classification: 'Medio Rischio', lifecycleState: 'Sviluppo', createdAt: now(), updatedAt: now(), tags: ['NLP'], riskLevel: 3, dataCategories: ['Anonimizzati'] }
  const systems = [s1, s2]

  const c1: Control = { id: uuid(), code: 'CTRL-001', title: 'Verifica Qualità Dati', description: 'Controllo qualità dataset', frequency: 'Trimestrale' }
  const c2: Control = { id: uuid(), code: 'CTRL-002', title: 'Audit Bias Algoritmico', description: 'Analisi fairness', frequency: 'Annuale' }
  const c3: Control = { id: uuid(), code: 'CTRL-003', title: 'Conformità GDPR', description: 'Verifica privacy', frequency: 'Semestrale' }
  const c4: Control = { id: uuid(), code: 'CTRL-004', title: 'Performance Monitoring', description: 'Monitoraggio metriche', frequency: 'Mensile' }
  const controls = [c1,c2,c3,c4]

  const r1: ControlRun = { id: uuid(), controlId: c1.id, aiSystemId: s1.id, plannedDate: addDaysISO(now(), 2), status: 'Pianificazione' }
  const r2: ControlRun = { id: uuid(), controlId: c2.id, aiSystemId: s1.id, plannedDate: addDaysISO(now(), 7), status: 'Esecuzione', executorId: 'Executor 1' }
  const runs = [r1,r2]

  const ent = <T,>(arr: T[], key: keyof T = 'id' as any): Entities<any> => ({ byId: Object.fromEntries(arr.map((x:any)=>[x[key], x])), allIds: arr.map((x:any)=>x[key]) })
  return {
    systems: ent(systems),
    controls: ent(controls),
    runs: ent(runs),
    results: empty(),
    remediations: empty()
  }
}

export const useAppStore = create<State>()(devtools((set, get) => ({
  currentUser: { id: 'u1', name: 'Admin User', role: 'Admin' },
  ...seed(),

  addSystem: (s) => set(state => {
    const id = uuid(); const record: AISystem = { ...s, id, createdAt: now(), updatedAt: now() }
    return { systems: { byId: { ...state.systems.byId, [id]: record }, allIds: [...state.systems.allIds, id] } }
  }),

  updateSystem: (id, patch) => set(state => {
    const curr = state.systems.byId[id]; if (!curr) return {}
    const upd = { ...curr, ...patch, updatedAt: now() }
    return { systems: { ...state.systems, byId: { ...state.systems.byId, [id]: upd } } }
  }),

  scheduleRun: (input) => set(state => {
    const id = uuid(); const run: ControlRun = { id, ...input, status: 'Pianificazione' }
    return { runs: { byId: { ...state.runs.byId, [id]: run }, allIds: [id, ...state.runs.allIds] } }
  }),

  progressRun: (id, to) => set(state => {
    const run = state.runs.byId[id]; if (!run) return {}
    // guard: valid transitions
    const allowed: Record<RunStatus, RunStatus[]> = {
      'Pianificazione': ['Approvazione'],
      'Approvazione': ['Esecuzione'],
      'Esecuzione': ['Esitazione'],
      'Esitazione': ['Chiuso'],
      'Chiuso': []
    }
    if (!allowed[run.status].includes(to)) return {}
    const upd = { ...run, status: to }
    return { runs: { ...state.runs, byId: { ...state.runs.byId, [id]: upd } } }
  }),

  submitResult: (runId, outcome, notes, evidenceUrl) => set(state => {
    const run = state.runs.byId[runId]; if (!run) return {}
    // enforce 1 result per run
    const already = Object.values(state.results.byId).some(r => r.controlRunId === runId)
    if (already) return {}

    const resultId = uuid()
    const result: ControlResult = {
      id: resultId, controlRunId: runId, outcome, notes: notes? { observation: notes }: undefined,
      evidenceUrl, submittedAt: now()
    }

    // Outcome handling
    const needsRem = outcome !== 'Positivo'
    let runs = state.runs
    if (!needsRem) {
      // transition Esitazione -> Chiuso
      runs = { ...runs, byId: { ...runs.byId, [runId]: { ...run, status: 'Chiuso' } } }
    } else {
      // keep run in Esitazione until all remediations complete
      runs = { ...runs, byId: { ...runs.byId, [runId]: { ...run, status: 'Esitazione' } } }
    }

    let remediations = state.remediations
    if (needsRem) {
      const rem: Remediation = {
        id: uuid(), controlResultId: resultId, aiSystemId: run.aiSystemId, controlId: run.controlId,
        description: `Remediation per controllo ${run.controlId}`,
        dueDate: addDaysISO(now(), 30), status: 'Aperta', assigneeId: run.executorId ?? null,
        updatedAt: now(), priority: 'Media'
      }
      remediations = { byId: { ...remediations.byId, [rem.id]: rem }, allIds: [rem.id, ...remediations.allIds] }
    }

    return {
      results: { byId: { ...state.results.byId, [resultId]: result }, allIds: [resultId, ...state.results.allIds] },
      runs,
      remediations
    }
  }),

  updateRemediation: (id, patch) => set(state => {
    const curr = state.remediations.byId[id]; if (!curr) return {}
    const upd: Remediation = { ...curr, ...patch, updatedAt: now() }
    // auto-close run if all remediations for its run are completed
    const resultsByRun: Record<string, string[]> = {}
    Object.values(state.results.byId).forEach(res => {
      if (!resultsByRun[res.controlRunId]) resultsByRun[res.controlRunId] = []
      resultsByRun[res.controlRunId].push(res.id)
    })
    const runId = Object.values(state.results.byId).find(r => r.id === upd.controlResultId)?.controlRunId
    let runs = state.runs
    const remsForRun = Object.values(state.remediations.byId).filter(r => r.controlResultId === upd.controlResultId)
    const allClosed = remsForRun.every(r => (r.id === id ? (patch.status ?? r.status) : r.status) === 'Completata') && remsForRun.length > 0
    if (runId && allClosed) {
      const run = state.runs.byId[runId]
      if (run && run.status !== 'Chiuso') {
        runs = { ...runs, byId: { ...runs.byId, [runId]: { ...run, status: 'Chiuso' } } }
      }
    }
    return {
      remediations: { ...state.remediations, byId: { ...state.remediations.byId, [id]: upd } },
      runs
    }
  })
})))
