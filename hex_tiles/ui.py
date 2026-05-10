import pygame

from .config import WIDTH


def draw_text(screen, font, text, pos):
    img = font.render(text, True, (230, 230, 230))
    screen.blit(img, pos)


def draw_overlay(font, params, texture_index):
    overlay = pygame.Surface((WIDTH, 72), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 230))
    pygame.draw.line(overlay, (255, 255, 255), (WIDTH // 2, 0), (WIDTH // 2, 72), 1)
    draw_text(overlay, font, "Regular repeated texture", (20, 16))
    draw_text(
        overlay,
        font,
        "OpenGL hex-tiled: random offset/rotation + noisy border blend",
        (WIDTH // 2 + 20, 16),
    )
    draw_text(
        overlay,
        font,
        f"freq={params.tile_freq:.2f}  hex={params.hex_size:.1f}  blend={params.blend_power:.2f}  "
        f"noise={params.noise_strength:.2f}  contrast={params.noise_contrast:.2f}  "
        f"noisy={params.noise_blend}  rotate={params.rotate}  texture={texture_index + 1}",
        (20, 44),
    )
    return overlay
