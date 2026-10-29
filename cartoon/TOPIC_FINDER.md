# Strong-emotion topic finder — DESIGN (29 Oct 2026) and BUILT (29 Oct evening)

**Built:** yt_auto/emotion_topics.py, entry cartoon/find_topics.py, settings cartoon/topic_finder.json (all numbers
below are there), workflow .github/workflows/cartoon-topics.yml (find / test-feeling / test-safety). The owner's
data answers (section 6) were not in yet, so defaults are used: watch list = the 4 channels below + the 6 channels
that appear most in the searches each run; red lines = T5; approval = the owner OKs the weekly list of 14.
Test B (plain-code part): 25/25 unsafe blocked, 0/25 false blocks (cartoon/topic_safety_test.json, written before
the filter). The AI adds a second safety flag in the feeling step.

Owner, 29 Oct: "build the strong emotion topic finder … should be more precise … first let's design it as a strong
one; if you need any data ask me, we collect it." Topics: any subject with a strong, TRUE feeling (like Zack D
Films), for the Stickman Thoughts template (cartoon/TEMPLATE.md): "What if …? He goes there. He feels it. He finds
out the truth."

## 1. What a good topic is (the target)

A topic passes only if ALL of these hold. Each one is checked by code or by a test, never assumed.

| # | Rule | Why | Checked by |
|---|------|-----|-----------|
| T1 | **One vivid situation the viewer can imagine being in** ("you fall into…", "you stand on…", "you were on the Titanic…") | the template: the stickman goes there and feels it | AI rubric + plain-code form check |
| T2 | **A strong feeling that the facts really support** (fear, awe, disgust, wonder, sadness, surprise) | R2: honest emotion, no fake drama | AI rubric; then the script's fact-check |
| T3 | **The answer is known and written down** (a real event, or a documented effect), not pure guessing | every line needs a source | the research step finds enough passages (measured) |
| T4 | **People already want it**: similar Shorts beat their channel's normal, or the subject has many Wikipedia readers | quality over volume (R3): spend each day on proven interest | measured signals (section 2) |
| T5 | **Safe**: no dangerous acts people could copy, no self-harm, no health/legal/money advice, no recent tragedy with living victims (<25 years), no politics/religion, no accusations against companies or people, no gore beyond cartoon | YouTube policies + India defamation risk + CLAUDE.md ground rules | safety filter (tested, section 5) |
| T6 | **Drawable** with our stickman, 12 backgrounds and things, or simple new props | the video must be makeable without manual work | props match (plain code) |
| T7 | **New**: not a past Short (library/), not a copy of a competitor's exact question, not the same subject area as the last 3 days | inauthentic-content rule, viewer variety | similarity check (existing topics.py code) |

## 2. Signals (measured, no AI)

| Signal | What | Cost |
|--------|------|------|
| S1 **Competitor Shorts that beat their channel's normal** | for a watch list of "what if" Shorts channels: their last ~100 Shorts (≤180 s); a "hit" = ≥3× the channel median views. The hit's SUBJECT and SITUATION type are the signal, never its words | YouTube API ~2 units per channel per week |
| S2 **Search demand for situations** | a few YouTube searches per week ("what happens if you", "what would it feel like", "what if you") limited to Shorts of the last 60 days, kept only if ≥100k views | 100 units per search, max 5 a week |
| S3 **Subject interest** | Wikipedia page views of the subject's article (last 6 months), and the "effect" article (e.g. Barotrauma) | free |
| S4 **Our own results** (later, the strongest signal) | our Shorts' views, "viewed vs swiped away" %, average % watched, subscribers gained | owner copies from YouTube Studio (section 6) |

## 3. Steps

1. **Collect signals** (GitHub, weekly, plain code, YouTube key): S1-S3 → signals.json.
2. **Ideas** (AI, on Kaggle): from the signals, propose ~40 situations across ALL subject areas (body, ocean,
   space, history, animals, nature, disasters, engineering, everyday life…). Each idea must name its signal, the
   feeling, the "answer" and 2-4 Wikipedia articles that should contain the answer. Rule from the research
   (28 Oct): one famous subject + a concrete situation + a twist.
3. **Hard gates** (plain code first, then AI): safety (T5), form (T1), repeat (T7), drawable (T6).
4. **Source check** (measured): fetch the named Wikipedia articles; count passages that describe the answer. An idea
   with too few passages is dropped (T3). This is what failed the first automatic Mariana run (5 of 11 sentences
   dropped) until effect articles were added.
5. **Score** (formula fixed before the first run):
   score = demand 0.35 (S1+S2+S3, measured) + feeling 0.25 (AI rubric, two different models, averaged)
           + sources 0.20 (passage count, measured) + drawable 0.10 + variety 0.10
6. **Queue**: the top 14 go into topics_queue.json with an evidence card each (signals, scores, articles,
   safety result). The daily run takes the next one (max 1 a day, R3). Refill once a week.

## 4. Feeling rubric (AI, 1-5 each)

stakes for the viewer ("you"), vividness (can you picture it?), surprise/twist, truth of the feeling (does the answer
really carry it?). The scorer never sees view counts. Two models score; if they differ by 2+ points the idea is
flagged.

## 5. Tests before use (rules written first, like phases 2-3)

| Test | Set | Pass rule |
|------|-----|-----------|
| A. Feeling scorer | ~300 competitor Shorts' situations: hits vs normal Shorts of the SAME channels | hits ranked above normals in ≥ 65 % of pairs (AUC ≥ 0.65). If it fails, feeling weight drops to 0.10 and demand gets the rest |
| B. Safety filter | 25 planted unsafe topics (dangerous challenges, self-harm, recent tragedies, accusations, medical advice) + 25 safe controls | catches ≥ 24/25, ≤ 2 false blocks |
| C. Source check | 20 proposed ideas | ≥ 70 % reach a fact-checked script of 110+ words |
| D. Owner check | the first queue of 14 | owner says yes to ≥ 10 |

Caveat (same as phase 2): our own test sets are written by us; add the owner's examples to B.

## 6. Data needed from the owner

1. **Watch list**: confirm Zack D Films, Flippo Explains, WorldMesh3D, Captain Workout, and add 5-15 more "what
   if" / animated Shorts channels you like (handle or link).
2. **Red lines**: subjects you never want (e.g. religion, animals dying, gore level).
3. **Our results**: for every uploaded Short, at 48 hours and 7 days, from YouTube Studio → Analytics: views,
   "Viewed vs swiped away" %, average percentage viewed, subscribers gained. (Later this can be automatic with the
   YouTube Analytics API; it needs a sign-in setup.)
4. **Approval**: daily automatic pick, or you approve the weekly list of 14 first.
5. **Your own ideas**: any topics you want in the first queue (they still go through the gates).

## 7. Cost

YouTube ~100-600 units a week (limit 10,000 a day). AI on Kaggle (~2-4 calls a week for ideas and scores), no
Gemini quota. GitHub ~5 minutes a week.
