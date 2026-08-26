#ifndef PLUSHIE_KERNELS
#define PLUSHIE_KERNELS

vec4 kernelSharp(sampler2D tex, vec2 uv, vec2 texSz) {
    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);

    vec4 c = vec4(0.0);
    float ws = 0.0;
    float sc = 1.28;

    for (int j = -1; j <= 2; ++j) {
        for (int i = -1; i <= 2; ++i) {
            float wx = cubic((f.x - float(i)) * sc);
            float wy = cubic((f.y - float(j)) * sc);
            float w = wx * wy;
            vec2 p = safeUV((base + vec2(float(i), float(j)) + 0.5) / texSz, texSz);
            c += texture(tex, p) * w;
            ws += w;
        }
    }
    return c / max(ws, 1e-5);
}

vec4 kernelBalanced(sampler2D tex, vec2 uv, vec2 texSz) {
    vec2 src = uv * texSz - 0.5;
    vec2 base = floor(src);
    vec2 f = fract(src);

    vec4 c = vec4(0.0);
    float ws = 0.0;
    float sc = 1.05;

    for (int j = -1; j <= 2; ++j) {
        for (int i = -1; i <= 2; ++i) {
            float wx = cubic((f.x - float(i)) * sc);
            float wy = cubic((f.y - float(j)) * sc);
            float w = wx * wy;
            vec2 p = safeUV((base + vec2(float(i), float(j)) + 0.5) / texSz, texSz);
            c += texture(tex, p) * w;
            ws += w;
        }
    }
    return c / max(ws, 1e-5);
}

vec4 kernelSmooth(sampler2D tex, vec2 uv, vec2 texSz) {
    vec2 px = 0.55 / texSz;
    vec4 c = texture(tex, safeUV(uv, texSz)) * 0.36;
    c += texture(tex, safeUV(uv + vec2(px.x, 0.0), texSz)) * 0.16;
    c += texture(tex, safeUV(uv - vec2(px.x, 0.0), texSz)) * 0.16;
    c += texture(tex, safeUV(uv + vec2(0.0, px.y), texSz)) * 0.16;
    c += texture(tex, safeUV(uv - vec2(0.0, px.y), texSz)) * 0.16;
    return c;
}

#endif
