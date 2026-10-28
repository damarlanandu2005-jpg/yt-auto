# Fact-check test (Phase 2)

Pass rule: catch at least 80% of errors overall and 60% in every type; at most 1 false alarm.

**Result: PASS**

| Checker | Caught | conflict | misquote | outdated | units | unsupported | False alarms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai_only | 30/30 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/16  |
| guard_only | 8/30 | 0/6 | 0/6 | 0/6 | 6/6 | 2/6 | 0/16  |
| combined | 30/30 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/16  |

## Misses and false alarms (combined)

