# EvidenceCheck — design-partner trial scopes

## The buyer's question
Can our research or AI product quickly flag when a financial figure in an AI-generated summary differs from an original company report, **with a reproducible link to the source?**

## $100 introductory validation (portfolio-design partner offer)
**Deliverable:** Run 10 pre-agreed financial figures from 3 publicly accessible source reports through a narrowly configured check, provide a simple CSV issue log, and demonstrate how to rerun the checks.

**Included:** (1) Agree on 3 public reports and 10 measurable claims, (2) format source evidence, (3) run validation, (4) identify actual discrepancies or unknowns, (5) share scripts and a 15-minute handover.

**Not included:** security assessment, live data integrations, SSO, automatic private-doc ingestion, full-document understanding, data entry from hundreds of filings, finance advice, production SLAs, or a guarantee of finding a real error.

**Buyer outcome:** They can judge whether a source-anchored numerical check adds value to an existing analysis workflow. Whether it saves time or reduces errors must be measured with their own team.

## $2,000 larger fixed-scope pilot (proposed price, subject to requirements)
**Deliverable:** A reusable prototype for a larger approved financial-document sample with batch claim validation, source evidence links, independent evaluation of mistakes and failures, a report export, a demonstration and documented handover.

Suggested milestones: (1) requirements and acceptance tests, (2) company/metric/period mapping and document intake, (3) validation engine and reviewer-friendly report, (4) evaluation on a held-out sample and handover. Source materials, ownership, data handling and acceptance criteria to be agreed in writing.

The current portfolio app demonstrates the workflow and UI. It does **not** include all production features implied by these possible paid engagements.

## Suggested buyer success measures
- Coverage: what fraction of target numerical statements can be parsed and checked against source-backed metrics?
- Correctness: discrepancy precision and missed-error rate on a fresh, human-labeled sample.
- Review cost: median time for an analyst to check and act on one flagged claim, compared with the current workflow.
- Traceability: percentage of verdicts with source citations that a reviewer can independently inspect.

**No measured efficiency savings, error reductions or financial ROI have been established.**
