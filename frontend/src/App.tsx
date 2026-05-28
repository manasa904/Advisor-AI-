import { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000";;

type Message = { role: "user" | "assistant"; content: string };
type Client = { client_id: string; name: string; age: number; segment: string; aum: number; risk_appetite: string; investment_goal: string; relationship_manager: string; };
type Holding = { ticker: string; company_name: string; sector: string; quantity: number; current_price: number; current_value: number; weight_pct: number; unrealized_pnl: number; };
type User = { access_token: string; role: string; full_name: string; username: string; rm_id: string | null; };

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [loginForm, setLoginForm] = useState({ username: "", password: "" });
  const [loginError, setLoginError] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);

  const [messages, setMessages] = useState<Message[]>([{ role: "assistant", content: "Hello! I'm your Advisor AI. Select a client or ask me anything." }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [clients, setClients] = useState<Client[]>([]);
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [holdings, setHoldings] = useState<Holding[]>([]);
  const [riskClients, setRiskClients] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<"holdings"|"risk"|"compliance"|"nba"|"scenarios">("holdings");
  const bottomRef = useRef<HTMLDivElement>(null);

  const [alerts, setAlerts] = useState<any[]>([]);
  const [alertsOpen, setAlertsOpen] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const [complianceForm, setComplianceForm] = useState({ ticker: "", sector: "Technology", action: "BUY", quantity: 100, price: 0 });
  const [complianceResult, setComplianceResult] = useState<any>(null);
  const [complianceLoading, setComplianceLoading] = useState(false);

  const [nbaData, setNbaData] = useState<any>(null);
  const [nbaLoading, setNbaLoading] = useState(false);
  const [lifeEvents, setLifeEvents] = useState<any[]>([]);
  const [scenarioResult, setScenarioResult] = useState<any>(null);
  const [scenarioLoading, setScenarioLoading] = useState(false);
  const [scenarioType, setScenarioType] = useState("MARKET_CRASH");
  const [scenarioMag, setScenarioMag] = useState(20);

  const [auditLog, setAuditLog] = useState<any[]>([]);
  const [violationsSummary, setViolationsSummary] = useState<any[]>([]);
  const [hitlQueue, setHitlQueue] = useState<any[]>([]);
  const [modelRegistry, setModelRegistry] = useState<any[]>([]);
  const [complianceView, setComplianceView] = useState<"violations"|"audit"|"hitl">("violations");

  const [opsSummary, setOpsSummary] = useState<any>(null);
  const [opsTransactions, setOpsTransactions] = useState<any[]>([]);
  const [rmSummary, setRmSummary] = useState<any[]>([]);
  const [sysMetrics, setSysMetrics] = useState<any>(null);
  const [opsView, setOpsView] = useState<"transactions"|"metrics"|"models">("transactions");
  const [anomalies, setAnomalies] = useState<any[]>([]);

  const [isListening, setIsListening] = useState(false);
  const recognitionRef = useRef<any>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    if (!user) return;
    const ws = new WebSocket("ws://localhost:8000/api/alerts/ws");
    wsRef.current = ws;
    ws.onmessage = (e) => { const a = JSON.parse(e.data); setAlerts(p => [a, ...p].slice(0, 50)); };
    ws.onerror = () => {};
    return () => ws.close();
  }, [user]);

  useEffect(() => {
    if (!user) return;
    if (user.role === "ADVISOR") { loadClients(); loadRiskClients(); }
    if (user.role === "COMPLIANCE") { loadAuditLog(); loadViolations(); loadHITL(); loadModelRegistry(); }
    if (user.role === "OPERATIONS") { loadOpsSummary(); loadOpsTransactions(); loadRmSummary(); loadMetrics(); loadAnomalies(); }
  }, [user]);

  const handleLogin = async () => {
    setLoginLoading(true); setLoginError("");
    try {
      const res = await axios.post(`${API}/api/auth/login`, loginForm);
      setUser(res.data);
    } catch {
      try {
        const res2 = await axios.post(`${API}/api/v1/auth/login`, loginForm);
        setUser(res2.data);
      } catch {
        setLoginError("Invalid username or password.");
      }
    } finally { setLoginLoading(false); }
  };

  const handleLogout = () => { setUser(null); setClients([]); setSelectedClient(null); setHoldings([]); setAlerts([]); setMessages([{ role: "assistant", content: "Hello! I'm your Advisor AI." }]); };

  const loadClients = async () => { try { console.log("Loading clients..."); const r = await axios.get(`${API}/api/v1/portfolio/clients`); console.log("CLIENT RESPONSE:", r.data); setClients(r.data); } catch (err) { console.error("CLIENT LOAD ERROR:", err); } };
  const loadRiskClients = async () => { try { const r = await axios.get(`${API}/api/portfolio/risk/concentration`); setRiskClients(r.data); } catch {} };
  const loadAuditLog = async () => { try { const r = await axios.get(`${API}/api/compliance/audit-log?limit=100`); setAuditLog(r.data); } catch {} };
  const loadViolations = async () => { try { const r = await axios.get(`${API}/api/compliance/violations-summary`); setViolationsSummary(r.data); } catch {} };
  const loadHITL = async () => { try { const r = await axios.get(`${API}/api/governance/hitl/queue`); setHitlQueue(r.data.items || []); } catch {} };
  const loadModelRegistry = async () => { try { const r = await axios.get(`${API}/api/governance/models/registry`); setModelRegistry(r.data.models || []); } catch {} };
  const loadOpsSummary = async () => { try { const r = await axios.get(`${API}/api/operations/summary`); setOpsSummary(r.data); } catch {} };
  const loadOpsTransactions = async () => { try { const r = await axios.get(`${API}/api/operations/transactions`); setOpsTransactions(r.data); } catch {} };
  const loadRmSummary = async () => { try { const r = await axios.get(`${API}/api/operations/rm-summary`); setRmSummary(r.data); } catch {} };
  const loadMetrics = async () => { try { const r = await axios.get(`${API}/api/metrics`); setSysMetrics(r.data); } catch {} };
  const loadAnomalies = async () => { try { const r = await axios.get(`${API}/api/analytics/anomalies`); setAnomalies(r.data.anomalies || []); } catch {} };

  const selectClient = async (client: Client) => {
    setSelectedClient(client); setActiveTab("holdings"); setComplianceResult(null); setNbaData(null); setLifeEvents([]); setScenarioResult(null);
    try { const r = await axios.get(`${API}/api/portfolio/clients/${client.client_id}/holdings`); setHoldings(r.data); } catch {}
    setMessages(p => [...p, { role: "assistant", content: `Loaded ${client.name}. AUM: Rs.${client.aum.toLocaleString()}. Risk: ${client.risk_appetite}. Goal: ${client.investment_goal}.` }]);
  };

  const loadNBA = async () => {
    if (!selectedClient) return;
    setNbaLoading(true);
    try {
      const [nbaRes, eventsRes] = await Promise.all([
        axios.get(`${API}/api/revenue/nba/${selectedClient.client_id}`),
        axios.get(`${API}/api/revenue/life-events/${selectedClient.client_id}`)
      ]);
      setNbaData(nbaRes.data);
      setLifeEvents(eventsRes.data.events || []);
    } catch {} finally { setNbaLoading(false); }
  };

  const runScenario = async () => {
    if (!selectedClient) return;
    setScenarioLoading(true);
    try { const r = await axios.post(`${API}/api/revenue/scenario/${selectedClient.client_id}`, { scenario_type: scenarioType, magnitude: Number(scenarioMag) }); setScenarioResult(r.data); }
    catch {} finally { setScenarioLoading(false); }
  };

  const runComplianceCheck = async () => {
    if (!selectedClient || !complianceForm.ticker) return;
    setComplianceLoading(true);
    try { const r = await axios.post(`${API}/api/compliance/pretrade-check`, { client_id: selectedClient.client_id, ...complianceForm, quantity: Number(complianceForm.quantity), price: Number(complianceForm.price) }); setComplianceResult(r.data); }
    catch {} finally { setComplianceLoading(false); }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const question = selectedClient ? `${input} (client: ${selectedClient.client_id} - ${selectedClient.name})` : input;
    setMessages(p => [...p, { role: "user", content: input }]); setInput(""); setLoading(true);
    try { const r = await axios.post(`${API}/api/chat/query`, { question }, { timeout: 120000 }); setMessages(p => [...p, { role: "assistant", content: r.data.answer }]); }
    catch { setMessages(p => [...p, { role: "assistant", content: "Error reaching AI backend." }]); }
    finally { setLoading(false); }
  };

  const startVoice = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) { alert("Voice not supported in this browser. Try Chrome."); return; }
    const rec = new SpeechRecognition();
    rec.lang = "en-US"; rec.continuous = false; rec.interimResults = false;
    rec.onstart = () => setIsListening(true);
    rec.onend = () => setIsListening(false);
    rec.onresult = (e: any) => { setInput(e.results[0][0].transcript); };
    rec.onerror = () => setIsListening(false);
    recognitionRef.current = rec;
    rec.start();
  };

  const totalValue = holdings.reduce((s, h) => s + h.current_value, 0);
  const totalPnL = holdings.reduce((s, h) => s + h.unrealized_pnl, 0);
  const sectorMap: Record<string, number> = {};
  holdings.forEach(h => { sectorMap[h.sector] = (sectorMap[h.sector] || 0) + h.current_value; });

  const SC: Record<string, string> = { Technology:"#3182ce", Financials:"#38a169", Energy:"#d69e2e", Commodities:"#e53e3e", Bonds:"#805ad5", Index:"#319795", Consumer:"#dd6b20", Automobile:"#d53f8c", Insurance:"#00b5d8", "Consumer Tech":"#f6ad55" };
  const AC: Record<string, {bg:string;border:string;text:string}> = { CRITICAL:{bg:"#fff5f5",border:"#fc8181",text:"#c53030"}, HIGH:{bg:"#fff5f5",border:"#feb2b2",text:"#c53030"}, MEDIUM:{bg:"#fffaf0",border:"#f6ad55",text:"#b7791f"}, INFO:{bg:"#ebf8ff",border:"#90cdf4",text:"#2b6cb0"} };
  const RC: Record<string,string> = {ADVISOR:"#3182ce",COMPLIANCE:"#c53030",OPERATIONS:"#276749"};

  // LOGIN SCREEN
  if (!user) return (
    <div style={{minHeight:"100vh",backgroundColor:"#f0f4f8",display:"flex",alignItems:"center",justifyContent:"center",fontFamily:"Inter,sans-serif"}}>
      <div style={{width:420}}>
        <div style={{textAlign:"center",marginBottom:32}}>
          <div style={{width:64,height:64,borderRadius:"50%",backgroundColor:"#1a365d",color:"white",fontSize:28,fontWeight:"bold",display:"flex",alignItems:"center",justifyContent:"center",margin:"0 auto 16px"}}>A</div>
          <div style={{fontSize:28,fontWeight:700,color:"#1a365d"}}>Advisor AI</div>
          <div style={{fontSize:14,color:"#718096",marginTop:4}}>Intelligent Financial Assistant</div>
        </div>
        <div style={{backgroundColor:"white",borderRadius:12,padding:36,boxShadow:"0 4px 24px rgba(0,0,0,0.08)"}}>
          <div style={{fontSize:18,fontWeight:700,color:"#1a202c",marginBottom:24}}>Sign In</div>
          {["username","password"].map(f => (
            <div key={f} style={{marginBottom:16}}>
              <div style={{fontSize:12,fontWeight:600,color:"#4a5568",marginBottom:6,textTransform:"capitalize"}}>{f}</div>
              <input type={f==="password"?"password":"text"} value={(loginForm as any)[f]} onChange={e=>setLoginForm(p=>({...p,[f]:e.target.value}))} onKeyDown={e=>e.key==="Enter"&&handleLogin()} placeholder={f==="username"?"e.g. advisor1":"Enter password"} style={{width:"100%",padding:"11px 14px",borderRadius:8,border:"1px solid #e2e8f0",fontSize:14,outline:"none",backgroundColor:"#f7fafc",boxSizing:"border-box"}} />
            </div>
          ))}
          {loginError && <div style={{backgroundColor:"#fff5f5",border:"1px solid #fed7d7",borderRadius:6,padding:"10px 14px",fontSize:13,color:"#c53030",marginBottom:16}}>{loginError}</div>}
          <button onClick={handleLogin} disabled={loginLoading||!loginForm.username||!loginForm.password} style={{width:"100%",padding:12,backgroundColor:loginLoading?"#a0aec0":"#1a365d",color:"white",border:"none",borderRadius:8,fontWeight:700,fontSize:15,cursor:"pointer",marginTop:8}}>{loginLoading?"Signing in...":"Sign In"}</button>
          <div style={{marginTop:28,padding:16,backgroundColor:"#f7fafc",borderRadius:8,border:"1px solid #e2e8f0"}}>
            <div style={{fontSize:11,fontWeight:700,color:"#718096",marginBottom:10,letterSpacing:0.5}}>TEST CREDENTIALS</div>
            {[{u:"advisor1",p:"advisor123",r:"ADVISOR",c:"#3182ce"},{u:"compliance1",p:"compliance123",r:"COMPLIANCE",c:"#c53030"},{u:"ops1",p:"ops123",r:"OPERATIONS",c:"#276749"}].map((c,i)=>(
              <div key={i} onClick={()=>setLoginForm({username:c.u,password:c.p})} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"8px 10px",borderRadius:6,marginBottom:6,cursor:"pointer",backgroundColor:"white",border:"1px solid #e2e8f0"}}>
                <span style={{fontSize:13,fontWeight:600,color:"#2d3748"}}>{c.u} / {c.p}</span>
                <span style={{fontSize:10,padding:"2px 8px",borderRadius:10,fontWeight:700,backgroundColor:c.c+"22",color:c.c}}>{c.r}</span>
              </div>
            ))}
            <div style={{fontSize:11,color:"#a0aec0",marginTop:6}}>Click any row to auto-fill</div>
          </div>
        </div>
      </div>
    </div>
  );

  const Header = () => (
    <div style={{backgroundColor:"#1a365d",color:"white",padding:"12px 24px",display:"flex",alignItems:"center",gap:12,boxShadow:"0 2px 8px rgba(0,0,0,0.3)",zIndex:10,flexShrink:0}}>
      <div style={{width:36,height:36,borderRadius:"50%",backgroundColor:RC[user.role]||"#3182ce",display:"flex",alignItems:"center",justifyContent:"center",fontWeight:"bold",fontSize:14}}>{user.full_name.charAt(0)}</div>
      <div><div style={{fontWeight:700,fontSize:17}}>Advisor AI</div><div style={{fontSize:11,opacity:0.75}}>Intelligent Financial Assistant · RAG + LLM</div></div>
      <div style={{marginLeft:"auto",display:"flex",gap:12,alignItems:"center"}}>
        <div style={{backgroundColor:"#2d3748",padding:"6px 14px",borderRadius:8,fontSize:13}}>
          <span style={{opacity:0.7}}>Signed in as </span><strong>{user.full_name}</strong>
          <span style={{marginLeft:8,fontSize:10,padding:"2px 8px",borderRadius:10,fontWeight:700,backgroundColor:(RC[user.role]||"#3182ce")+"44",color:"white"}}>{user.role}</span>
        </div>
        <button onClick={()=>setAlertsOpen(o=>!o)} style={{position:"relative",backgroundColor:"transparent",border:"1px solid #4a5568",color:"white",padding:"6px 14px",borderRadius:8,cursor:"pointer",fontSize:13}}>
          Alerts{alerts.length>0&&<span style={{position:"absolute",top:-6,right:-6,backgroundColor:"#e53e3e",color:"white",fontSize:10,fontWeight:"bold",width:18,height:18,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center"}}>{alerts.length>9?"9+":alerts.length}</span>}
        </button>
        <button onClick={handleLogout} style={{backgroundColor:"transparent",border:"1px solid #4a5568",color:"#a0aec0",padding:"6px 14px",borderRadius:8,cursor:"pointer",fontSize:13}}>Sign Out</button>
        <span style={{backgroundColor:"#276749",color:"white",fontSize:11,padding:"4px 12px",borderRadius:12}}>Live</span>
      </div>
    </div>
  );

  const AlertsPanel = () => alertsOpen ? (
    <div style={{position:"fixed",top:60,right:20,width:420,maxHeight:520,backgroundColor:"white",borderRadius:10,boxShadow:"0 8px 32px rgba(0,0,0,0.18)",zIndex:1000,display:"flex",flexDirection:"column",border:"1px solid #e2e8f0"}}>
      <div style={{padding:"14px 18px",display:"flex",justifyContent:"space-between",alignItems:"center",backgroundColor:"#1a365d",borderRadius:"10px 10px 0 0"}}>
        <span style={{fontWeight:700,color:"white",fontSize:15}}>Live Alerts ({alerts.length})</span>
        <button onClick={()=>setAlertsOpen(false)} style={{background:"transparent",border:"none",color:"white",fontSize:20,cursor:"pointer"}}>x</button>
      </div>
      <div style={{overflowY:"auto",flex:1}}>
        {alerts.length===0?<div style={{padding:24,textAlign:"center",color:"#a0aec0",fontSize:13}}>Waiting for Kafka alerts...</div>
         :alerts.map((a,i)=>{const c=AC[a.severity]||AC.INFO;return(
          <div key={i} style={{padding:"12px 16px",borderBottom:"1px solid #f0f0f0",backgroundColor:c.bg,borderLeft:`4px solid ${c.border}`}}>
            <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
              <span style={{fontSize:11,fontWeight:700,color:c.text}}>{a.severity} · {(a.alert_type||"").replace(/_/g," ")}</span>
              <span style={{fontSize:10,color:"#a0aec0"}}>{new Date(a.timestamp).toLocaleTimeString()}</span>
            </div>
            <div style={{fontSize:12,color:"#2d3748",lineHeight:1.5}}>{a.message}</div>
            {a.client_id&&a.client_id!=="ALL"&&<div style={{fontSize:11,color:"#718096",marginTop:4}}>Client: <strong>{a.client_id}</strong>{a.ticker&&<span> · {a.ticker}</span>}</div>}
          </div>
        );})}
      </div>
      <div style={{padding:"10px 16px",borderTop:"1px solid #e2e8f0",display:"flex",justifyContent:"space-between"}}>
        <span style={{fontSize:11,color:"#68d391"}}>Live via Kafka WebSocket</span>
        <button onClick={()=>setAlerts([])} style={{fontSize:11,color:"#e53e3e",background:"none",border:"none",cursor:"pointer"}}>Clear All</button>
      </div>
    </div>
  ):null;

  // COMPLIANCE VIEW
  if (user.role==="COMPLIANCE") return (
    <div style={{display:"flex",flexDirection:"column",height:"100vh",fontFamily:"Inter,sans-serif",backgroundColor:"#edf2f7"}}>
      <Header/><AlertsPanel/>
      <div style={{flex:1,overflowY:"auto",padding:24}}>
        <div style={{marginBottom:20}}><div style={{fontSize:22,fontWeight:700,color:"#1a365d"}}>Compliance Dashboard</div><div style={{fontSize:13,color:"#718096",marginTop:4}}>Pre-trade checks, violations, audit trail, HITL queue</div></div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:16,marginBottom:24}}>
          {[
            {label:"Total Violations",value:violationsSummary.filter(v=>v.severity==="HIGH"||v.severity==="CRITICAL").length,color:"#c53030"},
            {label:"Warnings",value:violationsSummary.filter(v=>v.severity==="MEDIUM").length,color:"#b7791f"},
            {label:"Audit Entries",value:auditLog.length,color:"#3182ce"},
            {label:"HITL Pending",value:hitlQueue.filter((h:any)=>h.status==="pending").length,color:"#805ad5"},
          ].map((s,i)=>(
            <div key={i} style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",borderTop:`3px solid ${s.color}`}}>
              <div style={{fontSize:11,color:"#718096",marginBottom:6}}>{s.label}</div>
              <div style={{fontSize:28,fontWeight:700,color:s.color}}>{s.value}</div>
            </div>
          ))}
        </div>
        <div style={{display:"flex",gap:8,marginBottom:16}}>
          {(["violations","audit","hitl"] as const).map(v=>(
            <button key={v} onClick={()=>setComplianceView(v)} style={{padding:"8px 20px",borderRadius:6,border:"none",fontWeight:600,fontSize:13,cursor:"pointer",backgroundColor:complianceView===v?"#1a365d":"white",color:complianceView===v?"white":"#4a5568",boxShadow:"0 1px 3px rgba(0,0,0,0.1)"}}>
              {v==="violations"?"Violations":v==="audit"?"Audit Log":"HITL Queue"}
            </button>
          ))}
        </div>
        {complianceView==="violations"&&(
          <div style={{backgroundColor:"white",borderRadius:10,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",overflow:"hidden"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
              <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Client","Rule","Severity","Count","Last Occurrence"].map(h=><th key={h} style={{padding:"12px 16px",textAlign:"left",fontWeight:600,color:"#4a5568",fontSize:12}}>{h}</th>)}</tr></thead>
              <tbody>{violationsSummary.map((v,i)=>(
                <tr key={i} style={{borderTop:"1px solid #edf2f7"}}>
                  <td style={{padding:"12px 16px",fontWeight:700,color:"#3182ce"}}>{v.client_id}</td>
                  <td style={{padding:"12px 16px"}}>{v.rule_name}</td>
                  <td style={{padding:"12px 16px"}}><span style={{fontSize:11,padding:"2px 10px",borderRadius:10,fontWeight:700,backgroundColor:v.severity==="CRITICAL"?"#fed7d7":v.severity==="HIGH"?"#feebc8":"#fefcbf",color:v.severity==="CRITICAL"?"#c53030":v.severity==="HIGH"?"#b7791f":"#744210"}}>{v.severity}</span></td>
                  <td style={{padding:"12px 16px",fontWeight:700}}>{v.count}</td>
                  <td style={{padding:"12px 16px",color:"#718096"}}>{new Date(v.last_occurrence).toLocaleString()}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
        {complianceView==="audit"&&(
          <div style={{backgroundColor:"white",borderRadius:10,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",overflow:"hidden"}}>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
              <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Time","Client","Rule","Ticker","Action","Result","Message"].map(h=><th key={h} style={{padding:"10px 12px",textAlign:"left",fontWeight:600,color:"#4a5568",fontSize:11}}>{h}</th>)}</tr></thead>
              <tbody>{auditLog.map((a,i)=>(
                <tr key={i} style={{borderTop:"1px solid #edf2f7",backgroundColor:a.result==="FAIL"?"#fff5f5":a.result==="WARN"?"#fffaf0":"white"}}>
                  <td style={{padding:"8px 12px",color:"#718096"}}>{new Date(a.timestamp).toLocaleTimeString()}</td>
                  <td style={{padding:"8px 12px",fontWeight:700,color:"#3182ce"}}>{a.client_id}</td>
                  <td style={{padding:"8px 12px"}}>{a.rule_name}</td>
                  <td style={{padding:"8px 12px"}}>{a.ticker||"-"}</td>
                  <td style={{padding:"8px 12px"}}>{a.action||"-"}</td>
                  <td style={{padding:"8px 12px"}}><span style={{fontSize:10,padding:"2px 8px",borderRadius:10,fontWeight:700,backgroundColor:a.result==="PASS"?"#c6f6d5":a.result==="FAIL"?"#fed7d7":"#feebc8",color:a.result==="PASS"?"#276749":a.result==="FAIL"?"#c53030":"#b7791f"}}>{a.result}</span></td>
                  <td style={{padding:"8px 12px",color:"#4a5568",maxWidth:300,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{a.message}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
        {complianceView==="hitl"&&(
          <div>
            {hitlQueue.length===0?<div style={{backgroundColor:"white",borderRadius:10,padding:40,textAlign:"center",color:"#718096",boxShadow:"0 1px 4px rgba(0,0,0,0.08)"}}>No items in HITL queue</div>
            :hitlQueue.map((h:any,i:number)=>(
              <div key={i} style={{backgroundColor:"white",borderRadius:10,padding:20,marginBottom:12,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",border:"1px solid #e2e8f0"}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                  <div><strong style={{fontSize:14}}>{h.request_type}</strong><span style={{marginLeft:8,fontSize:12,color:"#718096"}}>Client: {h.client_id}</span></div>
                  <span style={{fontSize:11,padding:"3px 10px",borderRadius:10,backgroundColor:h.status==="pending"?"#feebc8":"#c6f6d5",color:h.status==="pending"?"#b7791f":"#276749",fontWeight:700}}>{h.status}</span>
                </div>
                <div style={{fontSize:13,color:"#4a5568",marginBottom:12}}>{h.details}</div>
                <div style={{fontSize:11,color:"#a0aec0"}}>{new Date(h.submitted_at).toLocaleString()}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  // OPERATIONS VIEW
  if (user.role==="OPERATIONS") return (
    <div style={{display:"flex",flexDirection:"column",height:"100vh",fontFamily:"Inter,sans-serif",backgroundColor:"#edf2f7"}}>
      <Header/><AlertsPanel/>
      <div style={{flex:1,overflowY:"auto",padding:24}}>
        <div style={{marginBottom:20}}><div style={{fontSize:22,fontWeight:700,color:"#1a365d"}}>Operations Dashboard</div><div style={{fontSize:13,color:"#718096"}}>AUM overview, transactions, RM performance, system metrics</div></div>
        {opsSummary&&<div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:16,marginBottom:24}}>
          {[{label:"Total AUM",value:`Rs.${Number(opsSummary.aum_summary?.total_aum||0).toLocaleString()}`,color:"#3182ce"},{label:"Total Clients",value:String(opsSummary.aum_summary?.total_clients||0),color:"#805ad5"},{label:"Transactions",value:String(opsSummary.transaction_summary?.total_transactions||0),color:"#276749"},{label:"Total Trade Value",value:`Rs.${Number(opsSummary.transaction_summary?.total_value||0).toLocaleString()}`,color:"#b7791f"}].map((s,i)=>(
            <div key={i} style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",borderTop:`3px solid ${s.color}`}}>
              <div style={{fontSize:11,color:"#718096",marginBottom:6}}>{s.label}</div>
              <div style={{fontSize:20,fontWeight:700,color:s.color}}>{s.value}</div>
            </div>
          ))}
        </div>}
        <div style={{display:"flex",gap:8,marginBottom:16}}>
          {(["transactions","metrics","models"] as const).map(v=>(
            <button key={v} onClick={()=>setOpsView(v)} style={{padding:"8px 20px",borderRadius:6,border:"none",fontWeight:600,fontSize:13,cursor:"pointer",backgroundColor:opsView===v?"#1a365d":"white",color:opsView===v?"white":"#4a5568",boxShadow:"0 1px 3px rgba(0,0,0,0.1)"}}>
              {v==="transactions"?"All Transactions":v==="metrics"?"System Metrics":"Model Registry"}
            </button>
          ))}
        </div>
        {opsView==="transactions"&&(
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
            <div style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)"}}>
              <div style={{fontWeight:700,fontSize:15,marginBottom:16,color:"#1a365d"}}>RM Performance</div>
              {rmSummary.map((rm,i)=>(
                <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 0",borderBottom:"1px solid #f0f0f0"}}>
                  <div><div style={{fontWeight:600,fontSize:13}}>{rm.relationship_manager}</div><div style={{fontSize:11,color:"#718096"}}>{rm.client_count} clients</div></div>
                  <div style={{textAlign:"right"}}><div style={{fontWeight:700,fontSize:14,color:"#3182ce"}}>Rs.{Number(rm.total_aum).toLocaleString()}</div><div style={{fontSize:11,color:"#718096"}}>Avg Rs.{Number(rm.avg_aum).toLocaleString()}</div></div>
                </div>
              ))}
            </div>
            <div style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)"}}>
              <div style={{fontWeight:700,fontSize:15,marginBottom:16,color:"#1a365d"}}>Anomaly Flags</div>
              {anomalies.slice(0,5).map((a,i)=>(
                <div key={i} style={{backgroundColor:a.severity==="HIGH"?"#fff5f5":"#fffaf0",border:`1px solid ${a.severity==="HIGH"?"#fed7d7":"#feebc8"}`,borderRadius:6,padding:"10px 12px",marginBottom:8,fontSize:12}}>
                  <div style={{fontWeight:700,color:a.severity==="HIGH"?"#c53030":"#b7791f"}}>{a.anomaly_type} — {a.client_id}</div>
                  <div style={{color:"#4a5568",marginTop:4}}>{a.description}</div>
                </div>
              ))}
              {anomalies.length===0&&<div style={{color:"#718096",textAlign:"center",padding:20}}>Run anomaly detection first</div>}
            </div>
          </div>
        )}
        {opsView==="transactions"&&(
          <div style={{backgroundColor:"white",borderRadius:10,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",overflow:"hidden"}}>
            <div style={{padding:"16px 20px",borderBottom:"1px solid #e2e8f0",fontWeight:700,fontSize:15,color:"#1a365d"}}>All Transactions</div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
              <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Date","Client","Segment","Ticker","Type","Qty","Price","Amount","RM"].map(h=><th key={h} style={{padding:"10px 14px",textAlign:"left",fontWeight:600,color:"#4a5568",fontSize:12}}>{h}</th>)}</tr></thead>
              <tbody>{opsTransactions.map((t,i)=>(
                <tr key={i} style={{borderTop:"1px solid #edf2f7"}}>
                  <td style={{padding:"10px 14px",color:"#718096"}}>{t.txn_date}</td>
                  <td style={{padding:"10px 14px",fontWeight:600}}>{t.client_name}</td>
                  <td style={{padding:"10px 14px",color:"#718096",fontSize:12}}>{t.segment}</td>
                  <td style={{padding:"10px 14px",fontWeight:700,color:"#3182ce"}}>{t.ticker}</td>
                  <td style={{padding:"10px 14px"}}><span style={{fontSize:11,padding:"2px 8px",borderRadius:10,fontWeight:700,backgroundColor:t.txn_type==="BUY"?"#c6f6d5":"#fed7d7",color:t.txn_type==="BUY"?"#276749":"#c53030"}}>{t.txn_type}</span></td>
                  <td style={{padding:"10px 14px"}}>{t.quantity}</td>
                  <td style={{padding:"10px 14px"}}>Rs.{t.price}</td>
                  <td style={{padding:"10px 14px",fontWeight:600}}>Rs.{Number(t.amount).toLocaleString()}</td>
                  <td style={{padding:"10px 14px",color:"#718096"}}>{t.relationship_manager}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
        {opsView==="metrics"&&sysMetrics&&(
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            <div style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)"}}>
              <div style={{fontWeight:700,fontSize:15,marginBottom:16,color:"#1a365d"}}>API Metrics</div>
              {[{l:"Total Requests",v:sysMetrics.api_metrics?.total_requests},{l:"Avg Latency (ms)",v:sysMetrics.api_metrics?.avg_latency_ms},{l:"Error Rate %",v:sysMetrics.api_metrics?.error_rate_pct},{l:"Total Clients",v:sysMetrics.data_summary?.total_clients},{l:"Open Violations",v:sysMetrics.data_summary?.open_violations},{l:"Open Anomalies",v:sysMetrics.data_summary?.open_anomalies}].map((m,i)=>(
                <div key={i} style={{display:"flex",justifyContent:"space-between",padding:"10px 0",borderBottom:"1px solid #f0f0f0",fontSize:13}}>
                  <span style={{color:"#4a5568"}}>{m.l}</span><span style={{fontWeight:700}}>{m.v}</span>
                </div>
              ))}
            </div>
            <div style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)"}}>
              <div style={{fontWeight:700,fontSize:15,marginBottom:16,color:"#1a365d"}}>AI Model Performance</div>
              {(sysMetrics.ai_metrics||[]).map((m:any,i:number)=>(
                <div key={i} style={{backgroundColor:"#f7fafc",borderRadius:8,padding:"12px 14px",marginBottom:8}}>
                  <div style={{fontWeight:600,fontSize:13,color:"#1a365d",marginBottom:4}}>{m.model}</div>
                  <div style={{display:"flex",gap:16,fontSize:12,color:"#718096"}}>
                    <span>Calls: <strong>{m.calls}</strong></span>
                    <span>Avg: <strong>{Number(m.avg_latency||0).toFixed(0)}ms</strong></span>
                    <span>Success: <strong style={{color:"#276749"}}>{Number(m.success_rate||0).toFixed(1)}%</strong></span>
                  </div>
                </div>
              ))}
              {(sysMetrics.ai_metrics||[]).length===0&&<div style={{color:"#718096",textAlign:"center",padding:20}}>No AI calls logged yet</div>}
            </div>
          </div>
        )}
        {opsView==="models"&&(
          <div style={{backgroundColor:"white",borderRadius:10,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",overflow:"hidden"}}>
            <div style={{padding:"16px 20px",borderBottom:"1px solid #e2e8f0",fontWeight:700,fontSize:15,color:"#1a365d"}}>Model Registry</div>
            <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
              <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Model","Version","Status","Total Calls","Last Called","Description"].map(h=><th key={h} style={{padding:"10px 14px",textAlign:"left",fontWeight:600,color:"#4a5568",fontSize:12}}>{h}</th>)}</tr></thead>
              <tbody>{modelRegistry.map((m:any,i:number)=>(
                <tr key={i} style={{borderTop:"1px solid #edf2f7"}}>
                  <td style={{padding:"10px 14px",fontWeight:700,color:"#3182ce"}}>{m.model_name}</td>
                  <td style={{padding:"10px 14px"}}>{m.version}</td>
                  <td style={{padding:"10px 14px"}}><span style={{fontSize:11,padding:"2px 8px",borderRadius:10,fontWeight:700,backgroundColor:m.status==="active"?"#c6f6d5":"#e2e8f0",color:m.status==="active"?"#276749":"#718096"}}>{m.status}</span></td>
                  <td style={{padding:"10px 14px"}}>{m.total_calls||0}</td>
                  <td style={{padding:"10px 14px",color:"#718096",fontSize:12}}>{m.last_called?new Date(m.last_called).toLocaleString():"Never"}</td>
                  <td style={{padding:"10px 14px",color:"#718096"}}>{m.description}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );

  // ADVISOR VIEW
  return (
    <div style={{display:"flex",flexDirection:"column",height:"100vh",fontFamily:"Inter,sans-serif",backgroundColor:"#edf2f7"}}>
      <Header/><AlertsPanel/>
      <div style={{display:"flex",flex:1,overflow:"hidden"}}>
        <div style={{width:240,backgroundColor:"#1a202c",color:"white",overflowY:"auto",flexShrink:0}}>
          <div style={{padding:"14px 16px",fontSize:11,fontWeight:700,color:"#a0aec0",letterSpacing:1,borderBottom:"1px solid #2d3748"}}>CLIENTS ({clients.length})</div>
          {clients.map(c=>(
            <div key={c.client_id} onClick={()=>selectClient(c)} style={{padding:"12px 16px",cursor:"pointer",borderBottom:"1px solid #2d3748",backgroundColor:selectedClient?.client_id===c.client_id?"#2d3748":"transparent",borderLeft:selectedClient?.client_id===c.client_id?"3px solid #3182ce":"3px solid transparent",transition:"all 0.15s"}}>
              <div style={{fontWeight:600,fontSize:13}}>{c.name}</div>
              <div style={{fontSize:11,color:"#a0aec0",marginTop:2}}>Rs.{(c.aum/100000).toFixed(1)}L · {c.segment}</div>
              <div style={{marginTop:4}}><span style={{fontSize:10,padding:"2px 8px",borderRadius:10,fontWeight:600,backgroundColor:c.risk_appetite==="Aggressive"?"#742a2a":c.risk_appetite==="Moderate"?"#744210":"#1c4532",color:c.risk_appetite==="Aggressive"?"#fc8181":c.risk_appetite==="Moderate"?"#f6ad55":"#68d391"}}>{c.risk_appetite}</span></div>
            </div>
          ))}
        </div>

        <div style={{flex:1,overflowY:"auto",padding:20,display:"flex",flexDirection:"column",gap:16}}>
          {!selectedClient?(
            <div>
              <div style={{backgroundColor:"white",borderRadius:10,padding:20,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",marginBottom:16}}>
                <div style={{fontWeight:700,fontSize:15,marginBottom:12,color:"#c53030"}}>Concentration Risk Alerts</div>
                {riskClients.map((r,i)=>(
                  <div key={i} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px solid #f0f0f0",fontSize:13}}>
                    <span><strong>{r.client_id}</strong> — {r.sector}</span>
                    <span style={{color:"#c53030",fontWeight:700}}>{r.total_weight}% allocation</span>
                  </div>
                ))}
              </div>
              <div style={{textAlign:"center",color:"#718096",marginTop:40,fontSize:14}}>Select a client to view their portfolio dashboard</div>
            </div>
          ):(
            <div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr 1fr",gap:12,marginBottom:16}}>
                {[{label:"Total Portfolio Value",value:`Rs.${totalValue.toLocaleString()}`,color:"#3182ce"},{label:"Unrealized P&L",value:`Rs.${totalPnL.toLocaleString()}`,color:totalPnL>=0?"#38a169":"#e53e3e"},{label:"Holdings",value:String(holdings.length),color:"#805ad5"},{label:"Risk Appetite",value:selectedClient.risk_appetite,color:selectedClient.risk_appetite==="Aggressive"?"#e53e3e":selectedClient.risk_appetite==="Moderate"?"#d69e2e":"#38a169"}].map((card,i)=>(
                  <div key={i} style={{backgroundColor:"white",borderRadius:10,padding:16,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",borderTop:`3px solid ${card.color}`}}>
                    <div style={{fontSize:11,color:"#718096",marginBottom:6}}>{card.label}</div>
                    <div style={{fontSize:18,fontWeight:700,color:card.color}}>{card.value}</div>
                  </div>
                ))}
              </div>
              <div style={{backgroundColor:"white",borderRadius:10,padding:16,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",marginBottom:16}}>
                <div style={{fontWeight:700,fontSize:14,marginBottom:12}}>Sector Allocation</div>
                <div style={{display:"flex",height:20,borderRadius:6,overflow:"hidden",marginBottom:12}}>
                  {Object.entries(sectorMap).map(([s,v])=><div key={s} title={`${s}: ${(v/totalValue*100).toFixed(1)}%`} style={{width:`${v/totalValue*100}%`,backgroundColor:SC[s]||"#a0aec0"}}/>)}
                </div>
                <div style={{display:"flex",flexWrap:"wrap",gap:10}}>
                  {Object.entries(sectorMap).map(([s,v])=>(
                    <div key={s} style={{display:"flex",alignItems:"center",gap:6,fontSize:12}}>
                      <div style={{width:10,height:10,borderRadius:2,backgroundColor:SC[s]||"#a0aec0"}}/><span>{s}: <strong>{(v/totalValue*100).toFixed(1)}%</strong></span>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{backgroundColor:"white",borderRadius:10,boxShadow:"0 1px 4px rgba(0,0,0,0.08)",overflow:"hidden"}}>
                <div style={{display:"flex",borderBottom:"1px solid #e2e8f0",overflowX:"auto"}}>
                  {(["holdings","risk","compliance","nba","scenarios"] as const).map(tab=>(
                    <button key={tab} onClick={()=>{setActiveTab(tab);if(tab==="nba"&&!nbaData)loadNBA();}} style={{padding:"12px 16px",border:"none",cursor:"pointer",fontWeight:600,fontSize:12,whiteSpace:"nowrap",backgroundColor:activeTab===tab?"#ebf8ff":"white",color:activeTab===tab?"#3182ce":"#718096",borderBottom:activeTab===tab?"2px solid #3182ce":"2px solid transparent"}}>
                      {tab==="holdings"?"Holdings":tab==="risk"?"Risk Flags":tab==="compliance"?"Compliance":tab==="nba"?"NBA / Revenue":"Scenarios"}
                    </button>
                  ))}
                </div>

                {activeTab==="holdings"&&(
                  <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
                    <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Ticker","Company","Sector","Qty","Price","Value","Weight","P&L"].map(h=><th key={h} style={{padding:"10px 14px",textAlign:"left",fontWeight:600,color:"#4a5568",fontSize:12}}>{h}</th>)}</tr></thead>
                    <tbody>{holdings.map((h,i)=>(
                      <tr key={i} style={{borderTop:"1px solid #edf2f7"}}>
                        <td style={{padding:"10px 14px",fontWeight:700,color:"#3182ce"}}>{h.ticker}</td>
                        <td style={{padding:"10px 14px"}}>{h.company_name}</td>
                        <td style={{padding:"10px 14px"}}><span style={{backgroundColor:(SC[h.sector]||"#a0aec0")+"22",color:SC[h.sector]||"#718096",padding:"2px 8px",borderRadius:10,fontSize:11,fontWeight:600}}>{h.sector}</span></td>
                        <td style={{padding:"10px 14px"}}>{h.quantity}</td>
                        <td style={{padding:"10px 14px"}}>Rs.{h.current_price}</td>
                        <td style={{padding:"10px 14px",fontWeight:600}}>Rs.{h.current_value.toLocaleString()}</td>
                        <td style={{padding:"10px 14px"}}>{h.weight_pct}%</td>
                        <td style={{padding:"10px 14px",fontWeight:700,color:h.unrealized_pnl>=0?"#38a169":"#e53e3e"}}>{h.unrealized_pnl>=0?"+":""}Rs.{h.unrealized_pnl.toLocaleString()}</td>
                      </tr>
                    ))}</tbody>
                  </table>
                )}

                {activeTab==="risk"&&(
                  <div style={{padding:16}}>
                    {riskClients.filter(r=>r.client_id===selectedClient.client_id).length===0
                      ?<div style={{color:"#38a169",fontWeight:600,padding:8}}>No concentration risk flags.</div>
                      :riskClients.filter(r=>r.client_id===selectedClient.client_id).map((r,i)=>(
                        <div key={i} style={{backgroundColor:"#fff5f5",border:"1px solid #fed7d7",borderRadius:8,padding:14,marginBottom:10}}>
                          <div style={{color:"#c53030",fontWeight:700,fontSize:14}}>High Concentration: {r.sector}</div>
                          <div style={{fontSize:13,marginTop:6,color:"#4a5568"}}>{r.total_weight}% in {r.sector} — exceeds 40% threshold.</div>
                        </div>
                      ))}
                  </div>
                )}

                {activeTab==="compliance"&&(
                  <div style={{padding:20}}>
                    <div style={{fontWeight:700,fontSize:15,marginBottom:4,color:"#1a365d"}}>Pre-Trade Compliance Check</div>
                    <div style={{fontSize:12,color:"#718096",marginBottom:20}}>Running for: <strong>{selectedClient.name}</strong> · {selectedClient.risk_appetite}</div>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12,marginBottom:12}}>
                      {[{label:"Ticker",key:"ticker",type:"text",ph:"e.g. AAPL"},{label:"Quantity",key:"quantity",type:"number",ph:"100"},{label:"Price (Rs.)",key:"price",type:"number",ph:"500"}].map(f=>(
                        <div key={f.key}>
                          <div style={{fontSize:11,color:"#718096",marginBottom:4,fontWeight:600}}>{f.label}</div>
                          <input type={f.type} placeholder={f.ph} value={(complianceForm as any)[f.key]} onChange={e=>setComplianceForm(p=>({...p,[f.key]:e.target.value}))} style={{width:"100%",padding:"9px 12px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:13,outline:"none",backgroundColor:"#f7fafc",boxSizing:"border-box"}}/>
                        </div>
                      ))}
                    </div>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12,marginBottom:16}}>
                      <div><div style={{fontSize:11,color:"#718096",marginBottom:4,fontWeight:600}}>Sector</div>
                        <select value={complianceForm.sector} onChange={e=>setComplianceForm(p=>({...p,sector:e.target.value}))} style={{width:"100%",padding:"9px 12px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:13,backgroundColor:"#f7fafc"}}>
                          {["Technology","Financials","Energy","Commodities","Bonds","Index","Consumer","Automobile","Insurance","Consumer Tech"].map(s=><option key={s}>{s}</option>)}
                        </select>
                      </div>
                      <div><div style={{fontSize:11,color:"#718096",marginBottom:4,fontWeight:600}}>Action</div>
                        <select value={complianceForm.action} onChange={e=>setComplianceForm(p=>({...p,action:e.target.value}))} style={{width:"100%",padding:"9px 12px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:13,backgroundColor:"#f7fafc"}}>
                          <option>BUY</option><option>SELL</option>
                        </select>
                      </div>
                    </div>
                    <button onClick={runComplianceCheck} disabled={complianceLoading||!complianceForm.ticker||!complianceForm.price} style={{padding:"10px 28px",backgroundColor:complianceLoading||!complianceForm.ticker?"#a0aec0":"#1a365d",color:"white",border:"none",borderRadius:6,fontWeight:700,fontSize:14,cursor:"pointer",marginBottom:24}}>
                      {complianceLoading?"Checking...":"Run Pre-Trade Compliance Check"}
                    </button>
                    {complianceResult&&(
                      <div>
                        <div style={{padding:"14px 18px",borderRadius:8,marginBottom:16,fontWeight:700,fontSize:15,backgroundColor:complianceResult.overall_result==="APPROVED"?"#f0fff4":complianceResult.overall_result==="WARNING"?"#fffaf0":"#fff5f5",border:`1px solid ${complianceResult.overall_result==="APPROVED"?"#68d391":complianceResult.overall_result==="WARNING"?"#f6ad55":"#fc8181"}`,color:complianceResult.overall_result==="APPROVED"?"#276749":complianceResult.overall_result==="WARNING"?"#b7791f":"#c53030"}}>
                          Trade {complianceResult.overall_result} · <span style={{fontSize:12,fontWeight:400}}>{complianceResult.summary.passed} passed · {complianceResult.summary.violations} violations</span>
                        </div>
                        {complianceResult.checks.map((c:any,i:number)=>(
                          <div key={i} style={{padding:"10px 14px",marginBottom:8,borderRadius:6,fontSize:13,backgroundColor:c.result==="PASS"?"#f0fff4":c.result==="WARN"?"#fffaf0":"#fff5f5",border:`1px solid ${c.result==="PASS"?"#c6f6d5":c.result==="WARN"?"#feebc8":"#fed7d7"}`}}>
                            <strong>{c.result}</strong> <strong style={{color:"#1a202c"}}>{c.rule}</strong> <span style={{fontSize:10,padding:"1px 8px",borderRadius:10,fontWeight:700,backgroundColor:c.severity==="CRITICAL"?"#fed7d7":c.severity==="HIGH"?"#feebc8":"#e2e8f0",color:c.severity==="CRITICAL"?"#c53030":c.severity==="HIGH"?"#b7791f":"#718096"}}>{c.severity}</span>
                            <div style={{color:"#4a5568",fontSize:12,marginTop:4}}>{c.message}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab==="nba"&&(
                  <div style={{padding:20}}>
                    <div style={{fontWeight:700,fontSize:15,marginBottom:4,color:"#1a365d"}}>Next-Best-Action & Revenue Enablement</div>
                    <div style={{fontSize:12,color:"#718096",marginBottom:16}}>AI-powered recommendations for <strong>{selectedClient.name}</strong></div>
                    {!nbaData&&<button onClick={loadNBA} disabled={nbaLoading} style={{padding:"10px 24px",backgroundColor:nbaLoading?"#a0aec0":"#1a365d",color:"white",border:"none",borderRadius:6,fontWeight:700,cursor:"pointer",marginBottom:20}}>{nbaLoading?"Generating...":"Generate NBA Recommendations"}</button>}
                    {lifeEvents.length>0&&(
                      <div style={{marginBottom:20}}>
                        <div style={{fontWeight:700,fontSize:14,marginBottom:10,color:"#1a365d"}}>Life Events Detected</div>
                        {lifeEvents.map((e,i)=>(
                          <div key={i} style={{backgroundColor:e.urgency==="HIGH"?"#fff5f5":"#fffaf0",border:`1px solid ${e.urgency==="HIGH"?"#fed7d7":"#feebc8"}`,borderRadius:8,padding:14,marginBottom:10}}>
                            <div style={{display:"flex",justifyContent:"space-between"}}>
                              <span style={{fontWeight:700,fontSize:13,color:e.urgency==="HIGH"?"#c53030":"#b7791f"}}>{e.event_type.replace(/_/g," ")}</span>
                              <span style={{fontSize:11,padding:"2px 8px",borderRadius:10,backgroundColor:e.urgency==="HIGH"?"#fed7d7":"#feebc8",color:e.urgency==="HIGH"?"#c53030":"#b7791f",fontWeight:700}}>{e.urgency}</span>
                            </div>
                            <div style={{fontSize:13,color:"#4a5568",marginTop:6}}>{e.description}</div>
                            <div style={{fontSize:12,color:"#718096",marginTop:6,fontStyle:"italic"}}>{e.action}</div>
                          </div>
                        ))}
                      </div>
                    )}
                    {nbaData&&nbaData.recommendations&&(
                      <div>
                        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
                          <div style={{fontWeight:700,fontSize:14,color:"#1a365d"}}>{nbaData.total_recommendations} Recommendations</div>
                          <div style={{fontSize:13,color:"#276749",fontWeight:600}}>Total Expected Revenue: Rs.{nbaData.total_expected_revenue?.toLocaleString()}</div>
                        </div>
                        {nbaData.recommendations.map((r:any,i:number)=>(
                          <div key={i} style={{backgroundColor:"white",border:"1px solid #e2e8f0",borderRadius:8,padding:16,marginBottom:12,boxShadow:"0 1px 3px rgba(0,0,0,0.06)"}}>
                            <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                              <div>
                                <span style={{fontSize:11,padding:"2px 8px",borderRadius:10,fontWeight:700,marginRight:8,backgroundColor:r.type==="CROSS_SELL"?"#ebf8ff":r.type==="UPSELL"?"#faf5ff":r.type==="REBALANCE"?"#fffaf0":"#f0fff4",color:r.type==="CROSS_SELL"?"#3182ce":r.type==="UPSELL"?"#805ad5":r.type==="REBALANCE"?"#b7791f":"#276749"}}>{(r.type||"").replace(/_/g," ")}</span>
                                <span style={{fontWeight:700,fontSize:14,color:"#1a202c"}}>{r.product}</span>
                              </div>
                              <div style={{textAlign:"right"}}>
                                <div style={{fontSize:12,color:"#276749",fontWeight:700}}>Rs.{r.expected_revenue?.toLocaleString()} revenue</div>
                                <div style={{fontSize:11,color:"#718096"}}>Score: {r.confidence}</div>
                              </div>
                            </div>
                            <div style={{fontSize:13,color:"#4a5568",marginBottom:8}}>{r.rationale}</div>
                            <div style={{display:"flex",gap:8}}>
                              <span style={{fontSize:10,padding:"2px 8px",borderRadius:10,backgroundColor:r.urgency==="this_week"?"#feebc8":"#ebf8ff",color:r.urgency==="this_week"?"#b7791f":"#2b6cb0",fontWeight:600}}>Urgency: {(r.urgency||"").replace(/_/g," ")}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab==="scenarios"&&(
                  <div style={{padding:20}}>
                    <div style={{fontWeight:700,fontSize:15,marginBottom:4,color:"#1a365d"}}>Scenario Simulation</div>
                    <div style={{fontSize:12,color:"#718096",marginBottom:20}}>Model portfolio impact under different market conditions for <strong>{selectedClient.name}</strong></div>
                    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12,marginBottom:16}}>
                      <div>
                        <div style={{fontSize:11,color:"#718096",marginBottom:4,fontWeight:600}}>Scenario Type</div>
                        <select value={scenarioType} onChange={e=>setScenarioType(e.target.value)} style={{width:"100%",padding:"9px 12px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:13,backgroundColor:"#f7fafc"}}>
                          <option value="MARKET_CRASH">Market Crash</option>
                          <option value="RATE_HIKE">Rate Hike</option>
                          <option value="SECTOR_ROTATION">Sector Rotation</option>
                        </select>
                      </div>
                      <div>
                        <div style={{fontSize:11,color:"#718096",marginBottom:4,fontWeight:600}}>Magnitude (%)</div>
                        <input type="number" value={scenarioMag} onChange={e=>setScenarioMag(Number(e.target.value))} min={1} max={50} style={{width:"100%",padding:"9px 12px",borderRadius:6,border:"1px solid #e2e8f0",fontSize:13,outline:"none",backgroundColor:"#f7fafc",boxSizing:"border-box"}}/>
                      </div>
                      <div style={{display:"flex",alignItems:"flex-end"}}>
                        <button onClick={runScenario} disabled={scenarioLoading} style={{width:"100%",padding:"10px",backgroundColor:scenarioLoading?"#a0aec0":"#1a365d",color:"white",border:"none",borderRadius:6,fontWeight:700,cursor:"pointer",fontSize:13}}>{scenarioLoading?"Running...":"Run Simulation"}</button>
                      </div>
                    </div>
                    {scenarioResult&&(
                      <div>
                        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12,marginBottom:16}}>
                          {[{l:"Current Value",v:`Rs.${scenarioResult.current_portfolio_value?.toLocaleString()}`,c:"#3182ce"},{l:"Scenario Value",v:`Rs.${scenarioResult.scenario_portfolio_value?.toLocaleString()}`,c:scenarioResult.total_impact_rs>=0?"#38a169":"#e53e3e"},{l:"Total Impact",v:`Rs.${scenarioResult.total_impact_rs?.toLocaleString()} (${scenarioResult.total_impact_pct}%)`,c:scenarioResult.total_impact_rs>=0?"#38a169":"#e53e3e"}].map((s,i)=>(
                            <div key={i} style={{backgroundColor:"white",borderRadius:8,padding:14,border:`1px solid #e2e8f0`,borderTop:`3px solid ${s.c}`}}>
                              <div style={{fontSize:11,color:"#718096",marginBottom:4}}>{s.l}</div>
                              <div style={{fontWeight:700,fontSize:14,color:s.c}}>{s.v}</div>
                            </div>
                          ))}
                        </div>
                        <div style={{backgroundColor:"#ebf8ff",border:"1px solid #90cdf4",borderRadius:8,padding:14,marginBottom:16,fontSize:13,color:"#2b6cb0"}}><strong>Recommendation:</strong> {scenarioResult.recommendation}</div>
                        <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                          <thead><tr style={{backgroundColor:"#f7fafc"}}>{["Ticker","Sector","Current","Scenario","Change %","Impact Rs."].map(h=><th key={h} style={{padding:"8px 12px",textAlign:"left",fontWeight:600,color:"#4a5568"}}>{h}</th>)}</tr></thead>
                          <tbody>{(scenarioResult.holdings_impact||[]).sort((a:any,b:any)=>a.change_pct-b.change_pct).map((h:any,i:number)=>(
                            <tr key={i} style={{borderTop:"1px solid #edf2f7",backgroundColor:h.change_pct<-10?"#fff5f5":h.change_pct>5?"#f0fff4":"white"}}>
                              <td style={{padding:"8px 12px",fontWeight:700,color:"#3182ce"}}>{h.ticker}</td>
                              <td style={{padding:"8px 12px",color:"#718096"}}>{h.sector}</td>
                              <td style={{padding:"8px 12px"}}>Rs.{Number(h.current_value).toLocaleString()}</td>
                              <td style={{padding:"8px 12px"}}>Rs.{Number(h.new_value).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g,",")}</td>
                              <td style={{padding:"8px 12px",fontWeight:700,color:h.change_pct>=0?"#38a169":"#e53e3e"}}>{h.change_pct>=0?"+":""}{h.change_pct}%</td>
                              <td style={{padding:"8px 12px",fontWeight:700,color:h.impact_rs>=0?"#38a169":"#e53e3e"}}>{h.impact_rs>=0?"+":""}Rs.{Number(h.impact_rs).toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g,",")}</td>
                            </tr>
                          ))}</tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div style={{width:380,display:"flex",flexDirection:"column",backgroundColor:"white",borderLeft:"1px solid #e2e8f0"}}>
          <div style={{padding:"12px 16px",borderBottom:"1px solid #e2e8f0",fontWeight:700,fontSize:13,color:"#4a5568",backgroundColor:"#f7fafc"}}>
            AI Assistant {selectedClient&&<span style={{color:"#3182ce"}}>· {selectedClient.name}</span>}
          </div>
          <div style={{flex:1,overflowY:"auto",padding:16,display:"flex",flexDirection:"column",gap:12}}>
            {messages.map((msg,i)=>(
              <div key={i} style={{display:"flex",justifyContent:msg.role==="user"?"flex-end":"flex-start",gap:8,alignItems:"flex-end"}}>
                {msg.role==="assistant"&&<div style={{width:28,height:28,borderRadius:"50%",backgroundColor:"#1a365d",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:"bold",flexShrink:0}}>AI</div>}
                <div style={{maxWidth:"80%",padding:"10px 14px",fontSize:13,lineHeight:1.6,borderRadius:msg.role==="user"?"16px 16px 4px 16px":"16px 16px 16px 4px",backgroundColor:msg.role==="user"?"#3182ce":"#f7fafc",color:msg.role==="user"?"white":"#1a202c",boxShadow:"0 1px 3px rgba(0,0,0,0.08)"}}>{msg.content}</div>
              </div>
            ))}
            {loading&&<div style={{display:"flex",gap:8,alignItems:"flex-end"}}><div style={{width:28,height:28,borderRadius:"50%",backgroundColor:"#1a365d",color:"white",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:"bold"}}>AI</div><div style={{backgroundColor:"#f7fafc",padding:"10px 14px",borderRadius:"16px 16px 16px 4px",display:"flex",gap:4}}>{[0,1,2].map(i=><span key={i} style={{width:7,height:7,borderRadius:"50%",backgroundColor:"#3182ce",display:"inline-block",animation:`bounce 1.2s ${i*0.2}s infinite`}}/>)}</div></div>}
            <div ref={bottomRef}/>
          </div>
          <div style={{padding:12,borderTop:"1px solid #e2e8f0",display:"flex",gap:8}}>
            <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&sendMessage()} placeholder={selectedClient?`Ask about ${selectedClient.name}...`:"Ask anything..."} style={{flex:1,padding:"10px 14px",borderRadius:20,border:"1px solid #e2e8f0",fontSize:13,outline:"none",backgroundColor:"#f7fafc"}}/>
            <button onClick={startVoice} title="Voice input" style={{padding:"10px 12px",borderRadius:20,backgroundColor:isListening?"#e53e3e":"#e2e8f0",color:isListening?"white":"#4a5568",border:"none",cursor:"pointer",fontSize:13}}>{isListening?"●":"🎤"}</button>
            <button onClick={sendMessage} disabled={loading||!input.trim()} style={{padding:"10px 18px",borderRadius:20,backgroundColor:loading||!input.trim()?"#a0aec0":"#3182ce",color:"white",border:"none",fontWeight:700,cursor:"pointer",fontSize:13}}>{loading?"...":"->"}</button>
          </div>
        </div>
      </div>
      <style>{`@keyframes bounce{0%,80%,100%{transform:translateY(0);opacity:.5}40%{transform:translateY(-5px);opacity:1}}*{box-sizing:border-box;margin:0;padding:0}::-webkit-scrollbar{width:4px}::-webkit-scrollbar-thumb{background:#cbd5e0;border-radius:4px}`}</style>
    </div>
  );
}