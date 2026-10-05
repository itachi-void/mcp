import { useMemo } from "react";
import type { ReactNode } from "react";
import type * as THREE from "three";
import { RoundedBox } from "@react-three/drei";
import { marble, wood, tileFloor, fabric } from "../kitchen/textures";

// ─────────────────────────────────────────────────────────────────────────────
//  LUXURY GREIGE BATHROOM — matte-black accents, warm cove lighting.
//  Reproduces the reference photograph: floating fluted vanity + twin vessels &
//  a round backlit mirror on the LEFT wall, a freestanding oval tub centred on
//  the BACK wall against a fluted stone panel with a lit niche, a black-framed
//  glass rainfall shower in the back-RIGHT corner, and a wall-hung toilet on the
//  RIGHT wall — all over large greige stone tile with a textured runner rug.
//  Convention:  x = left(-)/right(+)   y = up   z = back(-)/front-camera(+)
// ─────────────────────────────────────────────────────────────────────────────

const C = {
  wall:      "#c4bcae",   // warm greige plaster
  wallWarm:  "#cabfae",   // sunlit patch tone
  ceiling:   "#cdc7bb",
  stone:     "#c9c1b4",   // large-format wall stone
  tile:      "#c6bfb2",   // floor
  vanity:    "#a07d54",   // warm fluted oak vanity
  vanityDk:  "#6f5433",
  counter:   "#ddd6c9",   // honed quartz top
  ceramic:   "#f3efe7",   // vessels / tub / toilet
  black:     "#141312",   // matte black fixtures
  blackSemi: "#1c1a18",
  brassDim:  "#7d6a4c",
  glass:     "#cfe0ea",
  ledWarm:   "#ffcf88",
  ledUnder:  "#ffdca8",
  mirror:    "#aabccb",
  rug:       "#b6ab98",
  plant:     "#3a5a34",
  vase:      "#20201e",
  amber:     "#c9a86a",
};

// Shell — same footprint as the other rooms so the camera framing matches.
const W = 6.6, D = 6.0, H = 2.8;
const BACK_Z = -D / 2;
const RIGHT_X = W / 2;
const LEFT_X = -W / 2;

// ── Procedural PBR (self-contained, no external files) ───────────────────────
function buildTextures() {
  return {
    floor:  tileFloor("#c6bfb2", [3, 3], 3),   // large greige floor tile w/ grout
    wall:   tileFloor("#c9c1b4", [2, 2], 1),   // seamless stone wall slabs
    wood:   wood("#a07d54", [1, 2], false),    // horizontal-cut warm oak
    quartz: marble("#ddd6c9", [1, 1]),         // honed counter / tub surround
    rug:    fabric("#b6ab98", [4, 2]),         // tufted runner
  };
}
let _tex: ReturnType<typeof buildTextures> | null = null;
function TEX() {
  if (!_tex) _tex = buildTextures();
  return _tex;
}

// ── material helpers (physical everywhere → sheen/clearcoat available) ────────
type M = Partial<{
  color: string; roughness: number; metalness: number; envMapIntensity: number;
  transparent: boolean; opacity: number; emissive: string; emissiveIntensity: number;
  map: THREE.Texture; bumpMap: THREE.Texture; bumpScale: number;
  normalMap: THREE.Texture; normalScale: THREE.Vector2;
  roughnessMap: THREE.Texture; clearcoat: number; clearcoatRoughness: number;
  transmission: number; thickness: number; ior: number; side: 0 | 1 | 2;
  sheen: number; sheenRoughness: number; sheenColor: string;
}>;

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
function RBox({ p, s, m, r = 0.02, cast = true, receive = true, children }: {
  p: [number, number, number]; s: [number, number, number]; m: M; r?: number;
  cast?: boolean; receive?: boolean; children?: ReactNode;
}) {
  return (
    <RoundedBox position={p} args={s} radius={Math.min(r, Math.min(...s) / 2 - 0.001)} smoothness={4} castShadow={cast} receiveShadow={receive}>
      <meshPhysicalMaterial {...m} />
      {children}
    </RoundedBox>
  );
}

const BLACK: M = { color: C.black, roughness: 0.5, metalness: 0.6, envMapIntensity: 0.7 };

export default function BathroomScene() {
  return (
    <group>
      <Room />
      <FlutedFeatureWall />
      <Vanity />
      <RoundMirror />
      <Pendant x={-W / 2 + 0.55} z={1.25} />
      <Bathtub />
      <NicheColumn />
      <Shower />
      <Toilet />
      <WallArt />
      <Rug />
      <FloorDecor />
      <Lighting />
    </group>
  );
}

// ═══ ROOM SHELL ═══════════════════════════════════════════════════════════════
function Room() {
  const drop = 0.16, bord = 0.55, cz = H - drop;
  return (
    <group>
      {/* large greige stone tile floor with a faint polish */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[W, D]} />
        <meshPhysicalMaterial map={TEX().floor.map} bumpMap={TEX().floor.bump} bumpScale={0.004}
          color={C.tile} roughness={0.5} metalness={0.0} envMapIntensity={0.9}
          clearcoat={0.35} clearcoatRoughness={0.4} />
      </mesh>
      {/* smooth microcement/plaster walls */}
      {([
        { p: [0, H / 2, BACK_Z], s: [W, H, 0.05] },
        { p: [LEFT_X, H / 2, 0], s: [0.05, H, D] },
        { p: [RIGHT_X, H / 2, 0], s: [0.05, H, D] },
      ] as { p: [number, number, number]; s: [number, number, number] }[]).map((b, i) => (
        <mesh key={i} position={b.p} receiveShadow>
          <boxGeometry args={b.s} />
          <meshPhysicalMaterial color={C.wall} roughness={0.88} metalness={0.0} envMapIntensity={0.2} />
        </mesh>
      ))}
      {/* ceiling */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, H, 0]}>
        <planeGeometry args={[W, D]} />
        <meshStandardMaterial color={C.ceiling} roughness={1} />
      </mesh>
      {/* recessed tray + warm cove LED around the perimeter */}
      {[
        { p: [0, cz + drop / 2, BACK_Z + bord / 2], s: [W, drop, bord] },
        { p: [0, cz + drop / 2, D / 2 - bord / 2], s: [W, drop, bord] },
        { p: [LEFT_X + bord / 2, cz + drop / 2, 0], s: [bord, drop, D - bord * 2] },
        { p: [RIGHT_X - bord / 2, cz + drop / 2, 0], s: [bord, drop, D - bord * 2] },
      ].map((b, i) => (
        <Box key={i} p={b.p as [number, number, number]} s={b.s as [number, number, number]} m={{ color: C.ceiling, roughness: 1 }} cast={false} />
      ))}
      <Box p={[0, cz, 0]} s={[W - bord * 2, 0.04, D - bord * 2]} m={{ color: C.ceiling, roughness: 1 }} cast={false} />
      {[
        { p: [0, cz - 0.02, BACK_Z + bord - 0.02], s: [W - bord, 0.03, 0.02] },
        { p: [0, cz - 0.02, D / 2 - bord + 0.02], s: [W - bord, 0.03, 0.02] },
        { p: [LEFT_X + bord - 0.02, cz - 0.02, 0], s: [0.02, 0.03, D - bord * 2] },
        { p: [RIGHT_X - bord + 0.02, cz - 0.02, 0], s: [0.02, 0.03, D - bord * 2] },
      ].map((b, i) => (
        <Box key={i} p={b.p as [number, number, number]} s={b.s as [number, number, number]}
          m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 3.8, roughness: 1 }} cast={false} receive={false} />
      ))}
      {/* recessed downlights — five low-glare pools, aimed vertically onto the floor */}
      {[[-1.6, -1.3], [1.5, -1.3], [-1.6, 1.2], [1.5, 1.2], [0, 0.2]].map(([x, z], i) => (
        <group key={i} position={[x, H - 0.005, z]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.05, 0.07, 24]} />
            <meshStandardMaterial color="#3a352f" roughness={0.4} metalness={0.5} side={2} />
          </mesh>
          <mesh position={[0, -0.01, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <circleGeometry args={[0.05, 20]} />
            <meshStandardMaterial color="#ffffff" emissive="#ffe6c2" emissiveIntensity={3.4} roughness={1} toneMapped={false} />
          </mesh>
          <spotLight
            position={[0, -0.05, 0]}
            rotation={[-Math.PI / 2, 0, 0]}
            intensity={7.5}
            color="#ffe2bc"
            angle={0.48}
            penumbra={0.72}
            distance={4.1}
            decay={2}
            castShadow
            shadow-mapSize={[512, 512]}
            shadow-bias={-0.00025}
          />
        </group>
      ))}
      {/* skirting */}
      <Box p={[0, 0.04, BACK_Z + 0.03]} s={[W - 0.1, 0.08, 0.02]} m={{ color: "#b3aa9a", roughness: 0.6 }} cast={false} />
      <Box p={[LEFT_X + 0.03, 0.04, 0]} s={[0.02, 0.08, D - 0.1]} m={{ color: "#b3aa9a", roughness: 0.6 }} cast={false} />
      <Box p={[RIGHT_X - 0.03, 0.04, 0]} s={[0.02, 0.08, D - 0.1]} m={{ color: "#b3aa9a", roughness: 0.6 }} cast={false} />
    </group>
  );
}

// ═══ BACK WALL — narrow fluted pillar + wide horizontal niche behind tub ══════
function FlutedFeatureWall() {
  const z = BACK_Z + 0.03;
  // narrow fluted decorative pillar between the niche column and horizontal niche
  const wWidth = 0.28, cx = -1.46, wy = H / 2, wh = H - 0.04;
  const slatW = 0.032, gap = 0.014;
  const n = Math.floor(wWidth / (slatW + gap));
  const x0 = cx - (n - 1) * (slatW + gap) / 2;
  const slats = useMemo(() => Array.from({ length: n }, (_, i) => x0 + i * (slatW + gap)), [n, x0]);
  return (
    <group>
      {/* backing panel for fluted pillar */}
      <Box p={[cx, wy, z]} s={[wWidth, wh, 0.02]} m={{ color: "#b5ac9d", roughness: 0.86 }} cast={false} />
      {slats.map((sx, i) => (
        <mesh key={i} position={[sx, wy, z + 0.03]} castShadow={false} receiveShadow>
          <cylinderGeometry args={[slatW / 2, slatW / 2, wh, 10, 1, false, 0, Math.PI]} />
          <meshPhysicalMaterial color={C.stone} roughness={0.78} envMapIntensity={0.4} />
        </mesh>
      ))}
      {/* wide horizontal lit niche behind bathtub — very prominent */}
      <Box p={[0.2, 1.05, z + 0.05]} s={[2.1, 0.40, 0.028]} m={{ color: "#a89e8d", roughness: 0.84 }} cast={false} />
      {/* LED strip at top of niche */}
      <Box p={[0.2, 1.26, z + 0.065]} s={[2.04, 0.018, 0.04]}
        m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 4.2, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[0.2, 1.0, z + 0.55]} intensity={2.2} color="#ffcf80" distance={2.8} decay={2} />
      {/* items in horizontal niche */}
      {([
        [-0.62, "#2b2723", 0.16], [-0.40, "#8c7150", 0.20], [-0.18, "#2b2723", 0.14],
        [0.10, "#c9bda6", 0.12], [0.55, "#2b2723", 0.18],
      ] as [number, string, number][]).map(([nx, col, h], i) => (
        <mesh key={i} position={[0.2 + nx, 0.97, z + 0.13]} castShadow>
          <cylinderGeometry args={[0.026, 0.029, h, 16]} />
          <meshPhysicalMaterial color={col} roughness={0.35} clearcoat={0.4} />
        </mesh>
      ))}
      <Vase p={[0.65, 0.93, z + 0.13]} h={0.17} r={0.048} sprigs />
    </group>
  );
}

// ═══ FLOATING FLUTED VANITY + TWIN VESSELS (left wall) ════════════════════════
function Vanity() {
  const px = LEFT_X + 0.02;          // wall face
  const d = 0.56;                    // depth off wall
  const cx = px + d / 2;             // centre depth
  const topY = 0.86;                 // countertop height
  const bodyH = 0.5;
  const zC = 0.28;                   // runs along the wall, from the foreground towards the tub
  const len = 3.3;                    // long, single-basin vanity like the reference
  const woodMat: M = { map: TEX().wood.map, bumpMap: TEX().wood.bump, bumpScale: 0.01, color: C.vanity, roughness: 0.5, envMapIntensity: 0.6 };
  const nSlats = 20;
  return (
    <group>
      {/* floating cabinet body */}
      <RBox p={[cx, topY - 0.03 - bodyH / 2, zC]} s={[d, bodyH, len]} r={0.012} m={{ color: C.vanityDk, roughness: 0.55 }} />
      {/* vertical fluted front */}
      {Array.from({ length: nSlats }, (_, i) => {
        const fz = zC - len / 2 + 0.08 + (i * (len - 0.16)) / (nSlats - 1);
        return (
          <mesh key={i} position={[cx + d / 2 - 0.006, topY - 0.03 - bodyH / 2, fz]} castShadow rotation={[Math.PI / 2, 0, 0]}>
            <cylinderGeometry args={[0.026, 0.026, bodyH - 0.02, 8, 1, false, 0, Math.PI]} />
            <meshPhysicalMaterial {...woodMat} />
          </mesh>
        );
      })}
      {/* honed quartz countertop with a slim waterfall front */}
      <RBox p={[cx, topY, zC]} s={[d + 0.02, 0.05, len + 0.02]} r={0.008}
        m={{ map: TEX().quartz.map, bumpMap: TEX().quartz.bump, bumpScale: 0.003, color: C.counter, roughness: 0.32, clearcoat: 0.5, clearcoatRoughness: 0.12, envMapIntensity: 0.8 }} />
      {/* warm LED underglow beneath the floating cabinet */}
      <Box p={[cx, topY - 0.03 - bodyH - 0.005, zC]} s={[d * 0.8, 0.012, len * 0.92]}
        m={{ color: C.ledUnder, emissive: C.ledUnder, emissiveIntensity: 1.6, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[cx, topY - bodyH - 0.1, zC]} intensity={1.4} color="#ffcc88" distance={2.2} decay={2} />
      {/* one generous vessel at the foreground end of the long counter */}
      {([0.98]).map((sz) => (
        <Vessel key={sz} x={cx} z={zC + sz} y={topY + 0.025} />
      ))}
      {/* wall-mounted faucet aligned with the single basin */}
      {([0.98]).map((sz) => (
        <group key={`f${sz}`} position={[px + 0.03, topY + 0.30, zC + sz]}>
          <Box p={[0, 0, 0]} s={[0.02, 0.12, 0.07]} m={BLACK} />
          <mesh position={[0.14, 0.02, 0]} rotation={[0, 0, -Math.PI / 2]} castShadow>
            <cylinderGeometry args={[0.011, 0.011, 0.28, 12]} />
            <meshStandardMaterial {...BLACK} />
          </mesh>
          <mesh position={[0.28, -0.05, 0]} castShadow>
            <cylinderGeometry args={[0.008, 0.008, 0.06, 10]} />
            <meshStandardMaterial {...BLACK} />
          </mesh>
          {/* lever handle */}
          <mesh position={[-0.02, -0.09, 0]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.008, 0.008, 0.09, 8]} />
            <meshStandardMaterial {...BLACK} />
          </mesh>
        </group>
      ))}
      {/* accessories on the counter */}
      {/* soap dispensers on a stone tray near the front */}
      <Box p={[cx + 0.05, topY + 0.04, zC + 1.24]} s={[0.16, 0.02, 0.24]} m={{ color: "#2a2622", roughness: 0.5 }} />
      {[-0.05, 0.05].map((o, i) => (
        <mesh key={i} position={[cx + 0.05 + o, topY + 0.10, zC + 1.24]} castShadow>
          <cylinderGeometry args={[0.026, 0.03, 0.13, 18]} />
          <meshStandardMaterial color={i === 0 ? "#22201d" : "#e9e3d8"} roughness={0.4} metalness={0.1} />
        </mesh>
      ))}
      {/* lit candle */}
      <group position={[cx - 0.02, topY + 0.03, zC + 0.58]}>
        <mesh castShadow><cylinderGeometry args={[0.05, 0.05, 0.06, 20]} /><meshStandardMaterial color="#e7e0d4" roughness={0.6} /></mesh>
        <mesh position={[0, 0.07, 0]}><sphereGeometry args={[0.014, 8, 8]} /><meshStandardMaterial color="#fff0cf" emissive="#ffbe66" emissiveIntensity={5} toneMapped={false} /></mesh>
        <pointLight position={[0, 0.08, 0]} intensity={0.5} color="#ffb455" distance={0.8} decay={2} />
      </group>
      {/* small vase with eucalyptus */}
      <Vase p={[cx - 0.06, topY + 0.03, zC - 0.02]} h={0.14} r={0.04} sprigs />
      {/* folded towel bundle at the base niche */}
      <Box p={[cx, topY - 0.03 - bodyH + 0.09, zC - len / 2 + 0.02]} s={[d - 0.06, 0.16, 0.02]} m={{ color: "#9a9184", roughness: 0.9 }} cast={false} />
    </group>
  );
}

function Vessel({ x, y, z }: { x: number; y: number; z: number }) {
  return (
    <group position={[x, y, z]}>
      {/* shallow oval basin */}
      <mesh castShadow scale={[1, 0.5, 0.72]}>
        <sphereGeometry args={[0.19, 32, 24, 0, Math.PI * 2, Math.PI / 2, Math.PI / 2]} />
        <meshPhysicalMaterial color={C.ceramic} roughness={0.18} clearcoat={0.7} clearcoatRoughness={0.1} envMapIntensity={1.0} />
      </mesh>
      <mesh scale={[1, 1, 0.72]}>
        <torusGeometry args={[0.185, 0.012, 16, 40]} />
        <meshPhysicalMaterial color={C.ceramic} roughness={0.18} clearcoat={0.7} clearcoatRoughness={0.1} />
      </mesh>
    </group>
  );
}

function Vase({ p, h, r, sprigs = false }: { p: [number, number, number]; h: number; r: number; sprigs?: boolean }) {
  return (
    <group position={p}>
      <mesh castShadow>
        <cylinderGeometry args={[r * 0.8, r, h, 20]} />
        <meshPhysicalMaterial color={C.vase} roughness={0.3} metalness={0.1} clearcoat={0.4} />
      </mesh>
      {sprigs && [0, 1, 2, 3, 4].map((j) => (
        <mesh key={j} position={[Math.sin(j * 1.3) * 0.04, h * 0.5 + 0.1 + j * 0.02, Math.cos(j * 1.3) * 0.04]} rotation={[0, 0, (j - 2) * 0.25]}>
          <boxGeometry args={[0.005, 0.22, 0.02]} />
          <meshStandardMaterial color={C.plant} roughness={0.85} />
        </mesh>
      ))}
    </group>
  );
}

// ═══ ROUND BACKLIT MIRROR (over the vanity, left wall) ════════════════════════
function RoundMirror() {
  const px = LEFT_X + 0.04;
  return (
    <group position={[px, 1.55, 1.1]} rotation={[0, Math.PI / 2, 0]}>
      {/* halo backlight */}
      <mesh position={[0, 0, -0.02]}>
        <circleGeometry args={[0.52, 64]} />
        <meshStandardMaterial color="#fff6e6" emissive="#ffdc9c" emissiveIntensity={2.6} roughness={1} toneMapped={false} />
      </mesh>
      {/* thin matte black rim */}
      <mesh castShadow>
        <torusGeometry args={[0.48, 0.012, 20, 72]} />
        <meshStandardMaterial {...BLACK} />
      </mesh>
      {/* reflective glass */}
      <mesh>
        <circleGeometry args={[0.475, 64]} />
        <meshPhysicalMaterial color={C.mirror} roughness={0.02} metalness={0.98} envMapIntensity={3.2} />
      </mesh>
      <pointLight position={[0, 0, 0.4]} intensity={1.6} color="#ffd68a" distance={2.4} decay={2} />
    </group>
  );
}

// ═══ PENDANT LIGHT (slim black cylinder beside the mirror) ════════════════════
function Pendant({ x, z }: { x: number; z: number }) {
  return (
    <group position={[x, 0, z]}>
      <mesh position={[0, H - 0.02, 0]}><cylinderGeometry args={[0.02, 0.02, 0.03, 16]} /><meshStandardMaterial {...BLACK} /></mesh>
      <mesh position={[0, (H + 1.55) / 2, 0]}><cylinderGeometry args={[0.003, 0.003, H - 1.55, 6]} /><meshStandardMaterial {...BLACK} /></mesh>
      <mesh position={[0, 1.5, 0]} castShadow><cylinderGeometry args={[0.045, 0.045, 0.26, 24]} /><meshStandardMaterial {...BLACK} /></mesh>
      <mesh position={[0, 1.38, 0]}><sphereGeometry args={[0.04, 16, 16]} /><meshStandardMaterial color="#fff0cf" emissive="#ffbe66" emissiveIntensity={5} roughness={1} toneMapped={false} /></mesh>
      <pointLight position={[0, 1.36, 0]} intensity={2.6} color="#ffbe66" distance={2.6} decay={2} />
    </group>
  );
}

// ═══ FREESTANDING OVAL TUB (centre, against the feature wall) ═════════════════
function Bathtub() {
  const cx = 0.15, cz = BACK_Z + 0.95, floorY = 0.0;
  const outer: M = { color: C.ceramic, roughness: 0.16, clearcoat: 0.75, clearcoatRoughness: 0.08, envMapIntensity: 1.0 };
  return (
    <group position={[cx, 0, cz]}>
      {/* solid outer shell — flared oval */}
      <mesh position={[0, 0.32, 0]} castShadow receiveShadow scale={[1, 1, 0.66]}>
        <cylinderGeometry args={[0.62, 0.52, 0.62, 48]} />
        <meshPhysicalMaterial {...outer} />
      </mesh>
      {/* rounded rim */}
      <mesh position={[0, 0.63, 0]} scale={[1, 1, 0.66]}>
        <torusGeometry args={[0.6, 0.03, 20, 56]} />
        <meshPhysicalMaterial {...outer} />
      </mesh>
      {/* hollowed interior */}
      <mesh position={[0, 0.4, 0]} scale={[1, 1, 0.66]}>
        <cylinderGeometry args={[0.55, 0.44, 0.46, 48, 1, true]} />
        <meshPhysicalMaterial color="#eae4da" roughness={0.2} side={2} />
      </mesh>
      <mesh position={[0, 0.44, 0]} rotation={[-Math.PI / 2, 0, 0]} scale={[1, 0.66, 1]}>
        <circleGeometry args={[0.44, 48]} />
        <meshPhysicalMaterial color="#e6dfd4" roughness={0.25} />
      </mesh>
      {/* wall-mounted filler on back wall (z_rel = BACK_Z+0.04 - cz ≈ -0.91) */}
      <group position={[0, 0, BACK_Z + 0.04 - (BACK_Z + 0.95)]}>
        {/* escutcheon plate on the wall */}
        <Box p={[0, 0.70, 0]} s={[0.055, 0.10, 0.03]} m={BLACK} />
        {/* horizontal spout arm extending from wall */}
        <mesh position={[0, 0.70, 0.22]} rotation={[Math.PI / 2, 0, 0]} castShadow>
          <cylinderGeometry args={[0.016, 0.016, 0.44, 12]} />
          <meshStandardMaterial {...BLACK} />
        </mesh>
        {/* downward arc at the end */}
        <mesh position={[0, 0.54, 0.42]} castShadow>
          <cylinderGeometry args={[0.013, 0.013, 0.30, 10]} />
          <meshStandardMaterial {...BLACK} />
        </mesh>
        {/* lever valve handle */}
        <mesh position={[0.10, 0.70, 0.06]} rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.009, 0.009, 0.09, 8]} />
          <meshStandardMaterial {...BLACK} />
        </mesh>
      </group>
      {/* small teak bath caddy across the rim */}
      <Box p={[0, 0.64, 0]} s={[0.5, 0.02, 0.14]} m={{ map: TEX().wood.map, color: "#8a6a45", roughness: 0.55 }} />
      <mesh position={[-0.12, 0.7, 0]} castShadow><cylinderGeometry args={[0.02, 0.022, 0.09, 12]} /><meshStandardMaterial color="#e9e3d8" roughness={0.4} /></mesh>
    </group>
  );
}

// ═══ TALL LIT NICHE COLUMN — left corner of back wall, nearly floor-to-ceiling ══
function NicheColumn() {
  // Sits in the left corner between left wall and back wall
  const x = LEFT_X + 0.62;  // -2.68, near the left corner
  const z = BACK_Z + 0.07;
  const unitW = 0.74;
  const unitH = 2.54;
  const centerY = unitH / 2 + 0.07;  // 1.34 from floor
  // 5 shelves evenly distributed across the full height
  const shelfOffsets = [-0.92, -0.45, 0.0, 0.46, 0.92];
  const itemColors = ["#2b2723", "#c9bda6", "#7d6448", "#e6e0d4", "#2b2723"];
  return (
    <group position={[x, centerY, z]}>
      {/* deep recessed back panel */}
      <Box p={[0, 0, -0.025]} s={[unitW, unitH, 0.05]} m={{ color: "#9e9585", roughness: 0.87 }} cast={false} />
      {/* vertical side jambs */}
      <Box p={[-unitW / 2 + 0.025, 0, 0.01]} s={[0.05, unitH, 0.20]} m={{ color: "#b4aa9a", roughness: 0.72 }} cast={false} />
      <Box p={[unitW / 2 - 0.025, 0, 0.01]} s={[0.05, unitH, 0.20]} m={{ color: "#b4aa9a", roughness: 0.72 }} cast={false} />
      {/* top and base panels */}
      <Box p={[0, unitH / 2 - 0.015, 0.01]} s={[unitW - 0.06, 0.03, 0.20]} m={{ color: "#b4aa9a", roughness: 0.72 }} cast={false} />
      <Box p={[0, -unitH / 2 + 0.015, 0.01]} s={[unitW - 0.06, 0.03, 0.20]} m={{ color: "#b4aa9a", roughness: 0.72 }} cast={false} />

      {shelfOffsets.map((sy, i) => (
        <group key={i} position={[0, sy, 0]}>
          {/* shelf slab */}
          <Box p={[0, 0, 0.01]} s={[unitW - 0.08, 0.026, 0.19]} m={{ color: "#bfb8a8", roughness: 0.55 }} cast={false} />
          {/* warm LED strip under the shelf above */}
          <Box p={[0, 0.115, 0.025]} s={[unitW - 0.14, 0.015, 0.018]}
            m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 3.6, roughness: 1 }} cast={false} receive={false} />
          {/* 2-3 items per shelf */}
          {([-0.18, -0.03, 0.14] as number[]).map((ox, j) => {
            if (j === 2 && i % 2 === 0) {
              return <Vase key={j} p={[ox, 0.08, 0.04]} h={0.12} r={0.028} />;
            }
            return (
              <mesh key={j} position={[ox, 0.09, 0.04]} castShadow>
                <cylinderGeometry args={[0.020, 0.023, 0.10 + j * 0.025, 14]} />
                <meshPhysicalMaterial color={itemColors[(i * 2 + j) % 5]} roughness={0.35} clearcoat={0.32} />
              </mesh>
            );
          })}
        </group>
      ))}
      <pointLight position={[0, 0, 0.65]} intensity={1.4} color="#ffcf80" distance={2.2} decay={2} />
    </group>
  );
}

// ═══ GLASS RAINFALL SHOWER (back-right corner) ════════════════════════════════
function Shower() {
  const x0 = RIGHT_X - 0.04;         // right wall face
  const zBack = BACK_Z + 0.04;
  const sw = 1.5;                    // depth along right wall (z)
  const sd = 1.35;                   // reach into room (x)
  const zC = zBack + sw / 2;
  const xC = x0 - sd / 2;
  const glassH = 2.2;
  const glassMat: M = { color: C.glass, transparent: true, opacity: 0.16, roughness: 0.02, metalness: 0.0, transmission: 0.9, thickness: 0.01, envMapIntensity: 1.2 };
  return (
    <group>
      {/* wet-zone floor pan (slightly darker wet stone) */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[xC, 0.006, zC]} receiveShadow>
        <planeGeometry args={[sd, sw]} />
        <meshPhysicalMaterial map={TEX().floor.map} color="#b4ad9f" roughness={0.28} clearcoat={0.6} clearcoatRoughness={0.2} />
      </mesh>
      {/* linear drain */}
      <Box p={[xC, 0.012, zBack + 0.2]} s={[sd - 0.3, 0.006, 0.04]} m={{ color: "#2a2824", roughness: 0.5, metalness: 0.5 }} cast={false} />
      {/* fixed glass panel facing the room (front, along x) */}
      <group>
        <mesh position={[xC, glassH / 2, zC + sw / 2]} castShadow>
          <boxGeometry args={[sd, glassH, 0.012]} />
          <meshPhysicalMaterial {...glassMat} />
        </mesh>
        {/* black frame around it */}
        <Box p={[xC, glassH, zC + sw / 2]} s={[sd, 0.03, 0.03]} m={BLACK} cast={false} />
        <Box p={[xC - sd / 2, glassH / 2, zC + sw / 2]} s={[0.03, glassH, 0.03]} m={BLACK} />
        <Box p={[xC + sd / 2, glassH / 2, zC + sw / 2]} s={[0.03, glassH, 0.03]} m={BLACK} />
        {/* pivot door handle */}
        <mesh position={[xC + sd / 2 - 0.12, glassH / 2, zC + sw / 2 + 0.03]}><boxGeometry args={[0.02, 0.28, 0.02]} /><meshStandardMaterial {...BLACK} /></mesh>
      </group>
      {/* return glass panel (along z, closing the corner toward camera) */}
      <mesh position={[xC - sd / 2, glassH / 2, zC]} castShadow>
        <boxGeometry args={[0.012, glassH, sw]} />
        <meshPhysicalMaterial {...glassMat} />
      </mesh>
      <Box p={[xC - sd / 2, glassH, zC]} s={[0.03, 0.03, sw]} m={BLACK} cast={false} />
      {/* ceiling-mount rainfall head */}
      <group position={[xC, 0, zBack + 0.55]}>
        <mesh position={[0, H - 0.02, 0]}><cylinderGeometry args={[0.02, 0.02, 0.04, 12]} /><meshStandardMaterial {...BLACK} /></mesh>
        <mesh position={[0, (H + 2.05) / 2, 0]}><cylinderGeometry args={[0.014, 0.014, H - 2.05, 12]} /><meshStandardMaterial {...BLACK} /></mesh>
        <mesh position={[0, 2.02, 0]} castShadow><cylinderGeometry args={[0.14, 0.14, 0.03, 28]} /><meshStandardMaterial {...BLACK} /></mesh>
      </group>
      {/* wall controls + slide bar + hand shower on the right wall */}
      <group position={[x0 - 0.02, 0, zBack + 0.2]}>
        <Box p={[0, 1.15, 0]} s={[0.02, 0.2, 0.09]} m={BLACK} />
        <mesh position={[0, 1.75, 0]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.01, 0.01, 0.6, 10]} /><meshStandardMaterial {...BLACK} /></mesh>
        <mesh position={[-0.04, 1.55, 0]} rotation={[0, 0, Math.PI / 6]}><cylinderGeometry args={[0.012, 0.012, 0.14, 12]} /><meshStandardMaterial {...BLACK} /></mesh>
        <mesh position={[-0.09, 1.47, 0]} rotation={[0, 0, Math.PI / 2]}><cylinderGeometry args={[0.05, 0.05, 0.02, 20]} /><meshStandardMaterial {...BLACK} /></mesh>
      </group>
      {/* small lit niche inside the shower on the back wall */}
      <Box p={[xC + 0.1, 1.3, zBack + 0.05]} s={[0.5, 0.34, 0.02]} m={{ color: "#a89f90", roughness: 0.85 }} cast={false} />
      <Box p={[xC + 0.1, 1.47, zBack + 0.06]} s={[0.48, 0.015, 0.03]}
        m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 2.8, roughness: 1 }} cast={false} receive={false} />
      {[-0.12, 0.02].map((ox, i) => (
        <mesh key={i} position={[xC + 0.1 + ox, 1.22, zBack + 0.12]} castShadow>
          <cylinderGeometry args={[0.026, 0.028, 0.15, 14]} />
          <meshPhysicalMaterial color={i === 0 ? "#2b2723" : "#8c7150"} roughness={0.35} clearcoat={0.35} />
        </mesh>
      ))}
      <pointLight position={[xC, 1.6, zC]} intensity={1.6} color="#ffd08a" distance={2.8} decay={2} />
    </group>
  );
}

// ═══ WALL-HUNG TOILET (right wall, toward the camera) ═════════════════════════
function Toilet() {
  const x = RIGHT_X - 0.04, z = 1.9;
  const cer: M = { color: C.ceramic, roughness: 0.18, clearcoat: 0.7, clearcoatRoughness: 0.1 };
  return (
    <group position={[x, 0, z]} rotation={[0, -Math.PI / 2, 0]}>
      {/* concealed cistern face */}
      <Box p={[0, 1.0, -0.14]} s={[0.4, 0.5, 0.06]} m={{ color: "#d8d1c4", roughness: 0.6 }} cast={false} />
      {/* flush plate */}
      <Box p={[0, 1.12, -0.1]} s={[0.11, 0.16, 0.01]} m={{ color: "#e8e2d6", roughness: 0.4, metalness: 0.2 }} />
      {/* bowl */}
      <mesh position={[0, 0.42, 0.05]} rotation={[Math.PI / 2, 0, 0]} castShadow scale={[1, 1, 0.7]}>
        <capsuleGeometry args={[0.19, 0.16, 8, 20]} />
        <meshPhysicalMaterial {...cer} />
      </mesh>
      {/* seat lid */}
      <RBox p={[0, 0.55, 0.06]} s={[0.36, 0.04, 0.5]} r={0.12} m={cer} />
      {/* toilet-paper holder on the wall */}
      <group position={[0, 0.75, 0.5]}>
        <Box p={[0, 0, -0.06]} s={[0.02, 0.03, 0.1]} m={BLACK} />
        <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.012, 0.012, 0.12, 10]} /><meshStandardMaterial {...BLACK} /></mesh>
        <mesh rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.055, 0.055, 0.1, 20]} /><meshStandardMaterial color="#f4f1ea" roughness={0.9} /></mesh>
      </group>
    </group>
  );
}

// ═══ FRAMED BOTANICAL ART (right wall, above the toilet) ══════════════════════
function WallArt() {
  const x = RIGHT_X - 0.04, z = 1.9;
  return (
    <group position={[x, 1.85, z]} rotation={[0, -Math.PI / 2, 0]}>
      <Box p={[0, 0, 0]} s={[0.5, 0.66, 0.02]} m={{ color: "#efe9dd", roughness: 0.5 }} cast={false} />
      <Box p={[0, 0, 0.011]} s={[0.42, 0.58, 0.005]} m={{ color: "#e7ded0", roughness: 0.7 }} cast={false} />
      {/* simple eucalyptus sprig */}
      <mesh position={[0, -0.16, 0.02]} rotation={[0, 0, 0.15]}><boxGeometry args={[0.006, 0.34, 0.004]} /><meshStandardMaterial color="#4a5c3e" roughness={0.8} /></mesh>
      {[0.02, 0.08, 0.14, 0.2].map((h, i) => (
        <group key={i} position={[0, -0.16 + h, 0.02]}>
          <mesh position={[-0.05, 0, 0]} rotation={[0, 0, 0.6]}><sphereGeometry args={[0.03, 8, 6]} /><meshStandardMaterial color="#5a6e4a" roughness={0.85} /></mesh>
          <mesh position={[0.05, 0, 0]} rotation={[0, 0, -0.6]}><sphereGeometry args={[0.03, 8, 6]} /><meshStandardMaterial color="#5a6e4a" roughness={0.85} /></mesh>
        </group>
      ))}
    </group>
  );
}

// ═══ RUNNER RUG (centre floor) ════════════════════════════════════════════════
function Rug() {
  return (
    <group>
      <Box p={[-0.35, 0.012, 1.0]} s={[0.92, 0.024, 2.7]}
        m={{ map: TEX().rug.map, bumpMap: TEX().rug.bump, bumpScale: 0.01, color: C.rug, roughness: 0.98, sheen: 0.6, sheenRoughness: 0.6, sheenColor: "#c6bca8" }} receive cast={false} />
      <Box p={[-0.35, 0.016, 1.0]} s={[0.84, 0.024, 2.6]} m={{ color: "#bcb2a0", roughness: 0.99 }} cast={false} />
    </group>
  );
}

// ═══ MISC FLOOR DECOR ═════════════════════════════════════════════════════════
function FloorDecor() {
  return (
    <group>
      {/* tall dark vase + branch near the tub (front-left of tub) */}
      <group position={[-0.9, 0, -0.9]}>
        <mesh position={[0, 0.28, 0]} castShadow><cylinderGeometry args={[0.09, 0.12, 0.56, 24]} /><meshPhysicalMaterial color={C.vase} roughness={0.32} metalness={0.1} clearcoat={0.35} /></mesh>
        {[0, 1, 2, 3].map((j) => (
          <mesh key={j} position={[Math.sin(j * 1.6) * 0.06, 0.72 + j * 0.06, Math.cos(j * 1.6) * 0.06]} rotation={[0, 0, (j - 1.5) * 0.3]}>
            <boxGeometry args={[0.008, 0.4, 0.02]} />
            <meshStandardMaterial color="#5a4a38" roughness={0.85} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

// ═══ LIGHTING ═════════════════════════════════════════════════════════════════
function Lighting() {
  return (
    <group>
      <ambientLight intensity={0.22} color="#ffe8d4" />
      {/* warm key from ceiling, shifted toward left to illuminate niche column */}
      <directionalLight
        position={[-1.0, 4.2, 3.0]} intensity={0.90} color="#ffe8cc"
        castShadow shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-6} shadow-camera-right={6}
        shadow-camera-top={6} shadow-camera-bottom={-6}
        shadow-bias={-0.0004}
      />
      {/* warm fill from camera side */}
      <directionalLight position={[-2, 2.5, 5]} intensity={0.28} color="#ffd8b0" />
      {/* general warm bounce */}
      <pointLight position={[-1.0, 2.2, 0.0]} intensity={0.9} color="#ffdcae" distance={8} decay={2} />
      {/* extra warm fill for left-wall vanity area */}
      <pointLight position={[-2.8, 1.8, 1.2]} intensity={0.8} color="#ffcc88" distance={4.0} decay={2} />
    </group>
  );
}
