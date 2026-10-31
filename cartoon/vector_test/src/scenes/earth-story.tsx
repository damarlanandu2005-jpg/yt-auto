import {
  Circle,
  Layout,
  Line,
  Rect,
  Txt,
  makeScene2D,
} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  waitFor,
} from '@motion-canvas/core';

// A reusable, code-drawn presenter. Coordinates are local to the character.
// Motion Canvas adaptation of the channel's recurring character.
// The main demo uses the astronaut look from cartoon/character.js OUTFITS.
function Stickman(props: {scale?: number; outfit?: 'astronaut' | 'explorer' | 'doctor' | 'diver'}) {
  const outfit = props.outfit ?? 'astronaut';
  const top = outfit === 'explorer' ? '#b8945a' : outfit === 'doctor' ? '#f4f4f6' : outfit === 'diver' ? '#2b2f38' : '#eeeeF2';
  const accent = outfit === 'diver' ? '#e8e8e8' : '#d7dce3';
  return (
    <Layout scale={props.scale ?? 1} width={180} height={390}>
      {/* Backpack sits behind the body. */}
      {#if outfit === 'astronaut'}
        <Rect x={-49} y={8} width={42} height={94} radius={12} fill="#c8cdd4" stroke="#202027" lineWidth={7} />
        <Rect x={-49} y={-12} width={30} height={20} fill="#e6a34c" stroke="#202027" lineWidth={4} />
      {/if}
      {/* Arms and legs: dark outer stroke with a light suit-coloured centre. */}
      <Line points={[[0, -62], [-62, -8]]} stroke="#202027" lineWidth={20} lineCap="round" />
      <Line points={[[0, -62], [-62, -8]]} stroke={top} lineWidth={11} lineCap="round" />
      <Line points={[[0, -62], [62, -8]]} stroke="#202027" lineWidth={20} lineCap="round" />
      <Line points={[[0, -62], [62, -8]]} stroke={top} lineWidth={11} lineCap="round" />
      <Line points={[[0, 62], [-42, 150]]} stroke="#202027" lineWidth={21} lineCap="round" />
      <Line points={[[0, 62], [-42, 150]]} stroke={top} lineWidth={12} lineCap="round" />
      <Line points={[[0, 62], [42, 150]]} stroke="#202027" lineWidth={21} lineCap="round" />
      <Line points={[[0, 62], [42, 150]]} stroke={top} lineWidth={12} lineCap="round" />
      <Rect y={2} width={76} height={125} radius={19} fill={top} stroke="#202027" lineWidth={8} />
      <Rect y={42} width={82} height={13} radius={4} fill="#333943" stroke="#202027" lineWidth={4} />
      <Circle x={0} y={-23} size={10} fill="#e6a34c" stroke="#202027" lineWidth={3} />
      <Circle x={0} y={4} size={8} fill="#79b6d5" stroke="#202027" lineWidth={3} />
      {#if outfit === 'astronaut'}
        <Rect x={0} y={-4} width={18} height={38} radius={4} fill="#d7dce3" stroke="#202027" lineWidth={3} />
        <Circle x={0} y={-145} size={125} fill="#d7dce3" stroke="#202027" lineWidth={7} />
        <Circle y={-145} size={105} fill="#fffdf7" stroke="#202027" lineWidth={8} />
      {:else}
        <Circle y={-145} size={105} fill="#fffdf7" stroke="#202027" lineWidth={9} />
      {/if}
      <Circle x={-20} y={-153} size={9} fill="#202027" />
      <Circle x={20} y={-153} size={9} fill="#202027" />
      <Ellipse y={-126} width={27} height={13} stroke="#202027" lineWidth={4} />
    </Layout>
  );
}

export default makeScene2D(function* (view) {
  view.fill('#f6edda');

  // Background stars and hand-drawn orbital lines.
  for (let i = 0; i < 34; i++) {
    const x = ((i * 173) % 980) - 490;
    const y = ((i * 293) % 1280) - 640;
    view.add(<Circle x={x} y={y - 170} size={i % 5 === 0 ? 8 : 4} fill="#8b8794" opacity={0.5} />);
  }
  view.add(<Circle x={30} y={-250} width={830} height={350} stroke="#c7b9a4" lineWidth={4} opacity={0.7} />);

  const title = createRef<Txt>();
  view.add(
    <Txt
      ref={title}
      y={-760}
      text="WHAT IF EARTH STOPPED?"
      fontFamily="Arial"
      fontSize={60}
      fontWeight={900}
      fill="#202027"
      textAlign="center"
      width={960}
      opacity={0}
    />,
  );

  const earth = createRef<Layout>();
  view.add(
    <Layout ref={earth} x={110} y={-180} scale={0.9}>
      <Circle size={490} fill="#4f91bd" stroke="#202027" lineWidth={10} />
      <Circle x={-70} y={-70} width={150} height={105} fill="#83a96b" stroke="#202027" lineWidth={5} rotation={-25} />
      <Circle x={95} y={55} width={190} height={120} fill="#83a96b" stroke="#202027" lineWidth={5} rotation={28} />
      <Circle x={-130} y={130} width={95} height={60} fill="#83a96b" stroke="#202027" lineWidth={5} rotation={-15} />
      <Circle width={560} height={175} stroke="#d2a45d" lineWidth={8} rotation={-18} opacity={0.75} />
    </Layout>,
  );

  const hero = createRef<Layout>();
  // Presenter is positioned separately from the planet so the visual stays readable.
  view.add(
    <Layout ref={hero} x={-310} y={480} scale={0.85}>
      <Stickman scale={1} outfit="astronaut" />
    </Layout>,
  );

  const rocket = createRef<Layout>();
  view.add(
    <Layout ref={rocket} x={-620} y={250} rotation={-28}>
      <Circle width={62} height={180} fill="#fffdf7" stroke="#202027" lineWidth={8} />
      <Circle y={-30} size={42} fill="#79b6d5" stroke="#202027" lineWidth={6} />
      <Line points={[[-27, 45], [-70, 95], [-22, 82]]} closed fill="#d66b50" stroke="#202027" lineWidth={6} />
      <Line points={[[27, 45], [70, 95], [22, 82]]} closed fill="#d66b50" stroke="#202027" lineWidth={6} />
      <Line points={[[-18, 85], [0, 145], [18, 85]]} closed fill="#e6a34c" stroke="#202027" lineWidth={5} />
    </Layout>,
  );

  const city = createRef<Layout>();
  view.add(
    <Layout ref={city} y={760} opacity={0}>
      {Array.from({length: 8}, (_, i) => (
        <Rect
          x={-470 + i * 135}
          y={-100 - (i % 3) * 38}
          width={105}
          height={220 + (i % 3) * 76}
          fill={i % 2 ? '#c9b6a0' : '#b5a28f'}
          stroke="#202027"
          lineWidth={7}
        />
      ))}
      <Line points={[[-540, 12], [540, 12]]} stroke="#202027" lineWidth={9} />
    </Layout>,
  );

  yield* title().opacity(1, 0.6);
  yield* waitFor(1.2);
  yield* all(
    earth().rotation(360, 5, easeInOutCubic),
    hero().position.x(-230, 1.5),
  );
  yield* waitFor(0.5);
  yield* all(
    rocket().position.x(560, 2.2, easeInOutCubic),
    rocket().position.y(-80, 2.2),
  );
  yield* waitFor(0.4);
  yield* all(
    city().opacity(1, 0.7),
    earth().scale(0.65, 0.7),
    earth().position.y(-390, 0.7),
  );
  yield* waitFor(1.5);
});
