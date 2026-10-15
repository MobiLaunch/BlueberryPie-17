"""CAM16-based HCT (hue, chroma, tone) color space and tonal palettes.

Written from the published CAM16 model and the Material Color Utilities
algorithm description (Apache-2.0 reference implementation) so the shell can
produce Material 3 dynamic color without a third-party dependency. Tone is
CIE L*; fixing tone fixes luminance, which is what makes M3 role pairs
accessible regardless of hue.
"""
import math

WHITE_D65 = (95.047, 100.0, 108.883)
_EPSILON = 216 / 24389
_KAPPA = 24389 / 27


def _clamp(value, low, high):
    return max(low, min(high, value))


def _sanitize(degrees):
    return degrees % 360.0


def linearize(channel):
    c = channel / 255
    return (c / 12.92 if c <= 0.040449936 else ((c + 0.055) / 1.055) ** 2.4) * 100


def delinearize(value):
    d = value / 100
    v = d * 12.92 if d <= 0.0031308 else 1.055 * d ** (1 / 2.4) - 0.055
    return _clamp(round(v * 255), 0, 255)


def y_from_lstar(lstar):
    ft = (lstar + 16) / 116
    ft3 = ft ** 3
    return 100 * (ft3 if ft3 > _EPSILON else (116 * ft - 16) / _KAPPA)


def lstar_from_y(y):
    t = y / 100
    f = t ** (1 / 3) if t > _EPSILON else (_KAPPA * t + 16) / 116
    return 116 * f - 16


def lstar_from_rgb(rgb):
    r, g, b = (linearize(c) for c in rgb)
    return lstar_from_y(0.2126 * r + 0.7152 * g + 0.0722 * b)


def rgb_from_lstar(lstar):
    gray = delinearize(y_from_lstar(lstar))
    return (gray, gray, gray)


_SRGB_TO_XYZ = ((0.41233895, 0.35762064, 0.18051042),
                (0.2126, 0.7152, 0.0722),
                (0.01932141, 0.11916382, 0.95034478))
_XYZ_TO_CAM = ((0.401288, 0.650173, -0.051461),
               (-0.250268, 1.204414, 0.045854),
               (-0.002079, 0.048952, 0.953127))
_LINRGB_FROM_SCALED = ((1373.2198709594231, -1100.4251190754821, -7.278681089101213),
                       (-271.815969077903, 559.6580465940733, -32.46047482791194),
                       (1.9622899599665666, -57.173814538844006, 308.7233197812385))
_Y_FROM_LINRGB = (0.2126, 0.7152, 0.0722)


def _matmul(row, matrix):
    return tuple(sum(row[i] * matrix[j][i] for i in range(3)) for j in range(3))


class _View:
    """Default CAM16 viewing conditions (D65, 50 L* background, average surround)."""

    def __init__(self):
        adapting = 200 / math.pi * y_from_lstar(50) / 100
        background_l = 50
        surround = 2.0
        rgb_w = _matmul(WHITE_D65, _XYZ_TO_CAM)
        f = 0.8 + surround / 10
        self.c = (0.525 + (0.59 - 0.525) * ((f - 0.8) * 10) if f < 0.9
                  else 0.59 + (0.69 - 0.59) * ((f - 0.9) * 10))
        self.nc = f
        d = _clamp(f * (1 - (1 / 3.6) * math.exp((-adapting - 42) / 92)), 0, 1)
        self.rgb_d = tuple(d * (100 / w) + 1 - d for w in rgb_w)
        k = 1 / (5 * adapting + 1)
        k4 = k ** 4
        k4f = 1 - k4
        self.fl = k4 * adapting + 0.1 * k4f * k4f * (5 * adapting) ** (1 / 3)
        self.n = y_from_lstar(background_l) / WHITE_D65[1]
        self.z = 1.48 + math.sqrt(self.n)
        self.nbb = 0.725 / self.n ** 0.2
        self.ncb = self.nbb
        factors = [(self.fl * self.rgb_d[i] * rgb_w[i] / 100) ** 0.42 for i in range(3)]
        adapted = [400 * x / (x + 27.13) for x in factors]
        self.aw = (40 * adapted[0] + 20 * adapted[1] + adapted[2]) / 20 * self.nbb


VIEW = _View()


def cam_from_rgb(rgb):
    """Return (hue, chroma, J) for an sRGB triple."""
    lin = tuple(linearize(c) for c in rgb)
    xyz = _matmul(lin, _SRGB_TO_XYZ)
    r_c, g_c, b_c = _matmul(xyz, _XYZ_TO_CAM)
    adapted = []
    for value, d in zip((r_c, g_c, b_c), VIEW.rgb_d):
        scaled = VIEW.fl * abs(d * value) / 100
        factor = scaled ** 0.42
        adapted.append(math.copysign(1, d * value) * 400 * factor / (factor + 27.13))
    r_a, g_a, b_a = adapted
    a = (11 * r_a - 12 * g_a + b_a) / 11
    b = (r_a + g_a - 2 * b_a) / 9
    u = (20 * r_a + 20 * g_a + 21 * b_a) / 20
    p2 = (40 * r_a + 20 * g_a + b_a) / 20
    hue = _sanitize(math.degrees(math.atan2(b, a)))
    ac = p2 * VIEW.nbb
    j = 100 * (ac / VIEW.aw) ** (VIEW.c * VIEW.z)
    hue_prime = hue + 360 if hue < 20.14 else hue
    e_hue = 0.25 * (math.cos(math.radians(hue_prime) + 2) + 3.8)
    p1 = 50000 / 13 * e_hue * VIEW.nc * VIEW.ncb
    t = p1 * math.hypot(a, b) / (u + 0.305)
    alpha = t ** 0.9 * (1.64 - 0.29 ** VIEW.n) ** 0.73
    chroma = alpha * math.sqrt(j / 100)
    return hue, chroma, j


def _find_result_by_j(hue_radians, chroma, y):
    """Exact sRGB for (hue, chroma, luminance y), or None when out of gamut."""
    j = math.sqrt(y) * 11
    t_inner = 1 / (1.64 - 0.29 ** VIEW.n) ** 0.73
    e_hue = 0.25 * (math.cos(hue_radians + 2) + 3.8)
    p1 = e_hue * (50000 / 13) * VIEW.nc * VIEW.ncb
    h_sin, h_cos = math.sin(hue_radians), math.cos(hue_radians)
    for iteration in range(5):
        j_norm = j / 100
        alpha = 0 if chroma == 0 or j == 0 else chroma / math.sqrt(j_norm)
        t = (alpha * t_inner) ** (1 / 0.9)
        ac = VIEW.aw * j_norm ** (1 / VIEW.c / VIEW.z)
        p2 = ac / VIEW.nbb
        gamma = 23 * (p2 + 0.305) * t / (23 * p1 + 11 * t * h_cos + 108 * t * h_sin)
        a, b = gamma * h_cos, gamma * h_sin
        adapted = ((460 * p2 + 451 * a + 288 * b) / 1403,
                   (460 * p2 - 891 * a - 261 * b) / 1403,
                   (460 * p2 - 220 * a - 6300 * b) / 1403)
        scaled = []
        for value in adapted:
            base = max(0, 27.13 * abs(value) / (400 - abs(value)))
            scaled.append(math.copysign(1, value) * base ** (1 / 0.42))
        lin = _matmul(scaled, _LINRGB_FROM_SCALED)
        if min(lin) < 0:
            return None
        fn_j = sum(k * v for k, v in zip(_Y_FROM_LINRGB, lin))
        if fn_j <= 0:
            return None
        if iteration == 4 or abs(fn_j - y) < 0.002:
            if max(lin) > 100.01:
                return None
            return tuple(delinearize(v) for v in lin)
        j -= (fn_j - y) * j / (2 * fn_j)
    return None


def hct_to_rgb(hue, chroma, tone):
    """Closest in-gamut sRGB for the requested HCT; chroma is reduced if necessary."""
    if chroma < 0.0001 or tone < 0.0001 or tone > 99.9999:
        return rgb_from_lstar(_clamp(tone, 0, 100))
    hue = _sanitize(hue)
    radians = math.radians(hue)
    y = y_from_lstar(tone)
    exact = _find_result_by_j(radians, chroma, y)
    if exact:
        return exact
    low, high, best = 0.0, chroma, rgb_from_lstar(tone)
    while high - low > 0.01:
        mid = (low + high) / 2
        candidate = _find_result_by_j(radians, mid, y)
        if candidate:
            best, low = candidate, mid
        else:
            high = mid
    return best


def hex_from_rgb(rgb):
    return "#%02x%02x%02x" % tuple(rgb)


def rgb_from_hex(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def hct_from_hex(value):
    rgb = rgb_from_hex(value)
    hue, chroma, _ = cam_from_rgb(rgb)
    return hue, chroma, lstar_from_rgb(rgb)


class TonalPalette:
    def __init__(self, hue, chroma):
        self.hue, self.chroma = _sanitize(hue), chroma
        self._cache = {}

    def tone(self, tone):
        if tone not in self._cache:
            self._cache[tone] = hex_from_rgb(hct_to_rgb(self.hue, self.chroma, tone))
        return self._cache[tone]
