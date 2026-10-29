# Fact-check test (Phase 2)

Pass rule: catch at least 80% of errors overall and 60% in every type; at most 1 false alarm.

**Result: PASS**

| Checker | Caught | conflict | misquote | outdated | units | unsupported | False alarms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ai_only | 28/30 | 6/6 | 5/6 | 6/6 | 6/6 | 5/6 | 0/16  |
| guard_only | 8/30 | 0/6 | 0/6 | 0/6 | 6/6 | 2/6 | 0/16  |
| combined | 28/30 | 6/6 | 5/6 | 6/6 | 6/6 | 5/6 | 0/16  |

## Misses and false alarms (combined)

- MISSED `u6` (unsupported): Did you know that more than 6 billion people use GPS every day?  
  AI: supported  · guard: -
- MISSED `q5` (misquote): In 1998, President Al Gore announced two new civilian GPS signals.  
  AI: supported  · guard: -
