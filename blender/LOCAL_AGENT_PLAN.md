# Local agent plan — install the real approved assets

You are an agent on the machine that holds Blender and the heavy asset files.
Follow these steps exactly. Never edit `apartment_master.blend`; the output is `apartment_final.blend`.
Stop and report to the user whenever a step says STOP.

## 0. Preconditions
1. Run `blender --version`. It must be **4.5.x**. If not, STOP and ask the user for the Blender 4.5 LTS path.
2. Get the repo folder (contains `blender/apartment_master.blend`, `blender/apply_decisions.py`, `blender/apartment/config.json`).
   If `apartment_master.blend` is missing, build it:
   `blender -b --factory-startup -P blender/build_apartment.py` (must print `BUILD OK`).

## 1. Specs to match (from config.json)
| key | what | expected size (m) W×D×H | tolerance |
|---|---|---|---|
| door02 | Door02 leaf, closed | 1.00 × 0.06 × 2.20 | ±0.08 |
| freedom_sofa | Freedom Sofa | 2.80 × 1.00 × 0.75 | ±0.15 |
| rembrandt | image scan | long edge ≥ 4000 px, canvas 0.84×1.03 (portrait) | — |

Accepted mesh formats: .blend (preferred), .glb/.gltf, .fbx, .obj, .usd*. cm/mm exports are rescaled automatically.

## 2. Scan (read-only)
Ask the user which folders hold their assets, then run:
```
blender -b --factory-startup -P blender/apply_decisions.py -- scan "<folder1>" "<folder2>"
```
Read `blender/scan_report.json`. For each key pick one candidate:
- prefer `.blend`; for a `.blend` choose the object name from `objects` (the root/parent of the asset, not a sub-part).
- rembrandt: must have `"ok": true`.
- If a key has no candidate, or several plausible ones: STOP, show the user the list and ask.

## 3. Write the map
Create `blender/assets_map.json`:
```json
{"door02":       {"file": "<abs path>", "object": "<name>"},
 "freedom_sofa": {"file": "<abs path>", "object": "<name>"},
 "rembrandt":    {"image": "<abs path>"}}
```
Keys you could not resolve may be omitted (their proxy stays).

## 4. Apply
```
blender -b blender/apartment_master.blend -P blender/apply_decisions.py -- apply blender/assets_map.json
```
- exit 0 → `blender/apartment_final.blend` saved. Go to 5.
- exit 2 → read `blender/apply_report.json`. For `dims` mismatch: tell the user the measured vs expected
  size; do NOT scale or edit the asset yourself. For `error`: fix the path/object name and rerun. Otherwise STOP.

## 5. Verify
Render one check frame per asset (preview quality):
```
blender -b blender/apartment_final.blend -P blender/render_frames.py -- preview 16x9
```
Look at `render/preview/16x9_F020.png` (door), `16x9_F120.png` (sofa), `16x9_F440.png` (painting area).
Check: asset is on the floor / in the wall opening, not floating, not intersecting, correct facing.
If the sofa faces the wall or the door is rotated, report it — the fix is a 180° yaw on `<PROXY>_REAL`.

## 6. Report back to the user
Send: `apply_report.json` contents, the three PNGs, and render time per frame + GPU name.
Final renders (only after the user approves), **1080p only**:
```
blender -b blender/apartment_final.blend -P blender/render_frames.py -- master 16x9
blender -b blender/apartment_final.blend -P blender/render_frames.py -- master 9x16
```
Both are resumable: if interrupted, rerun the same command.
Before a full master, render ONE frame first and report its time; if > 3 min/frame, STOP and ask.

## Rules
- **NEVER render 4K.** Never pass `--4k`, never use the `final` profile, never raise resolution_percentage
  above 50. This machine cannot handle it. Allowed: `preview` (960×540) and `master` default (1920×1080).
- Close other heavy apps before rendering; if Blender crashes or RAM > 90%, STOP and report.
- Do not delete or overwrite user files; do not run `git push` without asking.
- Do not change `config.json` values except asset paths unless the user says so.
- Never commit the heavy assets to git (only through LFS, and only if the user asks).
