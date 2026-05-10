# Hex Tiles

A pygame-ce/OpenGL prototype that compares regular repeated texture sampling
with GPU hex-tiled sampling using randomized offsets, randomized rotations,
noisy border masks, and optional luminance-aware blending.

The demo uses `c0ca617f-d836-45a5-9c48-7d0522272999.png` as a terrain atlas
when it is present. It crops the 8 by 4 grid of tile interiors into individual
textures, trims away the atlas gutters, and lets you cycle them at runtime.

## Run

```powershell
uv run main.py
```

Or, using the checked-out virtual environment:

```powershell
.\.venv\Scripts\python.exe main.py
```

The renderer requests an OpenGL 3.3 core profile context.

## Controls

The app opens a Dear PyGui control panel next to the pygame/OpenGL render window.
Use the panel to adjust tile frequency, hex size, blend sharpness, noisy border
settings, random rotation, random mirroring, luminance blending, pause state,
tiling mode, and atlas texture.

- `Esc`: quit from the render window
