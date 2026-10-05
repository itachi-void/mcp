import { useRef } from "react";
import * as THREE from "three";

// Room: floor, walls, false ceiling with cove
export default function KitchenRoom() {
  const W = 7.2;   // width
  const D = 6.0;   // depth
  const H = 2.85;  // height

  // Cream large-format floor tile
  const floorMat = {
    color: "#E5E0D5",
    roughness: 0.15,
    metalness: 0.05,
  };

  // Warm plaster walls
  const wallMat = {
    color: "#D6D0C8",
    roughness: 0.95,
    metalness: 0,
  };

  const ceilMat = {
    color: "#CCCBC6",
    roughness: 1,
    metalness: 0,
  };

  return (
    <group>
      {/* Floor */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[W, D, 8, 8]} />
        <meshStandardMaterial {...floorMat} />
      </mesh>

      {/* Floor tile grout lines */}
      {[-1.5, 0, 1.5].map((x) =>
        [-1.2, 0, 1.2].map((z, i) => (
          <mesh key={`${x}-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[x, 0.001, z]} receiveShadow>
            <planeGeometry args={[0.002, D]} />
            <meshStandardMaterial color="#C8C4BC" roughness={1} />
          </mesh>
        ))
      )}

      {/* Back wall */}
      <mesh position={[0, H / 2, -D / 2]} receiveShadow>
        <planeGeometry args={[W, H]} />
        <meshStandardMaterial {...wallMat} />
      </mesh>

      {/* Left wall */}
      <mesh rotation={[0, Math.PI / 2, 0]} position={[-W / 2, H / 2, 0]} receiveShadow>
        <planeGeometry args={[D, H]} />
        <meshStandardMaterial {...wallMat} />
      </mesh>

      {/* Right wall */}
      <mesh rotation={[0, -Math.PI / 2, 0]} position={[W / 2, H / 2, 0]} receiveShadow>
        <planeGeometry args={[D, H]} />
        <meshStandardMaterial {...wallMat} />
      </mesh>

      {/* Main ceiling */}
      <mesh rotation={[Math.PI / 2, 0, 0]} position={[0, H, 0]}>
        <planeGeometry args={[W, D]} />
        <meshStandardMaterial {...ceilMat} />
      </mesh>

      {/* False ceiling drop — cove perimeter */}
      <FalseCeiling W={W} D={D} H={H} />

      {/* Backsplash: marble-look behind counters */}
      <mesh position={[0, 1.35, -D / 2 + 0.003]} receiveShadow>
        <planeGeometry args={[W * 0.65, 0.7]} />
        <meshStandardMaterial color="#F0ECE4" roughness={0.08} metalness={0.02} />
      </mesh>
      <mesh rotation={[0, Math.PI / 2, 0]} position={[-W / 2 + 0.003, 1.35, -0.6]}>
        <planeGeometry args={[3.2, 0.7]} />
        <meshStandardMaterial color="#F0ECE4" roughness={0.08} metalness={0.02} />
      </mesh>
    </group>
  );
}

function FalseCeiling({ W, D, H }: { W: number; D: number; H: number }) {
  const drop = 0.22;
  const thickness = 0.12;
  const mat = { color: "#C8C7C2", roughness: 1, metalness: 0 };

  // Four border panels forming the cove frame
  return (
    <group position={[0, H - drop, 0]}>
      {/* Front border */}
      <mesh position={[0, -thickness / 2, D / 2 - 0.4]}>
        <boxGeometry args={[W, thickness, 0.8]} />
        <meshStandardMaterial {...mat} />
      </mesh>
      {/* Back border */}
      <mesh position={[0, -thickness / 2, -D / 2 + 0.4]}>
        <boxGeometry args={[W, thickness, 0.8]} />
        <meshStandardMaterial {...mat} />
      </mesh>
      {/* Left border */}
      <mesh position={[-W / 2 + 0.4, -thickness / 2, 0]}>
        <boxGeometry args={[0.8, thickness, D - 1.6]} />
        <meshStandardMaterial {...mat} />
      </mesh>
      {/* Right border */}
      <mesh position={[W / 2 - 0.4, -thickness / 2, 0]}>
        <boxGeometry args={[0.8, thickness, D - 1.6]} />
        <meshStandardMaterial {...mat} />
      </mesh>
      {/* Inner ceiling panel */}
      <mesh position={[0, -thickness, 0]}>
        <boxGeometry args={[W - 1.6, 0.02, D - 1.6]} />
        <meshStandardMaterial color="#CCCBC6" roughness={1} />
      </mesh>
    </group>
  );
}
