import { Canvas } from "@react-three/fiber";
import { OrbitControls, PerspectiveCamera, ContactShadows, Environment, Lightformer } from "@react-three/drei";
import { ACESFilmicToneMapping } from "three";
import { EffectComposer, Bloom, N8AO, SMAA, Vignette, DepthOfField, ChromaticAberration } from "@react-three/postprocessing";
import { BlendFunction } from "postprocessing";
import { Suspense, useState, useEffect } from "react";
import KitchenScene from "./components/kitchen/KitchenScene";
import BedroomScene from "./components/bedroom/BedroomScene";
import BathroomScene from "./components/bathroom/BathroomScene";
import LivingRoomScene from "./components/livingroom/LivingRoomScene";
import DiningScene from "./components/dining/DiningScene";

type Room = "kitchen" | "bedroom" | "bathroom" | "livingroom" | "dining";
const ROOMS: Record<Room, { label: string; sub: string; script: string; target: [number, number, number]; camera: [number, number, number]; fov: number }> = {
  kitchen:  { label: "Modern Luxury Kitchen", sub: "Blender Python Scene · PBR Materials", script: "/kitchen_blender.py",  target: [-0.3, 1.25, -1.2], camera: [3.6, 2.55, 6.6], fov: 52 },
  bedroom:  { label: "Master Bedroom",        sub: "Blender Python Scene · PBR Materials", script: "/bedroom_blender.py",  target: [0, 0.9, -0.6], camera: [3.6, 2.55, 6.6], fov: 52 },
  bathroom: { label: "Luxury Greige Bathroom", sub: "Blender Python Scene · PBR Materials", script: "/bathroom_blender.py", target: [-0.15, 1.0, -0.6], camera: [-0.5, 1.65, 7.2], fov: 44 },
  livingroom: { label: "Organic Luxury Living Room", sub: "Blender Python Scene · PBR Materials", script: "/livingroom_blender.py", target: [0, 0.9, -0.25], camera: [4.65, 2.25, 6.85], fov: 46 },
  dining: { label: "Organic Luxury Dining Room", sub: "Blender Python Scene · PBR Materials", script: "/dining_blender.py", target: [0, 0.95, -0.15], camera: [4.35, 2.3, 6.2], fov: 46 },
};

export default function App() {
  const [tab, setTab] = useState<"3d" | "code">("3d");
  const [room, setRoom] = useState<Room>("livingroom");
  const [copied, setCopied] = useState(false);
  const [scripts, setScripts] = useState<Partial<Record<Room, string>>>({});

  const scriptContent = scripts[room] ?? null;

  useEffect(() => { if (tab === "code") fetchScript(); /* eslint-disable-next-line */ }, [tab, room]);

  const fetchScript = async () => {
    if (scripts[room]) return scripts[room] as string;
    try {
      const res = await fetch(ROOMS[room].script);
      const text = res.ok ? await res.text() : `# ${ROOMS[room].script} not generated yet.\n# Send the Blender agent the Implementation Plan to produce it.`;
      setScripts((s) => ({ ...s, [room]: text }));
      return text;
    } catch {
      const text = `# ${ROOMS[room].script} could not be loaded.`;
      setScripts((s) => ({ ...s, [room]: text }));
      return text;
    }
  };

  const handleCopy = async () => {
    const text = await fetchScript();
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2200);
  };

  const handleDownload = async () => {
    const text = await fetchScript();
    const blob = new Blob([text], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = ROOMS[room].script.replace("/", "");
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-screen h-screen bg-[#111010] flex flex-col overflow-hidden">

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-6 py-3 bg-[#1a1917] border-b border-white/8 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-7 h-7 rounded bg-[#c9a96e] flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="#1a1917" strokeWidth="2.2" className="w-4 h-4">
              <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
              <polyline points="9 22 9 12 15 12 15 22"/>
            </svg>
          </div>
          <div>
            <h1 className="text-[13px] font-semibold text-white/90 leading-none">{ROOMS[room].label}</h1>
            <p className="text-[11px] text-white/38 mt-0.5">{ROOMS[room].sub}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Room switch */}
          <div className="flex rounded-md overflow-hidden border border-white/10 bg-white/5 mr-1">
            {(["livingroom", "dining", "bedroom", "kitchen", "bathroom"] as const).map((r) => (
              <button
                key={`room-tab-${r}`}
                onClick={() => setRoom(r)}
                className={`px-4 py-1.5 text-[12px] font-medium transition-colors ${
                  room === r ? "bg-white/90 text-[#1a1917]" : "text-white/50 hover:text-white/80"
                }`}
              >
                {r === "livingroom" ? "Living" : r === "dining" ? "Dining" : r === "kitchen" ? "Kitchen" : r === "bedroom" ? "Bedroom" : "Bathroom"}
              </button>
            ))}
          </div>
          {/* Tab pills */}
          <div className="flex rounded-md overflow-hidden border border-white/10 bg-white/5">
            {(["3d", "code"] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); if (t === "code") fetchScript(); }}
                className={`px-4 py-1.5 text-[12px] font-medium transition-colors ${
                  tab === t ? "bg-[#c9a96e] text-[#1a1917]" : "text-white/50 hover:text-white/80"
                }`}
              >
                {t === "3d" ? "3D Preview" : "Blender Code"}
              </button>
            ))}
          </div>

          {tab === "code" && (
            <>
              <button
                onClick={handleCopy}
                className="px-3 py-1.5 rounded text-[12px] font-medium border border-white/15 text-white/65 hover:text-white hover:border-white/30 transition-colors"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
              <button
                onClick={handleDownload}
                className="px-3 py-1.5 rounded text-[12px] font-medium bg-[#c9a96e] text-[#1a1917] hover:bg-[#d4b87a] transition-colors"
              >
                Download .py
              </button>
            </>
          )}
        </div>
      </header>

      {/* ── 3D Viewport ── */}
      {tab === "3d" && (
        <div className="flex-1 relative">
          <Canvas
            shadows="percentage"
            gl={{ antialias: false, toneMapping: ACESFilmicToneMapping, toneMappingExposure: 0.82 }}
            className="w-full h-full"
          >
            <PerspectiveCamera key={`camera-${room}`} makeDefault position={ROOMS[room].camera} fov={ROOMS[room].fov} />
            <Suspense fallback={null}>
              {room === "kitchen" ? <KitchenScene /> : room === "bedroom" ? <BedroomScene /> : room === "bathroom" ? <BathroomScene /> : room === "dining" ? <DiningScene /> : <LivingRoomScene />}
              {/* High-res env map — 512 for sharper reflections on glossy surfaces */}
              <Environment resolution={512} environmentIntensity={0.38}>
                {/* soft ceiling bounce */}
                <Lightformer form="rect" intensity={1.4} color="#fff4e0"
                  scale={[14, 10, 1]} position={[0, 7, 0]} rotation={[Math.PI / 2, 0, 0]} />
                {/* cool daylight from the window side */}
                <Lightformer form="rect" intensity={2.0} color="#d8e8ff"
                  scale={[7, 5, 1]} position={[-9, 3, -1]} rotation={[0, Math.PI / 2, 0]} />
                {/* warm fill from the camera side */}
                <Lightformer form="rect" intensity={0.9} color="#ffd099"
                  scale={[8, 5, 1]} position={[7, 3, 7]} rotation={[0, -Math.PI / 4, 0]} />
                {/* dim back wrap */}
                <Lightformer form="ring" intensity={0.4} color="#4a4642"
                  scale={[10, 10, 1]} position={[0, 3, -9]} />
              </Environment>
              <ContactShadows
                position={[0, 0.001, 0]}
                opacity={0.62}
                scale={13}
                blur={3.0}
                far={1.2}
              />
            </Suspense>
            <OrbitControls
              key={`controls-${room}`}
              enablePan
              enableZoom
              minDistance={2.5}
              maxDistance={14}
              maxPolarAngle={Math.PI / 2.05}
              target={ROOMS[room].target}
            />
            {/* Photoreal pass */}
            <EffectComposer multisampling={0} enableNormalPass>
              <N8AO aoRadius={0.55} intensity={1.5} distanceFalloff={1.0} quality="high" color="#000000" />
              <Bloom mipmapBlur intensity={0.35} luminanceThreshold={0.94} luminanceSmoothing={0.12} radius={0.6} />
              <ChromaticAberration
                blendFunction={BlendFunction.NORMAL}
                offset={[0.0004, 0.0002]}
                radialModulation
                modulationOffset={0.5}
              />
              <SMAA />
              <Vignette eskil={false} offset={0.26} darkness={0.42} />
            </EffectComposer>
          </Canvas>

          {/* HUD overlay */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4 px-5 py-2.5 rounded-full bg-black/55 backdrop-blur-sm border border-white/10">
            <span className="text-[11px] text-white/50">Drag to orbit</span>
            <span className="w-px h-3 bg-white/20"/>
            <span className="text-[11px] text-white/50">Scroll to zoom</span>
            <span className="w-px h-3 bg-white/20"/>
            <span className="text-[11px] text-white/50">Right-drag to pan</span>
          </div>

          {/* Material badge */}
          <div className="absolute top-4 right-4 px-3 py-1.5 rounded bg-black/55 border border-white/10 backdrop-blur-sm">
            <span className="text-[11px] text-[#c9a96e] font-medium">PBR · MeshStandardMaterial</span>
          </div>
        </div>
      )}

      {/* ── Code Viewer ── */}
      {tab === "code" && (
        <div className="flex-1 overflow-hidden flex">
          {/* Sidebar info */}
          <div className="w-60 shrink-0 bg-[#161514] border-r border-white/8 p-5 flex flex-col gap-5">
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">File</p>
              <p className="text-[13px] text-[#c9a96e] font-mono">{ROOMS[room].script.replace("/", "")}</p>
            </div>
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">Engine</p>
              <p className="text-[13px] text-white/75">Blender 3.x / 4.x</p>
            </div>
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">Renderer</p>
              <p className="text-[13px] text-white/75">Cycles (GPU)</p>
            </div>
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">Materials</p>
              <p className="text-[13px] text-white/75">Principled BSDF</p>
              <p className="text-[11px] text-white/40 mt-0.5">Full PBR workflow</p>
            </div>
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">Textures</p>
              <p className="text-[11px] text-white/55 leading-relaxed">
                Auto-loads from<br/>
                <span className="text-[#c9a96e] font-mono text-[10px]">C:\Users\itachi\Downloads\3d</span><br/>
                Falls back to procedural PBR if not found.
              </p>
            </div>
            <div>
              <p className="text-[11px] text-white/35 uppercase tracking-wider mb-2">How to run</p>
              <ol className="text-[11px] text-white/55 leading-relaxed list-decimal list-inside space-y-1">
                <li>Open Blender</li>
                <li>Go to Scripting tab</li>
                <li>Open this .py file</li>
                <li>Click Run Script</li>
                <li>Press F12 to render</li>
              </ol>
            </div>
          </div>

          {/* Code panel */}
          <div className="flex-1 overflow-auto bg-[#0e0d0c]">
            {scriptContent ? (
              <pre className="p-6 text-[12px] font-mono text-white/72 leading-relaxed whitespace-pre">
                <code>{scriptContent}</code>
              </pre>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-white/30 text-sm">Loading script...</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
