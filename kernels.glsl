#ifndef PLUSHIE_KERNELS
#define PLUSHIE_KERNELS

vec4 bilinear(sampler2D tex, vec2 uv, vec2 texSz) {
    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);
    vec4 c00 = texture(tex, safeUV((base + 0.5) / texSz, texSz));
    vec4 c10 = texture(tex, safeUV((base + vec2(1.5, 0.5)) / texSz, texSz));
    vec4 c01 = texture(tex, safeUV((base + vec2(0.5, 1.5)) / texSz, texSz));
    vec4 c11 = texture(tex, safeUV((base + vec2(1.5, 1.5)) / texSz, texSz));
    return mix(mix(c00, c10, f.x), mix(c01, c11, f.x), f.y);
}

bool atBorder(vec2 uv, vec2 texSz, float margin) {
    vec2 px = margin / texSz;
    return uv.x < px.x || uv.x > 1.0 - px.x || uv.y < px.y || uv.y > 1.0 - px.y;
}

vec4 kernelSharp(sampler2D tex, vec2 uv, vec2 texSz) {
    if (atBorder(uv, texSz, 2.0)) return bilinear(tex, uv, texSz);

    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);

    vec4 c = vec4(0.0);
    float ws = 0.0;
    vec4 mn = vec4(1e10);
    vec4 mx = vec4(-1e10);
    float sc = 1.75;

    for (int j = -1; j <= 2; ++j) {
        for (int i = -1; i <= 2; ++i) {
            float wx = cubic((f.x - float(i)) * sc);
            float wy = cubic((f.y - float(j)) * sc);
            float w = wx * wy;
            vec2 p = safeUV((base + vec2(float(i), float(j)) + 0.5) / texSz, texSz);
            vec4 s = texture(tex, p);
            c += s * w;
            ws += w;
            mn = min(mn, s);
            mx = max(mx, s);
        }
    }
    return clamp(c / max(ws, 1e-5), mn, mx);
}

vec4 kernelBalanced(sampler2D tex, vec2 uv, vec2 texSz) {
    if (atBorder(uv, texSz, 2.0)) return bilinear(tex, uv, texSz);

    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);

    vec4 c = vec4(0.0);
    float ws = 0.0;
    vec4 mn = vec4(1e10);
    vec4 mx = vec4(-1e10);
    float sc = 1.32;

    for (int j = -1; j <= 2; ++j) {
        for (int i = -1; i <= 2; ++i) {
            float wx = cubic((f.x - float(i)) * sc);
            float wy = cubic((f.y - float(j)) * sc);
            float w = wx * wy;
            vec2 p = safeUV((base + vec2(float(i), float(j)) + 0.5) / texSz, texSz);
            vec4 s = texture(tex, p);
            c += s * w;
            ws += w;
            mn = min(mn, s);
            mx = max(mx, s);
        }
    }
    return clamp(c / max(ws, 1e-5), mn, mx);
}

vec4 kernelSmooth(sampler2D tex, vec2 uv, vec2 texSz) {
    if (atBorder(uv, texSz, 2.0)) return bilinear(tex, uv, texSz);

    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);

    vec4 c = vec4(0.0);
    float ws = 0.0;
    vec4 mn = vec4(1e10);
    vec4 mx = vec4(-1e10);
    const float a = 3.0;

    for (int j = -2; j <= 2; ++j) {
        for (int i = -2; i <= 2; ++i) {
            float dx = f.x - float(i);
            float dy = f.y - float(j);
            float wx = abs(dx) < a ? sin(3.14159265 * dx) * sin(3.14159265 * dx / a) / (3.14159265 * dx * 3.14159265 * dx / a) : 0.0;
            float wy = abs(dy) < a ? sin(3.14159265 * dy) * sin(3.14159265 * dy / a) / (3.14159265 * dy * 3.14159265 * dy / a) : 0.0;
            if (abs(dx) < 1e-5) wx = 1.0;
            if (abs(dy) < 1e-5) wy = 1.0;
            float w = wx * wy;
            vec2 p = safeUV((base + vec2(float(i), float(j)) + 0.5) / texSz, texSz);
            vec4 s = texture(tex, p);
            c += s * w;
            ws += w;
            mn = min(mn, s);
            mx = max(mx, s);
        }
    }
    return clamp(c / max(ws, 1e-5), mn, mx);
}

#endif
