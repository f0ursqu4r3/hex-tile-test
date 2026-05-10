import numpy as np
import pygame
from OpenGL import GL

from .shaders import OVERLAY_FRAGMENT_SHADER, TEXTURE_FRAGMENT_SHADER, VERTEX_SHADER


def compile_shader(shader_type, source):
    shader = GL.glCreateShader(shader_type)
    GL.glShaderSource(shader, source)
    GL.glCompileShader(shader)
    if not GL.glGetShaderiv(shader, GL.GL_COMPILE_STATUS):
        log = GL.glGetShaderInfoLog(shader).decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenGL shader compile failed:\n{log}")
    return shader


def create_program(vertex_source, fragment_source):
    vertex = compile_shader(GL.GL_VERTEX_SHADER, vertex_source)
    fragment = compile_shader(GL.GL_FRAGMENT_SHADER, fragment_source)
    program = GL.glCreateProgram()
    GL.glAttachShader(program, vertex)
    GL.glAttachShader(program, fragment)
    GL.glLinkProgram(program)
    GL.glDeleteShader(vertex)
    GL.glDeleteShader(fragment)
    if not GL.glGetProgramiv(program, GL.GL_LINK_STATUS):
        log = GL.glGetProgramInfoLog(program).decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenGL program link failed:\n{log}")
    return program


class OpenGLRenderer:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.texture_program = create_program(VERTEX_SHADER, TEXTURE_FRAGMENT_SHADER)
        self.overlay_program = create_program(VERTEX_SHADER, OVERLAY_FRAGMENT_SHADER)
        self.vao = GL.glGenVertexArrays(1)
        self.texture_id = GL.glGenTextures(1)
        self.overlay_id = GL.glGenTextures(1)

        GL.glBindVertexArray(self.vao)
        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)

        self._init_texture(self.texture_id)
        self._init_texture(self.overlay_id)

    def _init_texture(self, texture_id):
        GL.glBindTexture(GL.GL_TEXTURE_2D, texture_id)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def upload_texture(self, tex):
        arr = np.ascontiguousarray((np.clip(tex, 0.0, 1.0) * 255).astype(np.uint8))
        h, w, _ = arr.shape
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            w,
            h,
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            arr,
        )

    def render_texture_view(self, viewport, params, hex_mode):
        x, y, w, h = viewport
        GL.glViewport(x, y, w, h)
        GL.glUseProgram(self.texture_program)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture_id)
        GL.glUniform1i(GL.glGetUniformLocation(self.texture_program, "u_texture"), 0)
        GL.glUniform2f(
            GL.glGetUniformLocation(self.texture_program, "u_resolution"), float(w), float(h)
        )
        GL.glUniform1f(GL.glGetUniformLocation(self.texture_program, "u_time"), params.t)
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_hex_size"), params.hex_size
        )
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_tile_freq"), params.tile_freq
        )
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_blend_power"), params.blend_power
        )
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_noise_strength"),
            params.noise_strength,
        )
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_noise_scale"),
            params.noise_scale,
        )
        GL.glUniform1f(
            GL.glGetUniformLocation(self.texture_program, "u_noise_contrast"),
            params.noise_contrast,
        )
        GL.glUniform1i(GL.glGetUniformLocation(self.texture_program, "u_rotate"), params.rotate)
        GL.glUniform1i(
            GL.glGetUniformLocation(self.texture_program, "u_lum_blend"),
            params.lum_blend,
        )
        GL.glUniform1i(
            GL.glGetUniformLocation(self.texture_program, "u_noise_blend"),
            params.noise_blend,
        )
        GL.glUniform1i(
            GL.glGetUniformLocation(self.texture_program, "u_hex_mode"), hex_mode
        )
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)

    def render_overlay(self, surface):
        arr = pygame.surfarray.pixels3d(surface).swapaxes(0, 1).copy()
        alpha = pygame.surfarray.pixels_alpha(surface).swapaxes(0, 1).copy()
        rgba = np.dstack((arr, alpha)).astype(np.uint8)
        h, w, _ = rgba.shape

        GL.glBindTexture(GL.GL_TEXTURE_2D, self.overlay_id)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGBA8,
            w,
            h,
            0,
            GL.GL_RGBA,
            GL.GL_UNSIGNED_BYTE,
            np.ascontiguousarray(rgba),
        )
        GL.glViewport(0, self.height - h, w, h)
        GL.glUseProgram(self.overlay_program)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.overlay_id)
        GL.glUniform1i(GL.glGetUniformLocation(self.overlay_program, "u_overlay"), 0)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)

    def render(self, overlay, params):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        self.render_texture_view((0, 0, self.width // 2, self.height), params, False)
        self.render_texture_view(
            (self.width // 2, 0, self.width // 2, self.height), params, True
        )
        self.render_overlay(overlay)
