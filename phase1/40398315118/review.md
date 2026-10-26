# Review: How GPS Knows Where You Are Without Tracking You

**Question:** How does a smartphone determine your exact position on Earth using signals from space?  
**Angle:** GPS satellites do not track you or receive any data from your phone; your device is purely a passive listener measuring microscopic time delays from orbiting atomic clocks.  
**Structure:** Step-by-step physical breakdown, moving from space-based satellite constellations down to mathematical trilateration on your phone.

Words: 372 · Video: 177.0 s · Visuals: 38 (7 photos, 31 cards)

## Fact-check summary

- Sentences checked: 65, passed first time: 61
- Fixed: 0, dropped: 4, bad source ids: 0, copied 8-word phrases: 1

- DROPPED s01.02: The surprising reality is that those satellites cannot see you at all. (States a factual claim without any cited passages.)
- DROPPED s01.06: Many people imagine that satellites in space actively monitor, trace, or track private mobile phones. (The cited passage does not mention public beliefs or what people imagine satellites do.)
- DROPPED s04.05: An atomic clock measures time by monitoring the resonant frequency of specific atoms. ()
- DROPPED s04.10: Clocks in orbit experience weaker gravity and travel at high speeds relative to Earth. (The passages mention special and general relativity but do not state that orbiting clocks experience weaker gravity or travel at high speeds relative to Earth.)

## Script with sources

### The Passive Listener Myth

- `s01.01` Have you ever wondered how navigation satellites high above Earth can watch your every step?  
  _framing, supported; sources: —_
- `s01.03` The Global Positioning System does not require your mobile phone to transmit any data.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.04` It operates completely independently of any mobile telephone network or internet connection.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.3](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s01.05` Even if you turn off mobile data, the system still delivers accurate location and time information.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.3](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s01.07` In reality, your mobile phone functions purely as a silent and passive radio receiver.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.69](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.08` The United States Space Force owns the satellite system and operates it through Mission Delta 31.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.09` Although the United States government maintains the constellation, anyone with a receiver can freely access it.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.10` The system was originally created for military use before being opened to civilians across the globe.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.6](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.20](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.11` Civilian access was authorised by President Ronald Reagan after an airliner was tragically shot down in 1983.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.20](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.26](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.12` Early civilian signals were intentionally degraded by a policy known as Selective Availability.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.21](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.13` This deliberate error degraded civilian accuracy to roughly 100 metres until the policy was ended in 2000.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.3](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.21](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.14` Today, modern consumer smartphones can determine a position to within 4.9 metres or even better.  
  _fact, supported; sources: [A1.4](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_

### Constellation of Orbiting Clocks

- `s02.01` To understand how your device knows its place, we must look up into orbit.  
  _framing, supported; sources: —_
- `s02.02` The space segment of GPS consists of between 24 and 32 operational satellites.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.24](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s02.03` These spacecraft circle our planet in what engineers call medium Earth orbit.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.4](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s02.04` Each satellite travels at an altitude of approximately 20,200 kilometres above the surface of the Earth.  
  _fact, supported; sources: [A1.71](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.4](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s02.05` The satellites are arranged across 6 separate orbital planes tilted at approximately 55 degrees to the equator.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.06` Each orbit takes approximately 11 hours and 58 minutes, completing 2 full trips every sidereal day.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.71](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.07` The satellites are not spaced at equal 90-degree intervals along each orbital ring.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.08` Instead, their spacing varies between 30 degrees, 105 degrees, and 120 degrees apart.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.09` This deliberate geometry guarantees that at least 6 satellites remain visible from almost anywhere on Earth.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.10` Day and night, every satellite continually broadcasts radio carrier waves down toward the ground below.  
  _fact, supported; sources: [A1.56](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.69](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.11` The transmission contains a unique pseudorandom code made of ones and zeros that receivers recognise.  
  _fact, supported; sources: [A1.57](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.12` It also broadcasts a continuous data message containing its exact orbital position and the departure time.  
  _fact, supported; sources: [A1.58](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.17](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s02.13` This detailed orbital data is called an ephemeris and allows receivers to pinpoint the satellite.  
  _fact, supported; sources: [A4.16](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107), [A4.17](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_

## Before you upload (owner checklist)

- [ ] Watch the whole video. Pictures match what is said? No wrong or odd photo?
- [ ] Read the script above. Any sentence that sounds wrong, check its source link.
- [ ] Title and description honest? Edit description.txt as you like.
- [ ] Upload subtitles.srt as English subtitles in YouTube Studio.
- [ ] AI disclosure ('altered or synthetic content'): only needed for realistic AI depictions of real people, places or events. This video uses real photos, charts and a TTS voice, so normally: No.
- [ ] Made for kids: No (general audience explainer).
