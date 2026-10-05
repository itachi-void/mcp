# Apartment flythrough — Blender pipeline

Pinned to **Blender 4.5 LTS** (the build aborts on any other version).

```bash
blender -b --factory-startup -P blender/build_apartment.py          # builds apartment_master.blend + build_report.json (exit≠0 on QA errors)
blender -b blender/apartment_master.blend -P blender/render_frames.py -- preview   # 10 frames per format, PNG
blender -b blender/apartment_master.blend -P blender/render_frames.py -- verify    # STILL_06_BATH
blender -b blender/apartment_master.blend -P blender/render_frames.py -- master 16x9   # resumable EXR
```

- Everything is driven by `apartment/config.json` (timeline 1–864 @24fps, shots, lights, assets).
- Naming: `SHOT_01..04` = film shots, `STILL_01..08` = stills. The bathroom is **stills only** (STILL_06_BATH), so the old CAM_06 clash is gone.
- Output: scene-linear OpenEXR half (PIZ) plus a 32-bit multilayer for data passes (Depth/AO/Crypto). AgX is only for the preview.
- Resolve: Input = Linear / Rec.709 primaries → DaVinci Wide Gamut Intermediate → Output Rec.709 Gamma 2.4.
- Lenses: 16:9 uses a horizontal 36mm sensor; 9:16 uses a vertical 36mm sensor with an 18/24mm override.
- Real assets: put door02 / freedom_sofa / rembrandt.jpg (≥4000px) in `blender/assets/`; the proxies use the correct dimensions.
- Time: ~35s per preview frame on 1 CPU; the final at 384 samples needs a GPU.
