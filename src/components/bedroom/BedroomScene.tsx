import { useMemo } from "react";
import type { ReactNode } from "react";
import type * as THREE from "three";
import { RoundedBox } from "@react-three/drei";
import { fabric, pbrSet } from "../kitchen/textures";

// ─────────────────────────────────────────────────────────────────────────────
//  MASTER BEDROOM — same photoreal logic/primitives as the kitchen scene.
//  Convention:  x = left(-)/right(+)   y = up   z = back(-)/front-camera(+)
//  Floor at y=0, ceiling at y=H. Back wall z=-D/2, left wall x=-W/2.
// ─────────────────────────────────────────────────────────────────────────────

const C = {
  wall:       "#c8c1b5",
  wallAccent: "#b9ad9a",   // headboard feature wall
  ceiling:    "#d3d0ca",
  walnut:     "#3a2513",   // fluted accent wood
  woodWarm:   "#7a5230",   // furniture wood
  bedBase:    "#6d6459",   // upholstered platform
  headboard:  "#8f8578",   // upholstered headboard (taupe)
  duvet:      "#e7e2d8",   // cream duvet
  sheet:      "#f2eee6",
  pillow:     "#efe9df",
  euroPillow: "#c9b79a",   // accent pillows
  throw:      "#9a7d5a",   // caramel throw
  lumbar:     "#3e4a44",   // deep green lumbar accent
  marble:     "#e8e5df",
  brass:      "#b0894f",
  trim:       "#141210",
  metal:      "#0a0a0a",
  fabricN:    "#8a8079",
  ledWarm:    "#ffcf82",
  ledUnder:   "#ffe0a6",
  lampGlow:   "#ffcd7a",
  green:      "#2c5a2a",
  terracotta: "#b16b42",
  glass:      "#aecadf",
  rug:        "#b8ab96",
};

// Room — identical shell dimensions to the kitchen so the camera framing matches.
const W = 6.6, D = 6.0, H = 2.8;
const BACK_Z = -D / 2;
const LEFT_X = -W / 2;

// ── Textures (same loaders as the kitchen) ───────────────────────────────────
function buildTextures() {
  return {
    floor:  pbrSet("wood",   [4, 4]),      // warm engineered-wood plank floor (real PBR)
    accent: pbrSet("wood",   [1, 3]),      // fluted headboard wall grain (real PBR)
    stone:  pbrSet("marble", [1, 1]),      // nightstand / dresser tops (real PBR)
    metal:  pbrSet("metal",  [2, 2]),      // brass frames / chandelier (real PBR)
    linen:  fabric("#e7e2d8", [3, 3]),     // bedding weave
    uphol:  fabric(C.headboard, [2, 2]),   // headboard / platform weave
  };
}
let _tex: ReturnType<typeof buildTextures> | null = null;
function TEX() {
  if (!_tex) _tex = buildTextures();
  return _tex;
}

// ── material helpers ─────────────────────────────────────────────────────────
type M = Partial<{
  color: string; roughness: number; metalness: number; envMapIntensity: number;
  transparent: boolean; opacity: number; emissive: string; emissiveIntensity: number;
  map: THREE.Texture; bumpMap: THREE.Texture; bumpScale: number;
  normalMap: THREE.Texture; normalScale: THREE.Vector2;
  roughnessMap: THREE.Texture; metalnessMap: THREE.Texture;
  clearcoat: number; clearcoatRoughness: number;
  // sheen — velvet/fabric micro-fibre effect (meshPhysicalMaterial only)
  sheen: number; sheenRoughness: number; sheenColor: string;
}>;

// Always use meshPhysicalMaterial so sheen and clearcoat are always available.
function Box({ p, s, m, cast = true, receive = true }: {
  p: [number, number, number]; s: [number, number, number]; m: M; cast?: boolean; receive?: boolean;
}) {
  return (
    <mesh position={p} castShadow={cast} receiveShadow={receive}>
      <boxGeometry args={s} />
      <meshPhysicalMaterial {...m} />
    </mesh>
  );
}
function RBox({ p, s, m, r = 0.02, cast = true, receive = true }: {
  p: [number, number, number]; s: [number, number, number]; m: M; r?: number; cast?: boolean; receive?: boolean;
}) {
  return (
    <RoundedBox position={p} args={s} radius={Math.min(r, Math.min(...s) / 2 - 0.001)} smoothness={4} castShadow={cast} receiveShadow={receive}>
      <meshPhysicalMaterial {...m} />
    </RoundedBox>
  );
}

export default function BedroomScene() {
  return (
    <group>
      <Room />
      <AccentWall />
      <Bed />
      <Nightstand x={-1.72} />
      <Nightstand x={1.72} />
      <Bench />
      <WardrobeSystem />
      <Rug />
      <ReadingNook />
      <HeadboardArt />
      <Chandelier x={0} z={0.55} />
      <DecorLighting />
      <Lighting />
    </group>
  );
}

// ═══ ROOM ════════════════════════════════════════════════════════════════════
function Room() {
  const drop = 0.2, bord = 0.7, cz = H - drop;
  return (
    <group>
      {/* warm wood plank floor with a soft sheen */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[W, D]} />
        <meshPhysicalMaterial map={TEX().floor.map} roughnessMap={TEX().floor.rgh} normalMap={TEX().floor.nrm}
          color="#c79a6a" roughness={0.55} metalness={0.0} envMapIntensity={1.0}
          clearcoat={0.25} clearcoatRoughness={0.35} />
      </mesh>
      {/* Walls */}
      <Box p={[0, H / 2, -D / 2]} s={[W, H, 0.05]} m={{ color: C.wall, roughness: 0.96 }} cast={false} />
      <Box p={[-W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: C.wall, roughness: 0.96 }} cast={false} />
      <Box p={[W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: C.wall, roughness: 0.96 }} cast={false} />
      {/* Ceiling */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, H, 0]}>
        <planeGeometry args={[W, D]} />
        <meshStandardMaterial color={C.ceiling} roughness={1} />
      </mesh>
      {/* Tray-ceiling cove border */}
      {[
        { p: [0, cz + drop / 2, -D / 2 + bord / 2], s: [W, drop, bord] },
        { p: [0, cz + drop / 2, D / 2 - bord / 2], s: [W, drop, bord] },
        { p: [-W / 2 + bord / 2, cz + drop / 2, 0], s: [bord, drop, D - bord * 2] },
        { p: [W / 2 - bord / 2, cz + drop / 2, 0], s: [bord, drop, D - bord * 2] },
      ].map((b, i) => (
        <Box key={i} p={b.p as [number, number, number]} s={b.s as [number, number, number]} m={{ color: C.ceiling, roughness: 1 }} />
      ))}
      <Box p={[0, cz, 0]} s={[W - bord * 2, 0.04, D - bord * 2]} m={{ color: C.ceiling, roughness: 1 }} cast={false} />
      {/* Warm cove LED around inner tray */}
      {[
        { p: [0, cz - 0.02, -D / 2 + bord - 0.03], s: [W - bord, 0.04, 0.02] },
        { p: [-W / 2 + bord - 0.03, cz - 0.02, 0], s: [0.02, 0.04, D - bord * 2] },
        { p: [W / 2 - bord + 0.03, cz - 0.02, 0], s: [0.02, 0.04, D - bord * 2] },
      ].map((b, i) => (
        <Box key={i} p={b.p as [number, number, number]} s={b.s as [number, number, number]}
          m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 1.5, roughness: 1 }} cast={false} receive={false} />
      ))}
      {/* Recessed downlights */}
      {[[-1.7, -1.4], [1.7, -1.4], [-1.7, 1.2], [1.7, 1.2], [0, 1.6]].map(([x, z], i) => (
        <group key={i} position={[x, H - 0.005, z]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.06, 0.082, 28]} />
            <meshStandardMaterial color="#3a352f" roughness={0.4} metalness={0.5} side={2} />
          </mesh>
          <mesh position={[0, -0.012, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <circleGeometry args={[0.06, 24]} />
            <meshStandardMaterial color="#ffffff" emissive="#fff2da" emissiveIntensity={3.6} roughness={1} toneMapped={false} />
          </mesh>
        </group>
      ))}
      {/* Window on the right wall with sheer curtains */}
      <Window />
      {/* Baseboards */}
      <Box p={[0, 0.05, -D / 2 + 0.06]} s={[W - 0.1, 0.1, 0.02]} m={{ color: "#e0dcd4", roughness: 0.5 }} cast={false} />
      <Box p={[-W / 2 + 0.06, 0.05, 0]} s={[0.02, 0.1, D - 0.1]} m={{ color: "#e0dcd4", roughness: 0.5 }} cast={false} />
    </group>
  );
}

function Window() {
  const x = W / 2 - 0.05, y = 1.5, z = 0.4, ww = 0.06, wwid = 1.8, wh = 1.35;
  return (
    <group position={[x, y, z]}>
      {/* frame */}
      <Box p={[0, 0, 0]} s={[ww + 0.06, wh + 0.14, wwid + 0.14]} m={{ color: "#eae7e1", roughness: 0.4 }} cast={false} />
      {/* bright sky glass */}
      <Box p={[0.02, 0, 0]} s={[0.02, wh, wwid]} m={{ color: "#d7ecfa", emissive: "#e6f3ff", emissiveIntensity: 1.0, roughness: 0.08 }} cast={false} receive={false} />
      {/* muntins */}
      <Box p={[-0.01, 0, 0]} s={[0.05, wh, 0.03]} m={{ color: "#eae7e1", roughness: 0.4 }} cast={false} />
      {/* sheer curtain panels */}
      {[-1, 1].map((sgn) => (
        <Box key={sgn} p={[-0.14, 0.05, sgn * (wwid / 2 + 0.18)]} s={[0.03, wh + 0.5, 0.5]}
          m={{ color: "#f3efe8", transparent: true, opacity: 0.5, roughness: 0.9 }} cast={false} receive={false} />
      ))}
      {/* curtain rod */}
      <mesh position={[-0.16, wh / 2 + 0.32, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.015, 0.015, wwid + 0.7, 12]} />
        <meshStandardMaterial color={C.brass} roughness={0.3} metalness={0.85} envMapIntensity={1.4} />
      </mesh>
    </group>
  );
}

// ═══ HEADBOARD FEATURE WALL (fluted walnut, behind the bed) ═══════════════════
function AccentWall() {
  const z = -D / 2 + 0.03;
  const wWidth = 3.0, wy = H / 2 - 0.15, wh = H - 0.3;
  const slatW = 0.06, gap = 0.03;
  const n = Math.floor(wWidth / (slatW + gap));
  const x0 = -(n - 1) * (slatW + gap) / 2;
  const slats = useMemo(() => Array.from({ length: n }, (_, i) => x0 + i * (slatW + gap)), [n, x0]);
  return (
    <group>
      {/* backing panel */}
      <Box p={[0, wy, z]} s={[wWidth, wh, 0.03]} m={{ color: C.walnut, roughness: 0.6 }} cast={false} />
      {/* vertical fluted slats */}
      {slats.map((sx, i) => (
        <Box key={i} p={[sx, wy, z + 0.04]} s={[slatW, wh, 0.05]}
          m={{ map: TEX().accent.map, normalMap: TEX().accent.nrm, color: "#5a3d20", roughness: 0.55, envMapIntensity: 0.5 }} cast={false} />
      ))}
    </group>
  );
}

// ═══ BED (king, upholstered headboard + layered bedding) ══════════════════════
function Bed() {
  const bw = 2.0, bl = 2.15;          // mattress footprint
  const cz = -D / 2 + 0.12;           // headboard against back wall
  const mattY = 0.55;                 // mattress top height
  const cx = 0;
  const bedFrontZ = cz + 0.18 + bl;   // foot of bed (+z toward camera)
  return (
    <group>
      {/* upholstered headboard (tall, channel-tufted look via seams) */}
      <RBox p={[cx, 1.15, cz]} s={[bw + 0.3, 1.3, 0.14]} r={0.04}
        m={{ map: TEX().uphol.map, bumpMap: TEX().uphol.bump, bumpScale: 0.01, color: C.headboard, roughness: 0.85, envMapIntensity: 0.4, sheen: 0.5, sheenRoughness: 0.7, sheenColor: "#a09589" }} />
      {[-0.75, -0.25, 0.25, 0.75].map((sx) => (
        <Box key={sx} p={[cx + sx, 1.15, cz + 0.075]} s={[0.012, 1.24, 0.02]} m={{ color: "#6f665b", roughness: 0.9 }} cast={false} />
      ))}
      {/* platform base (upholstered), slightly wider than mattress */}
      <RBox p={[cx, 0.22, cz + 0.18 + bl / 2]} s={[bw + 0.24, 0.44, bl + 0.2]} r={0.03}
        m={{ map: TEX().uphol.map, color: C.bedBase, roughness: 0.9, envMapIntensity: 0.3, sheen: 0.35, sheenRoughness: 0.8, sheenColor: "#7a6e65" }} />
      {/* mattress */}
      <RBox p={[cx, mattY - 0.1, cz + 0.18 + bl / 2]} s={[bw, 0.22, bl]} r={0.04}
        m={{ color: C.sheet, roughness: 0.9 }} />
      {/* fitted sheet flat top */}
      <RBox p={[cx, mattY + 0.005, cz + 0.18 + bl / 2 + 0.06]} s={[bw - 0.02, 0.03, bl - 0.1]} r={0.02}
        m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.006, color: C.sheet, roughness: 0.92 }} cast={false} />
      {/* duvet — folded down over lower two-thirds, with a soft turned edge */}
      <RBox p={[cx, mattY + 0.06, cz + 0.18 + bl * 0.62]} s={[bw + 0.06, 0.14, bl * 0.72]} r={0.05}
        m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.012, color: C.duvet, roughness: 0.95, envMapIntensity: 0.25, sheen: 0.45, sheenRoughness: 0.65, sheenColor: "#ede8de" }} />
      {/* folded duvet cuff */}
      <RBox p={[cx, mattY + 0.12, cz + 0.18 + bl * 0.30]} s={[bw + 0.06, 0.1, 0.34]} r={0.05}
        m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.012, color: "#f0ebe1", roughness: 0.95, sheen: 0.4, sheenRoughness: 0.65, sheenColor: "#f0ebe1" }} />
      {/* caramel throw blanket across the foot */}
      <RBox p={[cx, mattY + 0.02, bedFrontZ - 0.28]} s={[bw + 0.04, 0.09, 0.6]} r={0.04}
        m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.02, color: C.throw, roughness: 0.9, sheen: 0.55, sheenRoughness: 0.6, sheenColor: "#b89060" }} />
      {/* pillows: 2 euro shams (standing) + 2 sleeping + 1 lumbar */}
      {[-0.55, 0.55].map((sx) => (
        <RBox key={`e${sx}`} p={[cx + sx, mattY + 0.24, cz + 0.28]} s={[0.62, 0.5, 0.16]} r={0.07}
          m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.012, color: C.euroPillow, roughness: 0.9, sheen: 0.5, sheenRoughness: 0.68, sheenColor: "#c8b48e" }} />
      ))}
      {[-0.52, 0.52].map((sx) => (
        <RBox key={`s${sx}`} p={[cx + sx, mattY + 0.14, cz + 0.5]} s={[0.72, 0.22, 0.4]} r={0.1}
          m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.012, color: C.pillow, roughness: 0.92, sheen: 0.4, sheenRoughness: 0.72, sheenColor: "#efe9df" }} />
      ))}
      <RBox p={[cx, mattY + 0.16, cz + 0.72]} s={[1.0, 0.2, 0.28]} r={0.09}
        m={{ color: C.lumbar, roughness: 0.82, envMapIntensity: 0.3, sheen: 0.65, sheenRoughness: 0.55, sheenColor: "#3e6045" }} />
    </group>
  );
}

// ═══ NIGHTSTAND — modern floating cabinet w/ LED underglow ════════════════════
function Nightstand({ x }: { x: number }) {
  const z = -D / 2 + 0.42;
  const topY = 0.5;                 // wall-mounted floating height
  const w = 0.56, d = 0.42, bh = 0.24;
  return (
    <group>
      {/* floating body (matte walnut veneer) */}
      <RBox p={[x, topY - bh / 2, z]} s={[w, bh, d]} r={0.015}
        m={{ map: TEX().accent.map, normalMap: TEX().accent.nrm, color: C.woodWarm, roughness: 0.45, envMapIntensity: 0.5 }} />
      {/* single push-open drawer reveal line (handleless) */}
      <Box p={[x, topY - bh / 2 + 0.02, z + d / 2 + 0.004]} s={[w * 0.9, 0.006, 0.01]} m={{ color: "#4a3320", roughness: 0.6 }} cast={false} />
      {/* thin stone top */}
      <RBox p={[x, topY + 0.012, z]} s={[w + 0.02, 0.02, d + 0.02]} r={0.005}
        m={{ map: TEX().stone.map, roughnessMap: TEX().stone.rgh, normalMap: TEX().stone.nrm, color: "#ffffff", roughness: 0.5, clearcoat: 0.6, clearcoatRoughness: 0.1 }} />
      {/* warm LED underglow strip beneath the floating box */}
      <Box p={[x, topY - bh - 0.01, z + 0.02]} s={[w * 0.85, 0.015, d * 0.7]}
        m={{ color: C.ledUnder, emissive: C.ledUnder, emissiveIntensity: 1.4, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[x, topY - bh - 0.05, z + 0.05]} intensity={1.2} color="#ffcc88" distance={1.4} decay={2} />
      {/* table lamp */}
      <TableLamp x={x} z={z} y={topY + 0.022} />
      {/* slim book + tray */}
      <Box p={[x + 0.17, topY + 0.05, z + 0.02]} s={[0.16, 0.045, 0.12]} m={{ color: "#33413c", roughness: 0.6 }} />
    </group>
  );
}

function TableLamp({ x, y, z }: { x: number; y: number; z: number }) {
  return (
    <group position={[x - 0.12, y, z - 0.02]}>
      {/* brass base + stem */}
      <mesh position={[0, 0.02, 0]} castShadow>
        <cylinderGeometry args={[0.07, 0.08, 0.03, 24]} />
        <meshStandardMaterial color={C.brass} roughness={0.3} metalness={0.9} envMapIntensity={1.5} />
      </mesh>
      <mesh position={[0, 0.19, 0]} castShadow>
        <cylinderGeometry args={[0.012, 0.014, 0.32, 16]} />
        <meshStandardMaterial color={C.brass} roughness={0.3} metalness={0.9} envMapIntensity={1.5} />
      </mesh>
      {/* linen shade (glows warm from within) */}
      <mesh position={[0, 0.4, 0]} castShadow>
        <cylinderGeometry args={[0.11, 0.14, 0.2, 32, 1, true]} />
        <meshStandardMaterial color="#f2e6cf" emissive={C.lampGlow} emissiveIntensity={0.9} roughness={0.9} side={2} transparent opacity={0.96} />
      </mesh>
      {/* glowing bulb + cap disks */}
      <mesh position={[0, 0.4, 0]}>
        <sphereGeometry args={[0.04, 16, 16]} />
        <meshStandardMaterial color="#fff0d0" emissive="#ffcf82" emissiveIntensity={4.5} roughness={1} toneMapped={false} />
      </mesh>
      <mesh position={[0, 0.5, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.11, 24]} />
        <meshStandardMaterial color="#fff3dc" emissive={C.lampGlow} emissiveIntensity={1.6} roughness={1} />
      </mesh>
      <pointLight position={[0, 0.4, 0]} intensity={3.2} color="#ffbe66" distance={2.4} decay={2} />
    </group>
  );
}

// ═══ BENCH (foot of bed) ══════════════════════════════════════════════════════
function Bench() {
  const z = -D / 2 + 0.12 + 0.18 + 2.15 + 0.28;
  return (
    <group>
      <RBox p={[0, 0.34, z]} s={[1.5, 0.2, 0.5]} r={0.04}
        m={{ map: TEX().uphol.map, bumpMap: TEX().uphol.bump, bumpScale: 0.01, color: C.euroPillow, roughness: 0.85, envMapIntensity: 0.3 }} />
      {/* wood legs */}
      {[[-0.68, -0.2], [0.68, -0.2], [-0.68, 0.2], [0.68, 0.2]].map(([lx, lz], i) => (
        <mesh key={i} position={[lx, 0.12, z + lz]} castShadow>
          <cylinderGeometry args={[0.022, 0.03, 0.24, 12]} />
          <meshStandardMaterial color={C.woodWarm} roughness={0.4} metalness={0.1} />
        </mesh>
      ))}
    </group>
  );
}

// ═══ WARDROBE SYSTEM — glass-front sections FIRST, open shelving LAST.
// Clothes clearly visible through transparent bronze glass.
function WardrobeSystem() {
  const px    = -W / 2 + 0.31;
  const d     = 0.62;
  const uh    = 2.55;
  const front = px + d / 2;

  // LAYOUT — glass wardrobes FIRST (low-z), shelving LAST (high-z)
  const z0 = -0.55;            // left edge
  const z1 = z0 + 0.72;       // glass-1 right  ≈  0.17
  const z2 = z1 + 0.72;       // glass-2 right  ≈  0.89
  const z3 = z2 + 0.74;       // dressing right ≈  1.63
  const z4 = z3 + 0.72;       // glass-3 right  ≈  2.35
  const z5 = z4 + 0.52;       // open-shelf right ≈ 2.87
  const zC  = (z0 + z5) / 2;

  const sc = (a: number, b: number) => (a + b) / 2;
  const sw = (a: number, b: number) => b - a;

  const brass = {
    map: TEX().metal.map, roughnessMap: TEX().metal.rgh, normalMap: TEX().metal.nrm,
    color: C.brass, roughness: 0.22, metalness: 0.90, envMapIntensity: 1.7,
  };
  const walnut: M = {
    map: TEX().accent.map, normalMap: TEX().accent.nrm,
    color: "#3e2610", roughness: 0.55, envMapIntensity: 0.5,
  };
  const bodyDim: M = { color: "#8a8278", roughness: 0.52 };

  // ── transparent glass door ──────────────────────────────────────────────────
  const GlassDoor = ({ zSec, wSec }: { zSec: number; wSec: number }) => (
    <group>
      {/* brass outer frame */}
      <Box p={[front - 0.004, uh / 2, zSec]} s={[0.024, uh - 0.02, wSec - 0.01]}
        m={{ ...brass, color: "#7a6030" }} cast={false} />
      {/* clear bronze glass — transmission so interior is visible */}
      <mesh position={[front + 0.007, uh / 2, zSec]}>
        <boxGeometry args={[0.007, uh - 0.1, wSec - 0.08]} />
        <meshPhysicalMaterial
          color="#d4b870" transparent opacity={0.14}
          roughness={0.03} metalness={0.0}
          transmission={0.86} thickness={0.01}
          envMapIntensity={1.4}
        />
      </mesh>
      {/* brass bar pull */}
      <mesh position={[front + 0.013, uh * 0.5, zSec + wSec / 2 - 0.09]} castShadow>
        <boxGeometry args={[0.009, 0.18, 0.014]} />
        <meshStandardMaterial {...brass} />
      </mesh>
    </group>
  );

  // ── wardrobe interior: hanging rod + clothes + shelves + drawers + LED ──────
  type ClotheDef = { color: string; length?: number; width?: number };
  const WardrobeInterior = ({ zFrom, zTo, items }: {
    zFrom: number; zTo: number;
    items: ClotheDef[];
  }) => {
    const zSec = sc(zFrom, zTo);
    const wSec = sw(zFrom, zTo);
    const rodY  = uh - 0.62;
    const step  = (wSec - 0.18) / Math.max(items.length - 1, 1);
    return (
      <group>
        {/* interior back panel */}
        <Box p={[px - d / 2 + 0.04, uh / 2, zSec]} s={[0.018, uh - 0.04, wSec - 0.04]}
          m={{ color: "#a8a09a", roughness: 0.7 }} cast={false} />
        {/* upper shelf */}
        <Box p={[px - 0.02, uh - 0.26, zSec]} s={[d - 0.06, 0.022, wSec - 0.05]}
          m={{ color: "#c8c0b4", roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.2 }} cast={false} />
        {/* folded items on upper shelf */}
        {[0, 1].map((fi) => (
          <Box key={fi} p={[px - 0.06, uh - 0.15, zFrom + 0.12 + fi * 0.26]}
            s={[d * 0.55, 0.12, 0.22]}
            m={{ color: fi === 0 ? "#e8e2d8" : "#c0b8a8", roughness: 0.88 }} cast={false} />
        ))}
        {/* hanging rod */}
        <mesh position={[px - 0.05, rodY, zSec]} rotation={[0, Math.PI / 2, 0]}>
          <cylinderGeometry args={[0.008, 0.008, wSec - 0.1, 10]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        {/* hanging garments */}
        {items.map(({ color, length = 0.44, width = 0.36 }, hi) => {
          const hz = zFrom + 0.09 + hi * step;
          return (
            <group key={hi} position={[px - 0.05, rodY, hz]}>
              {/* hanger arc */}
              <mesh rotation={[0, Math.PI / 2, 0]}>
                <torusGeometry args={[0.09, 0.005, 8, 20, Math.PI]} />
                <meshStandardMaterial {...brass} />
              </mesh>
              {/* hanger hook */}
              <mesh position={[0, 0.094, 0]}>
                <cylinderGeometry args={[0.004, 0.004, 0.09, 6]} />
                <meshStandardMaterial {...brass} />
              </mesh>
              {/* garment body */}
              <mesh position={[0, -(length / 2) - 0.01, 0]} castShadow>
                <boxGeometry args={[0.016, length, width]} />
                <meshPhysicalMaterial color={color} roughness={0.88}
                  sheen={0.35} sheenRoughness={0.72} sheenColor={color} />
              </mesh>
            </group>
          );
        })}
        {/* lower drawers ×3 */}
        {[0.12, 0.31, 0.50].map((dy, i) => (
          <group key={i}>
            <Box p={[px - 0.01, dy, zSec]} s={[d - 0.06, 0.17, wSec - 0.05]}
              m={{ color: "#cac2b4", roughness: 0.5 }} cast={false} />
            <mesh position={[front - 0.03, dy, zSec]} castShadow>
              <boxGeometry args={[0.01, 0.007, 0.2]} />
              <meshStandardMaterial {...brass} />
            </mesh>
          </group>
        ))}
        {/* LED strip — top, brightly lit so visible through glass */}
        <Box p={[px - 0.05, uh - 0.13, zSec]} s={[0.013, 0.017, wSec - 0.09]}
          m={{ color: "#ffd090", emissive: "#ffd090", emissiveIntensity: 5.5, roughness: 1 }} cast={false} receive={false} />
        <pointLight position={[px - 0.05, uh - 0.3, zSec]} intensity={4.5} color="#ffcf78" distance={2.0} decay={2} />
        {/* LED floor wash */}
        <Box p={[px - d / 2 + 0.07, 0.07, zSec]} s={[0.01, 0.012, wSec - 0.12]}
          m={{ color: "#ffd090", emissive: "#ffd090", emissiveIntensity: 4.0, roughness: 1 }} cast={false} receive={false} />
        <pointLight position={[px - 0.1, 0.2, zSec]} intensity={2.0} color="#ffcf78" distance={1.2} decay={2} />
      </group>
    );
  };

  return (
    <group>
      {/* ══ CARCASS ══ */}
      {/* back panel */}
      <Box p={[px - d / 2 + 0.02, uh / 2, zC]} s={[0.04, uh, z5 - z0]}
        m={{ color: "#b0a898", roughness: 0.65 }} cast={false} />
      {/* top cornice */}
      <RBox p={[px + 0.01, uh + 0.034, zC]} s={[d + 0.05, 0.072, z5 - z0 + 0.06]} r={0.012}
        m={{ color: "#d2cab8", roughness: 0.48, clearcoat: 0.35, clearcoatRoughness: 0.25 }} />
      {/* base plinth */}
      <Box p={[px, 0.042, zC]} s={[d + 0.02, 0.084, z5 - z0 + 0.02]}
        m={{ color: "#c0b8a8", roughness: 0.55 }} cast={false} />
      {/* LED cove on top cornice */}
      <Box p={[front + 0.018, uh + 0.005, zC]} s={[0.012, 0.014, (z5 - z0) * 0.92]}
        m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 2.8, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[front + 0.14, uh + 0.01, zC]} intensity={0.9} color="#ffcf70" distance={4} decay={2} />

      {/* vertical dividers */}
      {[z1, z2, z3, z4].map((zd, i) => (
        <Box key={i} p={[px, uh / 2, zd]} s={[d - 0.02, uh - 0.02, 0.022]} m={bodyDim} cast={false} />
      ))}
      <Box p={[px, uh / 2, z0 - 0.012]} s={[d, uh, 0.024]} m={bodyDim} cast={false} />
      <RBox p={[px - 0.04, uh / 2, z5 + 0.012]} s={[d - 0.1, uh, 0.026]} r={0.02} m={bodyDim} cast={false} />

      {/* ══ GLASS WARDROBE 1 — FIRST (leftmost) ══ */}
      <GlassDoor zSec={sc(z0, z1)} wSec={sw(z0, z1)} />
      <WardrobeInterior zFrom={z0} zTo={z1} items={[
        { color: "#c4b5a0" },
        { color: "#2e2820" },
        { color: "#e8e0d4", length: 0.58 },
        { color: "#6a5540" },
        { color: "#b0a090", length: 0.58 },
      ]} />

      {/* ══ GLASS WARDROBE 2 — second ══ */}
      <GlassDoor zSec={sc(z1, z2)} wSec={sw(z1, z2)} />
      <WardrobeInterior zFrom={z1} zTo={z2} items={[
        { color: "#d8cfc0", length: 0.58 },
        { color: "#1a1612" },
        { color: "#c8b8a0", length: 0.52 },
        { color: "#8a7860", length: 0.48 },
      ]} />

      {/* ══ DRESSING STATION (center) ══ */}
      {/* fluted walnut back panel */}
      {Array.from({ length: 9 }, (_, fi) => {
        const fz = z2 + 0.04 + (fi * (sw(z2, z3) - 0.08)) / 8;
        return (
          <Box key={fi} p={[px - d / 2 + 0.06, uh * 0.55, fz]} s={[0.030, uh * 0.88, 0.036]}
            m={walnut} cast={false} />
        );
      })}
      {/* LED top strip lighting fluted panel */}
      <Box p={[px - d / 2 + 0.07, uh * 0.97, sc(z2, z3)]} s={[0.012, 0.016, sw(z2, z3) - 0.08]}
        m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 5.5, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[px - 0.01, uh * 0.88, sc(z2, z3)]} intensity={3.5} color="#ffdd90" distance={1.6} decay={2} />
      {/* floor uplighter */}
      <Box p={[px - d / 2 + 0.07, 0.07, sc(z2, z3)]} s={[0.01, 0.012, sw(z2, z3) - 0.1]}
        m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 4.0, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[px - 0.04, 0.22, sc(z2, z3)]} intensity={2.5} color="#ffcf70" distance={1.2} decay={2} />
      {/* dressing chest base (2 drawers) */}
      <RBox p={[px - 0.01, 0.40, sc(z2, z3)]} s={[d - 0.05, 0.76, sw(z2, z3) - 0.04]} r={0.012}
        m={{ color: "#cec7ba", roughness: 0.48, clearcoat: 0.28, clearcoatRoughness: 0.2 }} />
      {[-0.17, 0.17].map((dy, i) => (
        <group key={i}>
          <Box p={[front - 0.01, 0.40 + dy, sc(z2, z3)]} s={[0.012, 0.005, sw(z2, z3) - 0.14]}
            m={{ color: "#8a8278", roughness: 0.7 }} cast={false} />
          <mesh position={[front + 0.01, 0.40 + dy, sc(z2, z3)]} castShadow>
            <boxGeometry args={[0.012, 0.009, 0.24]} />
            <meshStandardMaterial {...brass} />
          </mesh>
        </group>
      ))}
      {/* desk top */}
      <RBox p={[px + 0.01, 0.80, sc(z2, z3)]} s={[d, 0.04, sw(z2, z3)]} r={0.008}
        m={{ color: "#d6cfca", roughness: 0.35, clearcoat: 0.55, clearcoatRoughness: 0.12 }} />
      {/* cosmetics tray */}
      <Box p={[px + 0.06, 0.824, sc(z2, z3) - 0.2]} s={[0.24, 0.018, 0.22]}
        m={{ map: TEX().metal.map, color: C.brass, roughness: 0.25, metalness: 0.88, envMapIntensity: 1.3 }} />
      {([["#e4c8d2", 0.12], ["#ccddd8", 0.14], ["#f0deb8", 0.10]] as [string, number][]).map(([col, bh], i) => (
        <mesh key={i} position={[px + 0.06 - 0.07 + i * 0.07, 0.824 + bh / 2, sc(z2, z3) - 0.2]} castShadow>
          <boxGeometry args={[0.038, bh, 0.038]} />
          <meshPhysicalMaterial color={col} roughness={0.04} transmission={0.74} thickness={0.04} transparent opacity={0.88} />
        </mesh>
      ))}
      {/* dark vase + plant */}
      <mesh position={[px + 0.04, 0.98, sc(z2, z3) + 0.22]} castShadow>
        <cylinderGeometry args={[0.038, 0.048, 0.22, 14]} />
        <meshPhysicalMaterial color="#141210" roughness={0.12} metalness={0.08} />
      </mesh>
      {[0, 1, 2].map((pi) => (
        <mesh key={pi} position={[px + 0.04 + Math.sin(pi * 2.1) * 0.04, 1.08, sc(z2, z3) + 0.22 + Math.cos(pi * 2.1) * 0.04]}>
          <sphereGeometry args={[0.028, 6, 4]} />
          <meshPhysicalMaterial color="#2e5226" roughness={0.9} />
        </mesh>
      ))}
      {/* OVAL LED MIRROR — faces +x into the room */}
      <group position={[front - 0.016, 1.48, sc(z2, z3)]} rotation={[0, Math.PI / 2, 0]}>
        <mesh castShadow scale={[1, 1.42, 1]}>
          <torusGeometry args={[0.30, 0.025, 22, 72]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        <mesh scale={[1, 1.42, 1]}>
          <torusGeometry args={[0.276, 0.015, 14, 72]} />
          <meshStandardMaterial color="#fffbf0" emissive="#ffe090" emissiveIntensity={4.5} roughness={1} toneMapped={false} />
        </mesh>
        <mesh position={[0, 0, -0.016]} scale={[1, 1.42, 1]}>
          <circleGeometry args={[0.258, 64]} />
          <meshStandardMaterial color="#9ab5c8" roughness={0.012} metalness={0.97} envMapIntensity={3.5} />
        </mesh>
        <pointLight position={[0, 0, 0.18]} intensity={2.2} color="#ffd060" distance={2.2} decay={2} />
      </group>

      {/* ══ GLASS WARDROBE 3 — right of dressing ══ */}
      <GlassDoor zSec={sc(z3, z4)} wSec={sw(z3, z4)} />
      <WardrobeInterior zFrom={z3} zTo={z4} items={[
        { color: "#e8ddd0", length: 0.54 },
        { color: "#b0a898" },
        { color: "#d4c8b8", length: 0.58 },
        { color: "#786858" },
      ]} />

      {/* ══ OPEN SHELVING — LAST (rightmost) ══ */}
      {/* interior back panel */}
      <Box p={[px - d / 2 + 0.04, uh / 2, sc(z4, z5)]} s={[0.02, uh - 0.04, sw(z4, z5) - 0.04]}
        m={{ color: "#a4a09a", roughness: 0.65 }} cast={false} />
      {[0.52, 1.06, 1.60, 2.10].map((sy, i) => (
        <group key={i}>
          <Box p={[px - 0.02, sy, sc(z4, z5)]} s={[d - 0.06, 0.022, sw(z4, z5) - 0.04]}
            m={{ color: "#d0c9bc", roughness: 0.45, clearcoat: 0.35, clearcoatRoughness: 0.18 }} cast={false} />
          <Box p={[front - 0.06, sy - 0.018, sc(z4, z5)]} s={[0.012, 0.014, sw(z4, z5) - 0.1]}
            m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 4.5, roughness: 1 }} cast={false} receive={false} />
        </group>
      ))}
      {/* hanging plant on top shelf */}
      <group position={[px - 0.01, 2.16, sc(z4, z5) - 0.06]}>
        <mesh><cylinderGeometry args={[0.05, 0.055, 0.1, 12]} /><meshPhysicalMaterial color="#5c7c5a" roughness={0.8} /></mesh>
        {[0, 1, 2, 3, 4].map((j) => (
          <mesh key={j} position={[Math.sin(j * 1.26) * 0.08, 0.07 + j * 0.02, Math.cos(j * 1.26) * 0.08]}>
            <sphereGeometry args={[0.032, 6, 4]} /><meshPhysicalMaterial color="#2e5c2a" roughness={0.9} />
          </mesh>
        ))}
      </group>
      {/* handbag on mid shelf */}
      <RBox p={[px - 0.01, 1.22, sc(z4, z5) + 0.02]} s={[0.08, 0.2, 0.17]} r={0.025}
        m={{ color: "#c8b48a", roughness: 0.55, clearcoat: 0.25 }} />
      {/* framed art on lower shelf */}
      <Box p={[px + 0.01, 0.70, sc(z4, z5)]} s={[0.04, 0.19, 0.14]}
        m={{ color: "#ddd6ca", roughness: 0.28, clearcoat: 0.5, clearcoatRoughness: 0.1 }} />
      {/* gold torus decor */}
      <mesh position={[px + 0.02, 0.57, sc(z4, z5) + 0.1]} castShadow>
        <torusGeometry args={[0.045, 0.012, 10, 24]} />
        <meshStandardMaterial {...brass} />
      </mesh>

      {/* ══ VELVET STOOL with gold ring base ══ */}
      <group position={[front + 0.52, 0, sc(z2, z3)]}>
        <mesh position={[0, 0.46, 0]} castShadow>
          <cylinderGeometry args={[0.24, 0.22, 0.14, 32]} />
          <meshPhysicalMaterial map={TEX().uphol.map} bumpMap={TEX().uphol.bump} bumpScale={0.014}
            color="#d8d0c2" roughness={0.86} envMapIntensity={0.25}
            sheen={0.65} sheenRoughness={0.58} sheenColor="#c5baa8" />
        </mesh>
        {Array.from({ length: 8 }, (_, ri) => (
          <mesh key={ri} position={[Math.sin(ri * Math.PI / 4) * 0.2, 0.46, Math.cos(ri * Math.PI / 4) * 0.2]}>
            <boxGeometry args={[0.01, 0.14, 0.01]} />
            <meshPhysicalMaterial color="#c8bfb0" roughness={0.9} />
          </mesh>
        ))}
        <mesh position={[0, 0.21, 0]}>
          <torusGeometry args={[0.2, 0.02, 12, 40]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        <mesh position={[0, 0.12, 0]}>
          <cylinderGeometry args={[0.018, 0.018, 0.22, 10]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        <mesh position={[0, 0.014, 0]}>
          <cylinderGeometry args={[0.2, 0.2, 0.028, 32]} />
          <meshStandardMaterial {...brass} />
        </mesh>
      </group>
    </group>
  );
}

// ═══ READING NOOK — accent armchair + arc floor lamp + side table ══════════════
function ReadingNook() {
  const x = 2.15, z = 1.85;
  const seatY = 0.42;
  const uphol = { map: TEX().uphol.map, bumpMap: TEX().uphol.bump, bumpScale: 0.01, color: "#6f7a6b", roughness: 0.85, envMapIntensity: 0.3 } as unknown as M;
  const brass = { map: TEX().metal.map, roughnessMap: TEX().metal.rgh, color: C.brass, roughness: 0.3, metalness: 0.95, envMapIntensity: 1.6 };
  return (
    <group position={[x, 0, z]} rotation={[0, -Math.PI / 4, 0]}>
      {/* armchair */}
      <RBox p={[0, seatY, 0]} s={[0.66, 0.16, 0.62]} r={0.06} m={uphol} />
      <RBox p={[0, seatY + 0.32, -0.28]} s={[0.66, 0.6, 0.14]} r={0.07} m={uphol} />
      {[-0.33, 0.33].map((ax) => (
        <RBox key={ax} p={[ax, seatY + 0.14, 0]} s={[0.12, 0.32, 0.6]} r={0.05} m={uphol} />
      ))}
      {/* wood legs */}
      {[[-0.26, -0.24], [0.26, -0.24], [-0.26, 0.24], [0.26, 0.24]].map(([lx, lz], i) => (
        <mesh key={i} position={[lx, 0.17, lz]} castShadow>
          <cylinderGeometry args={[0.02, 0.026, 0.34, 10]} />
          <meshStandardMaterial color={C.woodWarm} roughness={0.4} />
        </mesh>
      ))}
      {/* throw cushion */}
      <RBox p={[0.05, seatY + 0.14, 0.02]} s={[0.34, 0.14, 0.3]} r={0.06} m={{ color: C.throw, roughness: 0.9 }} />
      {/* arc floor lamp reaching over the chair */}
      <group position={[0.55, 0, -0.1]}>
        <mesh position={[0, 0.02, 0]} castShadow>
          <cylinderGeometry args={[0.13, 0.15, 0.03, 24]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        <mesh position={[0, 0.9, 0]} castShadow>
          <cylinderGeometry args={[0.014, 0.014, 1.8, 12]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        {/* curved arm */}
        <mesh position={[-0.3, 1.78, 0]} rotation={[0, 0, Math.PI / 2]}>
          <torusGeometry args={[0.32, 0.014, 10, 24, Math.PI / 2]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        {/* dome shade + glow */}
        <mesh position={[-0.62, 1.66, 0]} castShadow>
          <sphereGeometry args={[0.13, 24, 16, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2]} />
          <meshStandardMaterial {...brass} side={2} />
        </mesh>
        <mesh position={[-0.62, 1.6, 0]}>
          <sphereGeometry args={[0.06, 16, 16]} />
          <meshStandardMaterial color="#fff0cf" emissive="#ffcf82" emissiveIntensity={4.5} roughness={1} toneMapped={false} />
        </mesh>
        <pointLight position={[-0.62, 1.55, 0]} intensity={4} color="#ffbe66" distance={3} decay={2} />
      </group>
      {/* round marble side table */}
      <group position={[-0.6, 0, 0.15]}>
        <mesh position={[0, 0.48, 0]} castShadow>
          <cylinderGeometry args={[0.22, 0.22, 0.04, 32]} />
          <meshPhysicalMaterial map={TEX().stone.map} roughnessMap={TEX().stone.rgh} color="#ffffff" roughness={0.5} clearcoat={0.6} clearcoatRoughness={0.1} />
        </mesh>
        <mesh position={[0, 0.24, 0]} castShadow>
          <cylinderGeometry args={[0.02, 0.02, 0.48, 12]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        <mesh position={[0, 0.02, 0]}>
          <cylinderGeometry args={[0.16, 0.16, 0.02, 20]} />
          <meshStandardMaterial {...brass} />
        </mesh>
        {/* coffee mug */}
        <mesh position={[0.05, 0.52, 0.03]} castShadow>
          <cylinderGeometry args={[0.035, 0.03, 0.06, 18]} />
          <meshStandardMaterial color="#efe9df" roughness={0.4} />
        </mesh>
      </group>
    </group>
  );
}

// ═══ HEADBOARD ART — wide framed piece on the accent wall ══════════════════════
function HeadboardArt() {
  const z = -D / 2 + 0.11;
  return (
    <group position={[0, 2.2, z]}>
      {/* frame */}
      <Box p={[0, 0, 0]} s={[1.5, 0.5, 0.03]} m={{ map: TEX().metal.map, color: "#2a2622", roughness: 0.5, metalness: 0.7, envMapIntensity: 1.0 }} cast={false} />
      {/* abstract canvas: warm earth-tone bands */}
      <Box p={[0, 0, 0.02]} s={[1.4, 0.42, 0.01]} m={{ color: "#d8c7a8", roughness: 0.85 }} cast={false} />
      <Box p={[-0.35, -0.05, 0.03]} s={[0.55, 0.28, 0.008]} m={{ color: "#a9743f", roughness: 0.8 }} cast={false} />
      <Box p={[0.3, 0.06, 0.03]} s={[0.6, 0.18, 0.008]} m={{ color: "#5c6b57", roughness: 0.8 }} cast={false} />
      <Box p={[0.12, -0.1, 0.035]} s={[0.3, 0.12, 0.008]} m={{ color: "#3a3733", roughness: 0.8 }} cast={false} />
    </group>
  );
}

// ═══ RUG ══════════════════════════════════════════════════════════════════════
function Rug() {
  const z = -D / 2 + 0.12 + 0.18 + 1.2;
  return (
    <group>
      <Box p={[0, 0.006, z]} s={[3.4, 0.012, 2.8]} m={{ map: TEX().linen.map, bumpMap: TEX().linen.bump, bumpScale: 0.004, color: C.rug, roughness: 0.98, sheen: 0.7, sheenRoughness: 0.5, sheenColor: "#c8bca6" }} receive cast={false} />
      {/* border stripe */}
      <Box p={[0, 0.008, z]} s={[3.1, 0.012, 2.5]} m={{ color: "#c8bda8", roughness: 0.98 }} cast={false} />
    </group>
  );
}

// ═══ CHANDELIER (نجف) — brass tiered frame + glass crystals + candle bulbs ═════
function Chandelier({ x, z }: { x: number; z: number }) {
  const top = H - 0.03;
  const bodyY = top - 0.62;           // main frame height
  const rTop = 0.42, rBot = 0.28;
  const brass = {
    map: TEX().metal.map, roughnessMap: TEX().metal.rgh, normalMap: TEX().metal.nrm,
    color: C.brass, roughness: 0.3, metalness: 0.95, envMapIntensity: 1.8,
  };
  // real refractive glass crystal
  const crystal = {
    color: "#ffffff", roughness: 0.02, metalness: 0.0, transmission: 1.0, ior: 1.5,
    thickness: 0.05, transparent: true, opacity: 0.55, envMapIntensity: 2.2,
    emissive: "#fff2d6", emissiveIntensity: 0.35,
  } as unknown as M;
  const candles = 8, upperStrands = 12;
  const candleAng = Array.from({ length: candles }, (_, i) => (i / candles) * Math.PI * 2);
  const strandAng = Array.from({ length: upperStrands }, (_, i) => (i / upperStrands) * Math.PI * 2);
  return (
    <group position={[x, 0, z]}>
      {/* canopy + drop rod */}
      <mesh position={[0, top, 0]}>
        <cylinderGeometry args={[0.07, 0.09, 0.03, 24]} />
        <meshStandardMaterial {...brass} />
      </mesh>
      <mesh position={[0, (top + bodyY + 0.18) / 2, 0]}>
        <cylinderGeometry args={[0.012, 0.012, top - bodyY - 0.18, 12]} />
        <meshStandardMaterial {...brass} />
      </mesh>
      {/* two brass rings (tiers) */}
      <mesh position={[0, bodyY + 0.16, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <torusGeometry args={[rTop, 0.014, 12, 48]} />
        <meshStandardMaterial {...brass} />
      </mesh>
      <mesh position={[0, bodyY - 0.04, 0]} rotation={[Math.PI / 2, 0, 0]} castShadow>
        <torusGeometry args={[rBot, 0.012, 12, 48]} />
        <meshStandardMaterial {...brass} />
      </mesh>
      {/* candle arms with glowing bulbs on the top ring */}
      {candleAng.map((a, i) => {
        const cx = Math.cos(a) * rTop, cz = Math.sin(a) * rTop;
        return (
          <group key={i} position={[cx, bodyY + 0.16, cz]}>
            <mesh position={[0, 0.06, 0]}>
              <cylinderGeometry args={[0.016, 0.022, 0.09, 14]} />
              <meshStandardMaterial {...brass} />
            </mesh>
            {/* flame bulb */}
            <mesh position={[0, 0.14, 0]}>
              <sphereGeometry args={[0.032, 16, 16]} />
              <meshStandardMaterial color="#fff0cf" emissive="#ffcf82" emissiveIntensity={5} roughness={1} toneMapped={false} />
            </mesh>
          </group>
        );
      })}
      {/* hanging crystal strands from the top ring (3 beads each) */}
      {strandAng.map((a, i) => {
        const cx = Math.cos(a) * rTop, cz = Math.sin(a) * rTop;
        return (
          <group key={`s${i}`} position={[cx, bodyY + 0.16, cz]}>
            {[0.05, 0.13, 0.21].map((dy, k) => (
              <mesh key={k} position={[0, -dy, 0]} rotation={[0, a, 0]} castShadow>
                <octahedronGeometry args={[0.028 - k * 0.004, 0]} />
                <meshPhysicalMaterial {...crystal} />
              </mesh>
            ))}
          </group>
        );
      })}
      {/* inner crystal ring on the lower tier */}
      {Array.from({ length: 8 }, (_, i) => {
        const a = (i / 8) * Math.PI * 2, cx = Math.cos(a) * rBot, cz = Math.sin(a) * rBot;
        return (
          <mesh key={`b${i}`} position={[cx, bodyY - 0.1, cz]} castShadow>
            <octahedronGeometry args={[0.03, 0]} />
            <meshPhysicalMaterial {...crystal} />
          </mesh>
        );
      })}
      {/* central finial crystal drop */}
      <mesh position={[0, bodyY - 0.14, 0]} castShadow>
        <octahedronGeometry args={[0.055, 0]} />
        <meshPhysicalMaterial {...crystal} />
      </mesh>
      {/* glow core + real warm light */}
      <mesh position={[0, bodyY + 0.05, 0]}>
        <sphereGeometry args={[0.06, 16, 16]} />
        <meshStandardMaterial color="#fff3dc" emissive="#ffcf82" emissiveIntensity={3.4} roughness={1} toneMapped={false} />
      </mesh>
      <pointLight position={[0, bodyY + 0.05, 0]} intensity={11} color="#ffc978" distance={5.5} decay={2} castShadow />
    </group>
  );
}

// ═══ LIVING ELEMENTS ══════════════════════════════════════════════════════════
// Tall fiddle-leaf floor plant in a woven basket.
function FloorPlant({ p }: { p: [number, number, number] }) {
  const leaves = useMemo(
    () => Array.from({ length: 11 }, (_, i) => {
      const a = (i / 11) * Math.PI * 2 + i * 0.6;
      const h = 0.55 + (i % 4) * 0.16;
      return { a, h, tilt: 0.5 + (i % 3) * 0.25, r: 0.1 + (i % 3) * 0.05 };
    }),
    [],
  );
  return (
    <group position={p}>
      {/* woven basket pot */}
      <mesh position={[0, 0.22, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.24, 0.19, 0.44, 28]} />
        <meshStandardMaterial color="#a98455" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.44, 0]}>
        <cylinderGeometry args={[0.245, 0.245, 0.03, 28]} />
        <meshStandardMaterial color="#8f6c40" roughness={0.85} />
      </mesh>
      {/* soil */}
      <mesh position={[0, 0.45, 0]}>
        <cylinderGeometry args={[0.21, 0.21, 0.02, 20]} />
        <meshStandardMaterial color="#2a2018" roughness={1} />
      </mesh>
      {/* stems + broad leaves */}
      {leaves.map((lf, i) => {
        const lx = Math.cos(lf.a) * lf.r, lz = Math.sin(lf.a) * lf.r;
        return (
          <group key={i} position={[lx, 0.5, lz]} rotation={[lf.tilt * Math.cos(lf.a), lf.a, lf.tilt * Math.sin(lf.a)]}>
            <mesh position={[0, lf.h / 2, 0]} castShadow>
              <cylinderGeometry args={[0.008, 0.012, lf.h, 8]} />
              <meshStandardMaterial color="#3c5a2e" roughness={0.8} />
            </mesh>
            <mesh position={[0, lf.h, 0]} scale={[1, 1.5, 0.12]} castShadow>
              <sphereGeometry args={[0.13, 12, 10]} />
              <meshStandardMaterial color={i % 2 ? "#2f6b32" : "#3c7a3c"} roughness={0.7} />
            </mesh>
          </group>
        );
      })}
    </group>
  );
}

// Small trailing hanging plant from the ceiling near the window.
function HangingPlant({ p }: { p: [number, number, number] }) {
  const strands = useMemo(() => Array.from({ length: 9 }, (_, i) => ({ a: (i / 9) * Math.PI * 2, len: 0.3 + (i % 3) * 0.18 })), []);
  return (
    <group position={p}>
      {/* cord */}
      <mesh position={[0, -0.18, 0]}>
        <cylinderGeometry args={[0.004, 0.004, 0.36, 6]} />
        <meshStandardMaterial color="#c9b28c" roughness={0.8} />
      </mesh>
      {/* pot */}
      <mesh position={[0, -0.4, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.09, 0.16, 20]} />
        <meshStandardMaterial color="#e6ddcf" roughness={0.7} />
      </mesh>
      {/* trailing vines */}
      {strands.map((st, i) => {
        const vx = Math.cos(st.a) * 0.09, vz = Math.sin(st.a) * 0.09;
        return (
          <group key={i} position={[vx, -0.46, vz]}>
            {Array.from({ length: 5 }, (_, k) => (
              <mesh key={k} position={[Math.sin(k) * 0.02, -st.len * (k / 5), Math.cos(k) * 0.02]} castShadow>
                <sphereGeometry args={[0.028, 8, 8]} />
                <meshStandardMaterial color={k % 2 ? "#3c7a3c" : "#4f8a45"} roughness={0.75} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}

// ═══ SHARED: potted plant ═════════════════════════════════════════════════════
function Plant({ p, scale = 1 }: { p: [number, number, number]; scale?: number }) {
  const s = scale;
  return (
    <group position={p}>
      <mesh position={[0, 0.09 * s, 0]} castShadow>
        <cylinderGeometry args={[0.07 * s, 0.055 * s, 0.18 * s, 16]} />
        <meshStandardMaterial color={C.terracotta} roughness={0.85} />
      </mesh>
      {[
        [0, 0, 0, 0.13 * s],
        [0.05 * s, 0.03 * s, 0.06 * s, 0.1 * s],
        [-0.05 * s, 0.05 * s, -0.03 * s, 0.09 * s],
        [0.02 * s, 0.02 * s, -0.06 * s, 0.08 * s],
      ].map(([lx, ly, lz, ls], i) => (
        <mesh key={i} position={[lx, 0.2 * s + ly, lz]} castShadow>
          <sphereGeometry args={[ls, 10, 8]} />
          <meshStandardMaterial color={C.green} roughness={0.8} />
        </mesh>
      ))}
    </group>
  );
}

// ═══ DECOR LIGHTING — LED strips, box sconces, floor wash, accent spots ════════
function DecorLighting() {
  const bedCZ   = -D / 2 + 0.12 + 0.18 + 1.075; // ≈ -1.625  bed platform center-z
  const wdX     = -W / 2 + 0.6 / 2 + 0.03;       // ≈ -2.97   wardrobe center-x
  const ledWarm = "#ffd088";
  const ledHot  = "#ffe4b0";

  return (
    <>
      {/* ── FLOATING LED PANEL above the bed ── */}
      <Box p={[0, H - 0.07, bedCZ + 0.25]} s={[1.55, 0.045, 0.16]}
        m={{ color: "#e8e4dc", roughness: 0.6, metalness: 0.4 }} cast={false} receive={false} />
      <Box p={[0, H - 0.096, bedCZ + 0.25]} s={[1.46, 0.006, 0.09]}
        m={{ color: ledHot, emissive: ledHot, emissiveIntensity: 3.0, roughness: 1 }} cast={false} receive={false} />
      <Box p={[0, H - 0.048, bedCZ + 0.25]} s={[1.46, 0.006, 0.09]}
        m={{ color: ledHot, emissive: ledHot, emissiveIntensity: 1.6, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[0, H - 0.18, bedCZ + 0.25]} intensity={4} color="#ffc878" distance={3.5} decay={2} />
      <pointLight position={[0, H - 0.02, bedCZ + 0.25]} intensity={1.2} color="#ffe0a8" distance={1.8} decay={2} />

      {/* ── FLOOR-WASH LED STRIPS (base of every wall) ── */}
      {/* Back wall floor-wash */}
      <Box p={[0, 0.018, -D / 2 + 0.048]} s={[W - 0.18, 0.022, 0.01]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.2, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[0, 0.06, -D / 2 + 0.14]} intensity={1.4} color={ledWarm} distance={3.5} decay={2} />
      {/* Left wall floor-wash */}
      <Box p={[-W / 2 + 0.048, 0.018, 0]} s={[0.01, 0.022, D - 0.18]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.2, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-W / 2 + 0.14, 0.06, 0.1]} intensity={1.4} color={ledWarm} distance={4.0} decay={2} />
      {/* Right wall floor-wash */}
      <Box p={[W / 2 - 0.048, 0.018, 0]} s={[0.01, 0.022, D - 0.18]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.2, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[W / 2 - 0.14, 0.06, 0.1]} intensity={1.4} color={ledWarm} distance={4.0} decay={2} />

      {/* ── WALL BOX SCONCES on headboard wall (light UP + DOWN) ── */}
      {([-1.22, 1.22] as number[]).map((sx) => (
        <group key={sx} position={[sx, 1.86, -D / 2 + 0.085]}>
          {/* brass box body */}
          <Box p={[0, 0, 0]} s={[0.055, 0.21, 0.072]}
            m={{ color: "#b0894f", roughness: 0.22, metalness: 0.88, envMapIntensity: 1.6 }} cast={false} />
          {/* top slit — uplight */}
          <Box p={[0, 0.115, 0.012]} s={[0.038, 0.016, 0.055]}
            m={{ color: "#fff6e0", emissive: "#ffd070", emissiveIntensity: 3.5, roughness: 1 }} cast={false} receive={false} />
          {/* bottom slit — downlight */}
          <Box p={[0, -0.115, 0.012]} s={[0.038, 0.016, 0.055]}
            m={{ color: "#fff6e0", emissive: "#ffd070", emissiveIntensity: 3.5, roughness: 1 }} cast={false} receive={false} />
          <pointLight position={[0,  0.16, 0.08]} intensity={1.6} color="#ffbe60" distance={1.6} decay={2} />
          <pointLight position={[0, -0.16, 0.08]} intensity={1.6} color="#ffbe60" distance={1.6} decay={2} />
        </group>
      ))}

      {/* ── ACCENT SPOTLIGHTS on the fluted headboard wall ── */}
      <spotLight
        position={[-0.85, H - 0.08, -D / 2 + 0.75]}
        target-position={[-0.85, 1.1, -D / 2 + 0.05]}
        intensity={7} color="#fff8ee" angle={0.42} penumbra={0.8} distance={4} decay={2}
      />
      <spotLight
        position={[0.85, H - 0.08, -D / 2 + 0.75]}
        target-position={[0.85, 1.1, -D / 2 + 0.05]}
        intensity={7} color="#fff8ee" angle={0.42} penumbra={0.8} distance={4} decay={2}
      />

      {/* ── UNDER-BED LED ── */}
      <Box p={[0, 0.018, bedCZ - 0.05]} s={[2.05, 0.016, 1.95]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 1.8, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[0, 0.05, bedCZ]} intensity={1.4} color={ledWarm} distance={2.5} decay={2} />

      {/* ── UNDER-WARDROBE LED ── */}
      <Box p={[wdX, 0.016, 1.0]} s={[0.48, 0.014, 2.28]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.0, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[wdX + 0.28, 0.05, 1.0]} intensity={1.4} color={ledWarm} distance={2.8} decay={2} />

      {/* ── WARDROBE TOP LED ── */}
      <Box p={[wdX, 2.505, 1.0]} s={[0.54, 0.014, 2.28]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 1.6, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[wdX + 0.3, 2.55, 1.0]} intensity={1.0} color={ledWarm} distance={2.0} decay={2} />
    </>
  );
}

// ═══ LIGHTING (same rig as the kitchen) ═══════════════════════════════════════
function Lighting() {
  return (
    <>
      {/* Primary daylight from the window */}
      <directionalLight
        position={[9, 5.5, 0.5]} intensity={1.6} color="#fff4e8" castShadow
        shadow-mapSize={[2048, 2048]} shadow-bias={-0.0003}
        shadow-camera-near={0.5} shadow-camera-far={24}
        shadow-camera-left={-8} shadow-camera-right={8} shadow-camera-top={8} shadow-camera-bottom={-2}
      />
      {/* Window sunspot on the floor */}
      <spotLight
        position={[W / 2 + 0.4, 2.0, 0.4]}
        target-position={[-1.5, 0, 0.5]}
        intensity={9} color="#fff8ec"
        angle={0.38} penumbra={0.72}
        distance={10} decay={2}
        castShadow shadow-mapSize={[1024, 1024]} shadow-bias={-0.0006}
      />
      <ambientLight intensity={0.18} color="#fff0d5" />
      <hemisphereLight args={["#e4eeff", "#b8aa95", 0.35]} />
      {/* Recessed downlights */}
      {[[-1.7, -1.4], [1.7, -1.4], [-1.7, 1.2], [1.7, 1.2], [0, 1.6]].map(([x, z], i) => (
        <pointLight key={i} position={[x, H - 0.15, z]} intensity={4.5} color="#ffefd2" distance={4.0} decay={2} />
      ))}
      {/* Camera-side soft fill */}
      <pointLight position={[2.5, 2.4, 4.5]} intensity={4} color="#eef1ff" distance={8} decay={2} />
      {/* subtle back fill */}
      <pointLight position={[0, 2.2, -1.5]} intensity={1.5} color="#ffd9a8" distance={4} decay={2} />
    </>
  );
}

export { W as BEDROOM_W, D as BEDROOM_D };
