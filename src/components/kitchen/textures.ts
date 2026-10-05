import * as THREE from "three";

// ─────────────────────────────────────────────────────────────────────────────
//  Procedural PBR textures generated on a <canvas> — no external files/network.
//  Each generator returns fresh THREE.CanvasTexture instances so callers can set
//  their own .repeat without cross-contamination.
// ─────────────────────────────────────────────────────────────────────────────

// ── Real PBR maps (downloaded to /public/textures, CC0 from Poly Haven) ──────
const _loader = new THREE.TextureLoader();
function loadMap(url: string, repeat: [number, number], srgb = false) {
  const t = _loader.load(url);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = 8;
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}
/** Load a colour/roughness/normal set by base name from /textures/<name>_{col,rgh,nrm}.jpg */
export function pbrSet(name: string, repeat: [number, number] = [1, 1]) {
  return {
    map: loadMap(`/textures/${name}_col.jpg`, repeat, true),
    rgh: loadMap(`/textures/${name}_rgh.jpg`, repeat),
    nrm: loadMap(`/textures/${name}_nrm.jpg`, repeat),
  };
}

function makeCanvas(size = 512) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  return { c, ctx: c.getContext("2d")! };
}

function toTex(c: HTMLCanvasElement, repeat: [number, number]) {
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(repeat[0], repeat[1]);
  t.anisotropy = 8;
  t.needsUpdate = true;
  return t;
}

// value noise wash
function noise(ctx: CanvasRenderingContext2D, size: number, amount: number, alpha: number) {
  const img = ctx.getImageData(0, 0, size, size);
  const d = img.data;
  for (let i = 0; i < d.length; i += 4) {
    const n = (Math.random() - 0.5) * amount;
    d[i] += n; d[i + 1] += n; d[i + 2] += n;
    d[i + 3] = Math.min(255, d[i + 3]);
  }
  ctx.globalAlpha = alpha;
  ctx.putImageData(img, 0, 0);
  ctx.globalAlpha = 1;
}

// ── Marble / quartz: base + soft flowing veins ──────────────────────────────
export function marble(base = "#ece9e3", repeat: [number, number] = [1, 1]) {
  const size = 512;
  const { c, ctx } = makeCanvas(size);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  // veins
  const veinCols = ["rgba(150,146,138,0.35)", "rgba(120,116,108,0.25)", "rgba(200,196,188,0.4)"];
  for (let v = 0; v < 18; v++) {
    ctx.beginPath();
    let x = Math.random() * size, y = Math.random() * size;
    ctx.moveTo(x, y);
    const steps = 14 + Math.floor(Math.random() * 10);
    for (let s = 0; s < steps; s++) {
      x += (Math.random() - 0.5) * 90;
      y += (Math.random() - 0.4) * 70;
      ctx.lineTo(x, y);
    }
    ctx.strokeStyle = veinCols[v % veinCols.length];
    ctx.lineWidth = Math.random() * 2 + 0.4;
    ctx.stroke();
  }
  noise(ctx, size, 18, 0.5);
  const map = toTex(c, repeat);
  const bump = toTex(c, repeat);
  return { map, bump };
}

// ── Wood: vertical grain lines over a base tone ─────────────────────────────
export function wood(base = "#3a2513", repeat: [number, number] = [1, 1], vertical = true) {
  const size = 512;
  const { c, ctx } = makeCanvas(size);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  const b = new THREE.Color(base);
  for (let i = 0; i < 240; i++) {
    const t = Math.random();
    const shade = new THREE.Color(base).offsetHSL(0, (Math.random() - 0.5) * 0.05, (Math.random() - 0.5) * 0.14);
    ctx.strokeStyle = `rgba(${shade.r * 255 | 0},${shade.g * 255 | 0},${shade.b * 255 | 0},${0.25 + Math.random() * 0.35})`;
    ctx.lineWidth = Math.random() * 2.2 + 0.3;
    ctx.beginPath();
    if (vertical) {
      const x = t * size;
      ctx.moveTo(x, 0);
      for (let y = 0; y <= size; y += 32) ctx.lineTo(x + Math.sin(y * 0.02 + i) * 3, y);
    } else {
      const y = t * size;
      ctx.moveTo(0, y);
      for (let x = 0; x <= size; x += 32) ctx.lineTo(x, y + Math.sin(x * 0.02 + i) * 3);
    }
    ctx.stroke();
  }
  void b;
  noise(ctx, size, 14, 0.4);
  const map = toTex(c, repeat);
  const bump = toTex(c, repeat);
  return { map, bump };
}

// ── Brushed metal: fine horizontal streaks ──────────────────────────────────
export function brushed(base = "#8f9194", repeat: [number, number] = [1, 1]) {
  const size = 512;
  const { c, ctx } = makeCanvas(size);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  for (let i = 0; i < 900; i++) {
    const y = Math.random() * size;
    const g = Math.random() * 40 - 20;
    ctx.strokeStyle = `rgba(${128 + g},${129 + g},${132 + g},0.18)`;
    ctx.lineWidth = 0.6;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(size, y + (Math.random() - 0.5) * 2);
    ctx.stroke();
  }
  const map = toTex(c, repeat);
  const rough = toTex(c, repeat);
  return { map, rough };
}

// ── Fabric: subtle woven noise (bump only) ──────────────────────────────────
export function fabric(base = "#8a8079", repeat: [number, number] = [1, 1]) {
  const size = 256;
  const { c, ctx } = makeCanvas(size);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  for (let x = 0; x < size; x += 3) {
    for (let y = 0; y < size; y += 3) {
      const on = (x + y) % 6 === 0;
      ctx.fillStyle = on ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)";
      ctx.fillRect(x, y, 2, 2);
    }
  }
  noise(ctx, size, 22, 0.6);
  const map = toTex(c, repeat);
  const bump = toTex(c, repeat);
  return { map, bump };
}

// ── Tile floor: large stone slabs with grout lines + veining ────────────────
export function tileFloor(base = "#ddd8cf", repeat: [number, number] = [1, 1], grid = 2) {
  const size = 512;
  const { c, ctx } = makeCanvas(size);
  ctx.fillStyle = base;
  ctx.fillRect(0, 0, size, size);
  // soft veining
  for (let v = 0; v < 22; v++) {
    ctx.beginPath();
    let x = Math.random() * size, y = Math.random() * size;
    ctx.moveTo(x, y);
    for (let s = 0; s < 10; s++) { x += (Math.random() - 0.5) * 80; y += (Math.random() - 0.5) * 80; ctx.lineTo(x, y); }
    ctx.strokeStyle = "rgba(178,172,162,0.28)";
    ctx.lineWidth = Math.random() * 1.6 + 0.3;
    ctx.stroke();
  }
  noise(ctx, size, 12, 0.4);
  // grout
  const cell = size / grid;
  ctx.strokeStyle = "rgba(150,144,134,0.9)";
  ctx.lineWidth = 3;
  for (let i = 1; i < grid; i++) {
    ctx.beginPath(); ctx.moveTo(i * cell, 0); ctx.lineTo(i * cell, size); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(0, i * cell); ctx.lineTo(size, i * cell); ctx.stroke();
  }
  const map = toTex(c, repeat);
  const bump = toTex(c, repeat);
  return { map, bump };
}
