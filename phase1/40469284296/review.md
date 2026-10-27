# Review: How GPS Finds Your Location Using Satellite Timestamps

**Question:** How can your phone find your exact location on Earth just by listening to the time?  
**Angle:** Most people assume satellites track your phone, but GPS is completely one-way. Your device is a silent receiver calculating geometry from broadcast timestamps, where an error of a microsecond means missing your turn by hundreds of metres.  
**Structure:** Myth-busting into a step-by-step physical reveal: starting with the misconception that satellites watch you, then building up the mathematics of time delay, the sphere intersections, and the vital relativistic time fix.

Words: 900 · Video: 445.0 s · Visuals: 99 (44 photos, 55 cards)

## Fact-check summary

- Sentences checked: 72, passed first time: 52
- Fixed: 8, dropped: 12, bad source ids: 0, copied 8-word phrases: 1

- FIXED s01.05: ~~GPS operates completely independently of cellular phone towers, Wi-Fi networks, and Internet connections.~~ → GPS operates independently of telephone or Internet reception. (The cited passage specifies telephone or Internet reception, not cellular phone towers or Wi-Fi networks.)
- FIXED s02.09: ~~Multiplying this time delay by the speed of light reveals your exact distance from that satellite.~~ → Multiplying this time value by the speed of light yields a pseudorange rather than an exact distance. (Multiplying the time delay by the speed of light yields a pseudo-range (which includes receiver clock error), not the exact distance.)
- FIXED s03.06: ~~These two overlapping spherical shells intersect to form a two-dimensional ring in space.~~ → Taking several distance measurements allows a receiver to find the point where the spherical shells meet. (The cited passage states that measurements place the receiver on spherical shells, but does not mention intersecting into a two-dimensional ring.)
- FIXED s03.07: ~~Your true location must lie somewhere along the outer edge of that intersecting ring.~~ → Your receiver generates a position fix by finding where multiple spherical shells meet. (The cited passage does not mention an intersecting ring or location along its outer edge.)
- FIXED s03.09: ~~The intersection of three spheres narrows your location down to just two specific points in space.~~ → Combining multiple distance measurements allows the receiver to determine the point where the shells meet. (The cited passage does not state that three spheres narrow location down to two specific points.)
- FIXED s04.06: ~~To solve this problem without putting a heavy atomic clock inside your phone, engineers use a fourth signal.~~ → To solve this problem without needing an impractical receiver clock, the system uses signals from a fourth satellite. (The passages state that using four satellites eliminates the need for an impractical receiver clock, but do not mention heavy atomic clocks in phones.)
- FIXED s04.10: ~~The fourth signal fixes your phone's clock offset, turning cheap quartz timing into atomic-level precision.~~ → Solving the navigation equations gives receiver position and clock deviation, providing cheap and highly accurate timing. (The cited passages mention cheap and highly accurate timing, but do not state that quartz timing is turned into atomic-level precision.)
- FIXED s06.06: ~~Your device instantly projects these calculated coordinates onto digital moving map software on your screen.~~ → These calculated coordinates may be displayed on a moving map display or used by another system. (The passage says coordinates may be displayed on a moving map display, but does not state that the device instantly projects them onto software on your screen.)
- DROPPED s01.02: Many people assume that orbiting satellites watch your every step and actively track your mobile device. (This framing sentence makes a factual claim about common assumptions, but has no cited passages.)
- DROPPED s01.04: Your smartphone never transmits any data, signals, or location requests back up into space. (The cited passage states that GPS does not require users to transmit data, but does not state that smartphones never transmit signals back into space.)
- DROPPED s01.12: No satellite ever knows that your device is receiving its signals or where you are located. (The passage states that GPS does not require users to transmit data, but does not explicitly state what satellites know.)
- DROPPED s01.13: All location calculations happen locally inside the small computer processor inside your pocket. (The cited passages state that the receiver computes its position, but do not mention a small computer processor in your pocket.)
- DROPPED s02.10: Extreme accuracy is required for this time calculation to produce useful positioning results. (This framing sentence makes a factual claim about accuracy requirements, but has no cited passages.)
- DROPPED s02.12: A timing error of one microsecond would cause your calculated position to miss by hundreds of metres. (The cited passages mention that a 1 nanosecond error causes a 30 centimetre error, but do not state the effect of a 1 microsecond error.)
- DROPPED s02.13: Calculating location therefore depends entirely on measuring the precise travel time of radio waves. (Position calculation depends primarily on satellite position and signal delay, not entirely on travel time.)
- DROPPED s03.01: Knowing your distance from just one satellite is not enough to pinpoint your exact location. (This framing sentence makes a factual claim about single-satellite distance measurements, but has no cited passages.)
- DROPPED s03.10: Because one point is usually high in outer space, the other point marks your location on Earth. (This framing sentence makes a factual claim about intersection points, but has no cited passages.)
- DROPPED s04.03: However, smartphones use inexpensive quartz crystal oscillators that suffer from timing errors and clock drift. (The passages discuss quartz crystal oscillators in general, but do not mention smartphones or inexpensive components.)
- DROPPED s04.05: Even a tiny clock offset inside your phone would ruin the trilateration geometry completely. (The passages note specific distance errors per nanosecond, but do not state that a timing offset ruins geometry completely.)
- DROPPED s03.04: The satellite constellation is arranged so that at least six satellites are visible from almost anywhere. (reworded: too close to source wording)

## Script with sources

### The passive listener: why GPS satellites do not track you or receive signals from your phone

- `s01.01` How can your smartphone pinpoint your exact location anywhere on Earth just by receiving silent radio signals?  
  _framing, supported; sources: —_
- `s01.03` In reality, the Global Positioning System is a completely one-way passive broadcast network.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.05` GPS operates independently of telephone or Internet reception.  
  _fact, supported (after fix); sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.06` Owned by the United States Space Force, the satellite system is freely accessible to anyone.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.46](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.07` The constellation consists of at least 24 active satellites arranged across six distinct orbital planes.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.08` The first prototype spacecraft went into orbit in 1978 before reaching full operational status in 1995.  
  _fact, supported; sources: [A1.2](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.33](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.09` Each satellite completes two full orbits around Earth during every sidereal day.  
  _fact, supported; sources: [A1.70](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.71](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.10` As they orbit, these satellites continuously broadcast radio signals containing their exact position and precise time.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.56](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.58](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s01.11` Your phone acts as a silent receiver, quietly catching these incoming radio transmissions from the sky.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_

### Turning time into space: how measuring radio travel times reveals your distance from an orbit

- `s02.01` To figure out your exact location, your device converts time measurements directly into distance measurements.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.02` GPS satellites circle the Earth in medium orbit at an altitude of approximately 20,200 kilometres.  
  _fact, supported; sources: [A1.71](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.03` Radio signals broadcast from these satellites travel through space at the constant speed of light.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.04` Crucially, the speed of radio waves is constant and completely independent of the satellite's speed.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.05` Each satellite continually broadcasts a pseudorandom sequence of ones and zeros known to the receiver.  
  _fact, supported; sources: [A1.56](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.57](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.06` The transmission message includes a timestamp recording the exact time the signal left the satellite.  
  _fact, supported; sources: [A1.56](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.58](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.07` When your device receives the signal, it records the arrival time using its own internal clock.  
  _fact, supported; sources: [A1.57](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.08` By subtracting the transmission time from the arrival time, the receiver calculates the signal delay.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.09` Multiplying this time value by the speed of light yields a pseudorange rather than an exact distance.  
  _fact, supported (after fix); sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s02.11` Because light moves so fast, a tiny timing offset of just 10 nanoseconds causes a 3 metre distance error.  
  _fact, supported; sources: [A4.13](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_

### The sphere intersection: using trilateration to narrow your place on Earth to two points

- `s03.02` A single distance measurement places your device somewhere on a giant spherical shell centred on that satellite.  
  _fact, supported; sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.03` To narrow down your location, your phone needs signals from additional satellites orbiting above.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A5.17](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107), [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.05` When you receive a distance measurement from a second satellite, a second sphere is created.  
  _fact, supported; sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.06` Taking several distance measurements allows a receiver to find the point where the spherical shells meet.  
  _fact, supported (after fix); sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.07` Your receiver generates a position fix by finding where multiple spherical shells meet.  
  _fact, supported (after fix); sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.08` Adding a third satellite creates a third spherical surface around that third broadcasting source.  
  _fact, supported; sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.09` Combining multiple distance measurements allows the receiver to determine the point where the shells meet.  
  _fact, supported (after fix); sources: [A5.18](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s03.11` In special cases where elevation is already known, three satellites can determine a position.  
  _fact, supported; sources: [A1.68](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s03.12` This geometric technique of calculating positions using measured distances is known as trilateration.  
  _fact, supported; sources: [A2.1](https://en.wikipedia.org/wiki/Trilateration?oldid=1347869902), [A2.4](https://en.wikipedia.org/wiki/Trilateration?oldid=1347869902)_

### The fourth satellite trick: how an extra signal fixes the cheap quartz clock in your pocket

- `s04.01` Trilateration with three spheres assumes that your receiver clock is perfectly synchronized with the satellites.  
  _fact, supported; sources: [A1.64](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.02` GPS satellites carry extremely stable atomic clocks that are monitored and synchronized regularly by ground stations.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A5.17](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s04.04` Because your phone clock is inaccurate, measured travel times produce biased distances called pseudoranges.  
  _fact, supported; sources: [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A2.2](https://en.wikipedia.org/wiki/Trilateration?oldid=1347869902)_
- `s04.06` To solve this problem without needing an impractical receiver clock, the system uses signals from a fourth satellite.  
  _fact, supported (after fix); sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.67](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.07` Your GPS receiver requires signals from at least four satellites to solve its navigation equations.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.67](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.08` With four satellite signals, your phone calculates four unknown mathematical quantities simultaneously.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.09` These unknowns are three spatial coordinates representing position and the exact deviation of your phone clock.  
  _fact, supported; sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.10` Solving the navigation equations gives receiver position and clock deviation, providing cheap and highly accurate timing.  
  _fact, supported (after fix); sources: [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.67](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s04.11` This clever mathematical approach keeps consumer receivers light, affordable, and practical for daily use.  
  _fact, supported; sources: [A1.64](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.67](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_

### Einstein in orbit: why satellite clocks tick faster and how engineers correct for relativity

- `s05.01` Even with four satellite signals, GPS would fail quickly without accounting for Albert Einstein's theories of relativity.  
  _fact, supported; sources: [A1.7](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.41](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.42](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.02` Special relativity predicts that time passes slower for objects moving at higher speeds relative to an observer.  
  _fact, supported; sources: [A4.41](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.43](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.03` Because satellites travel at roughly 3,874 metres per second, their atomic clocks tick slower.  
  _fact, supported; sources: [A4.43](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.51](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.55](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.04` This speed effect causes orbital clocks to lose about 7.2 microseconds per day compared to ground clocks.  
  _fact, supported; sources: [A4.45](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.55](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.05` Meanwhile, general relativity shows that gravity slows down time closer to massive bodies like Earth.  
  _fact, supported; sources: [A4.42](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.46](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.06` Because satellites operate high above Earth's surface, they experience weaker gravity than receivers on the ground.  
  _fact, supported; sources: [A4.42](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.46](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.59](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.07` This weaker gravity causes satellite clocks to tick faster by about 45.8 microseconds per day.  
  _fact, supported; sources: [A4.46](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.63](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.08` Combining both relativistic effects, satellite clocks run faster by approximately 38.6 microseconds every day.  
  _fact, supported; sources: [A4.47](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.64](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A5.19](https://en.wikipedia.org/wiki/Satellite_navigation?oldid=1380001107)_
- `s05.09` If uncorrected, this timing difference would cause location errors of roughly 11.4 kilometres per day.  
  _fact, supported; sources: [A4.47](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.10` To correct this, engineers pre-adjust the atomic clock frequencies before launching the satellites into space.  
  _fact, supported; sources: [A4.48](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.11` They slow the clock rate from 10.23 megahertz down to 10.22999999543 megahertz.  
  _fact, supported; sources: [A4.48](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056), [A4.67](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_
- `s05.12` This pre-launch adjustment allows orbital clocks to stay synchronized with time on Earth's surface.  
  _fact, supported; sources: [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A4.48](https://en.wikipedia.org/wiki/Error_analysis_for_the_Global_Positioning_System?oldid=1377400056)_

### Mapping the numbers: how raw coordinates turn into a moving blue dot on your screen

- `s06.01` Once your device processes the satellite signals, it calculates raw three-dimensional position coordinates.  
  _fact, supported; sources: [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.02` The receiver then converts these spatial numbers into standard latitude, longitude, and height.  
  _fact, supported; sources: [A1.61](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.03` Consumer devices like smartphones can achieve horizontal positioning accuracy of 4.9 metres or better.  
  _fact, supported; sources: [A1.4](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.04` When paired with assistive services like Wi-Fi positioning, positioning performance becomes even more reliable.  
  _fact, supported; sources: [A1.4](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.05` High-end applications like land surveying can even achieve sub-millimetre accuracy with long-term measurements.  
  _fact, supported; sources: [A1.4](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.06` These calculated coordinates may be displayed on a moving map display or used by another system.  
  _fact, supported (after fix); sources: [A1.61](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.07` An internal tracker algorithm combines successive measurements to predict movement and filter out random errors.  
  _fact, supported; sources: [A1.65](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.08` By analyzing signal Doppler frequency shifts, your device can also calculate your exact velocity and direction.  
  _fact, supported; sources: [A1.66](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.09` More advanced navigation systems combine these satellite data with internal compasses or motion sensors.  
  _fact, supported; sources: [A1.66](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.10` Your phone finds your exact location by listening to broadcast timestamps, measuring radio travel times, and calculating geometry.  
  _fact, supported; sources: [A1.1](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.54](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.55](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.59](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385), [A1.60](https://en.wikipedia.org/wiki/Global_Positioning_System?oldid=1381199385)_
- `s06.11` Next time you follow that blue dot on your screen, consider how orbital geometry and atomic time keeping guide your path.  
  _framing, supported; sources: —_

## Before you upload (owner checklist)

- [ ] Watch the whole video. Pictures match what is said? No wrong or odd photo?
- [ ] Read the script above. Any sentence that sounds wrong, check its source link.
- [ ] Title and description honest? Edit description.txt as you like.
- [ ] Upload subtitles.srt as English subtitles in YouTube Studio.
- [ ] AI disclosure ('altered or synthetic content'): only needed for realistic AI depictions of real people, places or events. This video uses real photos, charts and a TTS voice, so normally: No.
- [ ] Made for kids: No (general audience explainer).
