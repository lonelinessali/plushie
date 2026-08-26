#ifndef PLUSHIE_SIZE
#define PLUSHIE_SIZE

int chunkSize(vec2 outSz) {
    float r = max(outSz.x, outSz.y);
    float ratio = r > 2800.0 ? 0.0104 :
                  r > 1600.0 ? 0.0125 :
                  r > 900.0  ? 0.0156 : 0.0208;
    float s = clamp(r * ratio, 6.0, 14.0);
    int n = int(floor(s * 0.5) * 2.0);
    return max(n, 6);
}

#endif
