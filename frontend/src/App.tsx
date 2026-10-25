import {useEffect,useState} from 'react';
import {ShieldCheck,FileCheck2,UploadCloud,Activity,RefreshCw,LogIn,Fingerprint,AlertTriangle,Search,LockKeyhole,ClipboardCheck,Download,Link as LinkIcon,ScrollText,FileBadge} from 'lucide-react';
import {api,login,type Evidence} from './api';

type Verify={
 evidence_id:string;
 recorded_sha256:string;
 observed_sha256:string|null;
 integrity_status:string;
 blockchain_status:string;
 certificate_status:string;
 statement:string;
};
type Certificate={
 payload:{
  certificate_id:string;
  evidence_id:string;
  sha256:string;
  issuer_id:string;
  issued_at:string;
  status:string;
  blockchain:{status:string;transaction_hash:string|null;block_number:number|null;digest:string};
  statement:string;
 };
 signature:string;
 signature_algorithm:string;
 signing_key_id:string;
 public_key_pem:string;
 signature_valid:boolean;
 key_trust_note:string;
 revocation:{status:string;revoked_at:string|null;reason:string|null};
};
type AuditEvent={id:string;actor_id:string|null;action:string;resource_type:string;resource_id:string|null;detail:string;created_at:string};
type PublicVerification={certificate_id:string;status:string;signature_valid:boolean;stored_document_integrity:string;blockchain_status:string;submitted_document_match:boolean|null;statement:string};
const API_BASE=import.meta.env.VITE_API_URL??'http://127.0.0.1:8000';

export default function App(){
 const[email,setEmail]=useState('analyst@example.com'),[password,setPassword]=useState(''),[token,setToken]=useState(localStorage.getItem('ai_token')??'');
 const[items,setItems]=useState<Evidence[]>([]),[selected,setSelected]=useState<Evidence|null>(null),[result,setResult]=useState<Verify|null>(null);
 const[caseRef,setCaseRef]=useState('DEMO-CASE-001'),[file,setFile]=useState<File|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
 const[search,setSearch]=useState(''),[certificate,setCertificate]=useState<Certificate|null>(null),[auditEvents,setAuditEvents]=useState<AuditEvent[]>([]),[auditLoaded,setAuditLoaded]=useState(false);
 const[activeNav,setActiveNav]=useState('overview');
 const[publicCertId]=useState(()=>new URLSearchParams(window.location.search).get('certificate')??'');
 const[publicFile,setPublicFile]=useState<File|null>(null),[publicResult,setPublicResult]=useState<PublicVerification|null>(null),[publicBusy,setPublicBusy]=useState(false),[publicError,setPublicError]=useState('');

 async function load(){
  if(!token)return;
  try{setItems(await api<Evidence[]>('/api/v1/evidence',token));setError('')}
  catch(e){setError((e as Error).message)}
 }
 useEffect(()=>{void load()},[token]);
 async function signIn(e:React.FormEvent){
  e.preventDefault();setError('');
  try{const t=await login(email,password);setToken(t.access_token);localStorage.setItem('ai_token',t.access_token)}
  catch(e){setError((e as Error).message)}
 }
 function signOut(){localStorage.removeItem('ai_token');setToken('');setItems([]);setCertificate(null);setResult(null)}
 async function upload(e:React.FormEvent){
  e.preventDefault();if(!file)return;setBusy(true);setError('');setNotice('');
  try{
   const body=new FormData();body.append('case_reference',caseRef);body.append('file',file);
   const item=await api<Evidence>('/api/v1/evidence',token,{method:'POST',body});
   setNotice('Evidence registered. SHA-256: '+item.sha256);setFile(null);await load();setSelected(item)
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function verify(item:Evidence){
  setBusy(true);setError('');setNotice('');
  try{setSelected(item);setResult(await api<Verify>(`/api/v1/evidence/${item.id}/verify`,token,{method:'POST'}));setActiveNav('verification')}
  catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function anchor(item:Evidence){
  setBusy(true);setError('');setNotice('');
  try{
   const response=await api<{status:string;tx_hash:string;block_number:number}>(`/api/v1/evidence/${item.id}/anchor`,token,{method:'POST'});
   setNotice(`Blockchain anchor confirmed in block ${response.block_number}. Transaction: ${response.tx_hash}`);
   await verify(item);await load()
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function issueCertificate(item:Evidence){
  setBusy(true);setError('');setNotice('');
  try{
   const created=await api<Certificate>(`/api/v1/evidence/${item.id}/certificate`,token,{method:'POST'});
   setCertificate(created);setSelected(item);setNotice('Integrity certificate issued and signature checked.');setActiveNav('certificate')
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function viewCertificate(item:Evidence){
  setBusy(true);setError('');
  try{
   const saved=await api<Certificate>(`/api/v1/evidence/${item.id}/certificate`,token);
   setCertificate(saved);setSelected(item);setActiveNav('certificate')
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function revokeCertificate(){
  if(!certificate)return;
  if(!window.confirm('Revoke this certificate? Future public verification will report REVOKED.'))return;
  const reason=window.prompt('Enter a reason for revocation (required):');
  if(!reason?.trim())return;
  setBusy(true);setError('');
  try{
   setCertificate(await api<Certificate>(`/api/v1/certificates/${certificate.payload.certificate_id}/revoke`,token,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason})}));
   setNotice('Certificate revocation recorded.');setError('')
  }catch(e){setError((e as Error).message)}finally{setBusy(false)}
 }
 async function loadAudit(){
  setError('');
  try{setAuditEvents(await api<AuditEvent[]>('/api/v1/audit?limit=100',token));setAuditLoaded(true)}
  catch(e){setError((e as Error).message);setAuditLoaded(false)}
 }
 function navigate(section:string,id:string){
  setActiveNav(section);
  if(section==='audit')void loadAudit();
  document.getElementById(id)?.scrollIntoView({behavior:'smooth',block:'start'});
 }
 async function copyVerificationLink(){
  if(!certificate)return;
  const link=`${window.location.origin}/?certificate=${encodeURIComponent(certificate.payload.certificate_id)}`;
  try{await navigator.clipboard.writeText(link);setNotice('Public verification link copied.')}
  catch{setError('Clipboard access is unavailable. Copy this link manually: '+link)}
 }
 function downloadCertificate(){
  if(!certificate)return;
  const blob=new Blob([JSON.stringify(certificate,null,2)],{type:'application/json'});
  const url=URL.createObjectURL(blob);const a=document.createElement('a');
  a.href=url;a.download=`ascentintegrity-${certificate.payload.certificate_id}.json`;a.click();URL.revokeObjectURL(url)
 }
 async function verifyPublic(e?:React.FormEvent){
  e?.preventDefault();if(!publicCertId)return;setPublicBusy(true);setPublicError('');
  try{
   const body=new FormData();if(publicFile)body.append('file',publicFile);
   const response=await fetch(`${API_BASE}/api/v1/public/certificates/${encodeURIComponent(publicCertId)}/verify`,{
    method:'POST',...(publicFile?{body}:{})
   });
   const data=await response.json().catch(()=>({detail:`HTTP ${response.status}`}));
   if(!response.ok)throw new Error(data.detail??'Verification request failed');
   setPublicResult(data as PublicVerification)
  }catch(e){setPublicError((e as Error).message)}finally{setPublicBusy(false)}
 }
 useEffect(()=>{if(publicCertId)void verifyPublic()},[publicCertId]);

 if(publicCertId)return <main className="login-wrap"><section className="login-card public-card">
  <div className="brand-mark"><ShieldCheck size={30}/></div><p className="eyebrow">ASCENTINTEGRITY / PUBLIC CHECK</p><h1>Certificate <span>verification</span></h1>
  <p className="muted">Certificate ID: <code>{publicCertId}</code></p>
  <form onSubmit={verifyPublic} className="stack">
   <label>Optional: upload the document to compare its SHA-256 hash<input type="file" onChange={e=>setPublicFile(e.target.files?.[0]??null)}/></label>
   <button className="primary" disabled={publicBusy}>{publicBusy?'Verifying…':'Verify certificate'}</button>
  </form>
  {publicError&&<p className="error" role="alert">{publicError}</p>}
  {publicResult&&<section className="public-result" aria-live="polite"><h2 className={publicResult.status==='VERIFIED'?'good':'bad'}>{publicResult.status}</h2><p>{publicResult.statement}</p><dl><dt>Certificate signature</dt><dd>{publicResult.signature_valid?'Valid against included public key':'Invalid'}</dd><dt>Stored document</dt><dd>{publicResult.stored_document_integrity}</dd><dt>Blockchain</dt><dd>{publicResult.blockchain_status}</dd><dt>Uploaded document match</dt><dd>{publicResult.submitted_document_match===null?'Not checked':publicResult.submitted_document_match?'Match':'Mismatch'}</dd></dl></section>}
  <p className="hint">A valid signature must be tied to a trusted issuer key. Integrity verification does not prove that document contents are true or legally valid.</p><a href="/">Open AscentIntegrity</a>
 </section></main>;

 if(!token)return <main className="login-wrap"><section className="login-card"><div className="brand-mark"><ShieldCheck size={30}/></div><p className="eyebrow">EVIDENCE INTEGRITY PLATFORM</p><h1>Ascent<span>Integrity</span></h1><p className="muted">Verify evidence bytes. Preserve a defensible audit trail.</p><form onSubmit={signIn} className="stack"><label>Email<input type="email" value={email} onChange={e=>setEmail(e.target.value)} required autoComplete="username"/></label><label>Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} required autoComplete="current-password"/></label><button className="primary"><LogIn size={16}/>Sign in</button></form><p className="hint">For local development, create an account using POST /api/v1/auth/register in the API docs. Public certificate verification does not require login.</p>{error&&<p className="error" role="alert">{error}</p>}</section></main>;

 const filteredItems=items.filter(item=>[item.filename,item.case_reference,item.sha256,item.id].some(value=>value.toLowerCase().includes(search.trim().toLowerCase())));
 const verificationLink=certificate?`${window.location.origin}/?certificate=${encodeURIComponent(certificate.payload.certificate_id)}`:''

 return <div className="app-shell">
  <aside className="sidebar">
   <div className="brand"><div className="brand-mark"><ShieldCheck/></div><div><b>AscentIntegrity</b><small>Certificates of Truth</small></div></div>
   <div className="nav-label">WORKSPACE</div>
   <button type="button" className={`nav-item ${activeNav==='overview'?'active':''}`} onClick={()=>navigate('overview','overview')}><Activity size={17}/>Overview</button>
   <button type="button" className={`nav-item ${activeNav==='register'?'active':''}`} onClick={()=>navigate('register','register')}><FileCheck2 size={17}/>Evidence register</button>
   <button type="button" className={`nav-item ${activeNav==='verification'?'active':''}`} onClick={()=>navigate('verification','verification')}><Fingerprint size={17}/>Integrity verification</button>
   <button type="button" className={`nav-item ${activeNav==='audit'?'active':''}`} onClick={()=>navigate('audit','audit')}><ScrollText size={17}/>Audit events</button>
   <button type="button" className={`nav-item ${activeNav==='certificate'?'active':''}`} onClick={()=>navigate('certificate','certificate')}><FileBadge size={17}/>Certificate</button>
   <div className="sidebar-bottom">Authenticated session<button className="ghost" onClick={signOut}>Sign out</button></div>
  </aside>
  <main className="main">
   <header className="topbar" id="overview"><div><p className="eyebrow">SECURE WORKSPACE / OVERVIEW</p><h2>Evidence integrity console</h2></div><button className="secondary" onClick={()=>void load()} disabled={busy}><RefreshCw size={15}/>Refresh</button></header>
   <div className="notice"><ShieldCheck size={18}/><div><b>Integrity is not factual truth</b><p>Hash verification checks whether stored bytes match a recorded digest. It does not prove document contents are true or legally admissible.</p></div></div>
   {error&&<div className="alert" role="alert"><AlertTriangle size={17}/>{error}</div>}{notice&&<div className="success" role="status">{notice}</div>}
   <section className="stats"><div className="stat"><span>Total evidence</span><b>{items.length}</b><small>Loaded from the API</small></div><div className="stat"><span>Stored records</span><b>{items.filter(x=>x.status==='stored').length}</b><small>Run verification to check integrity</small></div><div className="stat"><span>Selected record</span><b>{selected?'Selected':'None'}</b><small>{selected?selected.filename:'Choose a record below'}</small></div></section>
   <div className="content-grid">
    <section className="panel" id="upload-panel"><div className="panel-head"><div><h3>Register evidence</h3><p>Upload a file to compute SHA-256 and store original bytes privately.</p></div><UploadCloud/></div><form onSubmit={upload} className="stack"><label>Case reference<input value={caseRef} onChange={e=>setCaseRef(e.target.value)} maxLength={100} required/></label><label>Evidence file<input type="file" onChange={e=>setFile(e.target.files?.[0]??null)} required/></label><button className="primary" disabled={busy||!file}>{busy?'Processing…':'Register evidence'}</button></form></section>
    <section className="panel" id="verification"><div className="panel-head"><div><h3>Verification result</h3><p>{selected?.filename??'Select evidence from the register.'}</p></div><Fingerprint/></div>{result?<div className="stack"><b className={result.integrity_status==='VERIFIED'?'good':'bad'}>{result.integrity_status}</b><small>Recorded: <code>{result.recorded_sha256}</code></small><small>Observed: <code>{result.observed_sha256??'Object missing'}</code></small><small>Blockchain: {result.blockchain_status}</small><small>Certificate policy: {result.certificate_status}</small><p className="hint">{result.statement}</p></div>:<div className="empty"><Search/><b>No verification selected</b><span>Choose a record below and run verification.</span></div>}</section>
   </div>
   <section className="panel register" id="register"><div className="panel-head"><div><h3>Evidence register</h3><p>Records loaded from PostgreSQL through the FastAPI API.</p></div><Search/></div><label className="search-label">Search evidence<input type="search" value={search} onChange={e=>setSearch(e.target.value)} placeholder="Filename, case reference, digest or ID"/></label>{filteredItems.length===0?<div className="empty"><FileCheck2/><b>{items.length?'No matching evidence':'No evidence registered yet'}</b><span>{items.length?'Try another search.':'Upload a synthetic test file to begin.'}</span></div>:<div className="table-wrap"><table><thead><tr><th>Evidence / case</th><th>SHA-256</th><th>Size</th><th>Created</th><th>Actions</th></tr></thead><tbody>{filteredItems.map(item=><tr key={item.id}><td><b>{item.filename}</b><small>{item.case_reference}</small></td><td><code>{item.sha256.slice(0,18)}…</code></td><td>{(item.byte_size/1024).toFixed(1)} KB</td><td>{new Date(item.created_at).toLocaleString()}</td><td className="actions"><button className="small-button" disabled={busy} onClick={()=>void verify(item)}>Verify</button><button className="small-button" disabled={busy} onClick={()=>void anchor(item)}>Anchor</button><button className="small-button" disabled={busy} onClick={()=>void issueCertificate(item)}>Issue certificate</button><button className="small-button" disabled={busy} onClick={()=>void viewCertificate(item)}>View</button></td></tr>)}</tbody></table></div>}</section>
   <section className="panel register" id="certificate"><div className="panel-head"><div><h3>Integrity certificate</h3><p>Persisted certificate with an Ed25519 signature and public verification link.</p></div><FileBadge/></div>{certificate?<div className="stack"><div><b className={certificate.signature_valid?'good':'bad'}>{certificate.signature_valid?'Signature valid against included public key':'Signature invalid'}</b><p className="hint">Key ID: {certificate.signing_key_id}. The issuer key must be trusted through a separate channel.</p></div><dl><dt>Certificate ID</dt><dd><code>{certificate.payload.certificate_id}</code></dd><dt>Document SHA-256</dt><dd><code>{certificate.payload.sha256}</code></dd><dt>Issued at</dt><dd>{new Date(certificate.payload.issued_at).toLocaleString()}</dd><dt>Blockchain transaction</dt><dd><code>{certificate.payload.blockchain.transaction_hash??'Not available'}</code></dd><dt>Current status</dt><dd>{certificate.revocation.status}</dd></dl><div className="action-row"><button className="secondary" onClick={()=>void copyVerificationLink()}><ClipboardCheck size={15}/>Copy verification link</button><button className="secondary" onClick={downloadCertificate}><Download size={15}/>Download signed JSON</button><button className="secondary" onClick={()=>void revokeCertificate()} disabled={busy||certificate.revocation.status==='REVOKED'}>Revoke certificate</button></div><label>Public verification URL<input readOnly value={verificationLink}/></label><p className="hint">{certificate.payload.statement}</p><details><summary>Signature and public key</summary><p><code>{certificate.signature}</code></p><textarea readOnly value={certificate.public_key_pem} rows={5}/></details></div>:<div className="empty"><FileBadge/><b>No certificate selected</b><span>Select an evidence record and issue or view its certificate.</span></div>}</section>
   <section className="panel register" id="audit"><div className="panel-head"><div><h3>Audit events</h3><p>Real events returned by the API. Access depends on your role.</p></div><button className="secondary" onClick={()=>void loadAudit()}><RefreshCw size={15}/>Load / refresh</button></div>{!auditLoaded?<div className="empty"><ScrollText/><b>Audit events not loaded</b><span>Load audit events to inspect available records.</span></div>:auditEvents.length===0?<div className="empty"><b>No audit events returned</b></div>:<div className="table-wrap"><table><thead><tr><th>Time</th><th>Action</th><th>Resource</th><th>Actor</th><th>Details</th></tr></thead><tbody>{auditEvents.map(event=><tr key={event.id}><td>{new Date(event.created_at).toLocaleString()}</td><td>{event.action}</td><td>{event.resource_type} / {event.resource_id??'—'}</td><td>{event.actor_id??'Public verifier'}</td><td><code>{event.detail}</code></td></tr>)}</tbody></table></div>}</section>
   <footer>ASCENTINTEGRITY · INTEGRITY IS NOT FACTUAL TRUTH · VERIFY REAL RESULTS ONLY</footer>
  </main>
 </div>
}
