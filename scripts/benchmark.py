"""Generate reproducible *synthetic* controls, not external benchmark accuracy.

A positive assertion is derived from each of 45 published fact records. A seeded
negative is made by deliberately changing the USD amount. This checks basic
regression behavior only and is not a real-world precision/recall estimate.
"""
import json
from decimal import Decimal
from pathlib import Path
from evidencecheck.core import DATA,check_one

metric_names={'revenue':'revenue','gross_profit':'gross profit','operating_income':'operating income','net_income':'net income','diluted_eps':'diluted EPS'}
records=[]
for f in DATA['facts']:
    amount=Decimal(str(f['value']))
    for kind,value in [('true',amount),('altered',amount+(Decimal(2) if f['metric']=='diluted_eps' else Decimal(12345)))]:
        unit=' per share' if f['metric']=='diluted_eps' else ' million'
        claim=f"{f['company']} FY{f['fiscal_year']} {metric_names[f['metric']]} was ${value}{unit}."
        r=check_one(claim)
        expected='match' if kind=='true' else 'error'
        detected='match' if r['status']=='match' else ('error' if r['status'] in ('wrong_period','mismatch') else 'abstain')
        records.append({'claim':claim,'injected_type':kind,'actual_status':r['status'],'expected':expected,'detected':detected,'passed':expected==detected})
summary={'total':len(records),'passes':sum(x['passed'] for x in records),'true_controls':45,'deliberately_altered_controls':45,'method':'Deterministic synthetic controls from 45 curated financial fact entries. Not a field accuracy estimate; no unseen claims included.'}
output=Path(__file__).parent.parent/'samples'/'synthetic_regression_results.json'
output.write_text(json.dumps({'summary':summary,'tests':records},indent=2)+'\n')
print(json.dumps(summary,indent=2))
if summary['passes']!=len(records):raise SystemExit(1)
