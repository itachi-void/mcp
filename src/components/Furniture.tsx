interface FurnitureProps {
  room: "living" | "bedroom" | "kitchen";
}

export default function Furniture({ room }: FurnitureProps) {
  if (room === "living") return <LivingRoom />;
  if (room === "bedroom") return <Bedroom />;
  return <Kitchen />;
}

/* ─── Living Room ─── */
function LivingRoom() {
  return (
    <group>
      <Sofa position={[0, 0, -2.5]} />
      <CoffeeTable position={[0, 0, -0.5]} />
      <TVStand position={[0, 0, -4.7]} />
      <PlantPot position={[-4, 0, -4]} />
      <FloorLamp position={[3.5, 0, -3]} />
      <Bookshelf position={[-4.5, 0, -3]} />
    </group>
  );
}

/* ─── Bedroom ─── */
function Bedroom() {
  return (
    <group>
      <Bed position={[0, 0, -3]} />
      <Nightstand position={[1.8, 0, -3.8]} />
      <Nightstand position={[-1.8, 0, -3.8]} />
      <Wardrobe position={[-4.2, 0, -2]} />
      <PlantPot position={[3.5, 0, -4.5]} />
      <DeskChair position={[3.2, 0, 0.5]} />
    </group>
  );
}

/* ─── Kitchen ─── */
function Kitchen() {
  return (
    <group>
      <KitchenCounter position={[-3.5, 0, -3.5]} />
      <KitchenIsland position={[0, 0, -0.5]} />
      <BarStool position={[0, 0, 1.2]} />
      <BarStool position={[1.2, 0, 1.2]} />
      <BarStool position={[-1.2, 0, 1.2]} />
      <PlantPot position={[4, 0, -4.5]} />
    </group>
  );
}

/* ─── Components ─── */

function Sofa({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Base */}
      <mesh position={[0, 0.3, 0]} castShadow receiveShadow>
        <boxGeometry args={[3.2, 0.6, 1.2]} />
        <meshStandardMaterial color="#7a6552" roughness={0.85} />
      </mesh>
      {/* Back */}
      <mesh position={[0, 0.85, -0.5]} castShadow receiveShadow>
        <boxGeometry args={[3.2, 0.9, 0.25]} />
        <meshStandardMaterial color="#7a6552" roughness={0.85} />
      </mesh>
      {/* Arms */}
      {([-1.55, 1.55] as number[]).map((x, i) => (
        <mesh key={i} position={[x, 0.65, -0.1]} castShadow>
          <boxGeometry args={[0.2, 0.7, 1.0]} />
          <meshStandardMaterial color="#6a5545" roughness={0.8} />
        </mesh>
      ))}
      {/* Cushions */}
      {([-1, 0, 1] as number[]).map((x, i) => (
        <mesh key={i} position={[x, 0.65, 0.15]} castShadow>
          <boxGeometry args={[0.9, 0.15, 0.9]} />
          <meshStandardMaterial color="#8a7562" roughness={0.9} />
        </mesh>
      ))}
      {/* Legs */}
      {([-1.5, 1.5] as number[]).flatMap((x) =>
        ([-0.5, 0.5] as number[]).map((z, i) => (
          <mesh key={`${x}-${i}`} position={[x, 0.06, z]} castShadow>
            <cylinderGeometry args={[0.04, 0.04, 0.12, 8]} />
            <meshStandardMaterial color="#3d2b1f" roughness={0.4} metalness={0.1} />
          </mesh>
        ))
      )}
    </group>
  );
}

function CoffeeTable({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.35, 0]} castShadow receiveShadow>
        <boxGeometry args={[1.6, 0.06, 0.9]} />
        <meshStandardMaterial color="#5c3d2e" roughness={0.5} metalness={0.05} />
      </mesh>
      {([-0.7, 0.7] as number[]).flatMap((x) =>
        ([-0.38, 0.38] as number[]).map((z, i) => (
          <mesh key={`${x}-${i}`} position={[x, 0.17, z]} castShadow>
            <cylinderGeometry args={[0.03, 0.03, 0.35, 8]} />
            <meshStandardMaterial color="#3d2b1f" roughness={0.4} />
          </mesh>
        ))
      )}
      {/* Decorative tray */}
      <mesh position={[0.2, 0.39, 0]} castShadow>
        <boxGeometry args={[0.6, 0.02, 0.4]} />
        <meshStandardMaterial color="#c4a882" roughness={0.6} />
      </mesh>
    </group>
  );
}

function TVStand({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Cabinet */}
      <mesh position={[0, 0.35, 0]} castShadow receiveShadow>
        <boxGeometry args={[3, 0.7, 0.5]} />
        <meshStandardMaterial color="#2d2d2d" roughness={0.6} />
      </mesh>
      {/* TV screen */}
      <mesh position={[0, 1.3, 0.02]} castShadow>
        <boxGeometry args={[2.4, 1.35, 0.06]} />
        <meshStandardMaterial color="#111111" roughness={0.1} metalness={0.5} />
      </mesh>
      {/* Screen glow */}
      <mesh position={[0, 1.3, 0.06]}>
        <planeGeometry args={[2.2, 1.2]} />
        <meshStandardMaterial color="#1a3a5c" emissive="#1a3a5c" emissiveIntensity={0.4} roughness={0} />
      </mesh>
    </group>
  );
}

function FloorLamp({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.8, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.15, 0.3, 16]} />
        <meshStandardMaterial color="#d4c090" roughness={0.6} />
      </mesh>
      <mesh position={[0, 0.9, 0]} castShadow>
        <cylinderGeometry args={[0.015, 0.015, 1.8, 8]} />
        <meshStandardMaterial color="#8a8a8a" metalness={0.8} roughness={0.2} />
      </mesh>
      <mesh position={[0, 0.05, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.15, 0.08, 16]} />
        <meshStandardMaterial color="#3d3d3d" roughness={0.5} />
      </mesh>
    </group>
  );
}

function PlantPot({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.2, 0]} castShadow>
        <cylinderGeometry args={[0.18, 0.13, 0.4, 12]} />
        <meshStandardMaterial color="#c4784a" roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.55, 0]} castShadow>
        <sphereGeometry args={[0.28, 10, 10]} />
        <meshStandardMaterial color="#3a7a3a" roughness={1} />
      </mesh>
      {/* Stem */}
      <mesh position={[0.15, 0.75, 0.1]} rotation={[0, 0, 0.4]} castShadow>
        <cylinderGeometry args={[0.015, 0.01, 0.4, 6]} />
        <meshStandardMaterial color="#2d6b2d" roughness={1} />
      </mesh>
      <mesh position={[0.3, 0.92, 0.1]} castShadow>
        <sphereGeometry args={[0.1, 8, 8]} />
        <meshStandardMaterial color="#4a9a4a" roughness={1} />
      </mesh>
    </group>
  );
}

function Bookshelf({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.25, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.4, 2.5, 1.2]} />
        <meshStandardMaterial color="#5c3d2e" roughness={0.6} />
      </mesh>
      {([0.3, 0.9, 1.5, 2.1] as number[]).map((y, i) => (
        <mesh key={i} position={[0.21, y, 0]} castShadow>
          <boxGeometry args={[0.02, 0.04, 1.1]} />
          <meshStandardMaterial color="#3d2b1f" roughness={0.5} />
        </mesh>
      ))}
      {/* Books */}
      {([0.55, 1.15, 1.75] as number[]).map((y, row) =>
        ([...Array(5)] as undefined[]).map((_, col) => (
          <mesh key={`${row}-${col}`} position={[0.21, y, -0.4 + col * 0.18]} castShadow>
            <boxGeometry args={[0.06, 0.28, 0.14]} />
            <meshStandardMaterial
              color={["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#e67e22"][col % 5]}
              roughness={0.8}
            />
          </mesh>
        ))
      )}
    </group>
  );
}

function Bed({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Frame */}
      <mesh position={[0, 0.2, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.4, 0.4, 3.5]} />
        <meshStandardMaterial color="#4a3728" roughness={0.6} />
      </mesh>
      {/* Mattress */}
      <mesh position={[0, 0.45, 0.2]} castShadow>
        <boxGeometry args={[2.2, 0.25, 3.0]} />
        <meshStandardMaterial color="#e8e0d0" roughness={0.9} />
      </mesh>
      {/* Headboard */}
      <mesh position={[0, 0.85, -1.7]} castShadow>
        <boxGeometry args={[2.4, 1.0, 0.12]} />
        <meshStandardMaterial color="#4a3728" roughness={0.5} />
      </mesh>
      {/* Pillows */}
      {([-0.55, 0.55] as number[]).map((x, i) => (
        <mesh key={i} position={[x, 0.62, -1.2]} castShadow>
          <boxGeometry args={[0.9, 0.18, 0.6]} />
          <meshStandardMaterial color="#ffffff" roughness={0.95} />
        </mesh>
      ))}
      {/* Duvet */}
      <mesh position={[0, 0.56, 0.5]} castShadow>
        <boxGeometry args={[2.2, 0.12, 2.0]} />
        <meshStandardMaterial color="#c8b4d0" roughness={0.95} />
      </mesh>
    </group>
  );
}

function Nightstand({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.35, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.6, 0.7, 0.45]} />
        <meshStandardMaterial color="#5c4a3a" roughness={0.6} />
      </mesh>
      {/* Lamp */}
      <mesh position={[0, 0.85, 0]} castShadow>
        <cylinderGeometry args={[0.12, 0.08, 0.3, 12]} />
        <meshStandardMaterial color="#e8d8b0" roughness={0.6} />
      </mesh>
      <mesh position={[0, 0.72, 0]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, 0.15, 6]} />
        <meshStandardMaterial color="#8a7a6a" roughness={0.4} />
      </mesh>
    </group>
  );
}

function Wardrobe({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 1.25, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.6, 2.5, 2.2]} />
        <meshStandardMaterial color="#3d2b1f" roughness={0.5} />
      </mesh>
      {/* Door lines */}
      <mesh position={[0.31, 1.25, 0]} castShadow>
        <boxGeometry args={[0.02, 2.4, 0.04]} />
        <meshStandardMaterial color="#5c3d2e" roughness={0.4} />
      </mesh>
      {/* Handles */}
      {([0.55, -0.55] as number[]).map((z, i) => (
        <mesh key={i} position={[0.32, 1.3, z]} castShadow>
          <sphereGeometry args={[0.04, 8, 8]} />
          <meshStandardMaterial color="#c0a060" metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
    </group>
  );
}

function DeskChair({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.55, 0]} castShadow>
        <cylinderGeometry args={[0.35, 0.3, 0.1, 12]} />
        <meshStandardMaterial color="#2a2a2a" roughness={0.7} />
      </mesh>
      <mesh position={[0, 0.9, -0.15]} castShadow>
        <boxGeometry args={[0.65, 0.75, 0.08]} />
        <meshStandardMaterial color="#2a2a2a" roughness={0.7} />
      </mesh>
      <mesh position={[0, 0.28, 0]} castShadow>
        <cylinderGeometry args={[0.04, 0.04, 0.56, 8]} />
        <meshStandardMaterial color="#7a7a7a" metalness={0.6} roughness={0.3} />
      </mesh>
    </group>
  );
}

function KitchenCounter({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      {/* Base cabinet */}
      <mesh position={[0, 0.45, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.6, 0.9, 3.5]} />
        <meshStandardMaterial color="#e8e4dc" roughness={0.5} />
      </mesh>
      {/* Countertop */}
      <mesh position={[0, 0.92, 0]} castShadow>
        <boxGeometry args={[0.7, 0.05, 3.6]} />
        <meshStandardMaterial color="#888888" roughness={0.2} metalness={0.3} />
      </mesh>
      {/* Upper cabinets */}
      <mesh position={[0, 2.1, 0]} castShadow>
        <boxGeometry args={[0.4, 0.8, 3.5]} />
        <meshStandardMaterial color="#e8e4dc" roughness={0.5} />
      </mesh>
    </group>
  );
}

function KitchenIsland({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.5, 0]} castShadow receiveShadow>
        <boxGeometry args={[2.2, 1.0, 1.0]} />
        <meshStandardMaterial color="#d0c8bc" roughness={0.5} />
      </mesh>
      <mesh position={[0, 1.03, 0]} castShadow>
        <boxGeometry args={[2.3, 0.06, 1.1]} />
        <meshStandardMaterial color="#555555" roughness={0.15} metalness={0.4} />
      </mesh>
    </group>
  );
}

function BarStool({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh position={[0, 0.85, 0]} castShadow>
        <cylinderGeometry args={[0.22, 0.18, 0.08, 12]} />
        <meshStandardMaterial color="#2a2a2a" roughness={0.7} />
      </mesh>
      <mesh position={[0, 0.45, 0]} castShadow>
        <cylinderGeometry args={[0.025, 0.025, 0.9, 8]} />
        <meshStandardMaterial color="#9a9a9a" metalness={0.7} roughness={0.2} />
      </mesh>
      <mesh position={[0, 0.06, 0]} castShadow>
        <cylinderGeometry args={[0.22, 0.25, 0.06, 12]} />
        <meshStandardMaterial color="#3a3a3a" roughness={0.5} />
      </mesh>
    </group>
  );
}
