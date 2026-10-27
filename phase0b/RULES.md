# Phase 0b — niche data test: rules (written before any data, 27 Oct 2026)

Blueprint: "15–20 channels per niche, chosen by rules written down first; each channel's 10
latest long videos; views per day compared with the channel's own median; re-checked weekly
for 4 weeks. Report: which small channels grow, which videos beat their channel's normal
views, per niche; ONE niche chosen."

These rules and `niches.json` were committed **before** the first data pull. They are not
changed after seeing results. If a rule turns out broken, a new dated version is added and the
reason written here; old results stay.

## Niches

1. **How technology works**
2. **Science and space**
3. **Money and economics — education only** (no investing tips, crypto, trading or "make money"
   channels; see `exclude_title_words`)

## How channels are found and chosen (same for every niche)

1. **Find:** 8 fixed search phrases per niche (`queries`), YouTube search for English, medium-length
   (4–20 min) videos from the last 180 days. Every channel that made one of those videos is a candidate.
2. **Keep a candidate only if all are true:**
   - 1,000 to 100,000 subscribers (small channels; hidden counts are left out)
   - at least 10 long videos (4 minutes or longer) and one uploaded in the last 60 days
   - not made for kids; not mainly live streams
   - English: 90 %+ of title characters are plain Latin letters, or the channel says its language is English
   - **fits the niche:** at least 4 of its 10 latest long video titles contain a niche keyword (`keywords`)
   - money niche only: none of its 10 latest titles contains an advice/trading word (`exclude_title_words`)
3. **Choose:** sort the kept channels by niche fit (most matching titles first), then by fewest
   subscribers (smaller first), then by channel id (so the order never depends on chance).
   Take the first 20. A channel that fits two niches goes only to the one where it fits best.
   If a niche has fewer than 15, that is reported as a result (little room or few small creators).

## What is measured

- For each chosen channel, every week: subscribers, total views, video count, and its 10 latest long videos
  (views, likes, comments, age).
- **Views per day** of a video = views ÷ days since upload. Videos under 7 days old are listed but not used
  for medians (their views are still climbing).
- **Beats normal:** a video whose views per day are at least **2×** the channel's own median.
- **Channel growth:** change in subscribers and total views per week.
- Snapshots: week 0 (start) and then every 7 days, 5 snapshots in total (4 weeks of change).

## How the one niche is chosen (decided now, applied at the end)

For each niche, after 4 weeks:

1. **Main:** median weekly total-views growth (%) of its channels.
2. **Second:** share of channels whose subscribers grew.
3. **Third:** share of recent videos that beat their channel's normal (room for a new video to break out).

The niche that ranks best on the main measure wins, unless it is last on both the second and third,
in which case the runner-up wins. The report shows all three numbers and the owner confirms the choice.
A niche with fewer than 15 eligible channels cannot win (too little evidence).

## Cost

YouTube Data API free quota: 10,000 units a day. Search costs 100 units; channel and video details
cost 1 unit per 50 items. Expected: about 3,000 units for the first run, about 200 per weekly re-check.
The script stops at 8,000 units. No Gemini quota is used.

## Change log

- 27 Oct 2026, still before any data: removed format words that are not topics from the keyword
  lists ("how", "work", "works", "explained" from technology; "history", "country", "countries" from money).
  With them, a money channel titled "How Inflation Works" also counted as technology, and ties went to
  technology. Found by reading the code, not from data.
- 27 Oct 2026, **version 2** (owner approved), after the first pull but before any growth data: the first
  pull found only 7 technology and 4 money channels (rule needs 15) but 20 for science, from 8 searches per
  niche; 617 of 954 candidates had under 1,000 subscribers. Too few searches is the likely cause, so each
  niche gets **12 more search phrases** (`queries_v2`, same number for all). Channels already chosen stay;
  newly eligible channels fill each niche up to 20 by the same sort rule. Science was already full, so only
  technology and money can change. Every other rule is unchanged. New channels' growth is measured from
  their own first snapshot.
