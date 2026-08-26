#version 300 es
precision highp float;

uniform sampler2D uTex;
uniform vec2 uTexSize;
uniform vec2 uOutSize;

in vec2 vUV;
out vec4 fragColor;

vec3 sampleWeights(vec2 uv, int cs) {
    vec2 outPx = uv * uOutSize;
    vec2 chunk = floor(outPx / float(cs));
    vec2 local = fract(outPx / float(cs));

    // 4 neighbors for bilinear feather
    vec2 c00 = (chunk + 0.5) * float(cs) / uOutSize;
    vec2 c10 = (chunk + vec2(1.5, 0.5)) * float(cs) / uOutSize;
    vec2 c01 = (chunk + vec2(0.5, 1.5)) * float(cs) / uOutSize;
    vec2 c11 = (chunk + vec2(1.5, 1.5)) * float(cs) / uOutSize;

    Feat f00 = analyze(uTex, c00, uTexSize, float(cs));
    Feat f10 = analyze(uTex, c10, uTexSize, float(cs));
    Feat f01 = analyze(uTex, c01, uTexSize, float(cs));
    Feat f11 = analyze(uTex, c11, uTexSize, float(cs));

    vec3 w00 = weights(f00);
    vec3 w10 = weights(f10);
    vec3 w01 = weights(f01);
    vec3 w11 = weights(f11);

    vec3 w0 = mix(w00, w10, local.x);
    vec3 w1 = mix(w01, w11, local.x);
    return mix(w0, w1, local.y);
}

void main() {
    int cs = chunkSize(uOutSize);
    vec3 w = sampleWeights(vUV, cs);

    vec4 s = kernelSharp(uTex, vUV, uTexSize);
    vec4 r = kernelBalanced(uTex, vUV, uTexSize);
    vec4 m = kernelSmooth(uTex, vUV, uTexSize);

    vec4 res = w.x * s + w.y * r + w.z * m;

    float a = res.a;
    float edge = w.x * smoothstep(0.1, 0.6, a);
    res.rgb = mix(res.rgb, clamp(res.rgb, 0.0, 1.0), 0.10 + 0.25 * edge);
    res.a = a;

    fragColor = res;
}
