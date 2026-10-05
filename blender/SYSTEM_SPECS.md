# System Specifications & Render Performance

## Hardware & Environment

- **OS**: Microsoft Windows 10 Pro 64-bit (Version 22H2, Build 19045)
- **RAM**: 16 GB (15.88 GB Physical RAM)
- **GPU**: NVIDIA Quadro M1000M
  - **VRAM**: **4096 MiB (4 GB)** GDDR5
  - **Driver Version**: 573.71
  - **Compute APIs**: CUDA 12.8 / OptiX (Cycles compute fallback on Maxwell)
- **Blender Version**: Blender 5.2.1 LTS (Release build 9e2066aef7ef)

---

## Preview Render Benchmarks (16x9, Preview Profile, GPU Enabled)

Settings: `samples=48`, `min_samples=16`, `threshold=0.05`, `percentage=25`, `texture_limit=512`, `max_subdiv=1`

| Frame | Scene / Shot | Render Time | Key Assets In View |
| :--- | :--- | :---: | :--- |
| **16x9_F020.png** | Entrance / Console | 127.2s | Marble bust, entry console, LED strips |
| **16x9_F120.png** | Living Room (Updated) | 162.1s | Freedom Sofa, curved 3-cushion white sofa, travertine table, terrace greenery |
| **16x9_F270.png** | Coffee Table Details | 128.7s | Encyclopedia book set, carved wooden bowl, travertine seams |
| **16x9_F300.png** | Kitchen & Dining | 124.0s | Wine bottles, ceramic vases, wooden island bowl, Rembrandt frame |
| **16x9_F372.png** | Transition Corridor | 89.0s | Dining room & hallway corridor |
| **16x9_F440.png** | Living Room Angle | 74.4s | Rembrandt high-res scan painting, motion blur, terrace |
| **16x9_F520.png** | Bedroom Entrance | 107.5s | Door02 walnut door & frame in wall opening, cove lighting |
| **16x9_F600.png** | Master Bedroom | 80.7s | Headboard, bedside tables, table lamps, books |
| **16x9_F690.png** | Bedroom / Vanity | 86.3s | Bedroom joinery and bathroom hallway |
| **16x9_F860.png** | Terrace Panoramas | 84.2s | Terrace stone flooring, glass railing, potted plants, HDRI city |

---

## Asset & License Safety

- `blender/apartment_final.blend` has been **excluded** from git tracking.
- Heavy model files (`blender/assets/`) are completely excluded in `.gitignore`.
- Only clean procedural masters (`apartment_master.blend`), open CC0 source code, configs, logs, and lightweight preview renders (`render/preview/*.png`) are tracked.
