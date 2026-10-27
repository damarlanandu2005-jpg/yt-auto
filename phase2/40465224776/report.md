# Fact-check test (Phase 2)

Pass rule: catch at least 80% of errors overall and 60% in every type; at most 1 false alarm.

**Result: PASS**

| Checker | Caught | conflict | misquote | outdated | units | unsupported | False alarms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai_only | 28/30 | 4/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/16  |
| guard_only | 8/30 | 0/6 | 0/6 | 0/6 | 6/6 | 2/6 | 0/16  |
| combined | 28/30 | 4/6 | 6/6 | 6/6 | 6/6 | 6/6 | 0/16  |

## Misses and false alarms (combined)

- MISSED `c5` (conflict): International Atomic Time is a weighted average of about 450 clocks.  
  AI: supported  · guard: -
- MISSED `c6` (conflict): Bradford Parkinson retired from the Air Force in 1978.  
  AI: supported  · guard: -
