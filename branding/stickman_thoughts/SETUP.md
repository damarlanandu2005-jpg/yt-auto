# Stickman Thoughts: channel setup (29 Oct 2026)

All pictures in this folder are drawn in code with the same character as the videos (`brand.html`,
own work, font: Inter, SIL OFL, rendered into the image). Make them again with
`node cartoon/test/shoot.js "http://127.0.0.1:8766/branding/stickman_thoughts/brand.html?kind=logo" logo.png 800 800`
while `python3 -m http.server 8766 -d .` runs in the repo folder.

| File | Size | Where it goes in YouTube Studio |
| --- | --- | --- |
| `logo.png` | 800 x 800 | Customization → Profile → Picture |
| `banner.png` | 2560 x 1440 | Customization → Profile → Banner image (text sits inside the 1546 x 423 area every device shows) |
| `watermark.png` | 150 x 150 | Customization → Profile → Video watermark (display time: entire video) |
| `thumb.png` | 1280 x 720 | example thumbnail for one video (each video gets its own, made from its own scene) |
| `short.png` | 1080 x 1920 | example Shorts cover for one video (pick a cover in the YouTube app when uploading) |

## Customization → Profile

- **Name:** Stickman Thoughts
- **Handle:** @StickmanThoughts (if taken: @StickmanThoughtsYT or @TheStickmanThoughts)
- **Description** (paste as is; short and easy to keep up to date):

> Big questions. True stories. Simple drawings.
>
> What would happen if...? A stickman finds out. Space, history, the human body, animals, nature and more, each in under a minute.
>
> Facts checked, sources in every description. Voice: text-to-speech.

- **Links:** none for now.
- **Contact info:** your email (optional, for business enquiries).

## Settings → Channel → Basic info

- **Country of residence:** India (it must be your real country: it decides tax and monetisation rules).
- **Keywords:** stickman, explained, what if, what happens if, true story, science, history, curiosity, animation, shorts

## Settings → Channel → Advanced settings

- **Audience:** "No, set this channel as not made for kids". The stories (falling into a black hole, shipwrecks) are for a general audience, not made for children. Be honest here: YouTube checks.
- **Link to Google Ads account:** skip.

## Settings → Upload defaults (saves time on every upload)

| Setting | Value |
| --- | --- |
| Visibility | Private (you switch to Public after watching it on your phone) |
| Category | Education |
| Video language | English |
| Caption certification | This content has never aired on television in the U.S. |
| Licence | Standard YouTube Licence |
| Comments | On, "Hold potentially inappropriate comments for review" |
| Title | leave empty |
| Description | the sources and credits come in each video's description file |
| Tags | stickman, explained, what if |

## For every upload

- **Altered or synthetic content:** "No". Our videos are simple non-realistic drawings with a TTS voice and no realistic people, places or events made by AI, so YouTube's AI label is not required (CLAUDE.md ground rules). If a video ever shows a realistic AI picture of a real person, place or event, answer "Yes".
- **Made for kids:** No.
- Check the video plays correctly on your phone before switching it to Public.

## Settings → Channel → Feature eligibility

- Verify your phone number. This unlocks custom thumbnails, videos longer than 15 minutes and live streams.

## Old video

Video 2 (observable universe) can stay: it is a true "wait, really?" story and fits the new channel.

## If you prefer to make the logo and banner with ChatGPT

ChatGPT's pictures will not match the code-drawn character in the videos exactly. Use them only if you
like them more, and keep the same simple look. Check ChatGPT's image terms first; you are responsible
for the result.

Logo prompt:

> A simple, clean YouTube profile picture, square, 800x800. A classic black-line stickman with a big round
> white head and a thoughtful face (one eyebrow raised, hand on chin), drawn with thick, smooth black lines,
> like a hand-drawn doodle. A white thought bubble above his head with a bold red question mark. Plain warm
> off-white background (#fbf8f1). Flat 2D, no shading, no text, centred so it still looks good cut into a circle.

Banner prompt:

> A simple, clean YouTube channel banner, 2560x1440, plain warm off-white background (#fbf8f1). On the left,
> a black-line stickman with a big round white head thinking, hand on chin, a small thought bubble with a red
> question mark. In the middle, the words "STICKMAN THOUGHTS" in a thick bold black sans-serif font, and
> below it in red: "Big questions. True stories. Simple drawings." Below that, a row of small simple coloured
> doodles: a ship on waves, a ringed planet, a red heart, a yellow lightning bolt, a light bulb, an hourglass.
> Flat 2D, lots of empty space, all text and drawings inside the middle 1546x423 area.
