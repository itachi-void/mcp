import { useMemo } from "react";
import { RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { fabric, pbrSet, wood } from "../kitchen/textures";

const W = 6.0, D = 5.0, H = 3.0;
const C = {
  wall: "#d5cec2", ceiling: "#e6e0d6", floor: "#d4cab9", walnut: "#5e4028",
  walnutDark: "#2e211a", cream: "#e7dfd1", boucle: "#ded4c5", stone: "#cabca6",
  rug: "#b9aa94", olive: "#7b7655", black: "#171513", led: "#ffd49a", brass: "#b99d78",
};

type Material = Partial<{ color: string; roughness: number; metalness: number; map: THREE.Texture; bumpMap: THREE.Texture; bumpScale: number; normalMap: THREE.Texture; roughnessMap: THREE.Texture; emissive: string; emissiveIntensity: number; transparent: boolean; opacity: number; clearcoat: number; clearcoatRoughness: number; sheen: number; sheenRoughness: number; sheenColor: string; envMapIntensity: number; side: THREE.Side; toneMapped: boolean }>;
function Box({ p, s, m, cast = true, receive = true, rot }: { p: [number, number, number]; s: [number, number, number]; m: Material; cast?: boolean; receive?: boolean; rot?: [number, number, number] }) {
  return <mesh position={p} rotation={rot} castShadow={cast} receiveShadow={receive}><boxGeometry args={s} /><meshPhysicalMaterial {...m} /></mesh>;
}
function RBox({ p, s, r = 0.05, m, cast = true, receive = true, rot }: { p: [number, number, number]; s: [number, number, number]; r?: number; m: Material; cast?: boolean; receive?: boolean; rot?: [number, number, number] }) {
  return <RoundedBox position={p} rotation={rot} args={s} radius={Math.min(r, Math.min(...s) / 2 - 0.001)} smoothness={5} castShadow={cast} receiveShadow={receive}><meshPhysicalMaterial {...m} /></RoundedBox>;
}
function Tex() {
  return useMemo(() => ({ floor: pbrSet("floor", [3, 3]), walnut: pbrSet("wood", [2, 2]), stone: pbrSet("marble", [1, 1]), boucle: fabric(C.boucle, [4, 4]), rug: fabric(C.rug, [5, 4]), detailWood: wood(C.walnut, [2, 2], true) }), []);
}

export default function DiningScene() {
  const tex = Tex();
  return <group>
    <Room tex={tex} />
    <FeatureWall tex={tex} />
    <WindowWall />
    <Rug tex={tex} />
    <DiningTable tex={tex} />
    {[[-1.05, 1.05, 0], [0, 1.05, 0], [1.05, 1.05, 0], [-1.05, -1.05, Math.PI], [0, -1.05, Math.PI], [1.05, -1.05, Math.PI]].map(([x, z, ry], i) => <Chair key={i} tex={tex} p={[x, 0, z]} ry={ry} />)}
    <Chandelier />
    <Sideboard tex={tex} />
    <PottedTree p={[2.35, 0, -1.85]} h={1.6} />
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
    {/* recessed tray with warm cove */}
    {[[0, cz + 0.09, -2.18, 6.0, 0.18, 0.6], [0, cz + 0.09, 2.18, 6.0, 0.18, 0.6], [-2.7, cz + 0.09, 0, 0.6, 0.18, 3.8], [2.7, cz + 0.09, 0, 0.6, 0.18, 3.8]].map((v, i) => <Box key={i} p={[v[0], v[1], v[2]]} s={[v[3], v[4], v[5]]} m={{ color: C.ceiling, roughness: 1 }} cast={false} />)}
    {[[0, cz - 0.02, -1.88, 5.2, 0.025, 0.02], [0, cz - 0.02, 1.88, 5.2, 0.025, 0.02], [-2.4, cz - 0.02, 0, 0.02, 0.025, 3.76], [2.4, cz - 0.02, 0, 0.02, 0.025, 3.76]].map((v, i) => <Box key={i} p={[v[0], v[1], v[2]]} s={[v[3], v[4], v[5]]} m={{ color: C.led, emissive: C.led, emissiveIntensity: 2.4 }} cast={false} receive={false} />)}
    {[[1.9, 1.5], [-1.9, 1.5], [1.9, -1.5], [-1.9, -1.5]].map(([x, z], i) => <group key={i} position={[x, H - 0.01, z]}><mesh rotation={[Math.PI / 2, 0, 0]}><ringGeometry args={[0.05, 0.075, 24]} /><meshStandardMaterial color="#37302a" metalness={0.5} roughness={0.38} side={2} /></mesh><spotLight position={[0, -0.05, 0]} rotation={[-Math.PI / 2, 0, 0]} intensity={5.5} color="#ffe1bc" angle={0.5} penumbra={0.78} distance={4} decay={2} castShadow /></group>)}
  </group>;
}

// Left wall: vertical fluted walnut battens with a warm-lit framed artwork.
function FeatureWall({ tex }: { tex: ReturnType<typeof Tex> }) {
  const x = -W / 2 + 0.03;
  const slats = useMemo(() => Array.from({ length: 22 }, (_, i) => -1.75 + i * 0.16), []);
  return <group>
    <Box p={[x, 1.5, 0]} s={[0.04, 2.7, 3.7]} m={{ color: "#4a3728", roughness: 0.6 }} cast={false} />
    {slats.map((z, i) => <Box key={i} p={[x + 0.05, 1.5, z]} s={[0.06, 2.6, 0.09]} m={{ map: tex.walnut.map, normalMap: tex.walnut.nrm, color: C.walnut, roughness: 0.5 }} cast={false} />)}
    {/* framed artwork with picture light */}
    <Box p={[x + 0.12, 1.65, 0]} s={[0.05, 1.35, 0.95]} m={{ color: C.walnutDark, roughness: 0.5 }} />
    <Box p={[x + 0.15, 1.65, 0]} s={[0.015, 1.2, 0.82]} m={{ color: "#8a7f6d", emissive: "#6a6152", emissiveIntensity: 0.25, roughness: 0.7 }} />
    <mesh position={[x + 0.35, 2.42, 0]} rotation={[0, 0, -0.5]}><cylinderGeometry args={[0.03, 0.03, 0.34, 12]} /><meshStandardMaterial color={C.brass} metalness={0.6} roughness={0.35} /></mesh>
    <spotLight position={[x + 0.45, 2.45, 0]} rotation={[0, -Math.PI / 2, 0]} intensity={2.2} color="#ffd7a0" angle={0.6} penumbra={0.85} distance={2.2} />
  </group>;
}

function WindowWall() {
  const z = -D / 2 + 0.04;
  return <group position={[0, 1.54, z]}>
    {/* golden-hour backdrop */}
    <mesh position={[0, -0.2, -0.32]}><planeGeometry args={[4.4, 3.4]} /><meshStandardMaterial color="#ffe6bd" emissive="#ffdca6" emissiveIntensity={1.5} toneMapped={false} /></mesh>
    <mesh position={[0, 0.3, -0.28]}><planeGeometry args={[2.8, 1.7]} /><meshStandardMaterial color="#fff2d8" emissive="#fff0cf" emissiveIntensity={2.3} toneMapped={false} transparent opacity={0.85} /></mesh>
    <Box p={[0, 0, 0]} s={[3.3, 2.5, 0.025]} m={{ color: "#dbe7ea", roughness: 0.08, transparent: true, opacity: 0.28, metalness: 0.1 }} cast={false} receive={false} />
    {[-1.05, 0, 1.05].map((x) => <Box key={x} p={[x, 0, 0.03]} s={[0.035, 2.56, 0.05]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />)}
    <Box p={[0, 1.29, 0.03]} s={[3.45, 0.05, 0.06]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />
    <Box p={[0, -1.29, 0.03]} s={[3.45, 0.05, 0.06]} m={{ color: "#cfc6ba", roughness: 0.42 }} cast={false} />
    <SheerCurtain center={-1.55} width={1.45} />
    <SheerCurtain center={1.55} width={1.45} />
    <Box p={[0, 1.4, 0.11]} s={[4.6, 0.045, 0.045]} m={{ color: C.brass, roughness: 0.34, metalness: 0.45 }} cast={false} />
    {[-2.25, 2.25].map((x) => <mesh key={x} position={[x, 1.4, 0.11]}><sphereGeometry args={[0.05, 16, 12]} /><meshStandardMaterial color={C.brass} roughness={0.34} metalness={0.5} /></mesh>)}
  </group>;
}

function SheerCurtain({ center, width }: { center: number; width: number }) {
  const geo = useMemo(() => {
    const folds = 7, h = 2.74;
    const g = new THREE.PlaneGeometry(width, h, folds * 6, 10);
    const pos = g.attributes.position;
    for (let i = 0; i < pos.count; i++) {
      const px = pos.getX(i); const t = (px + width / 2) / width;
      pos.setZ(i, Math.sin(t * Math.PI * 2 * folds) * 0.05);
    }
    g.computeVertexNormals();
    return g;
  }, [center, width]);
  return <mesh geometry={geo} position={[center, -0.03, 0.14]} castShadow>
    <meshStandardMaterial color="#f2ece1" emissive="#ffdca8" emissiveIntensity={0.55} roughness={0.95} transparent opacity={0.62} side={THREE.DoubleSide} />
  </mesh>;
}

function Rug({ tex }: { tex: ReturnType<typeof Tex> }) { return <RBox p={[0, 0.02, 0]} s={[3.7, 0.03, 3.0]} r={0.06} m={{ map: tex.rug.map, bumpMap: tex.rug.bump, bumpScale: 0.016, color: C.rug, roughness: 0.96, sheen: 0.34, sheenRoughness: 0.75 }} cast={false} />; }

// Oval travertine top on a sculptural fluted pedestal.
function DiningTable({ tex }: { tex: ReturnType<typeof Tex> }) {
  const stone: Material = { map: tex.stone.map, normalMap: tex.stone.nrm, roughnessMap: tex.stone.rgh, color: C.stone, roughness: 0.34, clearcoat: 0.28 };
  return <group>
    <mesh position={[0, 0.75, 0]} scale={[1.55, 1, 1]} castShadow receiveShadow><cylinderGeometry args={[0.85, 0.85, 0.08, 64]} /><meshPhysicalMaterial {...stone} /></mesh>
    <mesh position={[0, 0.4, 0]} scale={[1.15, 1, 1]}><cylinderGeometry args={[0.42, 0.5, 0.62, 48]} /><meshPhysicalMaterial map={tex.stone.map} color="#c2b49c" roughness={0.5} /></mesh>
    {Array.from({ length: 26 }, (_, i) => { const a = (i / 26) * Math.PI * 2; return <mesh key={i} position={[Math.cos(a) * 0.55 * 1.15, 0.4, Math.sin(a) * 0.47]} rotation={[0, -a, 0]}><boxGeometry args={[0.03, 0.62, 0.05]} /><meshPhysicalMaterial color="#bcae94" roughness={0.55} /></mesh>; })}
    <mesh position={[0, 0.11, 0]} scale={[1.2, 1, 1]}><cylinderGeometry args={[0.6, 0.66, 0.06, 48]} /><meshPhysicalMaterial color="#b7a98d" roughness={0.5} /></mesh>
    <Tablescape />
  </group>;
}

// Centerpiece: runner, low bowl with branches, taper candles, plates.
function Tablescape() {
  return <group position={[0, 0.79, 0]}>
    <Box p={[0, 0.005, 0]} s={[2.1, 0.008, 0.42]} m={{ color: "#cfc4b2", roughness: 0.85 }} />
    {/* low bowl + branches */}
    <mesh position={[0, 0.05, 0]}><cylinderGeometry args={[0.16, 0.12, 0.09, 28]} /><meshPhysicalMaterial color="#4b3f35" roughness={0.4} clearcoat={0.2} /></mesh>
    {[0, 1, 2, 3, 4, 5].map((i) => <mesh key={i} position={[Math.sin(i * 1.3) * 0.12, 0.24 + (i % 2) * 0.05, Math.cos(i * 1.3) * 0.08]} rotation={[0, 0, (i - 2.5) * 0.3]}><boxGeometry args={[0.012, 0.36, 0.03]} /><meshStandardMaterial color={i % 2 ? "#7c855f" : "#5c6844"} roughness={0.9} /></mesh>)}
    {/* taper candles */}
    {[-0.62, 0.62].map((x) => <group key={x} position={[x, 0, 0]}><mesh position={[0, 0.02, 0]}><cylinderGeometry args={[0.06, 0.07, 0.04, 20]} /><meshStandardMaterial color={C.brass} metalness={0.6} roughness={0.3} /></mesh><mesh position={[0, 0.14, 0]}><cylinderGeometry args={[0.018, 0.02, 0.22, 16]} /><meshStandardMaterial color="#efe7d7" /></mesh><mesh position={[0, 0.27, 0]}><sphereGeometry args={[0.02, 10, 10]} /><meshStandardMaterial color="#ffcf7a" emissive="#ff9a3c" emissiveIntensity={6} toneMapped={false} /></mesh><pointLight position={[0, 0.3, 0]} intensity={0.4} color="#ffb45a" distance={0.9} decay={2} /></group>)}
    {/* place settings: plates */}
    {[[-1.05, 0.55], [-1.05, -0.55], [0, 0.6], [0, -0.6], [1.05, 0.55], [1.05, -0.55]].map(([x, z], i) => <group key={i} position={[x, 0.01, z]}><mesh><cylinderGeometry args={[0.15, 0.15, 0.012, 32]} /><meshPhysicalMaterial color="#efe9dd" roughness={0.35} clearcoat={0.3} /></mesh><mesh position={[0, 0.012, 0]}><cylinderGeometry args={[0.1, 0.1, 0.014, 32]} /><meshPhysicalMaterial color="#d8cdb8" roughness={0.4} /></mesh></group>)}
  </group>;
}

// Upholstered boucle dining chair with a softly curved back and walnut legs.
function Chair({ tex, p, ry }: { tex: ReturnType<typeof Tex>; p: [number, number, number]; ry: number }) {
  const m: Material = { map: tex.boucle.map, bumpMap: tex.boucle.bump, bumpScale: 0.012, color: C.cream, roughness: 0.92, sheen: 0.36, sheenRoughness: 0.72, sheenColor: "#eee6da" };
  const leg: Material = { map: tex.walnut.map, color: C.walnut, roughness: 0.48 };
  return <group position={p} rotation={[0, ry, 0]}>
    <RBox p={[0, 0.47, 0]} s={[0.5, 0.12, 0.48]} r={0.06} m={m} />
    <mesh position={[0, 0.75, -0.22]} rotation={[0.12, 0, 0]} castShadow><cylinderGeometry args={[0.26, 0.26, 0.56, 32, 1, false, 0, Math.PI]} /><meshPhysicalMaterial {...m} side={THREE.DoubleSide} /></mesh>
    <RBox p={[0, 0.75, -0.24]} s={[0.46, 0.5, 0.12]} r={0.09} m={m} />
    {[[-0.2, -0.2], [0.2, -0.2], [-0.2, 0.2], [0.2, 0.2]].map(([lx, lz], i) => <mesh key={i} position={[lx, 0.2, lz]} castShadow><cylinderGeometry args={[0.022, 0.028, 0.42, 12]} /><meshPhysicalMaterial {...leg} /></mesh>)}
  </group>;
}

// Double-ring suspended chandelier over the table (from the reference).
function Chandelier() {
  return <group position={[0, 0, 0]}>
    {[0, 1].map((i) => <mesh key={i} position={[i * 0.32, 2.28 - i * 0.06, 0]} rotation={[Math.PI / 2, 0, 0]}><torusGeometry args={[0.62 - i * 0.22, 0.035, 20, 60]} /><meshStandardMaterial color="#f6e9cf" emissive="#ffcf8f" emissiveIntensity={2.6} toneMapped={false} /></mesh>)}
    {[-0.5, 0.5].map((x) => <mesh key={x} position={[x, 2.64, 0]}><cylinderGeometry args={[0.004, 0.004, 0.72, 8]} /><meshStandardMaterial color={C.brass} metalness={0.6} roughness={0.3} /></mesh>)}
    <mesh position={[0, 3.0, 0]}><cylinderGeometry args={[0.06, 0.06, 0.03, 20]} /><meshStandardMaterial color={C.brass} metalness={0.6} roughness={0.3} /></mesh>
    <pointLight position={[0, 2.15, 0]} intensity={3.4} color="#ffcd85" distance={5} decay={2} castShadow />
    <pointLight position={[0, 1.55, 0]} intensity={1.2} color="#ffdca0" distance={3} decay={2} />
  </group>;
}

// Floating walnut buffet against the right wall with LED underglow + styling.
function Sideboard({ tex }: { tex: ReturnType<typeof Tex> }) {
  const x = W / 2 - 0.04;
  return <group>
    <Box p={[x - 0.28, 0.68, 0.4]} s={[0.5, 0.62, 2.4]} m={{ map: tex.walnut.map, normalMap: tex.walnut.nrm, roughnessMap: tex.walnut.rgh, color: C.walnut, roughness: 0.46 }} />
    <Box p={[x - 0.28, 0.375, 0.4]} s={[0.42, 0.012, 2.3]} m={{ color: C.led, emissive: "#ffb463", emissiveIntensity: 3.2 }} cast={false} receive={false} />
    {/* seams */}
    {[-0.4, 0.4, 1.2].map((z) => <Box key={z} p={[x - 0.03, 0.68, z]} s={[0.01, 0.6, 0.012]} m={{ color: C.walnutDark, roughness: 0.5 }} />)}
    {/* round mirror above */}
    <mesh position={[x - 0.02, 1.85, 0.4]} rotation={[0, -Math.PI / 2, 0]}><cylinderGeometry args={[0.55, 0.55, 0.04, 48]} /><meshStandardMaterial color="#b7c3c7" metalness={0.9} roughness={0.08} /></mesh>
    <mesh position={[x - 0.04, 1.85, 0.4]} rotation={[0, -Math.PI / 2, 0]}><torusGeometry args={[0.55, 0.03, 16, 60]} /><meshStandardMaterial color={C.brass} metalness={0.6} roughness={0.32} /></mesh>
    {/* styling: pampas vase, stacked bowls, sculpture */}
    <group position={[x - 0.28, 1.0, -0.5]}><mesh castShadow><cylinderGeometry args={[0.11, 0.14, 0.34, 24]} /><meshPhysicalMaterial color="#d8ccb8" roughness={0.5} /></mesh>{[0, 1, 2, 3, 4, 5, 6].map((i) => <mesh key={i} position={[Math.sin(i * 0.9) * 0.1, 0.35 + i * 0.05, Math.cos(i * 0.9) * 0.08]} rotation={[0, 0, (i - 3) * 0.22]}><boxGeometry args={[0.016, 0.42, 0.03]} /><meshStandardMaterial color="#cdbd9c" roughness={0.95} /></mesh>)}</group>
    <mesh position={[x - 0.28, 1.06, 0.5]}><sphereGeometry args={[0.1, 20, 16]} /><meshPhysicalMaterial color="#4b3f35" roughness={0.35} clearcoat={0.3} /></mesh>
    <mesh position={[x - 0.28, 1.05, 1.05]}><cylinderGeometry args={[0.12, 0.12, 0.06, 28]} /><meshPhysicalMaterial color="#e2d8c6" roughness={0.5} /></mesh>
    <pointLight position={[x - 0.5, 1.5, 0.4]} intensity={1.4} color="#ffd6a0" distance={2.6} decay={2} />
  </group>;
}

function PottedTree({ p, h }: { p: [number, number, number]; h: number }) {
  const leaves = useMemo(() => Array.from({ length: 40 }, (_, i) => {
    const a = i * 2.4, ry = 0.45 + Math.random() * (h - 0.9);
    const rad = 0.26 * (1 - (ry / h) * 0.3) * (0.4 + Math.random() * 0.9);
    return [Math.cos(a) * rad, 0.42 + ry, Math.sin(a) * rad, 0.5 + Math.random() * 0.5] as const;
  }), [h]);
  return <group position={p}>
    <mesh position={[0, 0.24, 0]} castShadow receiveShadow><cylinderGeometry args={[0.18, 0.15, 0.48, 24]} /><meshPhysicalMaterial color="#cabfae" roughness={0.55} /></mesh>
    <mesh position={[0, 0.46, 0]}><cylinderGeometry args={[0.16, 0.16, 0.04, 24]} /><meshStandardMaterial color="#2c2620" roughness={0.9} /></mesh>
    <mesh position={[0.01, 0.42 + (h - 0.42) / 2, 0]} castShadow><cylinderGeometry args={[0.025, 0.04, h - 0.42, 10]} /><meshStandardMaterial color="#5b4a37" roughness={0.85} /></mesh>
    {leaves.map(([x, y, z, s], i) => <mesh key={i} position={[x, y, z]} rotation={[Math.random(), Math.random() * 6, Math.random()]} castShadow><boxGeometry args={[0.1 * s, 0.03, 0.05 * s]} /><meshStandardMaterial color={i % 3 === 0 ? "#8a936a" : i % 3 === 1 ? "#6f7a52" : "#5c6844"} roughness={0.9} /></mesh>)}
  </group>;
}

function Lighting() { return <group>
  <ambientLight intensity={0.14} color="#fff0da" />
  <directionalLight position={[-1.2, 4.2, -3.6]} intensity={1.1} color="#ffd9a0" castShadow shadow-mapSize={[2048, 2048]} shadow-camera-left={-6} shadow-camera-right={6} shadow-camera-top={6} shadow-camera-bottom={-6} />
  <directionalLight position={[3.2, 3.4, 3.8]} intensity={0.3} color="#cfe0f2" />
  <pointLight position={[0, 2.2, 0]} intensity={1.2} color="#ffe8ce" distance={6} decay={2} />
</group>; }
