# Review: How GPS Knows Where You Are

**Question:** How does a phone determine your exact location on Earth using signals from space without sending any data back?  
**Angle:** Unpacking the common fear that GPS tracks you, revealing that GPS is actually a passive one-way network of ultra-precise floating clocks.  
**Structure:** Myth vs fact coupled with a step by step mechanism breakdown to show how simple time measurement creates global positioning.

Words: 538 · Video: 233.4 s · Visuals: 47 (23 photos, 24 cards)

## Fact-check summary

- Sentences checked: 44, passed first time: 31
- Fixed: 1, dropped: 12, bad source ids: 0, copied 8-word phrases: 11

- FIXED s06.07: ~~Without corrections, this would accumulate into positioning errors of roughly 11 kilometres every day.~~ → Without corrections, errors of roughly 11.4 km per day would accumulate in the position. (passes 11 kilometers instead of 11.4 km)
- DROPPED s01.03: The Global Positioning System is owned by the United States Space Force and operated by Mission Delta 31. ()
- DROPPED s02.05: The orbits are arranged so that at least 6 satellites are always within line of sight from everywhere on the Earth. ()
- DROPPED s02.06: Each satellite acts like a floating radio station that carries an accurate record of its own position and time. ()
- DROPPED s03.02: Each satellite carries very stable atomic clocks that are synchronized with reference clocks on the ground. ()
- DROPPED s03.03: An atomic clock measures time by monitoring the resonant frequency of atoms. ()
- DROPPED s03.04: Since the speed of radio waves is constant and independent of the satellite speed, time delay relates directly to distance. ()
- DROPPED s03.06: Your receiver compares the bit sequence received from the satellite with an internally generated version. ()
- DROPPED s04.02: Trilateration is the use of distances for determining the unknown position coordinates of a point of interest. ()
- DROPPED s05.02: While the satellites carry ultra-precise atomic clocks, your smartphone relies on a cheap internal quartz crystal clock. (smartphone and quartz crystal clock are not mentioned in the passages)
- DROPPED s05.06: At a minimum, four satellites must be in view for the receiver to compute three position coordinates and its clock deviation. ()
- DROPPED s06.02: According to special relativity, the faster an object moves, the slower its time appears to pass. ()
- DROPPED s06.03: The atomic clocks moving at orbital speeds tick more slowly than stationary clocks by a fraction of 8.349 parts in 10 to the 11th. ()

## Script with sources

### The Tracking Myth

- `s01.01` Many people worry that a global satellite network is constantly tracking the live location of their mobile phone.  
  _framing, supported; sources: —_
- `s01.02` You might wonder how your phone determines your exact position on Earth using signals from space without ever sending any data back.  
  _framing, supported; sources: —_
- `s01.04` It is a satellite-based navigation system that provides geolocation and time information to a receiver anywhere near the Earth.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.05` The entire network does not require you to transmit any data to function.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.06` Your device operates completely independently of any telephone or internet reception.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_

### Floating Radio Stations

- `s02.01` To understand how this passive network works, you need to look at the space segment of the system.  
  _framing, supported; sources: —_
- `s02.02` The space segment is composed of 24 to 32 space vehicles orbiting in medium Earth orbit.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.03` These satellites orbit at an altitude of approximately 20,200 kilometres.  
  _fact, supported; sources: [A1.71](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.04` Each vehicle makes two complete orbits each sidereal day, which is about 11 hours and 58 minutes.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.07` The satellites broadcast these vital data points continuously down to the surface of the planet.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_

### Measuring Signal Speed

- `s03.01` How do those radio waves turn into a measurement of distance on your device?  
  _framing, supported; sources: —_
- `s03.05` The time delay between when a satellite transmits a signal and when a receiver gets it is proportional to the distance.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s03.07` Modern electronics can measure this signal offset to within about 10 nanoseconds for the civilian code.  
  _fact, supported; sources: [A4.13](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_

### Combining Distance Spheres

- `s04.01` Once your device calculates the distance to a satellite, it uses that data to narrow down where you could be.  
  _framing, supported; sources: —_
- `s04.03` If you know you are a certain distance from a single satellite, you could be anywhere on a sphere surrounding it.  
  _framing, supported; sources: —_
- `s04.04` Adding a second satellite narrows your possible location down to the circle where two spheres intersect.  
  _framing, supported; sources: —_
- `s04.05` Bringing in a third satellite shrinks the intersection down to just two points in three-dimensional space.  
  _framing, supported; sources: —_
- `s04.06` One of those two points is usually out in space, leaving only a single realistic position on the Earth.  
  _framing, supported; sources: —_

### Correcting Clock Errors

- `s05.01` There is a major catch in this simple geometry that requires an extra step from your receiver.  
  _framing, supported; sources: —_
- `s05.03` That cheap clock has a time offset relative to the true time kept by the satellite network.  
  _fact, supported; sources: [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s05.04` Because of this offset, your device cannot measure true ranges and instead calculates pseudo-ranges.  
  _fact, supported; sources: [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A2.2](https://en.wikipedia.org/wiki/Trilateration?oldid=1347869902)_
- `s05.05` To solve for this extra unknown variable, your receiver must look at more than just three space vehicles.  
  _framing, supported; sources: —_

### The Power of Relativity

- `s06.01` Even with four satellites and good geometry, tiny invisible physics forces threaten to ruin the accuracy of your navigation.  
  _framing, supported; sources: —_
- `s06.04` General relativity also shows that clocks located deeper in a gravitational well tick slower.  
  _fact, supported; sources: [A4.42](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s06.05` Because the satellites are far above the Earth, their clocks run faster by about 45,850 nanoseconds per day due to gravity.  
  _fact, supported; sources: [A4.63](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s06.06` Combined, these relativistic effects cause satellite clocks to gain about 38.6 microseconds every single day.  
  _fact, supported; sources: [A4.47](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s06.07` Without corrections, errors of roughly 11.4 km per day would accumulate in the position.  
  _fact, supported (after fix); sources: [A4.47](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s06.08` Engineers solve this by giving the atomic clocks on board a rate offset prior to launch to keep them perfectly synced.  
  _fact, supported; sources: [A4.48](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_

### Passive Positioning

- `s07.01` So how does GPS know where you are without ever tracking you?  
  _framing, supported; sources: —_
- `s07.02` Your phone simply listens to passive radio signals broadcast by an overhead constellation of ultra-precise floating atomic clocks.  
  _framing, supported; sources: —_
- `s07.03` By measuring the time delay of signals from four separate satellites, your device calculates its exact position locally.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s07.04` No data travels back to space, leaving your location entirely private while guiding you precisely across the world.  
  _framing, supported; sources: —_

## Before you upload (owner checklist)

- [ ] Watch the whole video. Pictures match what is said? No wrong or odd photo?
- [ ] Read the script above. Any sentence that sounds wrong, check its source link.
- [ ] Title and description honest? Edit description.txt as you like.
- [ ] Upload subtitles.srt as English subtitles in YouTube Studio.
- [ ] AI disclosure ('altered or synthetic content'): only needed for realistic AI depictions of real people, places or events. This video uses real photos, charts and a TTS voice, so normally: No.
- [ ] Made for kids: No (general audience explainer).
