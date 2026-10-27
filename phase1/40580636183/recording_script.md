# Recording script: How GPS Finds Your Location Using Satellite Timestamps

How to record (about 10 minutes):
- Quiet room, phone about a hand's width from your mouth, same place for every scene.
- One file per scene, named s01, s02, ... (any phone format: m4a, mp3, wav). One file for the whole video also works.
- Read every sentence as written. A small slip is fine; don't skip or change sentences (each one was fact-checked as written).
- If you stumble, record that scene's file again (retakes inside a file stay in the video).
- Upload: GitHub repo -> Add file -> Upload files -> folder voice/<the name I give you>/

## s01 — The passive listener: why GPS satellites do not track you or receive signals from your phone

1. How can your smartphone pinpoint your exact location anywhere on Earth just by receiving silent radio signals?
2. In reality, the Global Positioning System is a completely one-way passive broadcast network.
3. GPS operates independently of telephone or Internet reception.
4. Owned by the United States Space Force, the satellite system is freely accessible to anyone.
5. The constellation consists of at least 24 active satellites arranged across six distinct orbital planes.
6. The first prototype spacecraft went into orbit in 1978 before reaching full operational status in 1995.
7. Each satellite completes two full orbits around Earth during every sidereal day.
8. As they orbit, these satellites continuously broadcast radio signals containing their exact position and precise time.
9. Your phone acts as a silent receiver, quietly catching these incoming radio transmissions from the sky.

## s02 — Turning time into space: how measuring radio travel times reveals your distance from an orbit

1. To figure out your exact location, your device converts time measurements directly into distance measurements.
2. GPS satellites circle the Earth in medium orbit at an altitude of approximately 20,200 kilometres.
3. Radio signals broadcast from these satellites travel through space at the constant speed of light.
4. Crucially, the speed of radio waves is constant and completely independent of the satellite's speed.
5. Each satellite continually broadcasts a pseudorandom sequence of ones and zeros known to the receiver.
6. The transmission message includes a timestamp recording the exact time the signal left the satellite.
7. When your device receives the signal, it records the arrival time using its own internal clock.
8. By subtracting the transmission time from the arrival time, the receiver calculates the signal delay.
9. Multiplying this time value by the speed of light yields a pseudorange rather than an exact distance.
10. Because light moves so fast, a tiny timing offset of just 10 nanoseconds causes a 3 metre distance error.
