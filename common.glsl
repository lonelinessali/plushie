#ifndef PLUSHIE_COMMON
#define PLUSHIE_COMMON

float luma(vec3 c) {
    return dot(c, vec3(0.2126, 0.7152, 0.0722));
}

vec2 safeUV(vec2 p, vec2 sz) {
    return clamp(p, 0.5/sz, 1.0 - 0.5/sz);
}

float cubic(float x) {
    x = abs(x);
    if (x < 1.0) return ((1.5*x - 2.5)*x)*x + 1.0;
    if (x < 2.0) return ((-0.5*x + 2.5)*x - 4.0)*x + 2.0;
    return 0.0;
}

#endif
