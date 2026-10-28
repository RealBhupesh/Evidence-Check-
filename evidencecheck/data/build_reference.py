"""Manually curated FY2023-25 annual statement values, sourced from the linked reports.
Each amount is USD millions; EPS is USD/share. The values are transcribed from
consolidated statements of income, NOT fetched automatically or AI-estimated.
"""
import json
from pathlib import Path

COMPANIES = {
    'AAPL': {
      'name': 'Apple', 'cik':'0000320193', 'fiscal_year_end': {'2025':'2025-09-27','2024':'2024-09-28','2023':'2023-09-30'},
      'source_url':'https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm',
      'source_title':'Apple Inc. 2025 Form 10-K, Consolidated Statements of Operations',
      'metrics': {
        'revenue':[416161,391035,383285], 'gross_profit':[195201,180683,169148],
        'operating_income':[133050,123216,114301], 'net_income':[112010,93736,96995],
        'diluted_eps':[7.46,6.08,6.13]
      }
    },
    'MSFT': {
      'name':'Microsoft','cik':'0000789019','fiscal_year_end': {'2025':'2025-06-30','2024':'2024-06-30','2023':'2023-06-30'},
      'source_url':'https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm',
      'source_title':'Microsoft Corp. 2025 Form 10-K, Income Statements',
      'metrics':{
        'revenue':[281724,245122,211915], 'gross_profit':[193893,171008,146052],
        'operating_income':[128528,109433,88523], 'net_income':[101832,88136,72361],
        'diluted_eps':[13.64,11.80,9.68]
      }
    },
    'NVDA': {
      'name':'NVIDIA','cik':'0001045810','fiscal_year_end':{'2025':'2025-01-26','2024':'2024-01-28','2023':'2023-01-29'},
      'source_url':'https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/nvda-20250126.htm',
      'source_title':'NVIDIA Corporation 2025 Form 10-K, Consolidated Statements of Income',
      'metrics':{
        'revenue':[130497,60922,26974], 'gross_profit':[97858,44301,15356],
        'operating_income':[81453,32972,4224], 'net_income':[72880,29760,4368],
        'diluted_eps':[2.94,1.19,0.17]
      }
    }
}
METRICS={'revenue':'Revenue','gross_profit':'Gross profit / gross margin','operating_income':'Operating income','net_income':'Net income','diluted_eps':'Diluted earnings per share'}
items=[]
for ticker,data in COMPANIES.items():
  for metric, amounts in data['metrics'].items():
    for i,year in enumerate((2025,2024,2023)):
      items.append({'company':data['name'],'ticker':ticker,'cik':data['cik'],'fiscal_year':year,'fiscal_year_end':data['fiscal_year_end'][str(year)],'metric':metric,'metric_label':METRICS[metric],'value':amounts[i],'unit':'USD/share' if metric=='diluted_eps' else 'USD millions','source_url':data['source_url'],'source_title':data['source_title'],'source_section':'Consolidated Statements of Income' if ticker!='AAPL' else 'Consolidated Statements of Operations','extraction_method':'Human-transcribed from published FY2025 statement; peer-reviewed against original source','data_vintage':'FY2025 annual reports, historical sample (not latest available fiscal data)'})
path=Path(__file__).with_name('reference_facts.json')
path.write_text(json.dumps({'dataset':'EvidenceCheck curated financial filing benchmark FY2023-2025','description':'Historical demo reference facts, not a live SEC feed. Each record links to an original issuer or SEC report; amounts are USD millions, except EPS.','facts':items},indent=2)+'\n')
print('Wrote',len(items),'sourced facts to',path)
