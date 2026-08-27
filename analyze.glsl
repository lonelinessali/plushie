#ifndef PLUSHIE_ANALYZE
#define PLUSHIE_ANALYZE

uniform float uThreshGradLow;
uniform float uThreshGradHigh;
uniform float uThreshVarLow;
uniform float uThreshVarHigh;

struct Feat {
    float var;
    float grad;
    float dirCons;
    float lum;
};

Feat analyze(sampler2D tex, vec2 center, vec2 texSz, float cpx) {
    Feat f;
    f.var = 0.0;
    f.grad = 0.0;
    f.dirCons = 0.0;
    f.lum = 0.0;

    float scale = cpx / max(texSz.x, texSz.y);
    vec2 o[5] = vec2[](
        vec2(0.0),
        vec2(0.40, 0.0), vec2(-0.40, 0.0),
        vec2(0.0, 0.40), vec2(0.0, -0.40)
    );

    float lum[5];
    for (int i = 0; i < 5; ++i) {
        vec2 p = safeUV(center + o[i] * scale, texSz);
        lum[i] = luma(texture(tex, p).rgb);
        f.lum += lum[i];
    }
    f.lum *= 0.2;

    float mean = f.lum;
    for (int i = 0; i < 5; ++i) {
        float d = lum[i] - mean;
        f.var += d * d;
    }
    f.var *= 0.2;

    float norm = max(f.lum, 0.04);
    f.var /= norm;

    float gx = lum[1] - lum[2];
    float gy = lum[3] - lum[4];
    f.grad = (gx*gx + gy*gy) / norm;

    float ang = atan(gy, gx + 1e-6);
    f.dirCons = abs(cos(ang * 2.0));

    return f;
}

vec3 weights(Feat f) {
    float gl = uThreshGradLow  > 0.0 ? uThreshGradLow  : 0.00008;
    float gh = uThreshGradHigh > 0.0 ? uThreshGradHigh : 0.0025;
    float vl = uThreshVarLow   > 0.0 ? uThreshVarLow   : 0.00015;
    float vh = uThreshVarHigh  > 0.0 ? uThreshVarHigh  : 0.005;

    float sharp = smoothstep(gl, gh, f.grad) * smoothstep(vl, vh, f.var);
    sharp = mix(sharp, min(sharp * 1.25, 1.0), f.dirCons);
    float sm = 1.0 - smoothstep(gl * 0.3, gh * 1.2, f.grad);
    sm = max(sm, 0.1);
    float rd = max(1.0 - sharp - sm, 0.0);
    float s = sharp + rd + sm + 1e-5;
    return vec3(sharp, rd, sm) / s;
}

#endif
