import { useRef } from "react";
import * as THREE from "three";

interface RoomProps {
  room: "living" | "bedroom" | "kitchen";
}

const ROOM_COLORS = {
  living: { walls: "#e8e0d8", floor: "#8B6F47", ceiling: "#f5f0eb" },
  bedroom: { walls: "#d4c8e0", floor: "#5c4a3a", ceiling: "#ede8f2" },
  kitchen: { walls: "#dde8e0", floor: "#c0c0b0", ceiling: "#f0f5f2" },
};

export default function Room({ room }: RoomProps) {
  const colors = ROOM_COLORS[room];
  const W = 10, H = 4, D = 10;

  return (
    <group>
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[W, D]} />
        <meshStandardMaterial color={colors.floor} roughness={0.8} metalness={0.05} />
      </mesh>

      {/* Ceiling */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, H, 0]} receiveShadow>
        <planeGeometry args={[W, D]} />
        <meshStandardMaterial color={colors.ceiling} roughness={1} />
      </mesh>

      {/* Back wall */}
      <mesh position={[0, H / 2, -D / 2]} receiveShadow>
        <planeGeometry args={[W, H]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>

      {/* Left wall */}
      <mesh rotation={[0, Math.PI / 2, 0]} position={[-W / 2, H / 2, 0]} receiveShadow>
        <planeGeometry args={[D, H]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>

      {/* Right wall */}
      <mesh rotation={[0, -Math.PI / 2, 0]} position={[W / 2, H / 2, 0]} receiveShadow>
        <planeGeometry args={[D, H]} />
        <meshStandardMaterial color={colors.walls} roughness={0.9} />
      </mesh>

      {/* Floor baseboard trim */}
      {[
        { pos: [0, 0.05, -D / 2 + 0.02] as [number,number,number], args: [W, 0.1, 0.04] as [number,number,number] },
        { pos: [-W / 2 + 0.02, 0.05, 0] as [number,number,number], args: [0.04, 0.1, D] as [number,number,number] },
        { pos: [W / 2 - 0.02, 0.05, 0] as [number,number,number], args: [0.04, 0.1, D] as [number,number,number] },
      ].map((t, i) => (
        <mesh key={i} position={t.pos} castShadow>
          <boxGeometry args={t.args} />
          <meshStandardMaterial color="#ffffff" roughness={0.3} />
        </mesh>
      ))}

      {/* Window on back wall */}
      <WindowFrame position={[2, 2.2, -D / 2 + 0.05]} />

      {/* Area rug */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.002, 0]} receiveShadow>
        <planeGeometry args={[4.5, 3]} />
        <meshStandardMaterial
          color={room === "living" ? "#c8a882" : room === "bedroom" ? "#9b7db5" : "#7da89b"}
          roughness={1}
        />
      </mesh>
    </group>
  );
}

function WindowFrame({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Glass pane */}
      <mesh>
        <planeGeometry args={[2.2, 1.8]} />
        <meshStandardMaterial color="#a8d4f5" transparent opacity={0.35} roughness={0} metalness={0.1} />
      </mesh>
      {/* Frame */}
      {[
        { pos: [0, 0.95, 0] as [number,number,number], args: [2.2, 0.1, 0.08] as [number,number,number] },
        { pos: [0, -0.95, 0] as [number,number,number], args: [2.2, 0.1, 0.08] as [number,number,number] },
        { pos: [-1.15, 0, 0] as [number,number,number], args: [0.1, 2.0, 0.08] as [number,number,number] },
        { pos: [1.15, 0, 0] as [number,number,number], args: [0.1, 2.0, 0.08] as [number,number,number] },
        { pos: [0, 0, 0] as [number,number,number], args: [0.06, 1.8, 0.06] as [number,number,number] },
      ].map((f, i) => (
        <mesh key={i} position={f.pos}>
          <boxGeometry args={f.args} />
          <meshStandardMaterial color="#f0ece6" roughness={0.4} />
        </mesh>
      ))}
    </group>
  );
}
