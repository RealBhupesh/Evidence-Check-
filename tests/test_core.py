import io
import csv
import pytest
from decimal import Decimal
from evidencecheck.core import DATA,DEMO_CLAIMS,audit,check_one,format_value,load_custom_facts,parse_claim,results_to_csv

@pytest.mark.parametrize('fact',DATA['facts'])
def test_every_primary_filing_fact_matches(fact):
    m=fact['metric']
    metric={'revenue':'revenue','gross_profit':'gross profit','operating_income':'operating income','net_income':'net income','diluted_eps':'diluted EPS'}[m]
    amount=f"${fact['value']}" + (' per share' if m=='diluted_eps' else ' million')
    claim=f"{fact['company']} FY{fact['fiscal_year']} {metric} was {amount}."
    result=check_one(claim)
    assert result['status']=='match',result
    assert result['source_url'].startswith('https://')

@pytest.mark.parametrize('fact',DATA['facts'])
def test_deliberately_changed_amount_is_flagged(fact):
    metric={'revenue':'revenue','gross_profit':'gross profit','operating_income':'operating income','net_income':'net income','diluted_eps':'diluted EPS'}[fact['metric']]
    shifted=Decimal(str(fact['value']))+(Decimal('2') if fact['metric']=='diluted_eps' else Decimal('12345'))
    amount=f"${shifted}" + (' per share' if fact['metric']=='diluted_eps' else ' million')
    result=check_one(f"{fact['company']} FY{fact['fiscal_year']} {metric} was {amount}.")
    assert result['status'] in ('mismatch','wrong_period'),result


def test_wrong_fiscal_year_is_distinct():
    x=check_one('Microsoft FY2025 net income was $88.136 billion.')
    assert x['status']=='wrong_period' and x['other_year']==2024


def test_rounding_precision_is_respected():
    assert check_one('Apple FY2025 revenue was $416.16 billion.')['status']=='match'
    assert check_one('Apple FY2025 revenue was $416 billion.')['status']=='match'
    assert check_one('Apple FY2025 revenue was $415 billion.')['status']=='mismatch'


def test_company_detection_does_not_assume_without_context():
    assert check_one('FY2025 revenue was $416.161 billion.')['status']=='needs_review'
    assert check_one('FY2025 revenue was $416.161 billion.',fallback_company='AAPL')['status']=='match'
    assert check_one('Apple and Microsoft FY2025 revenue was $100 billion.')['status']=='needs_review'


def test_missing_year_scale_and_unsupported_metric_are_not_silently_passed():
    for c in ['Apple revenue was $416.161 billion.',
              'Apple FY2025 revenue was $416161.',
              'Apple FY2025 net debt was $20 billion.',
              'Apple FY2025 diluted EPS was $7.46 billion.',
              'Apple FY2025 revenue was $416.161 billion and net income was $112.010 billion.',
              'Apple FY2025 revenue was $416.161 billion, up from $391.035 billion.']:
        assert check_one(c)['status']=='needs_review',c


def test_no_match_for_unsupported_reference_year():
    assert check_one('Apple FY2020 revenue was $274 billion.')['status']=='missing_evidence'


def test_sample_report_has_expected_outcomes():
    r=audit(DEMO_CLAIMS)
    assert r['summary']['total']==14
    assert r['summary']['verified']==9
    assert r['summary']['issues']==4
    assert r['summary']['needs_review']==1
    lines=results_to_csv(r)
    assert lines.count('\n')==15
    assert 'View original filing' not in lines


def test_multiple_lines_and_unsupported_claim():
    r=audit('Apple FY2025 revenue was $416.161 billion.\nMicrosoft FY2024 gross profit was $170 billion.\nThe stock price was $200.')
    assert [x['status'] for x in r['results']]==['match','mismatch','needs_review']


def test_max_input_and_empty_raises():
    with pytest.raises(ValueError):audit('')
    with pytest.raises(ValueError):audit('Apple FY2025 revenue was $10 billion.\n'*151)


def test_customer_reference_import_can_override_one_value():
    buf=io.StringIO()
    fields=['ticker','company','fiscal_year','metric','value','unit','source_url','source_title']
    w=csv.DictWriter(buf,fieldnames=fields)
    w.writeheader()
    w.writerow({'ticker':'AAPL','company':'Apple','fiscal_year':'2025','metric':'revenue','value':'420000','unit':'USD millions','source_url':'https://example.com/approved-source','source_title':'Customer approved value'})
    facts=load_custom_facts(buf.getvalue())
    assert check_one('Apple FY2025 revenue was $420 billion.',facts)['status']=='match'
    assert check_one('Apple FY2025 revenue was $416.161 billion.',facts)['status']=='mismatch'
    with pytest.raises(ValueError):load_custom_facts('hello,world\na,b')


def test_metric_eps_and_usd_amount_differ():
    assert check_one('NVIDIA FY2025 diluted EPS was $2.94 per share.')['status']=='match'
    assert check_one('NVIDIA FY2025 net income was $72.88 billion.')['status']=='match'


def test_source_link_has_original_issuer_or_sec_url():
    hosts=['sec.gov','microsoft.com']
    for fact in DATA['facts']:
        assert any(domain in fact['source_url'] for domain in hosts)
