"""Build a no-server, interactive single-file preview for portfolio reviews.

Real browser-side comparison logic is included (not a hardcoded screenshot).
PDF extraction and full REST API remain in the Python project. No private data is sent.
"""
import json
from pathlib import Path
from evidencecheck.core import DATA, DEMO_CLAIMS
ROOT=Path(__file__).resolve().parent.parent
html=(ROOT/'evidencecheck/static/index.html').read_text()
css=(ROOT/'evidencecheck/static/styles.css').read_text()
js=(ROOT/'evidencecheck/static/app.js').read_text()
css+='\n.upload-link{display:none!important}.top-help{display:none!important}\n'
shim=r'''
const referenceFacts=__FACTS__;
const demoClaims=__DEMO__;
const aliases={'AAPL':['apple','aapl'],'MSFT':['microsoft','msft'],'NVDA':['nvidia','nvda']};
const metricPatterns=[['diluted_eps',/\b(?:diluted\s+(?:eps|earnings\s+per\s+share)|eps\s*\(diluted\)|earnings\s+per\s+diluted\s+share)\b/i],['operating_income',/\boperating\s+(?:income|profit|earnings)\b/i],['net_income',/\bnet\s+(?:income|profit|earnings)\b/i],['gross_profit',/\bgross\s+(?:profit|margin)\b/i],['revenue',/\b(?:total\s+)?(?:net\s+)?(?:revenue|sales)\b/i]];
const stLabels={match:'Verified',mismatch:'Mismatch',wrong_period:'Wrong period',needs_review:'Needs review',missing_evidence:'Missing evidence'};
const demoClaimLines=demoClaims.trim().split('\n');
function offlineAudit(txt,defaultCompany){
 const lines=txt.split('\n').map(x=>x.trim().replace(/^[•*\-\s]+/,'')).filter(x=>x&&!x.startsWith('#')).flatMap(x=>x.split(/(?<=[.!?])\s+(?=[A-Z])/));
 if(!lines.length)throw new Error('Add at least one financial claim to verify.');
 if(lines.length>150 || txt.length>50000)throw new Error('Too many claims. Maximum 150 claims or 50,000 characters.');
 const results=lines.map(claim=>{
  let r={claim,status:'needs_review',status_label:'Needs review',company:null,ticker:null,fiscal_year:null,metric:null,metric_label:null,reported:null,expected:null,delta:null,reason:null,source_url:null,source_title:null,fiscal_year_end:null,unit:null,other_year:null};
  const matches=Object.entries(aliases).filter(([ticker,terms])=>terms.some(term=>new RegExp('\\b'+term+'\\b','i').test(claim))).map(([ticker])=>ticker);
  if(matches.length>1){r.reason='More than one company mentioned; split into separate claims.';return r;}
  const ticker=matches[0]||defaultCompany;
  if(!ticker||!aliases[ticker]){r.reason='Company not identified; include Apple, Microsoft, or NVIDIA (or select a company).';return r;}
  const years=[...claim.matchAll(/\b(?:FY\s*[-:]?\s*|fiscal\s+year\s*|fiscal\s+)(20\d{2})\b/gi)];
  if(years.length!==1){r.reason='Specify one fiscal year (for example FY2025). Calendar years and mixed years are not inferred.';return r;}
  const metricMatches=metricPatterns.filter(([m,re])=>re.test(claim));
  if(metricMatches.length!==1){r.reason='Specify one supported metric: revenue, gross profit, operating income, net income, or diluted EPS.';return r;}
  const mm=[...claim.matchAll(/\$\s*([\d,]+(?:\.\d+)?)\s*(billion|million|thousand|bn|mn|[bmk])?\b/gi)];
  if(mm.length!==1){r.reason='Include exactly one explicit USD amount, for example $416.161 billion or $7.46 per share.';return r;}
  const metric=metricMatches[0][0],scale=(mm[0][2]||'').toLowerCase(),amount=Number(mm[0][1].replaceAll(',',''));
  if(metric==='diluted_eps'){
    if(scale||!/(?:\beps\b|\bper\s+share\b)/i.test(claim)){r.reason='EPS must be expressed as USD per share.';return r;}
  }else if(!scale){r.reason='Currency scale is missing; use million, billion or thousand explicitly.';return r;}
  const mult=metric==='diluted_eps'?1:({billion:1000,bn:1000,b:1000,million:1,mn:1,m:1,thousand:.001,k:.001}[scale]);
  const decimals=(mm[0][1].split('.')[1]||'').length,tolerance=.5*10**(-decimals)*mult;
  const reported=amount*mult,year=Number(years[0][1]);
  r.ticker=ticker;r.fiscal_year=year;r.metric=metric;r.reported=String(reported);r.unit=metric==='diluted_eps'?'USD/share':'USD millions';
  const f=referenceFacts.find(f=>f.ticker===ticker&&Number(f.fiscal_year)===year&&f.metric===metric);
  if(!f){r.status='missing_evidence';r.status_label='Missing evidence';r.reason='No trusted source value is in the curated reference library for this company, metric and fiscal year.';return r;}
  const delta=reported-Number(f.value);
  Object.assign(r,{company:f.company,metric_label:f.metric_label,expected:String(f.value),delta:String(delta),source_url:f.source_url,source_title:f.source_title,fiscal_year_end:f.fiscal_year_end});
  if(Math.abs(delta)<=tolerance){r.status='match';r.reason='Consistent with the published statement, within the precision shown in the claim.';}
  else{
    const wrong=referenceFacts.find(x=>x.ticker===ticker&&x.fiscal_year!==year&&x.metric===metric&&Math.abs(reported-Number(x.value))<=tolerance);
    if(wrong){r.status='wrong_period';r.other_year=wrong.fiscal_year;r.reason=`Amount corresponds to FY${wrong.fiscal_year}, not FY${year}. Check the reporting period.`;}
    else{r.status='mismatch';r.reason='Reported amount does not match the source value for the specified metric and fiscal year.';}
  }
  r.status_label=stLabels[r.status];return r;
 });
 let counts=Object.fromEntries(Object.keys(stLabels).map(k=>[k,results.filter(r=>r.status===k).length]));
 let summary={total:results.length,verified:counts.match,issues:counts.mismatch+counts.wrong_period,needs_review:counts.needs_review+counts.missing_evidence,evaluated:counts.match+counts.mismatch+counts.wrong_period,counts};
 return {results,summary};
}
function csvFrom(report){const keys=['claim','status_label','ticker','fiscal_year','metric_label','reported','expected','delta','unit','reason','source_title','source_url'];const quote=v=>'"'+String(v??'').replaceAll('"','""')+'"';return [keys.join(','),...report.results.map(r=>keys.map(k=>quote(r[k])).join(','))].join('\r\n');}
window.fetch=async (url,options={})=>{
 const addr=String(url);
 if(addr==='/api/demo')return new Response(JSON.stringify({claims:demoClaims,report:offlineAudit(demoClaims)}),{headers:{'content-type':'application/json'}});
 if(addr==='/api/library')return new Response(JSON.stringify({facts:referenceFacts,description:'Historical source-backed reference library'}),{headers:{'content-type':'application/json'}});
 const p=options.body?JSON.parse(options.body):{};
 try{
  if(addr==='/api/audit')return new Response(JSON.stringify(offlineAudit(p.text||'',p.fallback_company)),{headers:{'content-type':'application/json'}});
  if(addr==='/api/export.csv')return new Response(csvFrom(offlineAudit(p.text||'',p.fallback_company)),{headers:{'content-type':'text/csv'}});
  return new Response(JSON.stringify({detail:'Only the desktop Python version supports this feature.'}),{status:422,headers:{'content-type':'application/json'}});
 }catch(e){return new Response(JSON.stringify({detail:e.message}),{status:422,headers:{'content-type':'application/json'}});}
};
'''.replace('__FACTS__',json.dumps(DATA['facts'],separators=(',',':'))).replace('__DEMO__',json.dumps(DEMO_CLAIMS))
html=html.replace('<link rel="stylesheet" href="/static/styles.css" />','<style>'+css+'</style>')
html=html.replace('Company figures are real historical published financials. Example audit statements contain intentional mistakes.','OFFLINE STANDALONE DEMO. Historical published figures; intentionally altered example claims. PDF import needs the Python version.')
html=html.replace('<script src="/static/app.js" defer></script>','<script>'+shim+'</script>\n<script>'+js+'</script>')
out=ROOT/'showcase'/'EvidenceCheck_Standalone_Demo.html'
out.write_text(html)
print('Wrote',out,out.stat().st_size,'bytes')
