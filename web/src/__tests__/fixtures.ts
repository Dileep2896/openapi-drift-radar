import type { Report } from '../types.ts'

export const report: Report = {
  changes: [
    {
      id: 'param_renamed:POST /v1/charges:source', kind: 'param_renamed', severity: 'breaking', method: 'POST',
      path: '/v1/charges', operation_id: 'createCharge', name: 'source', new_name: 'payment_method', value: null,
      location: 'body', replacement: null, detail: '`source` was renamed to `payment_method` (body, string).',
    },
    {
      id: 'endpoint_deprecated:GET /v1/charges/list', kind: 'endpoint_deprecated', severity: 'behavioral',
      method: 'GET', path: '/v1/charges/list', operation_id: 'listCharges', name: null, new_name: null, value: null,
      location: null, replacement: 'GET /v1/charges', detail: '`GET /v1/charges/list` is deprecated.',
    },
    {
      id: 'endpoint_added:POST /v1/payment_intents', kind: 'endpoint_added', severity: 'additive', method: 'POST',
      path: '/v1/payment_intents', operation_id: null, name: null, new_name: null, value: null, location: null,
      replacement: null, detail: 'New endpoint.',
    },
  ],
  impacts: [
    {
      path: 'api/charges.mdx', score: 8, hit_count: 3, severity: 'breaking',
      change_ids: ['param_renamed:POST /v1/charges:source', 'endpoint_deprecated:GET /v1/charges/list'],
      hits: [
        { path: 'api/charges.mdx', line: 18, excerpt: '| `source` | string | required |', context: 'table',
          change_id: 'param_renamed:POST /v1/charges:source', kind: 'param_renamed', severity: 'breaking', term: 'source' },
        { path: 'api/charges.mdx', line: 25, excerpt: "source: 'tok_visa',", context: 'code',
          change_id: 'param_renamed:POST /v1/charges:source', kind: 'param_renamed', severity: 'breaking', term: 'source' },
        { path: 'api/charges.mdx', line: 40, excerpt: '`GET /v1/charges/list` returns charges.', context: 'prose',
          change_id: 'endpoint_deprecated:GET /v1/charges/list', kind: 'endpoint_deprecated', severity: 'behavioral',
          term: '/v1/charges/list' },
      ],
      suggested_patch:
        "--- a/api/charges.mdx\n+++ b/api/charges.mdx\n@@ -17,3 +17,3 @@\n context line\n-  source: 'tok_visa',\n+  payment_method: 'tok_visa',\n",
    },
    {
      path: 'quickstart.mdx', score: 3, hit_count: 1, severity: 'breaking',
      change_ids: ['param_renamed:POST /v1/charges:source'],
      hits: [
        { path: 'quickstart.mdx', line: 22, excerpt: '-d source=tok_visa', context: 'code',
          change_id: 'param_renamed:POST /v1/charges:source', kind: 'param_renamed', severity: 'breaking', term: 'source' },
      ],
      suggested_patch: '--- a/quickstart.mdx\n+++ b/quickstart.mdx\n@@ -22 +22 @@\n-  -d source=tok_visa\n+  -d payment_method=tok_visa\n',
    },
  ],
  summary: {
    change_count: 3, breaking_count: 1, impacted_pages: 2, total_hits: 4, pages_scanned: 8, skip_llm: false,
    scan_ms: 4.2, drafter: 'rule-based',
  },
}

export const noopReport: Report = {
  changes: [],
  impacts: [],
  summary: { ...report.summary, change_count: 0, breaking_count: 0, impacted_pages: 0, total_hits: 0, skip_llm: true },
}
