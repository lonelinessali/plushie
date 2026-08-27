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

    vec2 c00 = clamp((chunk + 0.5) * float(cs) / uOutSize, 0.0, 1.0);
    vec2 c10 = clamp((chunk + vec2(1.5, 0.5)) * float(cs) / uOutSize, 0.0, 1.0);
    vec2 c01 = clamp((chunk + vec2(0.5, 1.5)) * float(cs) / uOutSize, 0.0, 1.0);
    vec2 c11 = clamp((chunk + vec2(1.5, 1.5)) * float(cs) / uOutSize, 0.0, 1.0);

    Feat f00 = analyze(uTex, c00, uTexSize, float(cs));
    Feat f10 = analyze(uTex, c10, uTexSize, float(cs));
    Feat f01 = analyze(uTex, c01, uTexSize, float(cs));
    Feat f11 = analyze(uTex, c11, uTexSize, float(cs));

    vec3 w00 = weights(f00);
    vec3 w10 = weights(f10);
    vec3 w01 = weights(f01);
    vec3 w11 = weights(f11);

    vec3 w0 = mix(w00, w10, smoothstep(0.0, 1.0, local.x));
    vec3 w1 = mix(w01, w11, smoothstep(0.0, 1.0, local.x));
    return mix(w0, w1, smoothstep(0.0, 1.0, local.y));
}

vec3 adaptiveSharpen(vec3 c, sampler2D tex, vec2 uv, vec2 texSz, float amount) {
    vec2 px = 1.0 / texSz;
    vec3 n = texture(tex, safeUV(uv + vec2(0.0, -px.y), texSz)).rgb;
    vec3 s = texture(tex, safeUV(uv + vec2(0.0,  px.y), texSz)).rgb;
    vec3 e = texture(tex, safeUV(uv + vec2( px.x, 0.0), texSz)).rgb;
    vec3 w = texture(tex, safeUV(uv + vec2(-px.x, 0.0), texSz)).rgb;
    vec3 blur = (n + s + e + w) * 0.25;
    float contrast = luma(abs(c - blur));
    float wgt = smoothstep(0.02, 0.12, contrast) * amount;
    // fade sharpening near image edges to prevent black ringing
    float edgeFade = smoothstep(0.0, 3.0 / texSz.x, uv.x)
                   * smoothstep(0.0, 3.0 / texSz.y, uv.y)
                   * smoothstep(0.0, 3.0 / texSz.x, 1.0 - uv.x)
                   * smoothstep(0.0, 3.0 / texSz.y, 1.0 - uv.y);
    wgt *= edgeFade;
    return mix(c, clamp(c + (c - blur) * 1.6, 0.0, 1.0), wgt);
}

void main() {
    int cs = chunkSize(uOutSize);
    vec3 w = sampleWeights(vUV, cs);

    vec4 s = kernelSharp(uTex, vUV, uTexSize);
    vec4 r = kernelBalanced(uTex, vUV, uTexSize);
    vec4 m = kernelSmooth(uTex, vUV, uTexSize);

    vec4 res = w.x * s + w.y * r + w.z * m;

    // stronger adaptive sharpen, scaled by sharp weight
    float amt = 0.55 + 0.45 * w.x;
    res.rgb = adaptiveSharpen(res.rgb, uTex, vUV, uTexSize, amt);

    float a = res.a;
    res.rgb = clamp(res.rgb, 0.0, 1.0);
    res.a = a;

    fragColor = res;
}
