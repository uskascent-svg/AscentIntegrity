import hashlib, json, uuid
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.config import settings
from app.db import get_db
from app.models import User, UserRole, Evidence, EvidenceVersion, AuditEvent, BlockchainAnchor
from app.security import hash_password, verify_password, create_access_token, get_current_user
from app.blockchain import configured as blockchain_configured, anchor_digest, verify_digest
from pydantic import BaseModel, EmailStr
app=FastAPI(title="AscentIntegrity API",version="0.1.0",description="Evidence integrity verification, not factual-truth certification.")
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.cors_origins.split(",")],allow_credentials=True,allow_methods=["GET","POST","OPTIONS"],allow_headers=["Authorization","Content-Type"])
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
def record(db,actor,action,kind,rid,detail=None):
    db.add(AuditEvent(actor_id=actor,action=action,resource_type=kind,resource_id=rid,detail=json.dumps(detail or {},sort_keys=True)))
@app.get("/health")
def health(): return {"status":"ok","service":"ascentintegrity-api"}
@app.post("/api/v1/auth/register",status_code=201)
def register(payload:RegisterIn,db:Session=Depends(get_db)):
    if settings.app_env!="development" or not settings.allow_dev_registration: raise HTTPException(403,"Development registration disabled")
    if db.scalar(select(User).where(User.email==payload.email.lower())): raise HTTPException(409,"Email already registered")
    try: u=User(email=payload.email.lower(),password_hash=hash_password(payload.password),role=UserRole.analyst)
    except ValueError as e: raise HTTPException(422,str(e))
    db.add(u);db.flush();record(db,u.id,"user.registered","user",u.id);db.commit()
    return {"id":u.id,"email":u.email,"role":u.role.value}
@app.post("/api/v1/auth/token")
def token(form:OAuth2PasswordRequestForm=Depends(),db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==form.username.lower()))
    if not u or not verify_password(form.password,u.password_hash) or not u.is_active: raise HTTPException(401,"Incorrect email or password")
    return {"access_token":create_access_token(u.id),"token_type":"bearer"}
@app.get("/api/v1/auth/me")
def me(user:User=Depends(get_current_user)): return {"id":user.id,"email":user.email,"role":user.role.value}
@app.post("/api/v1/evidence",status_code=201)
async def upload(case_reference:str=Form(...),file:UploadFile=File(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    case_reference=case_reference.strip()
    if not case_reference or len(case_reference)>100: raise HTTPException(422,"case_reference must be 1-100 characters")
    data=await file.read(settings.max_upload_bytes+1)
    if not data: raise HTTPException(422,"Empty files are not accepted")
    if len(data)>settings.max_upload_bytes: raise HTTPException(413,"Upload exceeds configured size limit")
    digest=hashlib.sha256(data).hexdigest();key=uuid.uuid4().hex
    root=Path(settings.storage_root).resolve();root.mkdir(parents=True,exist_ok=True)
    with (root/key).open("xb") as out: out.write(data)
    item=Evidence(case_reference=case_reference,filename=Path(file.filename or "evidence.bin").name[:255],media_type=(file.content_type or "application/octet-stream")[:150],byte_size=len(data),sha256=digest,storage_key=key,uploaded_by=user.id)
    db.add(item);db.flush()
    db.add(EvidenceVersion(evidence_id=item.id,version_number=1,sha256=digest,byte_size=len(data),storage_key=key,created_by=user.id))
    record(db,user.id,"evidence.ingested","evidence",item.id,{"sha256":digest,"byte_size":len(data)});db.commit();db.refresh(item)
    return evidence_out(item)
def evidence_out(i):
    return {"id":i.id,"case_reference":i.case_reference,"filename":i.filename,"media_type":i.media_type,"byte_size":i.byte_size,"sha256":i.sha256,"status":i.status,"created_at":i.created_at}
@app.get("/api/v1/evidence")
def list_evidence(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return [evidence_out(i) for i in db.scalars(select(Evidence).order_by(Evidence.created_at.desc()).limit(200))]
def get_item(eid,db):
    item=db.get(Evidence,eid)
    if not item: raise HTTPException(404,"Evidence not found")
    return item
@app.get("/api/v1/evidence/{evidence_id}")
def get_evidence(evidence_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    return evidence_out(get_item(evidence_id,db))
@app.post("/api/v1/evidence/{evidence_id}/anchor")
def anchor_evidence(evidence_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=get_item(evidence_id,db)
    if not blockchain_configured():
        raise HTTPException(503,"Blockchain is not configured. Set RPC URL, deployed contract address and signing key.")
    existing=db.scalar(select(BlockchainAnchor).where(BlockchainAnchor.evidence_id==item.id,BlockchainAnchor.status=="confirmed"))
    if existing:
        raise HTTPException(409,"This evidence already has a confirmed anchor; create a new evidence version to anchor a new digest.")
    try:
        tx_hash,block_number,confirmed=anchor_digest(item.id,item.sha256)
        if not confirmed: raise RuntimeError("On-chain read-back verification did not match")
    except Exception as exc:
        raise HTTPException(502,"Blockchain anchoring failed; no confirmed anchor was recorded.") from exc
    anchor=BlockchainAnchor(evidence_id=item.id,sha256=item.sha256,status="confirmed",tx_hash=tx_hash,block_number=block_number)
    db.add(anchor)
    record(db,user.id,"evidence.blockchain_anchored","evidence",item.id,{"tx_hash":tx_hash,"block_number":block_number,"sha256":item.sha256})
    db.commit()
    return {"evidence_id":item.id,"sha256":item.sha256,"status":"confirmed","tx_hash":tx_hash,"block_number":block_number,"statement":"The configured chain accepted this digest. This does not prove factual truth or lawful provenance."}
@app.post("/api/v1/evidence/{evidence_id}/verify")
def verify(evidence_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=get_item(evidence_id,db);path=Path(settings.storage_root).resolve()/item.storage_key
    observed=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    integrity="VERIFIED" if observed==item.sha256 else "FAILED"
    anchor=db.scalar(select(BlockchainAnchor).where(BlockchainAnchor.evidence_id==item.id).order_by(BlockchainAnchor.created_at.desc()))
    chain="not_configured"
    if blockchain_configured() and anchor:
        try:
            chain="confirmed" if verify_digest(item.id,anchor.sha256) and anchor.sha256==item.sha256 else "failed"
        except Exception:
            chain="unavailable"
    cert="VERIFIED" if integrity=="VERIFIED" and chain=="confirmed" else ("FAILED" if integrity=="FAILED" or chain=="failed" else "INCOMPLETE")
    record(db,user.id,"evidence.verified","evidence",item.id,{"integrity":integrity,"blockchain":chain});db.commit()
    return {"evidence_id":item.id,"recorded_sha256":item.sha256,"observed_sha256":observed,"integrity_status":integrity,"blockchain_status":chain,"certificate_status":cert,"statement":"Byte-level integrity checks do not establish factual truth, authorship, lawful collection, or admissibility."}
@app.get("/api/v1/evidence/{evidence_id}/certificate")
def certificate(evidence_id:str,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    item=get_item(evidence_id,db);path=Path(settings.storage_root).resolve()/item.storage_key
    observed=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
    anchor=db.scalar(select(BlockchainAnchor).where(BlockchainAnchor.evidence_id==item.id).order_by(BlockchainAnchor.created_at.desc()))
    chain="not_configured"
    if blockchain_configured() and anchor:
        try:
            chain="confirmed" if verify_digest(item.id,anchor.sha256) and anchor.sha256==item.sha256 else "failed"
        except Exception:
            chain="unavailable"
    if observed!=item.sha256: raise HTTPException(409,"Certificate unavailable: integrity verification failed")
    if chain!="confirmed": raise HTTPException(409,f"Certificate unavailable: blockchain verification status is {chain}")
    now=datetime.now(timezone.utc);cid=str(uuid.uuid4())
    record(db,user.id,"certificate.issued","evidence",item.id,{"sha256":item.sha256});db.commit()
    return {"certificate_id":cid,"evidence_id":item.id,"sha256":item.sha256,"issued_at":now,"status":"VERIFIED","statement":"Integrity checks passed for this evidence version at issuance time. This is not factual-truth certification.","checks":{"sha256":"passed","stored_object":"matched","blockchain_anchor":"confirmed"}}
@app.get("/api/v1/audit")
def audit(limit:int=100,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    if user.role not in (UserRole.admin,UserRole.analyst): raise HTTPException(403,"Insufficient role")
    return [{"id":e.id,"actor_id":e.actor_id,"action":e.action,"resource_type":e.resource_type,"resource_id":e.resource_id,"detail":e.detail,"created_at":e.created_at} for e in db.scalars(select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(max(1,min(limit,500))))]
