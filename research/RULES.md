# Research: what makes videos win (rules frozen 28 Oct 2026, before any data)

Owner asked (28 Oct): study successful channels in many niches, A to Z: how they design videos,
their style, and how they catch viewers emotionally. These rules are fixed before the data is pulled.

## Question

Inside the same channel, what is different about its **hit** videos compared with its **normal** videos?
(Comparing inside a channel removes channel size, niche and luck of the algorithm as much as we can.)

## Where the videos come from

- 9 niches × 2 searches (YouTube search, English, long videos 4–20 min, published in the last 120 days,
  sorted by views): space, science, history, geography, psychology, mysteries/true stories, nature/animals,
  engineering/how things work, illustrated/animated explainers. Queries are listed in `research/winners.py`.
- Keep channels **created in the last 24 months** (young channels: what is working now, for new channels).
- For each kept channel: its last 50 uploads; only videos over 3 minutes (no Shorts) and older than 7 days.
- A channel needs at least 8 such videos.

## Hit and normal

- Channel normal = median views of its long videos.
- **Hit** = at least 5× the channel median and at least 10,000 views.
- **Normal video** = between 0.5× and 2× the channel median. Same channels as the hits; up to as many normal
  videos as hits per channel, picked with a fixed random seed (42).
- **Struggling channels** (for the report only): young channels with 20+ long videos and median under 100 views.

## What is measured

By plain code: title words, question mark, number in title, "you/your", all-caps share, words before a
dash/colon, video length, days between uploads.

By an AI (Flash-Lite only; strong Gemini models are never used here), in batches:
- **Title**: main emotion: curiosity, awe/wonder, fear/danger, surprise/shock, personal stakes ("affects you"),
  nostalgia, humour, anger/outrage, none. Promise type: answer a question, list, story, warning, challenge.
- **Thumbnail** (looked at without the title): words of text on it, face (human / drawn character / animal /
  none), number of main subjects, style (photo, drawing/illustration, 3D render, screenshot/chart), mood
  (dark/bright), arrow or circle highlight, emotion it shows.

## How results are judged (fixed now)

- A feature is a **winning signal** if its share among hits is at least **10 points higher** than among normal
  videos, with at least **30 hits** in the comparison. Lower by 10+ points = **losing signal**. Otherwise: no clear
  difference.
- Per niche results are shown only as examples (too few hits per niche for rules).
- These are signals, not proof: hits can also come from timing, topic or luck. They become our working rules
  for titles, thumbnails and hooks, and are checked again by our own pilot videos' results.

## Limits (said in advance)

- YouTube blocks downloading videos from servers, so editing style and the first 30 seconds can't be
  measured automatically. The owner watches the top hits picked from this study and fills a short form.
- About 2,500 YouTube API units (of 10,000 a day) and about 20 Flash-Lite requests.
