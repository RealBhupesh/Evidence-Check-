"""Deterministic validation of straightforward historical US financial claims.

This is deliberately not a general-purpose hallucination detector: claims need an
explicit company, fiscal year, metric and USD amount. Unsupported claims are
flagged for review, never silently treated as true.
"""
from __future__ import annotations

import csv
import io
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

DATA_DIR = Path(__file__).parent / 'data'
DATA = json.loads((DATA_DIR/'reference_facts.json').read_text())
DEMO_CLAIMS = (DATA_DIR/'demo_claims.txt').read_text().strip()

COMPANY_ALIASES = {
    'AAPL': ('apple', 'aapl'),
    'MSFT': ('microsoft', 'msft'),
    'NVDA': ('nvidia', 'nvda'),
}
METRIC_PATTERNS = [
    ('diluted_eps', re.compile(r'\b(?:diluted\s+(?:eps|earnings\s+per\s+share)|eps\s*\(diluted\)|earnings\s+per\s+diluted\s+share)\b', re.I)),
    ('operating_income', re.compile(r'\b(?:operating\s+(?:income|profit|earnings))\b',re.I)),
    ('net_income', re.compile(r'\b(?:net\s+(?:income|profit|earnings))\b',re.I)),
    ('gross_profit', re.compile(r'\b(?:gross\s+(?:profit|margin))\b',re.I)),
    ('revenue', re.compile(r'\b(?:total\s+)?(?:net\s+)?(?:revenue|sales)\b', re.I)),
]
MONEY_PATTERN = re.compile(r'\$\s*(?P<number>[\d,]+(?:\.\d+)?)\s*(?P<scale>billion|million|thousand|bn|mn|[bmk])?\b',re.I)
YEAR_PATTERN = re.compile(r'\b(?:FY\s*[-:]?\s*|fiscal\s+year\s*|fiscal\s+)(20\d{2})\b',re.I)
SUPPORTED_METRICS = {k for k,_ in METRIC_PATTERNS}
STATUS_LABELS = {'match':'Verified','mismatch':'Mismatch','wrong_period':'Wrong period','needs_review':'Needs review','missing_evidence':'Missing evidence'}


def load_facts() -> list[dict]:
    return [dict(f) for f in DATA['facts']]


def normalize_company(text: str, fallback: str | None = None) -> str | None:
    found = []
    for ticker, aliases in COMPANY_ALIASES.items():
        if any(re.search(r'\b'+re.escape(alias)+r'\b',text,re.I) for alias in aliases):
            found.append(ticker)
    if len(found) == 1: return found[0]
    if found: return None
    if fallback:
        fallback = fallback.strip().upper()
        if fallback in COMPANY_ALIASES: return fallback
    return None


def parse_claim(claim: str, fallback_company: str | None = None) -> tuple[dict | None, str | None]:
    companies = [ticker for ticker,aliases in COMPANY_ALIASES.items() if any(re.search(r'\b'+re.escape(alias)+r'\b',claim,re.I) for alias in aliases)]
    if len(companies)>1: return None,'More than one company mentioned; split into separate claims.'
    ticker = normalize_company(claim,fallback_company)
    if ticker is None: return None,'Company not identified; include Apple, Microsoft, or NVIDIA (or select a company).'
    years=YEAR_PATTERN.findall(claim)
    if len(years)!=1: return None,'Specify one fiscal year (for example FY2025). Calendar years and mixed years are not inferred.'
    metric_matches = [metric for metric,pattern in METRIC_PATTERNS if pattern.search(claim)]
    if len(metric_matches)!=1: return None,'Specify one supported metric: revenue, gross profit, operating income, net income, or diluted EPS.'
    matches=list(MONEY_PATTERN.finditer(claim))
    if len(matches)!=1: return None,'Include exactly one explicit USD amount, for example $416.161 billion or $7.46 per share.'
    metric=metric_matches[0]
    m=matches[0]
    num=m.group('number').replace(',','')
    try: amount=Decimal(num)
    except InvalidOperation: return None,'Invalid numeric amount.'
    scale=(m.group('scale') or '').lower()
    if metric=='diluted_eps':
        if scale: return None,'EPS must be expressed in USD per share, not millions or billions.'
        if not re.search(r'\b(?:per\s+share|eps)\b',claim,re.I): return None,'Specify that the EPS figure is per share.'
        multiplier=Decimal('1')
        unit='USD/share'
    else:
        if not scale: return None,'Currency scale is missing; use million, billion or thousand explicitly.'
        multiplier={'billion':Decimal(1000),'bn':Decimal(1000),'b':Decimal(1000),'million':Decimal(1),'mn':Decimal(1),'m':Decimal(1),'thousand':Decimal('0.001'),'k':Decimal('0.001')}[scale]
        unit='USD millions'
    decimal_places = len(num.split('.')[1]) if '.' in num else 0
    # A value displayed to N decimals might have been rounded by half a least significant digit.
    tolerance=Decimal('0.5')*(Decimal(10)**(-decimal_places))*multiplier
    return {'ticker':ticker,'fiscal_year':int(years[0]),'metric':metric,'reported_value':str(amount*multiplier),'tolerance':str(tolerance),'original_amount':str(amount),'scale':scale,'unit':unit},None


def check_one(claim: str, facts: Iterable[dict] | None = None, fallback_company: str | None = None) -> dict:
    base = {'claim':claim.strip(),'status':'needs_review','status_label':'Needs review', 'company':None,'ticker':None,'fiscal_year':None,'metric':None,'metric_label':None,'reported':None,'expected':None,'delta':None,'reason':None,'source_url':None,'source_title':None,'fiscal_year_end':None,'unit':None,'other_year':None}
    info,error=parse_claim(claim,fallback_company)
    if error:
        base['reason']=error
        return base
    facts = list(facts) if facts is not None else DATA['facts']
    base.update({'ticker':info['ticker'],'fiscal_year':info['fiscal_year'],'metric':info['metric'],'reported':info['reported_value'],'unit':info['unit']})
    same=[f for f in facts if f['ticker']==info['ticker'] and int(f['fiscal_year'])==info['fiscal_year'] and f['metric']==info['metric']]
    if not same:
        base.update(status='missing_evidence',status_label='Missing evidence',reason='No trusted source value is in the curated reference library for this company, metric and fiscal year.')
        return base
    f=same[0]
    expected=Decimal(str(f['value'])); reported=Decimal(info['reported_value']); tolerance=Decimal(info['tolerance']); diff=reported-expected
    base.update(company=f['company'],metric_label=f['metric_label'],expected=str(expected),delta=str(diff),source_url=f['source_url'],source_title=f['source_title'],fiscal_year_end=f['fiscal_year_end'])
    if abs(diff)<=tolerance:
        base.update(status='match',status_label='Verified',reason='Consistent with the published statement, within the precision shown in the claim.')
        return base
    other=[x for x in facts if x['ticker']==info['ticker'] and int(x['fiscal_year'])!=info['fiscal_year'] and x['metric']==info['metric'] and abs(reported-Decimal(str(x['value'])))<=tolerance]
    if other:
        nearest=sorted(other,key=lambda x:abs(int(x['fiscal_year'])-info['fiscal_year']))[0]
        base.update(status='wrong_period',status_label='Wrong period',other_year=nearest['fiscal_year'],reason=f'Amount corresponds to FY{nearest["fiscal_year"]}, not FY{info["fiscal_year"]}. Check the reporting period.')
    else:
        base.update(status='mismatch',status_label='Mismatch',reason='Reported amount does not match the source value for the specified metric and fiscal year.')
    return base


def split_claims(text: str) -> list[str]:
    # Supports one assertion per line; sentence breaks only when a new sentence begins.
    result=[]
    for line in text.splitlines():
        line=line.strip().lstrip('•*- ').strip()
        if not line or line.startswith('#'):continue
        sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',line)
        result.extend(s.strip() for s in sentences if s.strip())
    return result


def audit(text: str, facts: Iterable[dict] | None = None, fallback_company: str | None = None) -> dict:
    if len(text)>50000: raise ValueError('Maximum input size is 50,000 characters.')
    claims=split_claims(text)
    if len(claims)>150: raise ValueError('Maximum 150 claims per audit.')
    if not claims: raise ValueError('Add at least one financial claim to verify.')
    results=[check_one(c,facts,fallback_company) for c in claims]
    counts={s:sum(r['status']==s for r in results) for s in STATUS_LABELS}
    inspected=counts['match']+counts['mismatch']+counts['wrong_period']
    return {'results':results,'summary':{'total':len(results),'verified':counts['match'],'issues':counts['mismatch']+counts['wrong_period'],'needs_review':counts['needs_review']+counts['missing_evidence'],'evaluated':inspected,'counts':counts},'methodology':'Deterministic comparison with curated issuer financial statements. Matches are not independent audits; results only cover explicitly supported metrics, fiscal periods and source data.','demo_disclosure':'Starter example assertions are deliberately mixed between true and altered statements; no model performance or client ROI is implied.'}


def results_to_csv(report: dict) -> str:
    fields=['claim','status_label','ticker','fiscal_year','metric_label','reported','expected','delta','unit','reason','source_title','source_url']
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(report['results']);return stream.getvalue()


def load_custom_facts(csv_string: str) -> list[dict]:
    """Allow client data into one request without persisting it or implying SEC provenance.

    Required columns: ticker,company,fiscal_year,metric,value,unit,source_url,source_title.
    All non-EPS values are normalized to USD millions.
    """
    reader=csv.DictReader(io.StringIO(csv_string))
    required={'ticker','company','fiscal_year','metric','value','unit','source_url','source_title'}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError('CSV requires columns: '+', '.join(sorted(required)))
    facts=[]
    for row in reader:
        if len(facts)>=250: raise ValueError('Maximum 250 custom reference facts.')
        try:
            ticker=row['ticker'].strip().upper();year=int(row['fiscal_year']);metric=row['metric'].strip();val=Decimal(row['value'])
            if ticker not in COMPANY_ALIASES:raise ValueError('This demo supports AAPL, MSFT and NVDA; use those company codes.')
            if metric not in SUPPORTED_METRICS:raise ValueError('Unsupported metric: '+metric)
            if row['unit'].strip() != ('USD/share' if metric=='diluted_eps' else 'USD millions'):raise ValueError('All values must use USD millions (or USD/share for EPS).')
            if not 2010<=year<=2035:raise ValueError('Invalid fiscal year')
            if not row['source_url'].startswith('https://'):raise ValueError('Source link must be HTTPS')
            facts.append({'ticker':ticker,'company':row['company'].strip(),'fiscal_year':year,'fiscal_year_end':row.get('fiscal_year_end',''), 'metric':metric,'metric_label':next((f['metric_label'] for f in DATA['facts'] if f['metric']==metric),metric),'value':str(val),'unit':row['unit'].strip(),'source_url':row['source_url'].strip(),'source_title':row['source_title'].strip()})
        except (TypeError,KeyError,InvalidOperation) as e:raise ValueError('Bad custom fact row: '+str(e)) from e
    if not facts:raise ValueError('No custom reference facts found.')
    if len({(f['ticker'],f['fiscal_year'],f['metric']) for f in facts}) != len(facts):raise ValueError('Duplicate company/year/metric pairs.')
    return facts


def format_value(value: str | None, unit: str | None) -> str:
    if value is None:return '—'
    x=Decimal(value)
    if unit=='USD/share':return '$'+f'{x:,.2f}'+'/share'
    return '$'+f'{(x/1000):,.3f}'+'B'
