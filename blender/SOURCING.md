# Realism kit — sources, palette, materials

Everything below is **CC0 / public domain** (Poly Haven, Wikimedia): OK to sell, no credit needed.
Download all of it with `python blender/fetch_assets.py` (~600 MB at 2k, resumable). The list lives in `apartment/sourcing.json`.

## Palette — "Warm Gallery"
| role | hex | where |
|---|---|---|
| Ivory plaster | `#EDE6DA` | walls, ceilings |
| Travertine | `#D8CBB6` | coffee table, island, bath counter |
| Light oak | `#B88E62` | floors |
| Walnut | `#5A3B26` | slat wall, media wall, doors |
| Smoked walnut | `#2E2018` | plinths, frames |
| Bouclé | `#E9E2D4` | Freedom Sofa, bedroom bench |
| Olive linen | `#7C7A5A` | cushions, bedding (1 accent per room) |
| Aged bronze | `#8C6A3F` | pulls, trims, lamp shades |
| Charcoal | `#2B2A28` | mullions, black metal |
| Rembrandt ochre/red | `#B4572E` / `#C9A055` | the painting — the room's only saturated colour |

Rule: 70 % warm neutrals, 25 % wood, 5 % bronze + one ochre/olive accent. No pure white (max `#F2EEE8`), no pure black (min `#1E1C1A`).

## Lighting for realism
- Ceiling 3500 K, practicals 2700 K, sun as the only cool source.
- Window view: HDRI `hotel_rooftop_balcony` (day) / `venice_sunset` (golden-hour version for a second cut). With a real HDRI behind the glass, the window view stops looking empty.
- Each LED cove: 1 cm emission strip plus a real area light. Never use emission alone as the light source.

## Texture mapping (2k, real-world scale)
| material | Poly Haven id | tile size |
|---|---|---|
| floor_oak | oak_veneer_01 | 1.2 m planks, rotated per board |
| walnut / walnut_dark | walnut_veneer / smoked_walnut_veneer | 1 m |
| plaster | white_plaster_02 | 2 m, micro-bump only |
| travertine | marble_01 (tinted warm) | 1.5 m |
| dark_stone | terrazzo_tiles | 1 m |
| boucle / linen / fabric_dark | wool_boucle / rough_linen / velour_velvet | 0.3 m |
| rug | poly_wool_herringbone | 0.5 m |
| tile (bath) | long_white_tiles | real tile size |
| terrace_stone | stone_tiles_02 | 1 m |

## Set dressing (sells the "lived-in luxury" look)
- Living: lounge chair + ottoman, throw pillows, vase, book stack, candles.
- Dining: brass vase, wooden bowl, goblets under the Rembrandt.
- Kitchen: vase plus wine bottles. Keep the counters 80 % empty.
- Entry: marble bust on the console, matching the slat wall.
- Bedroom: arm lamp, books, a framed photo.
- Terrace: 2–3 real potted plants instead of the cones.

Rule of three: on every surface group objects in threes at different heights, and leave negative space.

## Rembrandt
*The Return of the Prodigal Son* (c.1668, Hermitage). Downloaded at 3840×5011 px, public domain. The canvas in config is set to the true 0.766 aspect ratio (0.84 × 1.096 m).
