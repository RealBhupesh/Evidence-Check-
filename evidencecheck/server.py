"""FastAPI server for local browser dashboard and programmatic audits."""
from __future__ import annotations
import io
from pathlib import Path
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pypdf import PdfReader
from .core import DATA, DEMO_CLAIMS, audit, load_custom_facts, results_to_csv

ROOT = Path(__file__).parent
app=FastAPI(title='EvidenceCheck | Financial Claim Verification',description='Portfolio demonstration: deterministic fact checking against historical financial statements.',version='0.1.0')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')

class AuditRequest(BaseModel):
    text: str = Field(min_length=1,max_length=50000)
    fallback_company: str | None = None

class CustomAuditRequest(AuditRequest):
    reference_csv: str = Field(min_length=10,max_length=100000)

@app.get('/')
def index():return FileResponse(ROOT/'static'/'index.html')

@app.get('/api/health')
def health():return {'status':'ok','service':'EvidenceCheck','reference_records':len(DATA['facts']),'live_sec_integration':False,'data_vintage':'FY2023–FY2025 historical snapshot'}

@app.get('/api/library')
def library():return {'description':DATA['description'],'facts':DATA['facts'],'companies':[{'ticker':t,'name':n} for t,n in [('AAPL','Apple'),('MSFT','Microsoft'),('NVDA','NVIDIA')]]}

@app.get('/api/demo')
def demo():return {'claims':DEMO_CLAIMS,'report':audit(DEMO_CLAIMS),'sample_is_synthetic':True,'note':'Demo assertions are written for this project; some amounts have been intentionally changed. Reference source facts are sourced from issuer filings.'}

@app.post('/api/audit')
def run_audit(req:AuditRequest):
    try:return audit(req.text,fallback_company=req.fallback_company)
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e

@app.post('/api/audit/custom')
def custom_audit(req:CustomAuditRequest):
    try:
        facts=load_custom_facts(req.reference_csv)
        return {'report':audit(req.text,facts,fallback_company=req.fallback_company),'custom_reference':True,'note':'Customer-supplied facts are not independently validated by this application.'}
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e

@app.post('/api/export.csv')
def export_csv(req:AuditRequest):
    try:csv_data=results_to_csv(audit(req.text,fallback_company=req.fallback_company))
    except ValueError as e:raise HTTPException(status_code=422,detail=str(e)) from e
    return Response(csv_data,media_type='text/csv',headers={'Content-Disposition':'attachment; filename="evidencecheck-audit.csv"'})

@app.get('/api/demo/export.csv')
def demo_csv():
    return Response(results_to_csv(audit(DEMO_CLAIMS)),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="evidencecheck-demo-audit.csv"'})

@app.post('/api/extract')
async def extract(upload:UploadFile = File(...)):
    """Read user-uploaded claim summary PDF/TXT, not uploaded financial ground truth."""
    contents=await upload.read()
    if len(contents)>7*1024*1024:raise HTTPException(413,'File must be smaller than 7 MB.')
    ext=Path(upload.filename or '').suffix.lower()
    try:
        if ext=='.pdf':
            reader=PdfReader(io.BytesIO(contents))
            if len(reader.pages)>30:raise HTTPException(413,'Maximum 30 pages.')
            text='\n'.join((page.extract_text() or '') for page in reader.pages)
        elif ext=='.txt':text=contents.decode('utf-8')
        else:raise HTTPException(422,'Only .pdf and .txt summaries are supported.')
    except HTTPException:raise
    except Exception as e:raise HTTPException(422,'Could not extract text from this document.') from e
    if not text.strip():raise HTTPException(422,'No searchable text detected; scanned images need OCR and are not supported.')
    return {'text':text[:50000],'truncated':len(text)>50000,'disclaimer':'PDF text extraction only; factual assertions must still include company, FY, metric, and USD amounts.'}
