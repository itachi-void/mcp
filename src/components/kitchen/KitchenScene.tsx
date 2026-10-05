import { useMemo } from "react";
import type { ReactNode } from "react";
import type * as THREE from "three";
import { RoundedBox } from "@react-three/drei";
import { brushed, fabric, pbrSet, tileFloor } from "./textures";

// ─────────────────────────────────────────────────────────────────────────────
//  MODERN LUXURY KITCHEN — Y-up scene matching the reference photo.
//  Convention:  x = left(-)/right(+)   y = up   z = back(-)/front-camera(+)
//  Floor at y=0, ceiling at y=H. Back wall z=-D/2, left wall x=-W/2.
// ─────────────────────────────────────────────────────────────────────────────

const C = {
  wall:       "#c3bdb2",
  ceiling:    "#d0cec9",
  floor:      "#ddd8cf",
  cabinet:    "#a89a88",   // warm taupe/greige flat-panel
  cabinetDark:"#8a7d6c",   // carcass / reveal shadow behind fronts
  drawerInt:  "#c7c1b5",   // pale interior of an open drawer
  trim:       "#101010",
  marble:     "#e8e5df",   // light quartz counter
  backsplash: "#d9d5cd",
  walnut:     "#3a2513",   // dark fluted wood
  shelfWood:  "#4a3320",
  blackApp:   "#0b0b0b",
  stainless:  "#8f9194",   // dark stainless
  steel:      "#c2c4c6",
  sink:       "#0d0d0d",
  fabric:     "#8a8079",   // taupe upholstery
  metal:      "#0a0a0a",
  ledWarm:    "#ffcf82",
  ledUnder:   "#ffe0a6",
  green:      "#2c5a2a",
  terracotta: "#b16b42",
  glass:      "#aecadf",
};

// Room
const W = 6.6, D = 6.0, H = 2.8;
const BASE_H = 0.9, BASE_D = 0.62, CT_T = 0.04;
const UPP_H = 0.74, UPP_D = 0.34, UPP_Y0 = 1.5; // upper cabinet bottom
const BACK_Z = -D / 2 + BASE_D / 2 + 0.02;   // base run center against back wall
const LEFT_X = -W / 2 + BASE_D / 2 + 0.02;   // base run center against left wall

// ── Real CC0 PBR maps (Poly Haven) served from /public/textures ──────────────
function buildTextures() {
  return {
    floor:    tileFloor("#e7ded1", [4, 4], 2), // large cream polished porcelain tiles
    counter:  pbrSet("marble", [2, 1]),
    walnut:   pbrSet("wood",   [3, 1]),
    shelf:    pbrSet("wood",   [2, 2]),
    steel:    brushed("#b9bdc1", [1, 5]),
    fabric:   fabric(C.fabric, [2, 2]),
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

function RBox({ p, s, m, r = 0.014, cast = true, receive = true }: {
  p: [number, number, number]; s: [number, number, number]; m: M; r?: number; cast?: boolean; receive?: boolean;
}) {
  return (
    <RoundedBox position={p} args={s} radius={Math.min(r, Math.min(...s) / 2 - 0.001)} smoothness={4} castShadow={cast} receiveShadow={receive}>
      <meshPhysicalMaterial {...m} />
    </RoundedBox>
  );
}

export default function KitchenScene() {
  return (
    <group>
      <Room />
      <BackRun />
      <LeftRun />
      <RangeHood />
      <Fridge />
      <DisplayNiche />
      <KitchenCabinetDetails />
      <Peninsula />
      <Stools />
      <Pendants />
      <KitchenDecorLights />
      <Lighting />
    </group>
  );
}

// ═══ ROOM ════════════════════════════════════════════════════════════════════
function Room() {
  const drop = 0.2, bord = 0.7, cz = H - drop;
  return (
    <group>
      {/* Glossy tile floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[W, D]} />
        <meshPhysicalMaterial map={TEX().floor.map} bumpMap={TEX().floor.bump} bumpScale={0.002}
          color="#ffffff" roughness={0.32} metalness={0.0} envMapIntensity={1.4}
          clearcoat={0.6} clearcoatRoughness={0.08} />
      </mesh>
      {/* Walls */}
      <Box p={[0, H / 2, -D / 2]} s={[W, H, 0.05]} m={{ color: C.wall, roughness: 0.95 }} cast={false} />
      <Box p={[-W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: C.wall, roughness: 0.95 }} cast={false} />
      <Box p={[W / 2, H / 2, 0]} s={[0.05, H, D]} m={{ color: C.wall, roughness: 0.95 }} cast={false} />
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
      {/* Warm cove LED (emissive) around inner tray */}
      {[
        { p: [0, cz - 0.02, -D / 2 + bord - 0.03], s: [W - bord, 0.04, 0.02] },
        { p: [-W / 2 + bord - 0.03, cz - 0.02, 0], s: [0.02, 0.04, D - bord * 2] },
        { p: [W / 2 - bord + 0.03, cz - 0.02, 0], s: [0.02, 0.04, D - bord * 2] },
      ].map((b, i) => (
        <Box key={i} p={b.p as [number, number, number]} s={b.s as [number, number, number]}
          m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 1.5, roughness: 1 }} cast={false} receive={false} />
      ))}
      {/* Recessed downlights: dark trim ring + bright blown-out lens (blooms) */}
      {[[-1.7, -1.4], [0, -1.4], [1.7, -1.4], [-1.7, 0.4], [1.7, 0.4], [0, 1.0]].map(([x, z], i) => (
        <group key={i} position={[x, H - 0.005, z]}>
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.062, 0.085, 28]} />
            <meshStandardMaterial color="#3a352f" roughness={0.4} metalness={0.5} side={2} />
          </mesh>
          <mesh position={[0, -0.012, 0]} rotation={[Math.PI / 2, 0, 0]}>
            <circleGeometry args={[0.062, 24]} />
            <meshStandardMaterial color="#ffffff" emissive="#fff2da" emissiveIntensity={4.2} roughness={1} toneMapped={false} />
          </mesh>
        </group>
      ))}
      {/* Window on left wall over the sink */}
      <Window />
      {/* Baseboards */}
      <Box p={[0, 0.05, -D / 2 + 0.06]} s={[W - 0.1, 0.1, 0.02]} m={{ color: "#d6d2cb", roughness: 0.5 }} cast={false} />
      <Box p={[-W / 2 + 0.06, 0.05, 0]} s={[0.02, 0.1, D - 0.1]} m={{ color: "#d6d2cb", roughness: 0.5 }} cast={false} />
    </group>
  );
}

function Window() {
  const x = -W / 2 + 0.06, y = 1.45, z = -1.35, w = 0.06, ww = 1.5, wh = 1.0;
  return (
    <group position={[x, y, z]}>
      <Box p={[0, 0, 0]} s={[w + 0.06, wh + 0.12, ww + 0.12]} m={{ color: "#e7e4df", roughness: 0.4 }} cast={false} />
      {/* sky glass */}
      <Box p={[-0.02, 0, 0]} s={[0.02, wh, ww]} m={{ color: "#cfe6f4", emissive: "#dff0ff", emissiveIntensity: 0.9, roughness: 0.1 }} cast={false} receive={false} />
      {/* muntins */}
      <Box p={[0.01, 0, 0]} s={[0.05, 0.03, ww]} m={{ color: "#e7e4df", roughness: 0.4 }} cast={false} />
      <Box p={[0.01, 0, 0]} s={[0.05, wh, 0.03]} m={{ color: "#e7e4df", roughness: 0.4 }} cast={false} />
    </group>
  );
}

// ── shared cabinet builders ─────────────────────────────────────────────────
const PROUD = 0.016;   // how far the door/drawer face sits in front of the carcass
const REV   = 0.008;   // reveal gap between fronts (reads as a thin shadow line)

// A single base unit: carcass + proud fronts (drawers or doors) with reveal gaps.
// `handleless` draws a J-pull groove instead of a bar (modern integrated look).
function BaseCabinet({
  p, w, along = "x", variant = "door", drawers = 3, handleless = true,
}: {
  p: [number, number, number]; w: number; along?: "x" | "z";
  variant?: "door" | "drawers"; drawers?: number; handleless?: boolean;
}) {
  const s: [number, number, number] = along === "x" ? [w, BASE_H, BASE_D] : [BASE_D, BASE_H, w];
  // u = the horizontal face-width axis, v = vertical (y)
  const facePos = (u: number, v: number, out = PROUD / 2): [number, number, number] =>
    along === "x"
      ? [p[0] + u, p[1] + v, p[2] + BASE_D / 2 + out]
      : [p[0] + BASE_D / 2 + out, p[1] + v, p[2] + u];
  const faceSize = (uLen: number, vLen: number, dep = PROUD): [number, number, number] =>
    along === "x" ? [uLen, vLen, dep] : [dep, vLen, uLen];

  const faceMat = { color: C.cabinet, roughness: 0.4, metalness: 0.0, envMapIntensity: 0.5 };
  const gripMat = { color: C.cabinetDark, roughness: 0.6 };
  const barMat  = { color: C.trim, roughness: 0.25, metalness: 0.7, envMapIntensity: 1.2 };

  const grip = (u: number, vTop: number, uLen: number) =>          // handleless J-groove
    <Box p={facePos(u, vTop - 0.018, -0.006)} s={faceSize(uLen, 0.02, 0.03)} m={gripMat} cast={false} />;
  const barH = (u: number, v: number, uLen: number) =>              // horizontal bar pull
    <Box p={facePos(u, v, PROUD + 0.014)} s={faceSize(uLen, 0.014, 0.02)} m={barMat} cast={false} />;
  const barV = (u: number, v: number, vLen: number) =>              // vertical bar pull
    <Box p={facePos(u, v, PROUD + 0.014)} s={faceSize(0.02, vLen, 0.02)} m={barMat} cast={false} />;

  const fronts: ReactNode[] = [];
  if (variant === "drawers") {
    const av = BASE_H - 2 * REV;
    const vLen = (av - (drawers - 1) * REV) / drawers;
    const uLen = w - 2 * REV;
    for (let i = 0; i < drawers; i++) {
      const v = -BASE_H / 2 + REV + vLen / 2 + i * (vLen + REV);
      fronts.push(
        <group key={`d${i}`}>
          <Box p={facePos(0, v)} s={faceSize(uLen, vLen)} m={faceMat} />
          {handleless ? grip(0, v + vLen / 2, uLen * 0.96) : barH(0, v + vLen / 2 - 0.05, Math.min(uLen * 0.5, 0.3))}
        </group>,
      );
    }
  } else {
    const nd = w > 0.62 ? 2 : 1;
    const uLen = (w - 2 * REV - (nd - 1) * REV) / nd;
    const vLen = BASE_H - 2 * REV;
    for (let k = 0; k < nd; k++) {
      const u = -w / 2 + REV + uLen / 2 + k * (uLen + REV);
      const inner = u + (k === 0 ? uLen / 2 - 0.03 : -uLen / 2 + 0.03);
      fronts.push(
        <group key={`o${k}`}>
          <Box p={facePos(u, 0)} s={faceSize(uLen, vLen)} m={faceMat} />
          {handleless ? grip(u, vLen / 2, uLen * 0.96) : barV(inner, 0, vLen * 0.5)}
        </group>,
      );
    }
  }

  return (
    <group>
      {/* carcass sits slightly recessed & darker so the reveals read */}
      <Box p={p} s={s} m={{ color: C.cabinetDark, roughness: 0.5, metalness: 0.0, envMapIntensity: 0.4 }} />
      {fronts}
    </group>
  );
}

// A pulled-open drawer showing its interior box + cutlery dividers (hero detail).
function OpenDrawer({ p, w, out = 0.34 }: { p: [number, number, number]; w: number; out?: number }) {
  const y = p[1], z = p[2];
  const dh = 0.16, dd = BASE_D - 0.06;
  const front = z + BASE_D / 2 + out;         // pulled toward camera (+z)
  return (
    <group>
      {/* the carcass with the opening dark void where the drawer was */}
      <Box p={p} s={[w, BASE_H, BASE_D]} m={{ color: C.cabinetDark, roughness: 0.5 }} />
      <Box p={[p[0], y + BASE_H / 2 - 0.13, z + 0.02]} s={[w - 2 * REV, 0.2, BASE_D - 0.04]} m={{ color: "#2a2724", roughness: 0.9 }} cast={false} />
      {/* the drawer box, pulled out */}
      <group>
        {/* front panel */}
        <Box p={[p[0], y + BASE_H / 2 - 0.13, front]} s={[w - 2 * REV, dh + 0.06, PROUD]} m={{ color: C.cabinet, roughness: 0.4, envMapIntensity: 0.5 }} />
        <Box p={[p[0], y + BASE_H / 2 - 0.06, front + 0.006]} s={[(w - 2 * REV) * 0.96, 0.02, 0.03]} m={{ color: C.cabinetDark, roughness: 0.6 }} cast={false} />
        {/* interior box: base + 4 walls (pale) */}
        <Box p={[p[0], y + BASE_H / 2 - 0.2, front - dd / 2 - PROUD / 2]} s={[w - 0.08, 0.02, dd]} m={{ color: C.drawerInt, roughness: 0.7 }} />
        <Box p={[p[0], y + BASE_H / 2 - 0.14, front - dd - PROUD / 2]} s={[w - 0.08, dh, 0.02]} m={{ color: C.drawerInt, roughness: 0.7 }} cast={false} />
        <Box p={[p[0] - (w - 0.08) / 2, y + BASE_H / 2 - 0.14, front - dd / 2 - PROUD / 2]} s={[0.02, dh, dd]} m={{ color: C.drawerInt, roughness: 0.7 }} cast={false} />
        <Box p={[p[0] + (w - 0.08) / 2, y + BASE_H / 2 - 0.14, front - dd / 2 - PROUD / 2]} s={[0.02, dh, dd]} m={{ color: C.drawerInt, roughness: 0.7 }} cast={false} />
        {/* wooden cutlery dividers + utensils */}
        {[-0.22, -0.07, 0.08, 0.23].map((dx) => (
          <Box key={dx} p={[p[0] + dx, y + BASE_H / 2 - 0.17, front - dd / 2 - PROUD / 2]} s={[0.012, 0.07, dd - 0.04]} m={{ color: C.shelfWood, roughness: 0.7 }} cast={false} />
        ))}
        {[-0.15, 0.0, 0.16].map((dx, i) => (
          <mesh key={i} position={[p[0] + dx, y + BASE_H / 2 - 0.185, front - dd / 2]} rotation={[Math.PI / 2, 0, 0]} castShadow>
            <cylinderGeometry args={[0.012, 0.012, dd - 0.12, 10]} />
            <meshStandardMaterial color={C.steel} roughness={0.3} metalness={0.8} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

// A concealed full-height integrated unit (tall handleless pantry / appliance surround).
function TallCabinet({ p, w, h, d = BASE_D, doors = 2 }: {
  p: [number, number, number]; w: number; h: number; d?: number; doors?: number;
}) {
  const uLen = (w - 2 * REV - (doors - 1) * REV) / doors;
  const vLen = h - 2 * REV;
  return (
    <group>
      <Box p={p} s={[w, h, d]} m={{ color: C.cabinetDark, roughness: 0.5, envMapIntensity: 0.4 }} />
      {Array.from({ length: doors }, (_, k) => {
        const u = -w / 2 + REV + uLen / 2 + k * (uLen + REV);
        return (
          <group key={k}>
            <Box p={[p[0] + u, p[1], p[2] + d / 2 + PROUD / 2]} s={[uLen, vLen, PROUD]} m={{ color: C.cabinet, roughness: 0.4, envMapIntensity: 0.5 }} />
            {/* full-height handleless J-groove on the opening edge */}
            <Box p={[p[0] + u + (k === 0 ? uLen / 2 - 0.02 : -uLen / 2 + 0.02), p[1], p[2] + d / 2 - 0.004]}
              s={[0.02, vLen * 0.98, 0.03]} m={{ color: C.cabinetDark, roughness: 0.6 }} cast={false} />
          </group>
        );
      })}
    </group>
  );
}

function UpperCabinet({ p, w, glass, along = "x" }: { p: [number, number, number]; w: number; glass?: boolean; along?: "x" | "z" }) {
  const s: [number, number, number] = along === "x" ? [w, UPP_H, UPP_D] : [UPP_D, UPP_H, w];
  const faceOff = along === "x" ? [0, 0, UPP_D / 2] : [UPP_D / 2, 0, 0];
  return (
    <group>
      <Box p={p} s={s} m={{ color: glass ? C.walnut : C.cabinet, roughness: glass ? 0.5 : 0.42, envMapIntensity: 0.5 }} />
      {glass && (
        <>
          <Box p={[p[0] + faceOff[0] * 0.6, p[1], p[2] + faceOff[2] * 0.6] as [number, number, number]}
            s={along === "x" ? [w * 0.86, UPP_H * 0.86, 0.02] : [0.02, UPP_H * 0.86, w * 0.86]}
            m={{ color: C.glass, transparent: true, opacity: 0.22, roughness: 0.04, metalness: 0.0, envMapIntensity: 1.6 }} cast={false} />
          {/* interior warm light */}
          <Box p={[p[0], p[1] + UPP_H / 2 - 0.05, p[2]] as [number, number, number]}
            s={along === "x" ? [w * 0.8, 0.03, UPP_D * 0.6] : [UPP_D * 0.6, 0.03, w * 0.8]}
            m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 1.8, roughness: 1 }} cast={false} receive={false} />
          {/* A restrained stack of porcelain makes the lit glass cabinets feel lived-in. */}
          {[0.24, 0.28, 0.32].map((yy, i) => (
            <mesh key={i} position={along === "x" ? [p[0] - w * 0.2, p[1] - UPP_H * 0.22 + yy, p[2] + UPP_D * 0.18] : [p[0] + UPP_D * 0.18, p[1] - UPP_H * 0.22 + yy, p[2] - w * 0.2]} castShadow>
              <cylinderGeometry args={[0.075 - i * 0.004, 0.075 - i * 0.004, 0.012, 24]} />
              <meshPhysicalMaterial color="#eee9df" roughness={0.22} clearcoat={0.15} />
            </mesh>
          ))}
        </>
      )}
    </group>
  );
}

function Counter({ p, s }: { p: [number, number, number]; s: [number, number, number] }) {
  return <RBox p={p} s={s} r={0.01} m={{ map: TEX().counter.map, roughnessMap: TEX().counter.rgh, normalMap: TEX().counter.nrm, color: "#ffffff", roughness: 0.9, metalness: 0.0, envMapIntensity: 1.4, clearcoat: 0.7, clearcoatRoughness: 0.06 }} />;
}

// ═══ BACK WALL RUN ════════════════════════════════════════════════════════════
function BackRun() {
  const y = BASE_H / 2;
  const cty = BASE_H + CT_T / 2;
  const runL = -2.7, runR = 1.6;               // counter span
  return (
    <group>
      {/* base cabinets — mix of doors + drawer stacks, handleless (modern) */}
      <BaseCabinet p={[-2.4, y, BACK_Z]} w={0.86} variant="door" />
      <BaseCabinet p={[-1.5, y, BACK_Z]} w={0.86} variant="drawers" drawers={3} />
      <BaseCabinet p={[-0.6, y, BACK_Z]} w={0.86} variant="drawers" drawers={2} />
      <BaseCabinet p={[0.35, y, BACK_Z]} w={0.86} variant="door" />
      {/* pulled-open drawer (pull-out with cutlery dividers) */}
      <OpenDrawer p={[1.25, y, BACK_Z]} w={0.86} out={0.32} />
      {/* countertop */}
      <Counter p={[(runL + runR) / 2, cty, BACK_Z]} s={[runR - runL, CT_T, BASE_D + 0.04]} />
      {/* backsplash */}
      <Box p={[(runL + runR) / 2, (BASE_H + CT_T + UPP_Y0) / 2 + 0.02, -D / 2 + 0.03]}
        s={[runR - runL, UPP_Y0 - BASE_H - CT_T, 0.02]} m={{ color: C.backsplash, roughness: 0.18, metalness: 0.03, clearcoat: 0.6, clearcoatRoughness: 0.1 }} cast={false} />
      {/* upper cabinets flanking the hood */}
      <UpperCabinet p={[-2.1, UPP_Y0 + UPP_H / 2, -D / 2 + UPP_D / 2 + 0.02]} w={1.1} />
      <UpperCabinet p={[1.05, UPP_Y0 + UPP_H / 2, -D / 2 + UPP_D / 2 + 0.02]} w={0.9} />
      {/* under-cabinet warm strips */}
      {[-2.1, 1.05].map((x, i) => (
        <Box key={i} p={[x, UPP_Y0 - 0.02, -D / 2 + UPP_D + 0.04]} s={[i === 0 ? 1.1 : 0.9, 0.02, 0.03]}
          m={{ color: C.ledUnder, emissive: C.ledUnder, emissiveIntensity: 1.6, roughness: 1 }} cast={false} receive={false} />
      ))}
      {/* cooktop + pot */}
      <Cooktop x={-0.55} z={BACK_Z} />
      {/* counter styling: cutting board + jars */}
      <Box p={[0.55, cty + CT_T / 2 + 0.012, BACK_Z - 0.02]} s={[0.24, 0.02, 0.34]} m={{ color: C.shelfWood, roughness: 0.6 }} />
      {[0.15, 0.28, 0.41].map((x, i) => (
        <mesh key={i} position={[x, cty + 0.09, BACK_Z + 0.1]} castShadow>
          <cylinderGeometry args={[0.028, 0.028, 0.14, 14]} />
          <meshStandardMaterial color="#9a8258" roughness={0.1} transparent opacity={0.7} />
        </mesh>
      ))}
      <Plant p={[-2.15, cty + CT_T / 2, BACK_Z]} scale={0.75} />
    </group>
  );
}

function Cooktop({ x, z }: { x: number; z: number }) {
  const y = BASE_H + CT_T + 0.01;
  return (
    <group>
      <RBox p={[x, y, z]} s={[0.78, 0.02, 0.5]} r={0.008} m={{ color: "#080808", roughness: 0.1, metalness: 0.1, envMapIntensity: 1.4, clearcoat: 0.6, clearcoatRoughness: 0.08 }} />
      {[[-0.18, 0.1], [-0.18, -0.1], [0.14, 0.1], [0.14, -0.1]].map(([bx, bz], i) => (
        <mesh key={i} position={[x + bx, y + 0.03, z + bz]}>
          <cylinderGeometry args={[0.055, 0.055, 0.02, 18]} />
          <meshStandardMaterial color={C.metal} roughness={0.4} metalness={0.6} />
        </mesh>
      ))}
      {/* pot */}
      <mesh position={[x - 0.16, y + 0.11, z]} castShadow>
        <cylinderGeometry args={[0.1, 0.1, 0.16, 24]} />
        <meshStandardMaterial color="#141414" roughness={0.3} metalness={0.7} />
      </mesh>
      <mesh position={[x - 0.16, y + 0.2, z]} castShadow>
        <cylinderGeometry args={[0.105, 0.105, 0.02, 24]} />
        <meshStandardMaterial color="#141414" roughness={0.3} metalness={0.7} />
      </mesh>
    </group>
  );
}

// ═══ LEFT WALL RUN (sink under window) ════════════════════════════════════════
function LeftRun() {
  const y = BASE_H / 2;
  const cty = BASE_H + CT_T / 2;
  const runB = -2.4, runF = -0.2;
  return (
    <group>
      <BaseCabinet p={[LEFT_X, y, -2.1]} w={0.72} along="z" variant="drawers" drawers={3} />
      <BaseCabinet p={[LEFT_X, y, -1.35]} w={0.72} along="z" variant="door" />
      <BaseCabinet p={[LEFT_X, y, -0.6]} w={0.72} along="z" variant="drawers" drawers={2} />
      {/* concealed full-height tall pantry at the end of the run (integrated units) */}
      <TallCabinet p={[LEFT_X, 2.35 / 2, 0.15]} w={0.72} h={2.35} doors={2} />
      <Counter p={[LEFT_X, cty, (runB + runF) / 2]} s={[BASE_D + 0.04, CT_T, runF - runB]} />
      {/* glass-front upper cabinets */}
      <UpperCabinet p={[-W / 2 + UPP_D / 2 + 0.02, UPP_Y0 + UPP_H / 2, -0.55]} w={1.0} glass along="z" />
      <UpperCabinet p={[-W / 2 + UPP_D / 2 + 0.02, UPP_Y0 + UPP_H / 2, -2.15]} w={0.9} along="z" />
      {/* under-cabinet strip */}
      <Box p={[-W / 2 + UPP_D + 0.04, UPP_Y0 - 0.02, -1.4]} s={[0.03, 0.02, 2.0]}
        m={{ color: C.ledUnder, emissive: C.ledUnder, emissiveIntensity: 1.6, roughness: 1 }} cast={false} receive={false} />
      {/* sink + faucet */}
      <Sink x={LEFT_X + 0.05} z={-1.35} />
    </group>
  );
}

function Sink({ x, z }: { x: number; z: number }) {
  const top = BASE_H + CT_T;
  return (
    <group>
      <Box p={[x, top - 0.02, z]} s={[0.42, 0.04, 0.62]} m={{ color: C.sink, roughness: 0.2, metalness: 0.4 }} />
      <Box p={[x, top - 0.09, z]} s={[0.34, 0.12, 0.54]} m={{ color: "#050505", roughness: 0.15, metalness: 0.5 }} cast={false} />
      {/* gooseneck faucet */}
      <mesh position={[x - 0.02, top + 0.16, z - 0.22]} castShadow>
        <cylinderGeometry args={[0.018, 0.018, 0.32, 12]} />
        <meshStandardMaterial color={C.trim} roughness={0.15} metalness={0.7} />
      </mesh>
      <mesh position={[x + 0.05, top + 0.32, z - 0.16]} rotation={[0, 0, Math.PI / 2]} castShadow>
        <torusGeometry args={[0.08, 0.017, 10, 20, Math.PI]} />
        <meshStandardMaterial color={C.trim} roughness={0.15} metalness={0.7} />
      </mesh>
    </group>
  );
}

// ═══ RANGE HOOD ═══════════════════════════════════════════════════════════════
// ═══ LIVED-IN CABINETRY ═════════════════════════════════════════════════════
// The reference images favour a few purposeful moments of access over a kitchen
// full of permanently-open doors. These sit on top of the architectural cabinetry.
function KitchenCabinetDetails() {
  const frontX = LEFT_X + BASE_D / 2 + 0.02;
  const steel = { color: C.steel, roughness: 0.24, metalness: 0.88, envMapIntensity: 1.3 } as M;
  const interior = { color: C.drawerInt, roughness: 0.68 } as M;
  return (
    <group>
      {/* Integrated dishwasher: only the dark control seam and status light interrupt the taupe front. */}
      <Box p={[frontX, 0.45, -0.6]} s={[0.022, 0.68, 0.82]} m={{ color: C.cabinet, roughness: 0.4 }} />
      <Box p={[frontX + 0.012, 0.77, -0.6]} s={[0.028, 0.61, 0.028]} m={{ color: C.blackApp, roughness: 0.2, metalness: 0.45 }} cast={false} />
      <Box p={[frontX + 0.016, 0.77, -0.36]} s={[0.03, 0.02, 0.012]} m={{ color: "#e6b65a", emissive: "#e6b65a", emissiveIntensity: 1.8 }} cast={false} receive={false} />

      {/* Under-sink twin pull-outs: one concealed waste bin, one shallow cleaning caddy. */}
      <Box p={[frontX + 0.16, 0.31, -1.35]} s={[0.32, 0.27, 0.58]} m={interior} />
      <Box p={[frontX + 0.16, 0.31, -1.65]} s={[0.32, 0.27, 0.04]} m={steel} />
      <Box p={[frontX + 0.16, 0.31, -1.05]} s={[0.32, 0.27, 0.04]} m={steel} />
      <RBox p={[frontX + 0.16, 0.26, -1.5]} s={[0.25, 0.18, 0.19]} r={0.01} m={{ color: "#d9d4cc", roughness: 0.72 }} />
      <RBox p={[frontX + 0.16, 0.26, -1.2]} s={[0.25, 0.18, 0.19]} r={0.01} m={{ color: "#5c5a54", roughness: 0.72 }} />
      {[[-1.53, "#d9d4cc"], [-1.43, "#677966"], [-1.26, "#ece7de"], [-1.16, "#b7895f"]].map(([z, color], i) => (
        <mesh key={i} position={[frontX + 0.16, 0.51, z as number]} rotation={[0, 0, Math.PI / 2]} castShadow>
          <cylinderGeometry args={[0.032, 0.032, 0.13, 14]} /><meshStandardMaterial color={color as string} roughness={0.45} />
        </mesh>
      ))}

      {/* A single cookware roll-out on the back run, with slim steel rails and nested pans. */}
      <Box p={[0.35, 0.23, BACK_Z + BASE_D / 2 + 0.24]} s={[0.78, 0.36, 0.17]} m={interior} />
      {[-0.32, 0.32].map((dx) => <Box key={dx} p={[0.35 + dx, 0.23, BACK_Z + BASE_D / 2 + 0.24]} s={[0.018, 0.36, 0.18]} m={steel} cast={false} />)}
      {[0.09, 0.15].map((r, i) => (
        <group key={r} position={[0.35 + (i ? 0.14 : -0.13), 0.31, BACK_Z + BASE_D / 2 + 0.23]} rotation={[Math.PI / 2, 0, 0]}>
          <mesh castShadow><cylinderGeometry args={[r, r * 0.88, 0.06, 24, 1, true]} /><meshStandardMaterial color="#383a3c" roughness={0.25} metalness={0.85} /></mesh>
          <mesh position={[r * 1.3, 0, 0]}><boxGeometry args={[r * 0.9, 0.025, 0.035]} /><meshStandardMaterial color="#222222" roughness={0.45} /></mesh>
        </group>
      ))}

      {/* Narrow oil-and-spice pull-out: the reference's useful detail without countertop clutter. */}
      <Box p={[1.35, 0.38, BACK_Z + BASE_D / 2 + 0.17]} s={[0.22, 0.24, 0.62]} m={interior} />
      {[0.17, 0.4, 0.62].map((yy) => <Box key={yy} p={[1.35, yy, BACK_Z + BASE_D / 2 + 0.17]} s={[0.22, 0.02, 0.04]} m={steel} cast={false} />)}
      {[[-0.06, 0.27, "#6d8b67"], [0.01, 0.44, "#b8945d"], [0.07, 0.27, "#7f5436"]].map(([dx, yy, color], i) => (
        <mesh key={i} position={[1.35 + dx as number, yy as number, BACK_Z + BASE_D / 2 + 0.17]} castShadow>
          <cylinderGeometry args={[0.025, 0.025, 0.17, 12]} /><meshStandardMaterial color={color as string} roughness={0.25} transparent opacity={0.82} />
        </mesh>
      ))}
    </group>
  );
}

function RangeHood() {
  const x = -0.55, z = -D / 2 + 0.28;
  return (
    <group>
      <RBox p={[x, 1.62, z]} s={[0.9, 0.34, 0.52]} r={0.03} m={{ color: C.blackApp, roughness: 0.18, metalness: 0.4, envMapIntensity: 1.2, clearcoat: 0.8, clearcoatRoughness: 0.15 }} />
      <Box p={[x, 1.62, z + 0.27]} s={[0.94, 0.36, 0.02]} m={{ color: "#141414", roughness: 0.08, metalness: 0.5, envMapIntensity: 1.3 }} cast={false} />
      <Box p={[x, 2.2, z - 0.05]} s={[0.4, 0.9, 0.4]} m={{ color: C.blackApp, roughness: 0.18, metalness: 0.4, envMapIntensity: 1.2 }} />
      {/* hood light glow */}
      <Box p={[x, 1.45, z + 0.15]} s={[0.7, 0.02, 0.2]} m={{ color: C.ledUnder, emissive: C.ledUnder, emissiveIntensity: 1.2, roughness: 1 }} cast={false} receive={false} />
    </group>
  );
}

// ═══ FRIDGE (French-door, right end of back wall) ═════════════════════════════
function Fridge() {
  const w = 0.9, d = 0.72, h = 2.5;
  const x = W / 2 - w / 2 - 0.1, z = -D / 2 + d / 2 + 0.02;
  return (
    <group>
      <RBox p={[x, h / 2, z]} s={[w, h, d]} r={0.02} m={{ map: TEX().steel.map, roughnessMap: TEX().steel.rough, color: "#565a5e", roughness: 0.4, metalness: 0.9, envMapIntensity: 1.6 }} />
      {/* door split */}
      <Box p={[x, h * 0.62, z + d / 2 + 0.002]} s={[0.008, h * 0.72, 0.01]} m={{ color: "#3a3c3e", roughness: 0.3, metalness: 0.6 }} cast={false} />
      <Box p={[x, h * 0.26, z + d / 2 + 0.002]} s={[w * 0.94, 0.008, 0.01]} m={{ color: "#3a3c3e", roughness: 0.3, metalness: 0.6 }} cast={false} />
      {/* handles */}
      {[-0.18, 0.18].map((hx) => (
        <Box key={hx} p={[x + hx, h * 0.72, z + d / 2 + 0.03]} s={[0.03, 0.55, 0.04]} m={{ color: C.steel, roughness: 0.22, metalness: 0.95, envMapIntensity: 1.5 }} cast={false} />
      ))}
      {/* water/ice dispenser */}
      <Box p={[x - 0.2, h * 0.7, z + d / 2 + 0.006]} s={[0.22, 0.36, 0.02]} m={{ color: "#101112", roughness: 0.2, metalness: 0.5 }} cast={false} />
      {/* built-in surround: side panels + concealed cabinet above (integrated unit) */}
      <Box p={[x - w / 2 - 0.04, h / 2, z]} s={[0.04, h, d]} m={{ color: C.cabinetDark, roughness: 0.5 }} cast={false} />
      <Box p={[x + w / 2 + 0.04, h / 2, z]} s={[0.04, h, d]} m={{ color: C.cabinetDark, roughness: 0.5 }} cast={false} />
      <TallCabinet p={[x, (h + H) / 2, z + (d - BASE_D) / 2]} w={w + 0.16} h={H - h - 0.03} d={BASE_D} doors={2} />
    </group>
  );
}

// ═══ GLASS DISPLAY NICHE (right, above counter left of fridge) ════════════════
function DisplayNiche() {
  const x = W / 2 - 0.1 - 0.9 - 0.34, z = -D / 2 + 0.24;
  const y0 = 1.35, nh = 1.0, nw = 0.62;
  return (
    <group>
      <Box p={[x, y0 + nh / 2, z]} s={[nw, nh, 0.44]} m={{ color: C.walnut, roughness: 0.5 }} />
      {/* recessed lit back */}
      <Box p={[x, y0 + nh / 2, z - 0.18]} s={[nw - 0.06, nh - 0.06, 0.02]} m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 1.1, roughness: 1 }} cast={false} receive={false} />
      {/* glass shelf */}
      <Box p={[x, y0 + nh / 2, z]} s={[nw - 0.04, 0.02, 0.4]} m={{ color: C.glass, transparent: true, opacity: 0.35, roughness: 0.05 }} cast={false} />
      <Plant p={[x, y0 + nh / 2 + 0.01, z + 0.05]} scale={0.55} />
      <mesh position={[x + 0.14, y0 + 0.14, z + 0.05]} castShadow>
        <cylinderGeometry args={[0.05, 0.04, 0.18, 18]} />
        <meshStandardMaterial color="#8a7d6a" roughness={0.35} />
      </mesh>
    </group>
  );
}

// ═══ PENINSULA (foreground) ═══════════════════════════════════════════════════
function Peninsula() {
  const IW = 2.3, ID = 0.62, IH = 0.9;
  const ix = -0.35, iz = 0.9;
  const cty = IH + CT_T / 2;
  const slatW = 0.035, gap = 0.05;
  const n = Math.floor(IW * 0.8 / (slatW + gap));
  const x0 = ix - (n - 1) * (slatW + gap) / 2;
  const slats = useMemo(() => Array.from({ length: n }, (_, i) => x0 + i * (slatW + gap)), [n, x0]);
  return (
    <group>
      {/* body */}
      <RBox p={[ix, IH / 2, iz]} s={[IW, IH, ID]} r={0.02} m={{ map: TEX().walnut.map, roughnessMap: TEX().walnut.rgh, normalMap: TEX().walnut.nrm, color: "#8a6038", roughness: 0.72, envMapIntensity: 0.5 }} />
      {/* fluted vertical slats on the camera-facing front (+z) */}
      {slats.map((sx, i) => (
        <Box key={i} p={[sx, IH / 2, iz + ID / 2 + 0.012]} s={[slatW, IH * 0.94, 0.024]} m={{ map: TEX().walnut.map, normalMap: TEX().walnut.nrm, color: "#8a5f38", roughness: 0.6, envMapIntensity: 0.5 }} cast={false} />
      ))}
      {/* waterfall stone top */}
      <Counter p={[ix, cty, iz]} s={[IW + 0.06, CT_T, ID + 0.06]} />
      {/* waterfall side (right end drops to floor) */}
      <RBox p={[ix + IW / 2 + 0.02, IH / 2 + CT_T / 2, iz]} s={[CT_T, IH + CT_T, ID + 0.06]} r={0.01} m={{ map: TEX().counter.map, roughnessMap: TEX().counter.rgh, normalMap: TEX().counter.nrm, color: "#ffffff", roughness: 0.9, clearcoat: 0.7, clearcoatRoughness: 0.06 }} />
      {/* open shelf cube on right end (camera side) */}
      <group position={[ix + IW / 2 - 0.28, 0, iz + 0.02]}>
        <Box p={[0, IH / 2, 0]} s={[0.5, IH, ID - 0.04]} m={{ map: TEX().shelf.map, roughnessMap: TEX().shelf.rgh, normalMap: TEX().shelf.nrm, color: "#6f4c2c", roughness: 0.7 }} />
        {[0.28, 0.6].map((yy) => (
          <Box key={yy} p={[0, yy, 0.02]} s={[0.44, 0.02, ID - 0.1]} m={{ map: TEX().shelf.map, normalMap: TEX().shelf.nrm, color: "#6f4c2c", roughness: 0.7 }} />
        ))}
        <Box p={[0, 0.44, -0.02]} s={[0.4, 0.02, 0.1]} m={{ color: C.ledWarm, emissive: C.ledWarm, emissiveIntensity: 1.2, roughness: 1 }} cast={false} receive={false} />
        {/* props */}
        <mesh position={[0.1, 0.7, 0.06]} castShadow>
          <cylinderGeometry args={[0.06, 0.045, 0.09, 18]} />
          <meshStandardMaterial color="#efece7" roughness={0.3} />
        </mesh>
        <Plant p={[-0.08, 0.6, 0.06]} scale={0.45} />
        <mesh position={[0.02, 0.36, 0.06]} castShadow>
          <cylinderGeometry args={[0.07, 0.06, 0.1, 12]} />
          <meshStandardMaterial color="#9a7a48" roughness={0.9} />
        </mesh>
      </group>
      {/* tray + cups + plant on top */}
      <Box p={[ix - 0.35, cty + CT_T / 2 + 0.012, iz]} s={[0.34, 0.024, 0.26]} m={{ color: "#5e451f", roughness: 0.6 }} />
      {[-0.42, -0.28].map((dx) => (
        <mesh key={dx} position={[ix + dx, cty + 0.06, iz]} castShadow>
          <cylinderGeometry args={[0.035, 0.03, 0.08, 16]} />
          <meshStandardMaterial color="#ece9e4" roughness={0.3} />
        </mesh>
      ))}
      <Plant p={[ix - 0.05, cty + CT_T / 2, iz]} scale={0.5} />
    </group>
  );
}

// ═══ STOOLS ══════════════════════════════════════════════════════════════════
function Stool({ x, z }: { x: number; z: number }) {
  const sh = 0.62;
  // supple off-white leather: rounded cushions, low roughness for a soft sheen, faint clearcoat
  const leather = {
    map: TEX().fabric.map, bumpMap: TEX().fabric.bump, bumpScale: 0.004,
    color: "#ece6da", roughness: 0.55, metalness: 0, envMapIntensity: 0.6,
    clearcoat: 0.35, clearcoatRoughness: 0.5,
  } as unknown as M;
  return (
    <group position={[x, 0, z]}>
      {/* seat cushion */}
      <RBox p={[0, sh, 0]} s={[0.42, 0.13, 0.4]} m={leather} r={0.05} />
      {/* curved back cushion, slightly reclined */}
      <group position={[0, sh + 0.24, -0.16]} rotation={[-0.08, 0, 0]}>
        <RBox p={[0, 0, 0]} s={[0.4, 0.4, 0.09]} m={leather} r={0.05} />
      </group>
      {/* pedestal */}
      <mesh position={[0, sh / 2, 0]} castShadow>
        <cylinderGeometry args={[0.03, 0.03, sh, 16]} />
        <meshStandardMaterial color={C.metal} roughness={0.2} metalness={0.85} />
      </mesh>
      <mesh position={[0, 0.03, 0]} castShadow>
        <cylinderGeometry args={[0.24, 0.24, 0.05, 28]} />
        <meshStandardMaterial color={C.metal} roughness={0.2} metalness={0.85} />
      </mesh>
      {/* footrest ring */}
      <mesh position={[0, 0.24, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.14, 0.012, 8, 24]} />
        <meshStandardMaterial color={C.metal} roughness={0.25} metalness={0.8} />
      </mesh>
    </group>
  );
}

function Stools() {
  return (
    <>
      <Stool x={-0.95} z={1.62} />
      <Stool x={-0.2} z={1.62} />
    </>
  );
}

// ═══ PENDANTS (Edison, over peninsula) ════════════════════════════════════════
function Pendant({ x, z, drop }: { x: number; z: number; drop: number }) {
  const top = H - 0.04;
  const shadeY = top - drop;
  return (
    <group position={[x, 0, z]}>
      {/* ceiling canopy */}
      <mesh position={[0, top - 0.02, 0]}>
        <cylinderGeometry args={[0.05, 0.055, 0.03, 20]} />
        <meshStandardMaterial color="#2a2320" roughness={0.35} metalness={0.9} envMapIntensity={1.4} />
      </mesh>
      {/* braided cord */}
      <mesh position={[0, (top + shadeY) / 2, 0]}>
        <cylinderGeometry args={[0.006, 0.006, top - shadeY, 8]} />
        <meshStandardMaterial color="#1a1712" roughness={0.7} />
      </mesh>
      {/* matte-black tapered cone shade (matches reference) */}
      <mesh position={[0, shadeY, 0]} castShadow>
        <cylinderGeometry args={[0.052, 0.095, 0.27, 32, 1, true]} />
        <meshStandardMaterial color="#111111" roughness={0.5} metalness={0.4} envMapIntensity={0.9} side={2} />
      </mesh>
      {/* warm reflective interior of the shade */}
      <mesh position={[0, shadeY - 0.01, 0]}>
        <cylinderGeometry args={[0.046, 0.089, 0.25, 32, 1, true]} />
        <meshStandardMaterial color="#ffd9a0" emissive="#ffbe66" emissiveIntensity={1.4} roughness={0.5} metalness={0.6} side={1} />
      </mesh>
      {/* glowing opal glow disk at the mouth (spills light, blooms) */}
      <mesh position={[0, shadeY - 0.125, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.094, 32]} />
        <meshStandardMaterial color="#fff0d0" emissive="#ffcd7a" emissiveIntensity={3.0} roughness={1} />
      </mesh>
      {/* Edison bulb: glass envelope + bright filament */}
      <mesh position={[0, shadeY - 0.16, 0]}>
        <sphereGeometry args={[0.052, 20, 20]} />
        <meshStandardMaterial color="#ffe4ad" emissive="#ffbe4a" emissiveIntensity={5.5} roughness={1} transparent opacity={0.92} />
      </mesh>
      <mesh position={[0, shadeY - 0.16, 0]}>
        <boxGeometry args={[0.006, 0.05, 0.006]} />
        <meshStandardMaterial color="#fff2c0" emissive="#ffd257" emissiveIntensity={8} roughness={1} toneMapped={false} />
      </mesh>
      {/* actual light thrown on the counter below */}
      <pointLight position={[0, shadeY - 0.2, 0]} intensity={6} color="#ffb655" distance={2.6} decay={2} />
    </group>
  );
}

function Pendants() {
  return (
    <>
      <Pendant x={-1.0} z={0.95} drop={0.85} />
      <Pendant x={-0.5} z={0.95} drop={1.05} />
    </>
  );
}

// ═══ SHARED: potted plant ════════════════════════════════════════════════════
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

// ═══ KITCHEN DECOR LIGHTS — LED strips, toe-kick, spots, linear pendant ════════
function KitchenDecorLights() {
  const ledWarm  = "#ffd088";
  const ledCool  = "#deeeff";
  // upper-cabinet bottom face z — front edge of back-wall upper cabinets
  const ucFrontZ = -D / 2 + UPP_D + 0.04;
  // back-wall upper cabinet x run spans ≈ -2.8 to +2.8 minus fridge/hood zone
  const ucXStart = -2.2, ucXEnd = 1.4;
  const ucY      = UPP_Y0 - 0.015;   // just below the upper cabinet bottom

  return (
    <>
      {/* ── UNDER-CABINET LED STRIPS (back wall run) ── */}
      {/* visible emissive strip geometry sitting flush at the bottom of upper cabinets */}
      <Box p={[(ucXStart + ucXEnd) / 2, ucY, ucFrontZ - 0.01]} s={[ucXEnd - ucXStart, 0.012, 0.016]}
        m={{ color: ledCool, emissive: ledCool, emissiveIntensity: 3.5, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-1.2, ucY - 0.1, ucFrontZ + 0.1]} intensity={5} color="#dff0ff" distance={2.2} decay={2} />
      <pointLight position={[ 0.2, ucY - 0.1, ucFrontZ + 0.1]} intensity={5} color="#dff0ff" distance={2.2} decay={2} />

      {/* ── UNDER-CABINET LED STRIPS (left wall run — above the sink) ── */}
      <Box p={[-W / 2 + UPP_D / 2 + 0.04, ucY, -0.6]} s={[0.016, 0.012, 2.2]}
        m={{ color: ledCool, emissive: ledCool, emissiveIntensity: 3.5, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-W / 2 + UPP_D + 0.08, ucY - 0.1, -0.6]} intensity={4} color="#dff0ff" distance={2.0} decay={2} />

      {/* ── TOE-KICK LED STRIPS (floor level at base of cabinet runs) ── */}
      {/* Back run toe-kick */}
      <Box p={[0, 0.04, -D / 2 + 0.04]} s={[W - 1.6, 0.018, 0.01]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.8, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-1.0, 0.06, -D / 2 + 0.14]} intensity={2} color={ledWarm} distance={3} decay={2} />
      <pointLight position={[ 0.6, 0.06, -D / 2 + 0.14]} intensity={2} color={ledWarm} distance={3} decay={2} />
      {/* Left run toe-kick */}
      <Box p={[-W / 2 + 0.04, 0.04, -0.6]} s={[0.01, 0.018, 2.2]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.8, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-W / 2 + 0.14, 0.06, -0.6]} intensity={2} color={ledWarm} distance={3} decay={2} />

      {/* ── RANGE HOOD INTERIOR LED ── */}
      {/* Thin cool strip inside the hood opening, washing down onto the range */}
      <Box p={[-1.5, 1.98, -D / 2 + 0.3]} s={[0.56, 0.01, 0.1]}
        m={{ color: ledCool, emissive: ledCool, emissiveIntensity: 4.5, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[-1.5, 1.8, -D / 2 + 0.32]} intensity={6} color="#e8f4ff" distance={1.6} decay={2} castShadow />

      {/* ── DISPLAY NICHE ACCENT SPOT ── */}
      {/* The display niche is on the back wall around x=1.9~2.8 */}
      <spotLight
        position={[2.3, H - 0.05, -D / 2 + 0.5]}
        target-position={[2.3, 1.4, -D / 2 + 0.05]}
        intensity={16} color="#fff6e8" angle={0.35} penumbra={0.8} distance={3.5} decay={2}
      />
      {/* LED shelf strip inside the niche */}
      <Box p={[2.3, 1.55, -D / 2 + 0.14]} s={[0.82, 0.01, 0.02]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 3.0, roughness: 1 }} cast={false} receive={false} />

      {/* ── LINEAR LED PENDANT above the peninsula ── */}
      {/* slim anodised housing */}
      <Box p={[-0.35, H - 0.52, 0.92]} s={[1.4, 0.04, 0.08]}
        m={{ color: "#1c1a18", roughness: 0.35, metalness: 0.8, envMapIntensity: 1.2 }} cast={false} />
      {/* bottom emissive diffuser */}
      <Box p={[-0.35, H - 0.545, 0.92]} s={[1.32, 0.008, 0.065]}
        m={{ color: "#fffaf0", emissive: "#ffe8c0", emissiveIntensity: 4.5, roughness: 1 }} cast={false} receive={false} />
      {/* top bounce — ceiling wash */}
      <Box p={[-0.35, H - 0.498, 0.92]} s={[1.32, 0.006, 0.065]}
        m={{ color: "#fffaf0", emissive: "#ffe8c0", emissiveIntensity: 2.0, roughness: 1 }} cast={false} receive={false} />
      {/* suspension cables × 3 */}
      {[-0.6, -0.35, -0.1].map((cx, i) => (
        <mesh key={i} position={[cx, H - 0.27, 0.92]}>
          <cylinderGeometry args={[0.003, 0.003, 0.48, 6]} />
          <meshStandardMaterial color="#2a2622" roughness={0.5} metalness={0.7} />
        </mesh>
      ))}
      <pointLight position={[-0.35, H - 0.62, 0.92]} intensity={10} color="#ffcc80" distance={3.2} decay={2} />
      <pointLight position={[-0.35, H - 0.48, 0.92]} intensity={3}  color="#ffdcaa" distance={1.8} decay={2} />

      {/* ── PENINSULA SIDE LED STRIP (under the stone waterfall edge) ── */}
      {/* Right side waterfall: x ≈ -0.35 + 1.15 = 0.8, z from 0.59 to 1.25 */}
      <Box p={[1.15, 0.9 + 0.04 / 2, 0.92]} s={[0.01, 0.016, 0.58]}
        m={{ color: ledWarm, emissive: ledWarm, emissiveIntensity: 2.5, roughness: 1 }} cast={false} receive={false} />
      <pointLight position={[1.06, 0.5, 0.92]} intensity={1.8} color={ledWarm} distance={1.8} decay={2} />
    </>
  );
}

// ═══ LIGHTING ═════════════════════════════════════════════════════════════════
function Lighting() {
  return (
    <>
      {/* Cool daylight through the window */}
      <directionalLight
        position={[-7, 4.5, -1]} intensity={1.4} color="#dbeaff" castShadow
        shadow-mapSize={[2048, 2048]} shadow-bias={-0.0004}
        shadow-camera-near={0.5} shadow-camera-far={22}
        shadow-camera-left={-7} shadow-camera-right={7} shadow-camera-top={7} shadow-camera-bottom={-2}
      />
      <ambientLight intensity={0.18} color="#fff1d8" />
      <hemisphereLight args={["#e6efff", "#b6a894", 0.32]} />
      {/* Recessed downlights */}
      {[[-1.7, -1.4], [0, -1.4], [1.7, -1.4], [-1.7, 0.4], [1.7, 0.4], [0, 1.0]].map(([x, z], i) => (
        <pointLight key={i} position={[x, H - 0.15, z]} intensity={5} color="#ffefd2" distance={3.8} decay={2} />
      ))}
      {/* Pendant pools */}
      <pointLight position={[-1.0, 2.0, 0.95]} intensity={8} color="#ffb545" distance={2.8} decay={2} castShadow />
      <pointLight position={[-0.5, 1.8, 0.95]} intensity={8} color="#ffb545" distance={2.8} decay={2} />
      {/* Under-cabinet warm wash */}
      <pointLight position={[-1.5, 1.35, -2.4]} intensity={3} color="#ffcc88" distance={2.5} decay={2} />
      <pointLight position={[-W / 2 + 0.6, 1.35, -1.4]} intensity={3} color="#ffcc88" distance={2.5} decay={2} />
      {/* Camera-side soft fill */}
      <pointLight position={[2.5, 2.4, 4.5]} intensity={5} color="#f0f2ff" distance={8} decay={2} />
    </>
  );
}
