"""Forward Transverse Mercator for NAD83 / MTM zone 8 (GRS80; lon0 -73.5, k0 0.9999, FE 304800)."""
import math
A = 6378137.0; F = 1 / 298.257222101; E2 = F * (2 - F); EP2 = E2 / (1 - E2)
def mtm8(lon, lat):
    lon0 = math.radians(-73.5); k0 = 0.9999
    phi = math.radians(lat); lam = math.radians(lon) - lon0
    N = A / math.sqrt(1 - E2 * math.sin(phi) ** 2); T = math.tan(phi) ** 2; C = EP2 * math.cos(phi) ** 2; Aa = math.cos(phi) * lam
    e4, e6 = E2 ** 2, E2 ** 3
    M = A * ((1 - E2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi - (3 * E2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
             + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi) - (35 * e6 / 3072) * math.sin(6 * phi))
    x = 304800 + k0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6 + (5 - 18 * T + T * T + 72 * C - 58 * EP2) * Aa ** 5 / 120)
    y = k0 * (M + N * math.tan(phi) * (Aa ** 2 / 2 + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24 + (61 - 58 * T + T * T + 600 * C - 330 * EP2) * Aa ** 6 / 720))
    return x, y
