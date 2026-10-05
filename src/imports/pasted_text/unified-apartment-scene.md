# Unified Blender Master Scene — Full Apartment Realism & Cinematic Readiness (DaVinci Resolve)

## Overview & Goal
Transform the individual living room, dining room, kitchen, bathroom, and bedroom modules into a single, cohesive, photorealistic 1-bedroom luxury apartment master scene. The scene will feature seamless architectural transitions, real-world circulation, refined micro-architectural detailing (shadow-gap baseboards, curtain pockets, AC slot diffusers), updated kitchen living details with an integrated downdraft system (replacing the upper range hood), and 8 cinematic camera setups configured at 24 fps for editorial grading and montage in DaVinci Resolve.

---

## User Review Required

> [!IMPORTANT]
> **Key Architectural & Technical Decisions:**
> 1. **Upper Range Hood Removal & Downdraft Replacement**: All overhead hood geometry and hood lights (`Hood_Chimney`, `Hood_Body`, `Hood_Rim`, `Hood_Filter`, `Hood_LED`, `Hood_IntCoolLED`, `Hood_IntCool_Pt`, `Hood_LED_Area`) will be removed and replaced with a flush/recessed integrated downdraft system (`build_downdraft_system(M, state="closed")`).
> 2. **Modular Scene Refactoring**: `kitchen_blender.py`, `livingroom_blender.py`, `dining_blender.py`, `bathroom_blender.py`, and `bedroom_blender.py` will be protected with `if __name__ == "__main__": main()` so importing them does not clear the scene. Each will expose a clean `build_<room>_module(M, offset=(0,0,0), collection=None, ...)` function.
> 3. **Sync Across Locations**: Both `C:\Users\itachi\Downloads\Greeting User\public\` and `E:\Blender\Kitchen\` will be kept completely synchronized with identical scripts and assets.
> 4. **DaVinci Resolve Readiness**: 24 fps animation keyframes with soft Bezier easing for CAM_01 through CAM_08, Cycles AgX color management, and a Python automation script for batch rendering stills or frame sequences (EXR/PNG) ready for DaVinci Resolve import.

---

## Proposed Architectural Layout & Coordinates

The apartment is arranged as a unified 1-bedroom luxury residence:
- **Great Room (X: 0.0 to 4.4, Y: -4.4 to 3.8, Z: 0.0 to 2.75m)**:
  - **Kitchen**: North zone (Y: 1.15 to 3.80, X: 0.00 to 3.75). Peninsula facing south at Y=1.15.
  - **Dining**: East/Central zone alongside the island (X: 1.8 to 4.2, Y: 0.0 to 1.8), visible in CAM_02 & CAM_04.
  - **Living Lounge**: South zone (X: 0.0 to 4.2, Y: -4.4 to 0.0) with bouclé sectional, travertine table, fireplace/media wall.
  - **Terrace**: Along the entire west panoramic glazing (X: -3.0 to 0.0, Y: -4.4 to 1.0) with glass railing, two outdoor lounge chairs, and two large matte planters with Mediterranean olive trees.
- **Entry / Arrival Foyer**:
  - Main arrival point at the corridor / end of living wall (X: 3.8 to 4.8, Y: -3.8 to -2.0) with walnut console, round mirror, key tray, and warm sconce.
- **East Private Corridor & Wing (X: 4.40 to 8.20)**:
  - Private circulation corridor running south to north.
  - **Bathroom Suite**: North-East (X: 4.40 to 7.56, Y: 0.00 to 4.40), entered through a flush walnut door with jamb & threshold.
  - **Master Bedroom**: South-East (X: 4.40 to 8.20, Y: -4.40 to 0.00), entered through a flush walnut door with jamb & threshold.

---

## Blender Collections Hierarchy

All scene elements will be organized into standardized Blender collections:
- `00_SHELL`: Floor slabs, exterior perimeter walls, interior partitions, ceilings, tray ceiling, door jambs.
- `01_ENTRY_CORRIDOR`: Entry door, walnut console, round mirror, key tray, corridor doors, wall sconces.
- `02_LIVING`: Bouclé sectional, round travertine coffee table, fluted drum base, media wall, linear fireplace, rug.
- `03_DINING`: Oval travertine table, 4 bouclé dining chairs (one subtly offset), double-ring chandelier, buffet, tableware.
- `04_KITCHEN`: Cabinets, quartz/travertine waterfall island, cooktop, integrated downdraft, sink, living cabinet details.
- `05_TERRACE`: Glass railing with slim bronze frame, 2 outdoor lounge chairs, 2 matte planters with olive trees, city backdrop.
- `06_BATHROOM`: Floating vanity, backlit mirror, freestanding tub/shower, wall-hung toilet, bronze fittings, towels.
- `07_BEDROOM`: Upholstered bed, nightstands, pendant/chandelier, reading chair, wardrobe, imperfect throw.
- `08_SHARED_DETAILS`: 15mm shadow-gap baseboards, curtain pockets, linear AC slot diffusers, smart switches, thermostats, smoke detectors.
- `09_LIGHTS`: Architectural coves, downlights, practical lights, evening sun key & ambient fill.
- `10_CAMERAS`: Cameras `CAM_01` to `CAM_08` with animated motion paths and markers.
- `11_RENDER_HELPERS`: Targets, focal empties, ground planes, HDRI/sky background rigs.

---

## Detailed Step-by-Step Implementation

### Step 1: Refactor Room Blender Modules
Modify each script to:
1. Wrap standalone execution in `if __name__ == "__main__": main()`.
2. Expose `build_<room>_module(M=None, offset=(0,0,0), collection=None, ...)` that links into specified collections without clearing the scene:
   - [MODIFY] `kitchen_blender.py`: Remove old range hood objects; implement `build_downdraft_system(M, state="closed")`; implement `KITCHEN_STATES` presets; expose `build_kitchen_module`.
   - [MODIFY] `livingroom_blender.py`: Expose `build_livingroom_module(M, offset=(0,0,0), collection=None)`.
   - [MODIFY] `dining_blender.py`: Expose `build_dining_module(M, offset=(0,0,0), collection=None)`.
   - [MODIFY] `bathroom_blender.py`: Expose `build_bathroom_module(M, offset=(0,0,0), collection=None)`.
   - [MODIFY] `bedroom_blender.py`: Expose `build_bedroom_module(M, offset=(0,0,0), collection=None)`.

### Step 2: Update Web Component `KitchenScene.tsx`
- [MODIFY] `src/components/kitchen/KitchenScene.tsx`:
  - Replace `<RangeHood />` with `<DowndraftSystem state={activeState.downdraft} />`.
  - Expose discrete subcomponents:
    - `IntegratedDishwasher`
    - `UnderSinkPullout`
    - `NarrowOilPullout`
    - `DeepPotDrawer`
    - `GlassCabinetPorcelain`
    - `KitchenAccentLighting`
  - Control visibility and open states via `activeOpenUnit` / `activeState`.

### Step 3: Build `apartment_master_blender.py`
Create the master pipeline script in both `public/` and `E:\Blender\Kitchen\`:
1. **Scene Reset & Collections**: Initializes `Apartment_Master_Scene`, builds the 12 collections.
2. **Master PBR Material Library**:
   - Greige plaster wall with micro-noise bump
   - Travertine stone with subtle veins and soft roughness
   - Natural walnut with directional grain & bump
   - Bouclé fabric with fibrous micro-texture
   - Smoked / fluted glass with realistic IOR
   - Muted brushed bronze & matte black metal
   - Linen drapery
3. **Envelope & Shared Architecture (`00_SHELL`, `01_ENTRY_CORRIDOR`, `05_TERRACE`)**:
   - Continuous flooring with 15mm dark recessed shadow gaps at all floor-wall junctions.
   - Recessed curtain pocket slots along the west facade.
   - Linear AC slot diffusers integrated into ceiling bulkheads.
   - Entry foyer with walnut console, circular mirror, brass sconce, and key tray.
   - Proper door jambs, thresholds, and corridor doors to Bathroom and Master Bedroom.
   - Balcony glass railing (slim bronze profile), exterior floor drop (3cm), drainage slot, 2 outdoor lounge chairs, 2 matte planters with olive greenery, and evening skyline backdrop.
   - Smart switch plates at entry, bathroom, bedroom, and kitchen walls; corridor thermostat; smoke detector.
4. **Room Module Assembly**:
   - Calls `build_kitchen_module`, `build_livingroom_module`, `build_dining_module`, `build_bathroom_module`, and `build_bedroom_module` with tuned offsets into their respective collections.
5. **Lighting Presets (`09_LIGHTS`)**:
   - `ARRIVAL`: Warm 2700K entry and living lights, kitchen task low, cove soft.
   - `DINNER`: Dining chandelier active, warm island pendant, subtle under-cabinet task, warm cove.
   - `LATE_NIGHT`: Low ambient, toe-kick very dim, glass cabinet backlight, city lights prominent.
6. **Cinematic Cameras (`10_CAMERAS`) & Animation at 24 fps**:
   - `CAM_01_ENTRY_ARRIVAL`: 28mm, frames 1–168 (7s slow dolly from entry into Great Room reveal).
   - `CAM_02_GREAT_ROOM_REVEAL`: 30mm, frames 1–192 (8s gentle push/pan across living, dining, kitchen, terrace).
   - `CAM_03_KITCHEN_HERO`: 35mm, frames 1–144 (6s island orbit, all units closed, downdraft closed).
   - `CAM_04_DINING_TERRACE`: 40mm, frames 1–120 (5s elegant push connecting dining table and terrace).
   - `CAM_05_KITCHEN_DETAIL`: 55mm, frames 1–96 (4s close-up; downdraft raised for cooking detail or drawer open).
   - `CAM_06_BATHROOM_SUITE`: 32mm, frames 1–120 (5s lateral glide past vanity to tub/shower).
   - `CAM_07_BEDROOM_REST`: 40mm, frames 1–120 (5s slow push toward bed and reading corner).
   - `CAM_08_TERRACE_RETURN`: 35mm, frames 1–144 (6s pull-back from terrace gazing into warm interior).
   - All cameras configured with depth-of-field, physical sensor dimensions, and smooth Bezier easing.

### Step 4: DaVinci Resolve Output Pipeline
- Add `render_master_sequence.py` utility:
  - Allows rendering still plates for all 8 cameras at 4K/2K with Cycles + AgX + OpenImageDenoise.
  - Allows rendering animated frame sequences (PNG 16-bit / EXR) at 24 fps for CAM_01 through CAM_08 ready for direct import into DaVinci Resolve timelines.

---

## Verification Plan

### Automated / Headless Verification
1. **Module Import Test**:
   - Run Python test script importing all 5 refactored modules to confirm none clears the scene or errors out when imported.
2. **Master Scene Build Test**:
   - Execute `apartment_master_blender.py` via Blender MCP client or headless Blender.
   - Verify all 12 collections exist and contain their expected objects.
   - Verify range hood objects are absent and downdraft system exists.
   - Verify all 8 cameras exist, have focal lengths and animation keyframes set to 24 fps.
3. **Test Render**:
   - Render a quick preview pass of `CAM_02_GREAT_ROOM_REVEAL` and `CAM_03_KITCHEN_HERO` to verify materials, lighting, and composition.
4. **TypeScript Build Verification**:
   - Run `pnpm build` or `npx vite build` in `C:\Users\itachi\Downloads\Greeting User` to verify `KitchenScene.tsx` compiles cleanly.
