import numpy as np
import pygame

from .config import (
    ATLAS_CROP_INSET,
    ATLAS_PATH,
    ATLAS_X_RANGES,
    ATLAS_Y_RANGES,
    TEX_SIZE,
)


def surface_to_float_rgb(surface):
    arr = pygame.surfarray.array3d(surface).swapaxes(0, 1)
    return arr.astype(np.float32) / 255.0


def make_source_texture(seed=1):
    rng = np.random.default_rng(seed)

    y, x = np.mgrid[0:TEX_SIZE, 0:TEX_SIZE]
    tex = np.zeros((TEX_SIZE, TEX_SIZE, 3), dtype=np.float32)

    base = 0.42 + 0.12 * np.sin(x * 0.10) + 0.10 * np.cos(y * 0.13)
    fine = rng.normal(0.0, 0.08, (TEX_SIZE, TEX_SIZE))
    tex[..., 0] = base + fine
    tex[..., 1] = base * 0.92 + fine * 0.6
    tex[..., 2] = base * 0.78 + fine * 0.4

    for _ in range(120):
        cx, cy = rng.integers(0, TEX_SIZE, size=2)
        rad = rng.uniform(2.0, 9.0)
        color = rng.uniform(0.25, 0.85, size=3)

        dx = ((x - cx + TEX_SIZE // 2) % TEX_SIZE) - TEX_SIZE // 2
        dy = ((y - cy + TEX_SIZE // 2) % TEX_SIZE) - TEX_SIZE // 2
        mask = np.exp(-(dx * dx + dy * dy) / (2.0 * rad * rad))[..., None]
        tex = tex * (1.0 - mask * 0.45) + color * (mask * 0.45)

    return np.clip(tex, 0.0, 1.0)


def load_atlas_textures(path=ATLAS_PATH):
    try:
        atlas = pygame.image.load(path)
        if pygame.display.get_surface() is not None:
            atlas = atlas.convert_alpha()
    except (FileNotFoundError, pygame.error):
        return []

    textures = []

    for y0, y1 in ATLAS_Y_RANGES:
        for x0, x1 in ATLAS_X_RANGES:
            x = x0 + ATLAS_CROP_INSET
            y = y0 + ATLAS_CROP_INSET
            w = x1 - x0 - ATLAS_CROP_INSET * 2
            h = y1 - y0 - ATLAS_CROP_INSET * 2
            crop = atlas.subsurface(pygame.Rect(x, y, w, h))
            scaled = pygame.transform.smoothscale(crop, (TEX_SIZE, TEX_SIZE))
            textures.append(surface_to_float_rgb(scaled))

    return textures

