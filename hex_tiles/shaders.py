VERTEX_SHADER = """
#version 330 core

const vec2 VERTICES[3] = vec2[3](
    vec2(-1.0, -1.0),
    vec2(3.0, -1.0),
    vec2(-1.0, 3.0)
);

out vec2 v_uv;

void main() {
    vec2 pos = VERTICES[gl_VertexID];
    v_uv = pos * 0.5 + 0.5;
    gl_Position = vec4(pos, 0.0, 1.0);
}
"""

TEXTURE_FRAGMENT_SHADER = """
#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_texture;
uniform vec2 u_resolution;
uniform float u_time;
uniform float u_hex_size;
uniform float u_tile_freq;
uniform float u_blend_power;
uniform float u_noise_strength;
uniform float u_noise_scale;
uniform float u_noise_contrast;
uniform bool u_rotate;
uniform bool u_mirror;
uniform bool u_lum_blend;
uniform bool u_noise_blend;
uniform bool u_hex_mode;
uniform int u_tiling_mode;

const float SQRT3 = 1.7320508075688772;
const float INV_SQRT3 = 0.5773502691896258;
const vec2 NEIGHBORS[6] = vec2[6](
    vec2(1.0, 0.0),
    vec2(-1.0, 0.0),
    vec2(0.0, 1.0),
    vec2(0.0, -1.0),
    vec2(1.0, -1.0),
    vec2(-1.0, 1.0)
);

uint hash_u32(uint x) {
    x ^= x >> 16;
    x *= 0x7feb352du;
    x ^= x >> 15;
    x *= 0x846ca68bu;
    x ^= x >> 16;
    return x;
}

float rand01(uint seed) {
    return float(hash_u32(seed)) / 4294967295.0;
}

float value_noise(vec2 p) {
    ivec2 i = ivec2(floor(p));
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);

    uint a = hash_u32(uint(i.x) * 73856093u ^ uint(i.y) * 19349663u);
    uint b = hash_u32(uint(i.x + 1) * 73856093u ^ uint(i.y) * 19349663u);
    uint c = hash_u32(uint(i.x) * 73856093u ^ uint(i.y + 1) * 19349663u);
    uint d = hash_u32(uint(i.x + 1) * 73856093u ^ uint(i.y + 1) * 19349663u);

    float x0 = mix(rand01(a), rand01(b), f.x);
    float x1 = mix(rand01(c), rand01(d), f.x);
    return mix(x0, x1, f.y);
}

float fbm(vec2 p) {
    float n = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 4; i++) {
        n += value_noise(p) * amp;
        p = p * 2.03 + vec2(17.1, 9.2);
        amp *= 0.5;
    }
    return n;
}

float contrast_noise(float n) {
    return clamp((n - 0.5) * u_noise_contrast + 0.5, 0.0, 1.0);
}

uint hex_seed(ivec2 cell) {
    return hash_u32(uint(cell.x) * 73856093u ^ uint(cell.y) * 19349663u);
}

vec2 pixel_to_axial(vec2 p, float size) {
    return vec2((SQRT3 / 3.0 * p.x - p.y / 3.0) / size, (2.0 / 3.0 * p.y) / size);
}

ivec2 cube_round(vec2 axial) {
    float x = axial.x;
    float z = axial.y;
    float y = -x - z;

    float rx = round(x);
    float ry = round(y);
    float rz = round(z);

    float dx = abs(rx - x);
    float dy = abs(ry - y);
    float dz = abs(rz - z);

    if (dx > dy && dx > dz) {
        rx = -ry - rz;
    } else if (dy > dz) {
        ry = -rx - rz;
    } else {
        rz = -rx - ry;
    }

    return ivec2(int(rx), int(rz));
}

vec2 axial_to_pixel(ivec2 cell, float size) {
    return vec2(size * SQRT3 * (float(cell.x) + float(cell.y) * 0.5), size * 1.5 * float(cell.y));
}

vec3 sample_tile(vec2 p, ivec2 cell, float tile_freq) {
    uint seed = hex_seed(cell);
    vec2 center = axial_to_pixel(cell, u_hex_size);
    vec2 local = p - center;

    if (u_rotate) {
        float angle = float(hash_u32(seed + 37u) % 6u) * 1.0471975511965976;
        float ca = cos(angle);
        float sa = sin(angle);
        local = vec2(local.x * ca - local.y * sa, local.x * sa + local.y * ca);
    }

    vec2 offset = vec2(rand01(seed + 11u), rand01(seed + 23u));
    vec2 uv = local * tile_freq / vec2(textureSize(u_texture, 0)) + offset;

    if (u_mirror) {
        if (rand01(seed + 53u) < 0.5) {
            uv.x = -uv.x;
        }
        if (rand01(seed + 71u) < 0.5) {
            uv.y = -uv.y;
        }
    }

    return texture(u_texture, uv).rgb;
}

float luminance(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

vec3 restore_detail(vec3 blended, vec3 anchor, float strength) {
    float blended_lum = max(luminance(blended), 0.0001);
    float anchor_lum = max(luminance(anchor), 0.0001);
    vec3 detail = anchor * (blended_lum / anchor_lum);
    return clamp(mix(blended, detail, strength), 0.0, 1.0);
}

vec2 triangular_to_pixel(ivec2 cell, float size) {
    return vec2(
        size * (float(cell.x) + float(cell.y) * 0.5),
        size * 0.8660254037844386 * float(cell.y)
    );
}

vec2 pixel_to_triangular(vec2 p, float size) {
    return vec2(
        p.x / size - p.y * INV_SQRT3 / size,
        p.y * 2.0 * INV_SQRT3 / size
    );
}

vec3 sample_stochastic_tile(vec2 p, ivec2 cell, float tile_freq) {
    uint seed = hex_seed(cell);
    vec2 center = triangular_to_pixel(cell, u_hex_size);
    vec2 local = p - center;

    float scale = mix(0.9, 1.12, rand01(seed + 89u));
    vec2 texture_size = vec2(textureSize(u_texture, 0));
    vec2 uv_base = local * tile_freq * scale / texture_size;
    vec2 dx = dFdx(p) * tile_freq * scale / texture_size;
    vec2 dy = dFdy(p) * tile_freq * scale / texture_size;

    if (u_rotate) {
        float angle = float(hash_u32(seed + 37u) % 6u) * 1.0471975511965976;
        float ca = cos(angle);
        float sa = sin(angle);
        mat2 rotation = mat2(ca, sa, -sa, ca);
        uv_base = rotation * uv_base;
        dx = rotation * dx;
        dy = rotation * dy;
    }

    vec2 mirror = vec2(1.0);
    if (u_mirror) {
        if (rand01(seed + 53u) < 0.5) {
            mirror.x = -1.0;
        }
        if (rand01(seed + 71u) < 0.5) {
            mirror.y = -1.0;
        }
    }

    vec2 offset = vec2(rand01(seed + 11u), rand01(seed + 23u));
    vec2 uv = uv_base * mirror + offset;
    return textureGrad(u_texture, uv, dx * mirror, dy * mirror).rgb;
}

vec3 render_triangular_stochastic(vec2 p) {
    vec2 grid = pixel_to_triangular(p, u_hex_size);
    ivec2 base = ivec2(floor(grid));
    vec2 f = fract(grid);

    ivec2 c0;
    ivec2 c1;
    ivec2 c2;
    vec3 weights;

    if (f.x + f.y < 1.0) {
        c0 = base;
        c1 = base + ivec2(1, 0);
        c2 = base + ivec2(0, 1);
        weights = vec3(1.0 - f.x - f.y, f.x, f.y);
    } else {
        c0 = base + ivec2(1, 1);
        c1 = base + ivec2(0, 1);
        c2 = base + ivec2(1, 0);
        weights = vec3(f.x + f.y - 1.0, 1.0 - f.x, 1.0 - f.y);
    }

    weights = pow(max(weights, vec3(0.0)), vec3(u_blend_power));
    weights /= max(weights.x + weights.y + weights.z, 0.000001);

    if (u_noise_blend) {
        vec3 noise_weights = vec3(
            contrast_noise(fbm((p - triangular_to_pixel(c0, u_hex_size)) * u_noise_scale + vec2(11.0, 3.0))),
            contrast_noise(fbm((p - triangular_to_pixel(c1, u_hex_size)) * u_noise_scale + vec2(29.0, 47.0))),
            contrast_noise(fbm((p - triangular_to_pixel(c2, u_hex_size)) * u_noise_scale + vec2(61.0, 13.0)))
        );
        weights *= mix(vec3(1.0), vec3(0.45) + noise_weights * 1.1, u_noise_strength);
        weights /= max(weights.x + weights.y + weights.z, 0.000001);
    }

    vec3 c0_sample = sample_stochastic_tile(p, c0, u_tile_freq);
    vec3 c1_sample = sample_stochastic_tile(p, c1, u_tile_freq);
    vec3 c2_sample = sample_stochastic_tile(p, c2, u_tile_freq);
    vec3 color = c0_sample * weights.x + c1_sample * weights.y + c2_sample * weights.z;

    int dominant_index = weights.y > weights.x ? 1 : 0;
    float dominant_weight = max(weights.x, weights.y);
    if (weights.z > dominant_weight) {
        dominant_index = 2;
    }
    vec3 anchor = dominant_index == 0 ? c0_sample : dominant_index == 1 ? c1_sample : c2_sample;
    color = restore_detail(color, anchor, 0.35 * (1.0 - max(max(weights.x, weights.y), weights.z)));

    if (u_lum_blend) {
        float lum = luminance(color);
        float anchor_lum = max(luminance(anchor), 0.0001);
        color = clamp(mix(color, anchor * (lum / anchor_lum), 0.25), 0.0, 1.0);
    }

    return color;
}

void main() {
    vec2 p = vec2(v_uv.x * u_resolution.x, (1.0 - v_uv.y) * u_resolution.y);
    p.x += u_time * 20.0;

    if (!u_hex_mode) {
        vec2 uv = p * u_tile_freq / vec2(textureSize(u_texture, 0));
        frag_color = vec4(texture(u_texture, uv).rgb, 1.0);
        return;
    }

    if (u_tiling_mode == 1) {
        frag_color = vec4(render_triangular_stochastic(p), 1.0);
        return;
    }

    ivec2 center = cube_round(pixel_to_axial(p, u_hex_size));
    vec2 center_pos = axial_to_pixel(center, u_hex_size);
    float center_d2 = dot(p - center_pos, p - center_pos);

    ivec2 best_a = center + ivec2(NEIGHBORS[0]);
    ivec2 best_b = center + ivec2(NEIGHBORS[1]);
    float best_a_d2 = 3.402823e38;
    float best_b_d2 = 3.402823e38;

    for (int i = 0; i < 6; i++) {
        ivec2 candidate = center + ivec2(NEIGHBORS[i]);
        vec2 candidate_pos = axial_to_pixel(candidate, u_hex_size);
        float d2 = dot(p - candidate_pos, p - candidate_pos);
        if (d2 < best_a_d2) {
            best_b = best_a;
            best_b_d2 = best_a_d2;
            best_a = candidate;
            best_a_d2 = d2;
        } else if (d2 < best_b_d2) {
            best_b = candidate;
            best_b_d2 = d2;
        }
    }

    vec3 c0 = sample_tile(p, center, u_tile_freq);
    vec3 c1 = sample_tile(p, best_a, u_tile_freq);
    vec3 c2 = sample_tile(p, best_b, u_tile_freq);

    float d0 = sqrt(center_d2);
    float d1 = sqrt(best_a_d2);
    float d2 = sqrt(best_b_d2);
    float blend_width = mix(46.0, 4.0, smoothstep(0.3, 8.0, u_blend_power));

    float w1 = 1.0 - smoothstep(0.0, blend_width, d1 - d0);
    float w2 = 1.0 - smoothstep(0.0, blend_width, d2 - d0);
    float w0 = 1.0;

    if (u_noise_blend) {
        float n0 = fbm((p - axial_to_pixel(center, u_hex_size)) * u_noise_scale + vec2(11.0, 3.0));
        float n1 = fbm((p - axial_to_pixel(best_a, u_hex_size)) * u_noise_scale + vec2(29.0, 47.0));
        float n2 = fbm((p - axial_to_pixel(best_b, u_hex_size)) * u_noise_scale + vec2(61.0, 13.0));
        n0 = contrast_noise(n0);
        n1 = contrast_noise(n1);
        n2 = contrast_noise(n2);
        float edge_noise = (n0 + n1 + n2) * 0.3333333 - 0.5;
        float noisy_width = blend_width * mix(1.0, 0.55 + edge_noise * 0.9, u_noise_strength);
        w1 = 1.0 - smoothstep(0.0, max(noisy_width, 1.0), d1 - d0);
        w2 = 1.0 - smoothstep(0.0, max(noisy_width, 1.0), d2 - d0);
    }

    float total = max(w0 + w1 + w2, 0.000001);
    w0 /= total;
    w1 /= total;
    w2 /= total;

    if (u_lum_blend) {
        float l0 = luminance(c0);
        float l1 = luminance(c1);
        float l2 = luminance(c2);
        float mean_lum = l0 * w0 + l1 * w1 + l2 * w2;
        w0 *= 1.0 / (0.18 + abs(l0 - mean_lum));
        w1 *= 1.0 / (0.18 + abs(l1 - mean_lum));
        w2 *= 1.0 / (0.18 + abs(l2 - mean_lum));
        total = max(w0 + w1 + w2, 0.000001);
        w0 /= total;
        w1 /= total;
        w2 /= total;
    }

    vec3 color = c0 * w0 + c1 * w1 + c2 * w2;
    float border_mix = clamp(w1 + w2, 0.0, 1.0);
    color = restore_detail(color, c0, 0.45 * border_mix);

    frag_color = vec4(color, 1.0);
}
"""

OVERLAY_FRAGMENT_SHADER = """
#version 330 core

in vec2 v_uv;
out vec4 frag_color;

uniform sampler2D u_overlay;

void main() {
    frag_color = texture(u_overlay, vec2(v_uv.x, 1.0 - v_uv.y));
}
"""
