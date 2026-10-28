from fastapi.testclient import TestClient
from evidencecheck.server import app
client=TestClient(app)

def test_health_and_library():
    assert client.get('/api/health').json()['reference_records']==45
    assert len(client.get('/api/library').json()['facts'])==45

def test_demo_report_and_exports():
    d=client.get('/api/demo').json()
    assert d['report']['summary']=={'total':14,'verified':9,'issues':4,'needs_review':1,'evaluated':13,'counts':{'match':9,'mismatch':3,'wrong_period':1,'needs_review':1,'missing_evidence':0}}
    exported=client.get('/api/demo/export.csv')
    assert exported.status_code==200 and 'text/csv' in exported.headers['content-type']
    assert 'Wrong period' in exported.text

def test_user_text_endpoint():
    r=client.post('/api/audit',json={'text':'Apple FY2025 net income was $112.010 billion.'})
    assert r.status_code==200
    assert r.json()['results'][0]['status']=='match'

def test_bad_input_is_rejected():
    assert client.post('/api/audit',json={'text':''}).status_code==422
    assert client.post('/api/audit',json={'text':'\n\n'}).status_code==422

def test_static_html_has_dashboard():
    r=client.get('/')
    assert r.status_code==200 and 'Every number' in r.text
    assert client.get('/static/app.js').status_code==200

def test_pdf_upload_rejects_bad_file_and_invalid_ext():
    r=client.post('/api/extract',files={'upload':('bad.jpg',b'a jpeg','image/jpeg')})
    assert r.status_code==422
    r=client.post('/api/extract',files={'upload':('claim.txt',b'Microsoft FY2025 revenue was $281.724 billion.','text/plain')})
    assert r.status_code==200 and 'FY2025' in r.json()['text']
