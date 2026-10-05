import { useMemo } from "react";
import { RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { fabric, pbrSet, wood } from "../kitchen/textures";

const W = 7.2, D = 6.0, H = 3.0;
const C = {
  wall: "#d5cec2", ceiling: "#e6e0d6", floor: "#d4cab9", walnut: "#5e4028",
  walnutDark: "#2e211a", cream: "#e7dfd1", boucle: "#ded4c5", stone: "#c9bba7",
  rug: "#b9aa94", olive: "#7b7655", black: "#171513", led: "#ffd49a", glass: "#dbe7ea",
  pillowOlive: "#7c7f54", pillowSage: "#9a9c72", knit: "#d9cdb6",
};

type Material = Partial<{ color: string; roughness: number; metalness: number; map: THREE.Texture; bumpMap: THREE.Texture; bumpScale: number; normalMap: THREE.Texture; roughnessMap: THREE.Texture; emissive: string; emissiveIntensity: number; transparent: boolean; opacity: number; clearcoat: number; clearcoatRoughness: number; sheen: number; sheenRoughness: number; sheenColor: string; envMapIntensity: number; side: THREE.Side; toneMapped: boolean }>;
function Box({ p, s, m, cast = true, receive = true }: { p: [number, number, number]; s: [number, number, number]; m: Material; cast?: boolean; receive?: boolean }) {
  return <mesh position={p} castShadow={cast} receiveShadow={receive}><boxGeometry args={s} /><meshPhysicalMaterial {...m} /></mesh>;
}
function RBox({ p, s, r = 0.05, m, cast = true, receive = true, rot }: { p: [number, number, number]; s: [number, number, number]; r?: number; m: Material; cast?: boolean; receive?: boolean; rot?: [number, number, number] }) {
  return <RoundedBox position={p} rotation={rot} args={s} radius={Math.min(r, Math.min(...s) / 2 - 0.001)} smoothness={5} castShadow={cast} receiveShadow={receive}><meshPhysicalMaterial {...m} /></RoundedBox>;
}
function Tex() {
  return useMemo(() => ({ floor: pbrSet("floor", [3, 3]), walnut: pbrSet("wood", [2, 2]), stone: pbrSet("marble", [1, 1]), boucle: fabric(C.boucle, [4, 4]), rug: fabric(C.rug, [5, 4]), detailWood: wood(C.walnut, [2, 2], true) }), []);
}

export default function LivingRoomScene() {
  const tex = Tex();
  return <group>
    <Room tex={tex} />
    <MediaWall tex={tex} />
    <WindowWall />
    <Sectional tex={tex} />
    <ThrowBlanket />
    <CoffeeTable tex={tex} />
    <Rug tex={tex} />
    <AccentChair tex={tex} />
    <SlattedDivider tex={tex} />
    <PottedTree p={[-0.95, 0, -2.35]} h={1.75} />
    <PottedTree p={[1.5, 0, -2.4]} h={1.55} />
    <SideTableLamp tex={tex} />
    <FloorLamp />
    <Decor />
    <Lighting />
  </group>;
}

function Room({ tex }: { tex: ReturnType<typeof Tex> }) {
  const cz = H - 0.18;
  return <group>
    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow><planeGeometry args={[W, D]} /><meshPhysicalMaterial map={tex.floor.map} normalMap={tex.floor.nrm} roughnessMap={tex.floor.rgh} color={C.floor} roughness={0.34} clearcoat={0.4} clearcoatRoughness={0.28} /></mesh>
    <Box p={[0, H / 2, -D / 2]} s={[W, H, 0.05]} m={{ color: C.wall, roughness: 0.94 }} cast={false} />
    <Box p={[-W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: C.wall, roughness: 0.94 }} cast={false} />
    <Box p={[W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: "#cbc0b0", roughness: 0.92 }} cast={false} />
    <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, H, 0]}><planeGeometry args={[W, D]} /><meshStandardMaterial color={C.ceiling} roughness={1} /></mesh>
    {/* dropped-ceiling cove tray */}
    {[[0, cz + 0.09, -2.68, 7.2, 0.18, 0.64], [0, cz + 0.09, 2.68, 7.2, 0.18, 0.64], [-3.28, cz + 0.09, 0, 0.64, 0.18, 4.72], [3.28, cz + 0.09, 0, 0.64, 0.18, 4.72]].map((v, i) => <Box key={i} p={[v[0], v[1], v[2]]} s={[v[3], v[4], v[5]]} m={{ color: C.ceiling, roughness: 1 }} cast={false} />)}
    {[[0, cz - 0.02, -2.37, 6.3, 0.025, 0.02], [0, cz - 0.02, 2.37, 6.3, 0.025, 0.02], [-3.07, cz - 0.02, 0, 0.02, 0.025, 4.7], [3.07, cz - 0.02, 0, 0.02, 0.025, 4.7]].map((v, i) => <Box key={i} p={[v[0], v[1], v[2]]} s={[v[3], v[4], v[5]]} m={{ color: C.led, emissive: C.led, emissiveIntensity: 2.4 }} cast={false} receive={false} />)}
    {[[1.65, 1.6], [-1.6, 1.6], [1.65, -1.6], [-1.6, -1.6], [0, 0.2]].map(([x, z], i) => <group key={i} position={[x, H - 0.01, z]}><mesh rotation={[Math.PI / 2, 0, 0]}><ringGeometry args={[0.05, 0.075, 24]} /><meshStandardMaterial color="#37302a" metalness={0.5} roughness={0.38} side={2} /></mesh><spotLight position={[0, -0.05, 0]} rotation={[-Math.PI / 2, 0, 0]} intensity={6.5} color="#ffe1bc" angle={0.48} penumbra={0.75} distance={4} decay={2} castShadow /></group>)}
    {/* wall-mounted AC unit, upper corner — a quiet realism cue from the reference */}
    <group position={[-2.15, 2.62, -2.9]}><RBox p={[0, 0, 0]} s={[0.92, 0.28, 0.18]} r={0.05} m={{ color: "#f4f1ea", roughness: 0.5 }} cast={false} /><Box p={[0, -0.11, 0.02]} s={[0.86, 0.03, 0.16]} m={{ color: "#cfc8bd", roughness: 0.6 }} cast={false} /></group>
  </group>;
}

function MediaWall({ tex }: { tex: ReturnType<typeof Tex> }) {
  const x = -W / 2 + 0.055;
  return <group>
    {/* dark stone feature panel behind the television */}
    <Box p={[x, 1.48, -0.55]} s={[0.08, 2.72, 3.65]} m={{ color: C.walnutDark, roughness: 0.7 }} cast={false} />
    <RBox p={[x + 0.06, 1.55, -0.55]} s={[0.035, 1.44, 2.32]} r={0.01} m={{ map: tex.stone.map, normalMap: tex.stone.nrm, roughnessMap: tex.stone.rgh, color: "#4c433b", roughness: 0.54 }} cast={false} />
    {/* television screen showing a warm landscape */}
    <RBox p={[x + 0.09, 1.55, -0.55]} s={[0.035, 0.82, 1.48]} r={0.025} m={{ color: "#0b0b0b", roughness: 0.18, clearcoat: 0.7 }} cast={false} />
    <Box p={[x + 0.11, 1.55, -0.55]} s={[0.01, 0.74, 1.38]} m={{ color: "#6a5233", emissive: "#8a6a3f", emissiveIntensity: 0.5, roughness: 0.6 }} cast={false} receive={false} />
    {/* floating walnut console with warm LED under-glow */}
    <Box p={[x + 0.11, 0.25, -0.55]} s={[0.38, 0.38, 3.48]} m={{ map: tex.walnut.map, normalMap: tex.walnut.nrm, roughnessMap: tex.walnut.rgh, color: C.walnut, roughness: 0.46 }} />
    <Box p={[x + 0.31, 0.47, -0.55]} s={[0.02, 0.022, 3.25]} m={{ color: C.led, emissive: C.led, emissiveIntensity: 2.7 }} cast={false} receive={false} />
    <Box p={[x + 0.24, 0.05, -0.55]} s={[0.3, 0.015, 3.3]} m={{ color: C.led, emissive: "#ffb463", emissiveIntensity: 3.4 }} cast={false} receive={false} />
    {/* soundbar */}
    <RBox p={[x + 0.2, 0.86, -0.55]} s={[0.09, 0.07, 1.35]} r={0.02} m={{ color: "#1a1714", roughness: 0.6 }} cast={false} />
    {/* console styling: small plants + stacked vase */}
    <group position={[x + 0.26, 0.45, 0.75]}><mesh castShadow><cylinderGeometry args={[0.085, 0.1, 0.16, 18]} /><meshPhysicalMaterial color="#3f342c" roughness={0.4} /></mesh>{[0, 1, 2, 3].map((i) => <mesh key={i} position={[Math.sin(i * 1.6) * 0.09, 0.16 + i * 0.045, Math.cos(i * 1.6) * 0.07]} rotation={[0, 0, (i - 2) * 0.3]}><boxGeometry args={[0.015, 0.3, 0.045]} /><meshStandardMaterial color={i % 2 ? "#6e7859" : "#4b6043"} roughness={0.9} /></mesh>)}</group>
    <Vase p={[x + 0.26, 0.5, -1.75]} scale={0.7} />
    {/* linear fireplace: a warm focal line under the television */}
    <Box p={[x + 0.105, 0.72, -0.55]} s={[0.06, 0.24, 2.3]} m={{ color: "#0d0b09", roughness: 0.5 }} cast={false} />
    <Box p={[x + 0.14, 0.62, -0.55]} s={[0.05, 0.03, 2.1]} m={{ color: "#2a2320", roughness: 0.9 }} cast={false} />
    <Flames x={x + 0.17} baseY={0.66} z0={-1.55} z1={0.45} count={22} />
    {/* upper floating shelf with led backing, framed art, trailing plant, vases */}
    <group position={[x + 0.12, 2.42, 0.55]}>
      <Box p={[0, 0, 0]} s={[0.28, 0.06, 1.9]} m={{ map: tex.walnut.map, color: C.walnut, roughness: 0.5 }} />
      <Box p={[-0.02, 0.02, 0]} s={[0.02, 0.018, 1.78]} m={{ color: C.led, emissive: "#ffbf78", emissiveIntensity: 3.2 }} cast={false} receive={false} />
      <RBox p={[0.02, 0.28, -0.5]} s={[0.03, 0.42, 0.32]} r={0.005} m={{ color: "#2a231d", roughness: 0.5 }} />
      <Box p={[0.05, 0.28, -0.5]} s={[0.008, 0.34, 0.24]} m={{ color: "#b8b0a2", emissive: "#8a8172", emissiveIntensity: 0.2, roughness: 0.7 }} cast={false} />
      <Vase p={[0.02, 0.19, 0.4]} scale={0.6} />
      {/* trailing pothos over the shelf edge */}
      <mesh position={[0.02, 0.12, 0.72]} castShadow><cylinderGeometry args={[0.07, 0.085, 0.14, 16]} /><meshPhysicalMaterial color="#463a30" roughness={0.4} /></mesh>
      {[0, 1, 2, 3, 4].map((i) => <mesh key={i} position={[0.1, -0.02 - i * 0.06, 0.72 + Math.sin(i) * 0.04]} rotation={[0, 0, 0.4]}><boxGeometry args={[0.02, 0.14, 0.05]} /><meshStandardMaterial color={i % 2 ? "#5f7048" : "#4a5c39"} roughness={0.9} /></mesh>)}
    </group>
    {/* tall recessed niches flanking the panel with picture lights */}
    {[-1.8, 0.7].map((z, i) => <group key={i} position={[x + 0.1, 1.5, z]}><Box p={[0, 0, 0]} s={[0.24, 2.35, 0.68]} m={{ color: "#29231f", roughness: 0.75 }} cast={false} />{[0.72, 0, -0.72].map((y) => <Box key={y} p={[0.025, y, 0]} s={[0.25, 0.025, 0.62]} m={{ color: "#4a3b2e", roughness: 0.6 }} cast={false} />)}<spotLight position={[0.15, 0.98, 0]} rotation={[0, -Math.PI / 2, 0]} intensity={1.5} color="#ffd29b" angle={0.65} penumbra={0.8} distance={1.3} /></group>)}
  </group>;
}

// Layered flame tongues: warm cones with additive-ish emissive so bloom catches them.
function Flames({ x, baseY, z0, z1, count }: { x: number; baseY: number; z0: number; z1: number; count: number }) {
  const flames = useMemo(() => Array.from({ length: count }, (_, i) => {
    const z = z0 + (i / (count - 1)) * (z1 - z0);
    const h = 0.13 + Math.abs(Math.sin(i * 1.7)) * 0.14;
    const r = 0.028 + (i % 3) * 0.006;
    const j = (Math.sin(i * 3.1) * 0.5 + 0.5) * 0.02;
    return { z, h, r, j };
  }), [count, z0, z1]);
  return <group>
    {flames.map((f, i) => <group key={i} position={[x, baseY, f.z]}>
      <mesh position={[f.j, f.h / 2, 0]}><coneGeometry args={[f.r * 1.5, f.h, 10]} /><meshStandardMaterial color="#ff8a3c" emissive="#ff6a1f" emissiveIntensity={4.5} transparent opacity={0.85} toneMapped={false} /></mesh>
      <mesh position={[f.j, f.h * 0.42, 0]}><coneGeometry args={[f.r, f.h * 0.7, 10]} /><meshStandardMaterial color="#ffd98a" emissive="#ffcf6a" emissiveIntensity={7} transparent opacity={0.95} toneMapped={false} /></mesh>
    </group>)}
    <pointLight position={[x + 0.15, baseY + 0.15, (z0 + z1) / 2]} intensity={2.6} color="#ff9a4a" distance={2.6} decay={2} />
  </group>;
}

function WindowWall() {
  const z = -D / 2 + 0.04;
  return <group position={[0, 1.54, z]}>
    {/* golden-hour backdrop glow behind the glazing */}
    <mesh position={[0, -0.2, -0.35]}><planeGeometry args={[4.6, 3.6]} /><meshStandardMaterial color="#ffe6bd" emissive="#ffdca6" emissiveIntensity={1.5} toneMapped={false} /></mesh>
    <mesh position={[0, 0.35, -0.3]}><planeGeometry args={[3.0, 1.8]} /><meshStandardMaterial color="#fff2d8" emissive="#fff0cf" emissiveIntensity={2.4} toneMapped={false} transparent opacity={0.85} /></mesh>
    {/* glazing + mullions */}
    <Box p={[0, 0, 0]} s={[3.55, 2.55, 0.025]} m={{ color: C.glass, roughness: 0.08, transparent: true, opacity: 0.28, metalness: 0.1 }} cast={false} receive={false} />
    {[-1.15, 0, 1.15].map((x) => <Box key={x} p={[x, 0, 0.03]} s={[0.035, 2.62, 0.05]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />)}
    <Box p={[0, 1.32, 0.03]} s={[3.7, 0.05, 0.06]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />
    <Box p={[0, -1.32, 0.03]} s={[3.7, 0.05, 0.06]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />
    {/* floor-length sheer curtains with continuous folds */}
    <SheerCurtain center={-1.75} width={1.55} />
    <SheerCurtain center={1.75} width={1.55} />
    {/* curtain rod */}
    <Box p={[0, 1.42, 0.11]} s={[4.95, 0.045, 0.045]} m={{ color: "#b99d78", roughness: 0.34, metalness: 0.45 }} cast={false} />
    {[-2.4, 2.4].map((x) => <mesh key={x} position={[x, 1.42, 0.11]}><sphereGeometry args={[0.05, 16, 12]} /><meshStandardMaterial color="#b99d78" roughness={0.34} metalness={0.5} /></mesh>)}
  </group>;
}

// Continuous folded sheer built from a displaced plane so it reads as fabric, not slats.
function SheerCurtain({ center, width }: { center: number; width: number }) {
  const geo = useMemo(() => {
    const folds = 7, h = 2.78;
    const g = new THREE.PlaneGeometry(width, h, folds * 6, 10);
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const px = pos.getX(i);
      const t = (px + width / 2) / width;
      pos.setZ(i, Math.sin(t * Math.PI * 2 * folds) * 0.05);
    }
    g.computeVertexNormals();
    return g;
  }, [center, width]);
  return <mesh geometry={geo} position={[center, -0.05, 0.14]} castShadow>
    <meshStandardMaterial color="#f2ece1" emissive="#ffdca8" emissiveIntensity={0.55} roughness={0.95} transparent opacity={0.62} side={THREE.DoubleSide} />
  </mesh>;
}

function Sectional({ tex }: { tex: ReturnType<typeof Tex> }) {
  const mat: Material = { map: tex.boucle.map, bumpMap: tex.boucle.bump, bumpScale: 0.012, color: C.cream, roughness: 0.92, sheen: 0.38, sheenRoughness: 0.72, sheenColor: "#eee6da" };
  // back cushions: slight size + tilt variation so the seat reads lived-in
  const backs = [[-0.2, 0.85, 1.85], [0.85, 0.9, 1.85], [1.85, 0.86, 1.85]] as const;
  return <group>
    <RBox p={[0.95, 0.42, -1.58]} s={[3.8, 0.62, 0.88]} r={0.22} m={mat} />
    <RBox p={[2.38, 0.42, -0.1]} s={[0.95, 0.62, 2.25]} r={0.22} m={mat} />
    <RBox p={[1.0, 0.93, -1.93]} s={[3.65, 0.64, 0.23]} r={0.11} m={mat} />
    <RBox p={[2.82, 0.93, -0.15]} s={[0.23, 0.64, 2.05]} r={0.11} m={mat} />
    {/* seat cushions */}
    {backs.map(([x, , ], i) => <RBox key={i} p={[x, 0.78, -1.58]} s={[0.86 + (i % 2) * 0.05, 0.16, 0.76]} r={0.11} m={{ ...mat, color: i === 1 ? "#ebe4d9" : C.cream }} />)}
    {/* left-arm back cushion for the chaise */}
    <RBox p={[2.02, 0.78, -0.1]} s={[0.72, 0.16, 1.9]} r={0.11} m={mat} />
    {/* throw pillows — varied colour, size, and tilt (olive + sage + cream) */}
    <RBox p={[-0.2, 1.12, -1.32]} s={[0.66, 0.5, 0.16]} r={0.08} rot={[0, 0.1, 0.06]} m={{ ...mat, color: "#e2dacd" }} />
    <RBox p={[0.75, 1.1, -1.33]} s={[0.62, 0.46, 0.16]} r={0.08} rot={[0, -0.08, -0.05]} m={{ ...mat, color: C.pillowOlive, sheen: 0.2 }} />
    <RBox p={[1.72, 1.14, -1.31]} s={[0.7, 0.52, 0.16]} r={0.08} rot={[0, 0.06, 0.08]} m={{ ...mat, color: C.pillowSage }} />
    <RBox p={[2.02, 0.72, 0.72]} s={[0.62, 0.46, 0.16]} r={0.08} rot={[0.12, 0, 0.1]} m={{ ...mat, color: C.pillowOlive }} />
    <RBox p={[2.02, 0.74, -0.28]} s={[0.6, 0.44, 0.16]} r={0.08} rot={[0.1, 0, -0.06]} m={{ ...mat, color: "#d8cfbf" }} />
  </group>;
}

// Chunky knit throw draped over the right arm and cascading toward the seat.
function ThrowBlanket() {
  const m: Material = { color: C.knit, roughness: 0.98, sheen: 0.3, sheenRoughness: 0.85, sheenColor: "#efe6d6" };
  return <group position={[1.85, 0, -0.35]} rotation={[0, -0.15, 0]}>
    <RBox p={[0, 0.86, 0]} s={[0.62, 0.1, 0.7]} r={0.05} m={m} />
    <RBox p={[0.05, 0.7, 0.35]} s={[0.58, 0.09, 0.42]} r={0.05} rot={[0.5, 0, 0]} m={m} />
    <RBox p={[0.08, 0.5, 0.5]} s={[0.55, 0.08, 0.34]} r={0.05} rot={[0.9, 0, 0.05]} m={m} />
    <RBox p={[0.1, 0.3, 0.55]} s={[0.5, 0.07, 0.26]} r={0.04} rot={[1.1, 0, 0.08]} m={m} />
  </group>;
}

function CoffeeTable({ tex }: { tex: ReturnType<typeof Tex> }) {
  return <group position={[0.15, 0, 0.18]}>
    {/* round travertine top on a fluted drum base */}
    <mesh position={[0, 0.4, 0]} castShadow receiveShadow><cylinderGeometry args={[0.72, 0.72, 0.11, 48]} /><meshPhysicalMaterial map={tex.stone.map} normalMap={tex.stone.nrm} roughnessMap={tex.stone.rgh} color="#d3c6b2" roughness={0.34} clearcoat={0.3} /></mesh>
    <mesh position={[0, 0.2, 0]} castShadow><cylinderGeometry args={[0.5, 0.56, 0.32, 48]} /><meshPhysicalMaterial map={tex.stone.map} color="#c9bca6" roughness={0.5} /></mesh>
    {/* fluting */}
    {Array.from({ length: 22 }, (_, i) => { const a = (i / 22) * Math.PI * 2; return <mesh key={i} position={[Math.cos(a) * 0.53, 0.2, Math.sin(a) * 0.53]} rotation={[0, -a, 0]}><boxGeometry args={[0.03, 0.32, 0.05]} /><meshPhysicalMaterial color="#bfb096" roughness={0.55} /></mesh>; })}
    {/* lived-in styling: stacked art books, tray, remote, candle, greenery */}
    <Box p={[0.16, 0.475, 0.05]} s={[0.3, 0.04, 0.2]} m={{ color: "#d8d0c4", roughness: 0.72 }} />
    <Box p={[0.18, 0.515, 0.07]} s={[0.28, 0.04, 0.18]} m={{ color: "#8d7760", roughness: 0.68 }} />
    <mesh position={[-0.22, 0.475, 0.1]}><cylinderGeometry args={[0.19, 0.19, 0.02, 32]} /><meshPhysicalMaterial color="#2a2420" roughness={0.4} metalness={0.3} /></mesh>
    <RBox p={[0.42, 0.48, -0.18]} s={[0.055, 0.025, 0.15]} r={0.012} m={{ color: "#171513", roughness: 0.42 }} />
    <mesh position={[-0.22, 0.505, 0.1]}><cylinderGeometry args={[0.045, 0.05, 0.07, 16]} /><meshPhysicalMaterial color="#e9e1d4" roughness={0.54} clearcoat={0.18} /></mesh>
    <pointLight position={[-0.22, 0.6, 0.1]} intensity={0.3} color="#ffbd70" distance={0.55} decay={2} />
    <Vase p={[0.12, 0.455, 0.0]} greenery />
  </group>;
}

function Rug({ tex }: { tex: ReturnType<typeof Tex> }) { return <RBox p={[0.32, 0.025, 0.12]} s={[4.65, 0.04, 3.28]} r={0.08} m={{ map: tex.rug.map, bumpMap: tex.rug.bump, bumpScale: 0.016, color: C.rug, roughness: 0.96, sheen: 0.36, sheenRoughness: 0.75 }} cast={false} />; }

function AccentChair({ tex }: { tex: ReturnType<typeof Tex> }) {
  const m: Material = { map: tex.boucle.map, bumpMap: tex.boucle.bump, bumpScale: 0.014, color: "#d8cdbc", roughness: 0.95, sheen: 0.42, sheenRoughness: 0.7 };
  // curved boucle swivel chair (barrel form)
  return <group position={[-1.55, 0, 1.15]} rotation={[0, 0.55, 0]}>
    <mesh position={[0, 0.42, 0]} castShadow receiveShadow><cylinderGeometry args={[0.52, 0.48, 0.42, 40]} /><meshPhysicalMaterial {...m} /></mesh>
    <mesh position={[0, 0.5, 0]} scale={[1, 1, 1]} castShadow><torusGeometry args={[0.46, 0.16, 20, 40, Math.PI * 1.15]} /><meshPhysicalMaterial {...m} /></mesh>
    <RBox p={[0, 0.5, 0.02]} s={[0.72, 0.16, 0.7]} r={0.08} m={m} />
    {/* swivel base */}
    <mesh position={[0, 0.05, 0]} castShadow><cylinderGeometry args={[0.28, 0.32, 0.06, 32]} /><meshStandardMaterial color="#2a241f" roughness={0.4} metalness={0.4} /></mesh>
  </group>;
}

function SlattedDivider({ tex }: { tex: ReturnType<typeof Tex> }) {
  const xs = useMemo(() => Array.from({ length: 12 }, (_, i) => -2.86 + i * 0.135), []);
  return <group>
    {/* frame */}
    <Box p={[-1.75, 1.5, 2.18]} s={[2.5, 0.08, 0.28]} m={{ map: tex.walnut.map, color: C.walnut, roughness: 0.5 }} cast={false} />
    {/* vertical slats */}
    {xs.map((x, i) => <Box key={i} p={[x, 1.55, 2.18]} s={[0.06, 2.4, 0.1]} m={{ map: tex.walnut.map, color: C.walnut, roughness: 0.48 }} />)}
    {/* integrated open shelves with LED + styling (from the divider reference) */}
    {[2.32, 1.62, 0.92].map((y, i) => <group key={i}>
      <Box p={[-2.35, y, 2.18]} s={[1.0, 0.05, 0.34]} m={{ map: tex.walnut.map, color: C.walnut, roughness: 0.5 }} />
      <Box p={[-2.35, y + 0.03, 2.05]} s={[0.9, 0.015, 0.02]} m={{ color: C.led, emissive: "#ffbf78", emissiveIntensity: 2.6 }} cast={false} receive={false} />
    </group>)}
    <Vase p={[-2.35, 1.72, 2.2]} scale={0.7} greenery />
    <Vase p={[-2.55, 1.02, 2.2]} scale={0.55} greenery />
    {/* base cabinet */}
    <RBox p={[-2.12, 0.28, 2.18]} s={[1.64, 0.52, 0.5]} r={0.03} m={{ color: "#e5ddce", roughness: 0.6 }} />
    <Box p={[-2.12, 0.28, 2.44]} s={[0.006, 0.06, 0.006]} m={{ color: "#3a322b", roughness: 0.4 }} />
    <Vase p={[-2.55, 0.58, 2.18]} greenery />
  </group>;
}

// Tall potted olive-style tree
function PottedTree({ p, h }: { p: [number, number, number]; h: number }) {
  const leaves = useMemo(() => Array.from({ length: 42 }, (_, i) => {
    const a = i * 2.4, ry = 0.45 + Math.random() * (h - 0.9);
    const rad = 0.28 * (1 - (ry / h) * 0.3) * (0.4 + Math.random() * 0.9);
    return [Math.cos(a) * rad, 0.42 + ry, Math.sin(a) * rad, 0.5 + Math.random() * 0.5] as const;
  }), [h]);
  return <group position={p}>
    <mesh position={[0, 0.24, 0]} castShadow receiveShadow><cylinderGeometry args={[0.19, 0.16, 0.48, 24]} /><meshPhysicalMaterial color="#cabfae" roughness={0.55} /></mesh>
    <mesh position={[0, 0.46, 0]}><cylinderGeometry args={[0.17, 0.17, 0.04, 24]} /><meshStandardMaterial color="#2c2620" roughness={0.9} /></mesh>
    <mesh position={[0.01, 0.42 + (h - 0.42) / 2, 0]} castShadow><cylinderGeometry args={[0.025, 0.04, h - 0.42, 10]} /><meshStandardMaterial color="#5b4a37" roughness={0.85} /></mesh>
    {leaves.map(([x, y, z, s], i) => <mesh key={i} position={[x, y, z]} rotation={[Math.random(), Math.random() * 6, Math.random()]} castShadow><boxGeometry args={[0.11 * s, 0.03, 0.05 * s]} /><meshStandardMaterial color={i % 3 === 0 ? "#8a936a" : i % 3 === 1 ? "#6f7a52" : "#5c6844"} roughness={0.9} /></mesh>)}
  </group>;
}

function SideTableLamp({ tex }: { tex: ReturnType<typeof Tex> }) {
  return <group position={[3.0, 0, 1.7]}>
    {/* round fluted side table */}
    <mesh position={[0, 0.28, 0]} castShadow receiveShadow><cylinderGeometry args={[0.3, 0.3, 0.05, 32]} /><meshPhysicalMaterial map={tex.walnut.map} color={C.walnut} roughness={0.5} /></mesh>
    {Array.from({ length: 16 }, (_, i) => { const a = (i / 16) * Math.PI * 2; return <mesh key={i} position={[Math.cos(a) * 0.24, 0.14, Math.sin(a) * 0.24]}><boxGeometry args={[0.03, 0.28, 0.04]} /><meshStandardMaterial color="#4a3524" roughness={0.6} /></mesh>; })}
    {/* ceramic base + warm drum shade */}
    <mesh position={[0, 0.42, 0]} castShadow><cylinderGeometry args={[0.06, 0.09, 0.22, 24]} /><meshPhysicalMaterial color="#b8a488" roughness={0.5} clearcoat={0.2} /></mesh>
    <mesh position={[0, 0.62, 0]}><cylinderGeometry args={[0.17, 0.2, 0.2, 32, 1, true]} /><meshStandardMaterial color="#f3e7cf" emissive="#ffcf8f" emissiveIntensity={1.6} roughness={0.9} side={THREE.DoubleSide} transparent opacity={0.92} /></mesh>
    <pointLight position={[0, 0.62, 0]} intensity={2.4} color="#ffcd85" distance={3.2} decay={2} />
    {/* candles + bowl */}
    <mesh position={[0.16, 0.33, 0.08]}><cylinderGeometry args={[0.03, 0.032, 0.06, 16]} /><meshStandardMaterial color="#e7ddcb" emissive="#ffb45a" emissiveIntensity={0.5} /></mesh>
  </group>;
}

function FloorLamp() {
  return <group position={[3.15, 0, -1.6]}>
    <mesh position={[0, 0.02, 0]}><cylinderGeometry args={[0.16, 0.18, 0.04, 24]} /><meshStandardMaterial color="#2a241f" roughness={0.5} metalness={0.4} /></mesh>
    <mesh position={[0, 0.85, 0]}><cylinderGeometry args={[0.018, 0.018, 1.7, 12]} /><meshStandardMaterial color="#b99d78" roughness={0.4} metalness={0.5} /></mesh>
    <mesh position={[0, 1.68, 0]}><cylinderGeometry args={[0.19, 0.22, 0.24, 32, 1, true]} /><meshStandardMaterial color="#f3e7cf" emissive="#ffcf8f" emissiveIntensity={1.7} roughness={0.9} side={THREE.DoubleSide} transparent opacity={0.92} /></mesh>
    <pointLight position={[0, 1.62, 0]} intensity={3.2} color="#ffcd85" distance={4} decay={2} />
  </group>;
}

function Vase({ p, scale = 1, greenery = false }: { p: [number, number, number]; scale?: number; greenery?: boolean }) {
  return <group position={p} scale={scale}>
    <mesh castShadow><cylinderGeometry args={[0.1, 0.13, 0.28, 20]} /><meshPhysicalMaterial color="#514339" roughness={0.36} clearcoat={0.25} /></mesh>
    {(greenery ? [0, 1, 2, 3, 4, 5] : [0, 1, 2, 3, 4]).map((i) => <mesh key={i} position={[Math.sin(i * 1.4) * 0.13, 0.3 + i * 0.06, Math.cos(i * 1.4) * 0.1]} rotation={[0, 0, (i - 2) * 0.28]}><boxGeometry args={[0.018, 0.42, 0.055]} /><meshStandardMaterial color={i % 2 ? "#6e7859" : "#4b6043"} roughness={0.9} /></mesh>)}
  </group>;
}

function Decor() { return <group>{[[-2.85, -1.75], [2.92, -2.1]].map(([x, z], i) => <group key={i} position={[x, 0, z]}><Vase p={[0, 0.25, 0]} greenery /><pointLight position={[0, 1.0, 0.2]} intensity={i ? 1.4 : 0.8} color="#ffd19b" distance={2.2} decay={2} /></group>)}</group>; }

function Lighting() { return <group>
  <ambientLight intensity={0.14} color="#fff0da" />
  {/* warm golden key from the window side (evening) */}
  <directionalLight position={[-1.5, 4.2, -3.8]} intensity={1.15} color="#ffd9a0" castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-6} shadow-camera-right={6} shadow-camera-top={6} shadow-camera-bottom={-6} />
  {/* cooler subtle fill from the room side to add depth */}
  <directionalLight position={[3.5, 3.5, 4.0]} intensity={0.32} color="#cfe0f2" />
  <pointLight position={[0, 2.15, -1.5]} intensity={1.4} color="#ffe0b2" distance={7} decay={2} />
  <pointLight position={[0, 1.7, -2.35]} intensity={2.5} color="#ffe8ce" distance={5} decay={2} />
</group>; }
