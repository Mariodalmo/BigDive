import React, { useMemo, useState } from 'react'
import { Shield, Home, Database, ClipboardCheck, AlertTriangle, FileText, Bell, Settings, Search, Plus, Eye, Edit, Download } from 'lucide-react'
import { useAppStore } from './store'
import { formatIT, daysUntil, exportCSV, addDaysISO } from './utils'
import type { Classification, Lifecycle, Outcome, RemediationStatus } from './types'

const Sidebar: React.FC<{view:string,setView:(v:string)=>void,userName:string,role:string}> = ({view,setView,userName,role}) => (
  <div className="w-64 bg-gray-900 text-white h-screen p-4">
    <div className="mb-8">
      <h1 className="text-2xl font-bold flex items-center gap-2"><Shield className="w-8 h-8 text-blue-400"/>AI Governance</h1>
    </div>
    {[
      {key:'dashboard', label:'Dashboard', icon: <Home className="w-5 h-5"/>},
      {key:'systems', label:'Sistemi AI', icon:<Database className="w-5 h-5"/>},
      {key:'controls', label:'Controlli', icon:<ClipboardCheck className="w-5 h-5"/>},
      {key:'remediations', label:'Remediation', icon:<AlertTriangle className="w-5 h-5"/>},
      {key:'reports', label:'Report', icon:<FileText className="w-5 h-5"/>}
    ].map(i=> (
      <button key={i.key} onClick={()=>setView(i.key)} className={`w-full text-left p-3 rounded flex items-center gap-3 transition ${view===i.key? 'bg-blue-600':'hover:bg-gray-800'}`}>
        {i.icon}{i.label}
      </button>
    ))}
    <div className="absolute bottom-4 left-4 right-4">
      <div className="border-t border-gray-700 pt-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">{userName[0]}</div>
          <div><div className="text-sm font-medium">{userName}</div><div className="text-xs text-gray-400">{role}</div></div>
        </div>
      </div>
    </div>
  </div>
)

const TopBar: React.FC<{title:string, search:string,setSearch:(v:string)=>void, overdue:number, onToggleNotif:()=>void}> = ({title, search, setSearch, overdue, onToggleNotif}) => (
  <div className="bg-white border-b px-6 py-4 flex items-center justify-between">
    <h2 className="text-2xl font-semibold capitalize">{title}</h2>
    <div className="flex items-center gap-4">
      <div className="relative">
        <input aria-label="Cerca" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Cerca..." className="pl-10 pr-4 py-2 border rounded-lg w-64"/>
        <Search className="w-5 h-5 absolute left-3 top-2.5 text-gray-400"/>
      </div>
      <button onClick={onToggleNotif} className="relative p-2 hover:bg-gray-100 rounded-lg" aria-label="Notifiche">
        <Bell className="w-5 h-5"/>
        {overdue>0 && <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">{overdue}</span>}
      </button>
      <button className="p-2 hover:bg-gray-100 rounded-lg" aria-label="Impostazioni"><Settings className="w-5 h-5"/></button>
    </div>
  </div>
)

const DashboardView: React.FC = () => {
  const { systems, runs, results, remediations } = useAppStore()
  const metrics = useMemo(()=>{
    const totalSystems = systems.allIds.length
    const systemsByClass: Record<string, number> = {}
    systems.allIds.forEach(id=>{ const s = systems.byId[id]; systemsByClass[s.classification] = (systemsByClass[s.classification]||0)+1 })
    const runsByStatus: Record<string, number> = {}
    runs.allIds.forEach(id=>{ const r = runs.byId[id]; runsByStatus[r.status] = (runsByStatus[r.status]||0)+1 })
    const resultsByOutcome: Record<string, number> = {}
    Object.values(results.byId).forEach(res=>{ resultsByOutcome[res.outcome] = (resultsByOutcome[res.outcome]||0)+1 })
    const openRem = remediations.allIds.filter(id=>{
      const r = remediations.byId[id]; return r.status==='Aperta' || r.status==='In Corso'
    }).length
    const overdue = remediations.allIds.filter(id=>{
      const r = remediations.byId[id]; return daysUntil(r.dueDate)<0 && r.status!=='Completata'
    }).length
    const completionRate = (()=>{
      const arr = Object.values(results.byId); if (!arr.length) return 0
      const pos = arr.filter(r=>r.outcome==='Positivo').length
      return Math.round((pos/arr.length)*1000)/10
    })()
    return { totalSystems, systemsByClass, runsByStatus, resultsByOutcome, openRem, overdue, completionRate }
  },[systems, runs, results, remediations])

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPI icon="📦" value={metrics.totalSystems} label="Sistemi AI" details={Object.entries(metrics.systemsByClass).map(([k,v])=>`${k}: ${v}`).join(' • ')}/>
        <KPI icon="✅" value={Object.values(metrics.runsByStatus).reduce((a,b)=>a+b,0)} label="Controlli Totali" details={`Chiuso: ${metrics.runsByStatus['Chiuso']||0} • In corso: ${((Object.values(metrics.runsByStatus).reduce((a,b)=>a+b,0))-(metrics.runsByStatus['Chiuso']||0))}`}/>
        <KPI icon="📈" value={`${metrics.completionRate}%`} label="Tasso Conformità"/>
        <KPI icon="⚠️" value={metrics.openRem} label="Remediation Aperte" details={metrics.overdue>0? `${metrics.overdue} scadute`: '—'}/>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Distribuzione Esiti Controlli">
          {Object.keys(metrics.resultsByOutcome).length? (
            <div className="space-y-4">
              {Object.entries(metrics.resultsByOutcome).map(([outcome,count])=>{
                const tot = Object.values(metrics.resultsByOutcome).reduce((a,b)=>a+b,0)
                const perc = Math.round((count/tot)*1000)/10
                const color = outcome==='Positivo'? 'bg-green-500': outcome==='Negativo'? 'bg-red-500':'bg-yellow-500'
                return (
                  <div key={outcome}>
                    <div className="flex justify-between text-sm mb-1"><span>{outcome}</span><span className="font-medium">{count} ({perc}%)</span></div>
                    <div className="w-full bg-gray-200 rounded-full h-4"><div className={`${color} h-4 rounded-full`} style={{width:`${perc}%`}}/></div>
                  </div>
                )
              })}
            </div>
          ): <EmptyState title="Nessun esito" description="I risultati appariranno qui"/>}
        </Card>
        <Card title="Sistemi per Stato Lifecycle">
          {(['Idea','Sviluppo','Uso','Dismissione'] as Lifecycle[]).map(state=>{
            const count = useAppStore.getState().systems.allIds.filter(id=>useAppStore.getState().systems.byId[id].lifecycleState===state).length
            const total = useAppStore.getState().systems.allIds.length || 1
            const perc = Math.round((count/total)*1000)/10
            return (
              <div key={state} className="flex items-center justify-between p-3 bg-gray-50 rounded mb-2">
                <span className="font-medium">{state}</span>
                <div className="flex items-center gap-3">
                  <div className="w-32 bg-gray-200 rounded-full h-2"><div className="bg-blue-500 h-2 rounded-full" style={{width:`${perc}%`}}/></div>
                  <span className="text-sm text-gray-600 w-12 text-right">{count}</span>
                </div>
              </div>
            )
          })}
        </Card>
      </div>

      <Card title="Attività Recenti">
        <div className="divide-y">
          {useAppStore.getState().runs.allIds.slice(0,5).map(id=>{
            const run = useAppStore.getState().runs.byId[id]
            const ctrl = useAppStore.getState().controls.byId[run.controlId]
            const sys = useAppStore.getState().systems.byId[run.aiSystemId]
            return (
              <div key={id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <div className="font-medium">{ctrl.title}</div>
                  <div className="text-sm text-gray-500">{sys.name} • {run.status}</div>
                </div>
                <div className="text-sm text-gray-500">{formatIT(run.plannedDate)}</div>
              </div>
            )
          })}
        </div>
      </Card>
    </div>
  )
}

const SystemsView: React.FC = () => {
  const { systems, addSystem, updateSystem } = useAppStore()
  const [filters, setFilters] = useState<{classification: ''|Classification, lifecycle: ''|Lifecycle}>({classification:'', lifecycle:''})
  const [search, setSearch] = useState('')

  const rows = useMemo(()=> systems.allIds.map(id=>systems.byId[id]).filter(s=>{
    const txt = (s.name + s.owner + s.description).toLowerCase()
    const matchSearch = txt.includes(search.toLowerCase())
    const matchC = !filters.classification || s.classification===filters.classification
    const matchL = !filters.lifecycle || s.lifecycleState===filters.lifecycle
    return matchSearch && matchC && matchL
  }),[systems, search, filters])

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-3">
          <select value={filters.classification} onChange={e=>setFilters(f=>({...f, classification: e.target.value as any}))} className="px-4 py-2 border rounded-lg">
            <option value="">Tutte le Classificazioni</option>
            {(['Alto Rischio','Medio Rischio','Basso Rischio','Interno'] as Classification[]).map(c=> <option key={c} value={c}>{c}</option>)}
          </select>
          <select value={filters.lifecycle} onChange={e=>setFilters(f=>({...f, lifecycle: e.target.value as any}))} className="px-4 py-2 border rounded-lg">
            <option value="">Tutti gli Stati</option>
            {(['Idea','Sviluppo','Uso','Dismissione'] as Lifecycle[]).map(l=> <option key={l} value={l}>{l}</option>)}
          </select>
          <input value={search} onChange={e=>setSearch(e.target.value)} className="px-4 py-2 border rounded-lg" placeholder="Cerca..."/>
        </div>
        <button onClick={()=>{
          addSystem({ name: 'Nuovo Sistema', owner: 'Owner', description: 'Descrizione', classification:'Interno', lifecycleState:'Idea', tags:[], riskLevel:1, dataCategories:[] })
        }} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"><Plus className="w-5 h-5"/>Nuovo Sistema</button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50"><tr>
            <Th> Sistema </Th><Th> Owner </Th><Th> Classificazione </Th><Th> Lifecycle </Th><Th> Aggiornato </Th><Th> Azioni </Th>
          </tr></thead>
          <tbody className="divide-y">
            {rows.map(s => (
              <tr key={s.id} className="hover:bg-gray-50">
                <Td><div className="font-medium">{s.name}</div><div className="text-sm text-gray-500">{s.description}</div></Td>
                <Td>{s.owner}</Td>
                <Td><Badge label={s.classification} kind={s.classification}/></Td>
                <Td><Badge label={s.lifecycleState} kind={s.lifecycleState}/></Td>
                <Td className="text-gray-500">{formatIT(s.updatedAt)}</Td>
                <Td>
                  <div className="flex gap-2">
                    <IconBtn label="Dettagli"><Eye className="w-4 h-4"/></IconBtn>
                    <IconBtn label="Modifica" onClick={()=> updateSystem(s.id, { name: s.name + ' *' })}><Edit className="w-4 h-4"/></IconBtn>
                  </div>
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const ControlsView: React.FC = () => {
  const store = useAppStore()
  const [selectedRunId, setSelectedRunId] = useState<string|undefined>()
  const [outcome, setOutcome] = useState<''|Outcome>('')
  const [notes, setNotes] = useState('')

  const columns: {status: string}[] = [
    {status:'Pianificazione'},{status:'Approvazione'},{status:'Esecuzione'},{status:'Esitazione'},{status:'Chiuso'}
  ]

  const runsByStatus = useMemo(()=>{
    const obj: Record<string, string[]> = {}
    store.runs.allIds.forEach(id=>{ const r=store.runs.byId[id]; (obj[r.status] ||= []).push(id) })
    return obj
  },[store.runs])

  const handleSubmit = () => {
    if (!selectedRunId || !outcome) return
    store.submitResult(selectedRunId, outcome, notes, 'blob://local')
    setSelectedRunId(undefined); setOutcome(''); setNotes('')
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <button className="px-4 py-2 rounded-lg bg-blue-600 text-white">Kanban</button>
        </div>
        <button onClick={()=> store.scheduleRun({ controlId: store.controls.allIds[0], aiSystemId: store.systems.allIds[0], plannedDate: new Date().toISOString() })} className="bg-blue-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-blue-700"><Plus className="w-5 h-5"/>Pianifica Controllo</button>
      </div>

      <div className="grid grid-cols-5 gap-4">
        {columns.map(col=> (
          <div key={col.status} className="bg-gray-50 rounded-lg p-4">
            <h4 className="font-semibold mb-3 text-sm flex items-center justify-between">{col.status}
              <span className="bg-gray-200 text-gray-700 px-2 py-1 rounded-full text-xs">{(runsByStatus[col.status]||[]).length}</span>
            </h4>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {(runsByStatus[col.status]||[]).map(id=>{
                const run = store.runs.byId[id]
                const ctrl = store.controls.byId[run.controlId]
                const sys = store.systems.byId[run.aiSystemId]
                return (
                  <div key={id} className="bg-white p-3 rounded shadow-sm hover:shadow-md transition cursor-pointer" onClick={()=> setSelectedRunId(id)}>
                    <div className="text-sm font-medium mb-1">{ctrl.code}</div>
                    <div className="text-xs text-gray-600 mb-2">{sys.name}</div>
                    <div className="text-xs text-gray-500">{formatIT(run.plannedDate)}</div>
                    {run.executorId && <div className="mt-2 text-xs text-blue-600">{run.executorId}</div>}
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      {selectedRunId && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold mb-4">Dettaglio Controllo</h3>
          {(()=>{
            const run = store.runs.byId[selectedRunId]
            const ctrl = store.controls.byId[run.controlId]
            const sys = store.systems.byId[run.aiSystemId]
            return (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label="Controllo" value={`${ctrl.title} (${ctrl.code})`}/>
                <Field label="Sistema AI" value={sys.name}/>
                <Field label="Stato" value={run.status}/>
                <Field label="Data Pianificata" value={formatIT(run.plannedDate)}/>
                {run.status==='Esecuzione' && (
                  <div className="md:col-span-2 border-t pt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-1">Esito *</label>
                        <select value={outcome} onChange={e=>setOutcome(e.target.value as Outcome)} className="w-full px-4 py-2 border rounded-lg">
                          <option value="">Seleziona Esito</option>
                          <option value="Positivo">Positivo</option>
                          <option value="Negativo">Negativo</option>
                          <option value="Positivo con Osservazioni">Positivo con Osservazioni</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Note</label>
                        <textarea value={notes} onChange={e=>setNotes(e.target.value)} className="w-full px-4 py-2 border rounded-lg" rows={3}/>
                      </div>
                    </div>
                    <button onClick={handleSubmit} className="mt-4 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">Salva Esito</button>
                  </div>
                )}
              </div>
            )
          })()}
        </div>
      )}
    </div>
  )
}

const RemediationsView: React.FC = () => {
  const store = useAppStore()
  const [status, setStatus] = useState<''|RemediationStatus>('')
  const rows = useMemo(()=> store.remediations.allIds.map(id=>store.remediations.byId[id]).filter(r=> !status || r.status===status ),[store.remediations, status])

  return (
    <div className="p-6 space-y-6">
      <div className="flex gap-3 items-center">
        <select value={status} onChange={e=>setStatus(e.target.value as RemediationStatus| '')} className="px-4 py-2 border rounded-lg">
          <option value="">Tutti gli stati</option>
          {(['Aperta','In Corso','Sospesa','Completata','Scaduta'] as RemediationStatus[]).map(s=> <option key={s} value={s}>{s}</option>)}
        </select>
        <button onClick={()=> exportCSV(rows, 'remediations.csv')} className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700"><Download className="w-5 h-5"/>Export CSV</button>
      </div>

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50"><tr>
            <Th> Remediation </Th><Th> Sistema/Controllo </Th><Th> Assegnatario </Th><Th> Scadenza </Th><Th> Stato </Th><Th> Azioni </Th>
          </tr></thead>
          <tbody className="divide-y">
            {rows.map(r=>{
              const sys = store.systems.byId[r.aiSystemId]
              const ctrl = store.controls.byId[r.controlId]
              const d = daysUntil(r.dueDate)
              const overdue = d<0 && r.status!=='Completata'
              return (
                <tr key={r.id} className="hover:bg-gray-50">
                  <Td><div className="font-medium">{r.description}</div>{r.priority==='Alta' && <span className="text-xs text-red-600 font-medium">⚠️ Priorità Alta</span>}</Td>
                  <Td><div className="text-sm">{sys?.name}</div><div className="text-gray-500 text-sm">{ctrl?.code}</div></Td>
                  <Td className="text-sm">{r.assigneeId}</Td>
                  <Td className="text-sm">
                    <div className={overdue? 'text-red-600 font-medium':''}>{formatIT(r.dueDate)}</div>
                    <div className="text-xs text-gray-500">{overdue? `Scaduta da ${Math.abs(d)} giorni` : d===0? 'Scade oggi' : `${d} giorni rimanenti`}</div>
                  </Td>
                  <Td><span className="px-2 py-1 text-xs rounded-full bg-gray-100">{r.status}</span></Td>
                  <Td>
                    <div className="flex gap-2">
                      {r.status!=='Completata' && (
                        <>
                          <button className="text-blue-600 hover:text-blue-800 text-sm" onClick={()=> store.updateRemediation(r.id, { status: 'Completata' })}>Completa</button>
                          <button className="text-gray-600 hover:text-gray-800 text-sm" onClick={()=> store.updateRemediation(r.id, { dueDate: addDaysISO(r.dueDate, 7) })}>Rinvia</button>
                        </>
                      )}
                    </div>
                  </Td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const ReportsView: React.FC = () => {
  const store = useAppStore()
  const overdue = store.remediations.allIds.filter(id=>{
    const r = store.remediations.byId[id]; return daysUntil(r.dueDate)<0 && r.status!=='Completata'
  }).length
  const systemsCompliance = store.systems.allIds.map(id=>{
    const sys = store.systems.byId[id]
    const runs = store.runs.allIds.map(rid=>store.runs.byId[rid]).filter(r=> r.aiSystemId===id)
    const closed = runs.filter(r=> r.status==='Chiuso').length
    const compliance = runs.length? Math.round((closed/runs.length)*1000)/10 : 0
    return { id, name: sys.name, classification: sys.classification, compliance }
  })

  return (
    <div className="p-6 space-y-6">
      <Card title="Report Conformità Sistemi">
        <div className="grid grid-cols-3 gap-4 mb-6">
          <Stat label="Tasso Conformità Globale" value={`${Math.round((systemsCompliance.reduce((a,b)=>a+b.compliance,0)/(systemsCompliance.length||1))*10)/10}%`} color="text-green-600"/>
          <Stat label="Controlli Totali" value={`${store.runs.allIds.length}`} color="text-blue-600"/>
          <Stat label="Remediation Scadute" value={`${overdue}`} color="text-red-600"/>
        </div>
        {systemsCompliance.map(s=> (
          <div key={s.id} className="flex items-center justify-between p-3 bg-gray-50 rounded mb-2">
            <div><div className="font-medium">{s.name}</div><div className="text-sm text-gray-500">{s.classification}</div></div>
            <div className="flex items-center gap-3">
              <div className="w-32 bg-gray-200 rounded-full h-2"><div className={`${s.compliance>=80? 'bg-green-500': s.compliance>=50? 'bg-yellow-500':'bg-red-500'} h-2 rounded-full`} style={{width:`${s.compliance}%`}}/></div>
              <span className="text-sm font-medium w-12 text-right">{s.compliance}%</span>
            </div>
          </div>
        ))}
        <div className="mt-4">
          <button onClick={()=> exportCSV(systemsCompliance, 'compliance.csv')} className="bg-green-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 hover:bg-green-700"><Download className="w-5 h-5"/>Export CSV</button>
        </div>
      </Card>
    </div>
  )
}

// --- UI primitives ---
const EmptyState: React.FC<{title:string,description:string}> = ({title,description}) => (
  <div className="text-center py-6">
    <div className="text-lg font-medium">{title}</div>
    <div className="text-sm text-gray-500">{description}</div>
  </div>
)
const Stat: React.FC<{label:string,value:string,color?:string}> = ({label,value,color=''}) => (
  <div className="text-center">
    <div className={`text-2xl font-bold ${color}`}>{value}</div>
    <div className="text-sm text-gray-500">{label}</div>
  </div>
)
// --- UI primitives ---

const Card: React.FC<{title:string, children:React.ReactNode}> = ({title, children}) => (
  <div className="bg-white rounded-lg shadow p-6">
    <h3 className="text-lg font-semibold mb-4">{title}</h3>
    {children}
  </div>
)
const KPI: React.FC<{icon:string,value:React.ReactNode,label:string,details?:string}> = ({icon,value,label,details}) => (
  <div className="bg-white rounded-lg shadow p-6">
    <div className="flex items-center justify-between mb-4">
      <span className="text-2xl">{icon}</span>
      <span className="text-3xl font-bold">{value}</span>
    </div>
    <h3 className="text-gray-600 text-sm">{label}</h3>
    {details && <div className="mt-2 text-xs text-gray-500">{details}</div>}
  </div>
)
const Th: React.FC<{children:React.ReactNode}> = ({children}) => <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">{children}</th>
const Td: React.FC<{children:React.ReactNode, className?:string}> = ({children, className}) => <td className={`px-6 py-4 ${className||''}`}>{children}</td>
const IconBtn: React.FC<{children:React.ReactNode,onClick?:()=>void,label:string}> = ({children,onClick,label}) => (
  <button aria-label={label} onClick={onClick} className="text-gray-600 hover:text-gray-800" title={label}>{children}</button>
)
const Field: React.FC<{label:string,value:string}> = ({label,value}) => (
  <div><div className="text-sm text-gray-600">{label}</div><div className="font-medium">{value}</div></div>
)
const Badge: React.FC<{label:string, kind: string}> = ({label, kind}) => {
  const map: Record<string,string> = {
    'Alto Rischio':'bg-red-100 text-red-800','Medio Rischio':'bg-yellow-100 text-yellow-800','Basso Rischio':'bg-green-100 text-green-800','Interno':'bg-gray-100 text-gray-800',
    'Uso':'bg-blue-100 text-blue-800','Sviluppo':'bg-purple-100 text-purple-800','Dismissione':'bg-gray-100 text-gray-800','Idea':'bg-cyan-100 text-cyan-800'
  }
  return <span className={`px-2 py-1 text-xs rounded-full ${map[kind]||'bg-gray-100 text-gray-800'}`}>{label}</span>
}

const App: React.FC = () => {
  const { currentUser, remediations } = useAppStore()
  const [view, setView] = useState('dashboard')
  const [search, setSearch] = useState('')
  const overdue = remediations.allIds.filter(id=>{
    const r = remediations.byId[id]; return daysUntil(r.dueDate)<0 && r.status!=='Completata'
  }).length

  return (
    <div className="flex h-screen bg-gray-100">
      <Sidebar view={view} setView={setView} userName={currentUser.name} role={currentUser.role}/>
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar title={view} search={search} setSearch={setSearch} overdue={overdue} onToggleNotif={()=>{}}/>
        <div className="flex-1 overflow-y-auto">
          {view==='dashboard' && <DashboardView/>}
          {view==='systems' && <SystemsView/>}
          {view==='controls' && <ControlsView/>}
          {view==='remediations' && <RemediationsView/>}
          {view==='reports' && <ReportsView/>}
        </div>
      </div>
    </div>
  )
}

export default App
