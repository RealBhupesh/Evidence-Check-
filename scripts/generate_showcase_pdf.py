"""Two-page, evidence-grounded portfolio case study. Uses no customer claims."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from evidencecheck.core import DEMO_CLAIMS,audit
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'showcase'/'EvidenceCheck_Case_Study.pdf'
W,H=A4
INK=HexColor('#16202A');TEXT=HexColor('#344050');GRAY=HexColor('#738192');RED=HexColor('#DF6659');GREEN=HexColor('#137F5B');LINE=HexColor('#E3E8EC');PALE=HexColor('#F6F7F9');ORANGE=HexColor('#D17D32')
c=canvas.Canvas(str(OUT),pagesize=A4)
c.setTitle('EvidenceCheck | Source-grounded financial verification - Redowl Studio')
c.setAuthor('Redowl Studio')

def text(x,y,t,size=10,color=TEXT,bold=False):
    c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.setFillColor(color);c.drawString(x,y,t)

def rule(y):c.setStrokeColor(LINE);c.setLineWidth(.8);c.line(42,y,W-42,y)

def wrap(x,y,s,maxw=500,leading=16,size=10,color=TEXT,font='Helvetica'):
    c.setFont(font,size);c.setFillColor(color);words=s.split();line='';lines=[]
    for wd in words:
        t=wd if not line else line+' '+wd
        if c.stringWidth(t,font,size)>maxw and line:lines.append(line);line=wd
        else:line=t
    if line:lines.append(line)
    for l in lines:c.drawString(x,y,l);y-=leading
    return y

def badge(x,y,letter,label,color):
    c.setFillColor(color);c.roundRect(x,y-8,28,28,5,fill=1,stroke=0)
    text(x+9,y,letter,12,HexColor('#FFFFFF'),True)
    text(x+39,y+3,label,10,INK,True)

def footer(page):
    rule(45)
    text(43,30,'REDOWL STUDIO  /  PORTFOLIO DEMONSTRATION',8,GRAY,True)
    text(W-77,30,str(page)+' / 2',8,GRAY)

# PAGE 1
c.setFillColor(INK);c.rect(0,H-135,W,135,fill=1,stroke=0)
c.setFillColor(RED);c.roundRect(42,H-69,35,35,8,fill=1,stroke=0)
text(51,H-58,'E',21,HexColor('#FFFFFF'),True)
text(88,H-51,'EVIDENCECHECK',12,HexColor('#FFFFFF'),True)
text(88,H-68,'A financial-claim verification prototype',10,HexColor('#BFC8D2'))
text(42,H-108,'Confidence starts with evidence.',23,HexColor('#FFFFFF'),True)
text(42,H-156,'WHY IT EXISTS',9,RED,True)
wrap(42,H-175,'Financial teams increasingly review AI-generated explanations and summaries. A convincing sentence can still contain a wrong amount or a mismatched reporting year. This prototype gives analysts a quick, traceable numerical cross-check.',510,17,10)

r=audit(DEMO_CLAIMS)
ks=[('14','TOTAL CLAIMS'),('9','VERIFIED'),('4','DISCREPANCIES'),('1','HUMAN REVIEW')]
for i,(num,label) in enumerate(ks):
    x=42+i*133
    c.setFillColor(PALE);c.roundRect(x,H-287,123,70,8,fill=1,stroke=0)
    text(x+13,H-245,num,22,INK,True)
    text(x+13,H-268,label,8,GRAY,True)
text(42,H-316,'THE WORKING DEMO',9,RED,True)
img=ImageReader(str(ROOT/'screenshots'/'dashboard-preview.png'))
# Top of the dashboard is deliberately shown as a visual product preview.
c.drawImage(img,42,H-623,width=511,height=292,mask='auto',preserveAspectRatio=False)
text(42,H-648,'Source-backed results, not a simulated screenshot.',9,INK,True)
wrap(42,H-668,'The dashboard runs on a FastAPI application with 45 historical issuer facts, an explainable comparison engine, PDF/TXT claim input, CSV export and API endpoints. Source links point to published reports.',505,15,9,GRAY)
text(42,H-746,'EVIDENCE & LIMITATIONS',9,RED,True)
wrap(42,H-764,'The 14 sample statements were authored for testing, including intentional errors. The results do not establish production model accuracy, analyst time savings, or an audit opinion.',510,15,9,GRAY)
footer(1);c.showPage()

# PAGE 2
text(42,H-55,'What the verifier actually finds',22,INK,True)
text(42,H-77,'Selected controlled examples from the working application',10,GRAY)
rule(H-92)
issues=[
    ('WRONG FISCAL PERIOD','Microsoft FY2025 net income: $88.136B','Source: FY2025 $101.832B. The claimed value belongs to FY2024.',ORANGE),
    ('WRONG AMOUNT','NVIDIA FY2025 diluted EPS: $2.49','Source: FY2025 diluted EPS $2.94 per share.',RED),
    ('CORRECT AMOUNT','Apple FY2025 revenue: $416.161B','Source: FY2025 net sales $416,161M (equivalent to $416.161B).',GREEN),
]
y=H-127
for title,claim,reason,color in issues:
    c.setFillColor(PALE);c.roundRect(42,y-91,W-84,85,9,fill=1,stroke=0)
    c.setFillColor(color);c.roundRect(56,y-31,4,19,2,fill=1,stroke=0)
    text(71,y-19,title,8,color,True)
    text(71,y-40,claim,12,INK,True)
    wrap(71,y-58,reason,465,13,9,GRAY)
    y-=103

text(42,y-2,'HOW IT WORKS',9,RED,True)
steps=[('1','Parse','Company + fiscal year + financial metric + USD amount'),('2','Normalize','Convert billions/millions and account for displayed precision'),('3','Verify','Compare with 45 reference facts from three FY2025 filings'),('4','Explain','Report outcome, expected value and source link')]
y-=33
for n,title,detail in steps:
    c.setFillColor(INK);c.circle(51,y+2,11,fill=1,stroke=0)
    text(47.8,y-1,n,10,HexColor('#FFFFFF'),True)
    text(72,y+4,title,10,INK,True)
    text(148,y+4,detail,9,TEXT)
    y-=31

rule(y-2)
text(42,y-27,'SMALL, PAID VALIDATION OFFER',9,RED,True)
text(42,y-49,'$100 design-partner trial',15,INK,True)
wrap(42,y-69,'Check 10 agreed financial claims against three public documents; share the reusable script, exceptions and sources. This is an introductory discovery scope, not production integration.',515,15,9,TEXT)

text(42,124,'PUBLISHED REFERENCE SOURCES',9,RED,True)
links=[
 ('Apple 2025 Form 10-K','https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm'),
 ('Microsoft 2025 Form 10-K','https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm'),
 ('NVIDIA 2025 Form 10-K','https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/nvda-20250126.htm')
]
for i,(name,url) in enumerate(links):
    ypos=106-i*15
    text(42,ypos,name+'  |  open source',8,GRAY)
    c.linkURL(url,(42,ypos-2,240,ypos+11),relative=0)
footer(2)
c.save()
print('Created',OUT)
