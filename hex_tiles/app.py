from dataclasses import dataclass

import pygame

from .atlas import load_atlas_textures, make_source_texture
from .config import HEIGHT, WIDTH
from .control_panel import ControlPanel
from .gl_renderer import OpenGLRenderer
from .ui import draw_overlay


@dataclass
class RenderParams:
    t: float = 0.0
    hex_size: float = 56.0
    tile_freq: float = 1.0
    blend_power: float = 2.0
    noise_strength: float = 0.65
    noise_scale: float = 0.035
    noise_contrast: float = 1.5
    rotate: bool = True
    lum_blend: bool = False
    noise_blend: bool = True


def create_window():
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
    pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
    pygame.display.gl_set_attribute(
        pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE
    )
    pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("Practical Real-Time Hex-Tiling - OpenGL")


def handle_keydown(event, state):
    if event.key == pygame.K_ESCAPE:
        state["running"] = False


def cycle_texture(state, direction=1):
    textures = state["atlas_textures"]
    if textures:
        state["texture_index"] = (state["texture_index"] + direction) % len(textures)
        tex = textures[state["texture_index"]]
    else:
        state["seed"] += direction
        tex = make_source_texture(state["seed"])

    state["renderer"].upload_texture(tex)


def request_texture_cycle(state, direction=1):
    state["pending_texture_delta"] += direction


def process_pending_texture_cycle(state):
    direction = state["pending_texture_delta"]
    if direction == 0:
        return

    state["pending_texture_delta"] = 0
    cycle_texture(state, direction)


def main():
    pygame.init()
    create_window()

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    renderer = OpenGLRenderer(WIDTH, HEIGHT)
    atlas_textures = load_atlas_textures()
    seed = 1
    initial_texture = atlas_textures[0] if atlas_textures else make_source_texture(seed)
    renderer.upload_texture(initial_texture)

    params = RenderParams()
    state = {
        "atlas_textures": atlas_textures,
        "request_texture_cycle": None,
        "pending_texture_delta": 0,
        "paused": False,
        "params": params,
        "renderer": renderer,
        "running": True,
        "seed": seed,
        "texture_index": 0,
    }
    state["request_texture_cycle"] = lambda direction=1: request_texture_cycle(
        state, direction
    )
    control_panel = ControlPanel(params, state)

    try:
        while state["running"] and not control_panel.should_close:
            dt = clock.tick(60) / 1000.0
            if not state["paused"]:
                params.t += dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    state["running"] = False
                if event.type == pygame.KEYDOWN:
                    handle_keydown(event, state)

            process_pending_texture_cycle(state)

            overlay = draw_overlay(font, params, state["texture_index"])
            renderer.render(overlay, params)
            pygame.display.flip()
            control_panel.render_frame()

    finally:
        control_panel.destroy()
        pygame.quit()
