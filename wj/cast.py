"""The cast. Every character is built from morph targets + fitted CC0 wardrobe, tinted to period colours."""
from .mh import Human
from .anim import Actor, attach
from . import props

MALE = dict(gender=1.0); FEMALE = dict(gender=0.0)


def T(c, flat=0.0, sat=0.0, val=1.0, **k):
    return dict(tint=c, flat=flat, sat=sat, val=val, **k)


GREY = T((0.75, 0.75, 0.75), sat=0.05)
DARKHAIR = T((0.55, 0.45, 0.4), sat=0.6)


def _mk(name, seed, hats=(), **kw):
    h = Human(name, **kw)
    a = Actor(h, seed=seed)
    top = h.height
    for hat, dz, rot in hats:
        tl = h.rest['head'][1]
        attach(hat, h, 'head', (tl.x, tl.y + 0.01, top + dz), rot, scale=hat.get('s', 1.0))
    a.hats = [x[0] for x in hats]
    return a


def purefinder():
    return _mk('finder', 1,                skin='skin_old_caucasian_male.jpg', eyes='eye_grey.jpg', skin_bump=0.6, age={'old': 0.85, 'young': 0.15}, weight=0.35, muscle=0.4, height=0.4,
               items=['eyebrow006', 'beard_short', 'male_casualsuit05', 'shoes03', 'fedora01'],
               tints={'beard_short': GREY, 'eyebrow006': GREY, 'male_casualsuit05': T((0.5, 0.4, 0.28), flat=0.3, val=1.8), 'fedora01': T((0.3, 0.24, 0.18), val=1.2), 'shoes03': T((0.35, 0.28, 0.2))},
               details={'nose/nose-hump-incr': 0.6, 'head/head-rectangular': 0.4, 'cheek/l-cheek-bones-incr': 0.5, 'cheek/r-cheek-bones-incr': 0.5}, **MALE)


def tanner():
    return _mk('tanner', 2, skin='skin_middleage_caucasian_male.jpg', eyes='eye_brown.jpg', age={'young': 0.55, 'old': 0.45}, weight=0.75, muscle=0.85, height=0.6,
               items=['short04', 'eyebrow001', 'rehmanpolanski_beard_viking', 'rehmanpolanski_viking_tunic', 'toigo_wool_pants', 'rehmanpolanski_viking_boots'],
               tints={'rehmanpolanski_viking_tunic': T((0.5, 0.33, 0.2), flat=0.85, val=1.2), 'toigo_wool_pants': T((0.3, 0.24, 0.18), flat=0.3), 'rehmanpolanski_viking_boots': T((0.3, 0.2, 0.13)),
                      'short04': DARKHAIR, 'rehmanpolanski_beard_viking': DARKHAIR},
               details={'head/head-square': 0.6, 'nose/nose-scale-horiz-incr': 0.5}, **MALE)


def leech_woman():
    return _mk('leecher', 3, skin='skin_middleage_caucasian_female.jpg', eyes='eye_green.jpg', age={'young': 0.7, 'old': 0.3}, weight=0.45, muscle=0.5, height=0.45,
               items=['braid01', 'eyebrow004', 'joepal_crude_t-shirt_female', 'toigo_skirt_with_lace_ruffle'],
               tints={'joepal_crude_t-shirt_female': T((0.62, 0.56, 0.44)), 'toigo_skirt_with_lace_ruffle': T((0.32, 0.36, 0.42), flat=0.75), 'braid01': T((0.8, 0.6, 0.45), sat=0.7)},
               details={'head/head-oval': 0.5}, **FEMALE)


def doctor():
    return _mk('doctor', 4, hats=[(props.tophat(), -0.06, (0.05, 0, 0))], skin='skin_middleage_caucasian_male.jpg', eyes='eye_blue.jpg',
               age={'young': 0.5, 'old': 0.5}, weight=0.6, muscle=0.4, height=0.65,
               items=['short03', 'eyebrow002', 'rehmanpolanski_moustache_viking', 'male_elegantsuit01', 'shoes02', 'toigo_round_glasses_leopard'],
               tints={'toigo_round_glasses_leopard': T((0.25, 0.2, 0.1), flat=0.8, kind='wet'), 'rehmanpolanski_moustache_viking': DARKHAIR},
               details={'head/head-oval': 0.6, 'nose/nose-point-down': 0.5}, **MALE)


def tosher(name='tosher', seed=5):
    return _mk(name, seed, skin='skin_middleage_caucasian_male.jpg', eyes='eye_brownlight.jpg',
               age={'young': 0.75, 'old': 0.25}, weight=0.35, muscle=0.65, height=0.5,
               items=['eyebrow005', 'beard_short', 'toigo_fisherman_sweater', 'toigo_wool_pants', 'rehmanpolanski_viking_boots', 'fedora_cocked'],
               tints={'fedora_cocked': T((0.25, 0.22, 0.18)), 'toigo_fisherman_sweater': T((0.4, 0.4, 0.33)), 'toigo_wool_pants': T((0.2, 0.17, 0.14), flat=0.3), 'rehmanpolanski_viking_boots': T((0.2, 0.14, 0.1)), 'beard_short': DARKHAIR},
               details={'head/head-diamond': 0.5, 'nose/nose-hump-incr': 0.4}, **MALE)


def ratcatcher():
    return _mk('ratcatcher', 6, skin='skin_young_caucasian_male.jpg', eyes='eye_green.jpg', age={'young': 0.85, 'old': 0.15}, weight=0.5, muscle=0.6, height=0.55,
               items=['eyebrow003', 'rehmanpolanski_moustache_viking', 'fedora_cocked', 'male_casualsuit05', 'shoes01'],
               tints={'male_casualsuit05': T((0.5, 0.55, 0.36), flat=0.3, val=1.8), 'fedora_cocked': T((0.3, 0.24, 0.18)), 'rehmanpolanski_moustache_viking': T((0.7, 0.45, 0.3), sat=0.8)},
               details={'head/head-triangular': 0.4, 'nose/nose-point-up': 0.4}, **MALE)


def towns_woman(name='woman', seed=7, skirt=(0.35, 0.16, 0.14), top=(0.6, 0.56, 0.48), hair='long01', old=0.2, hat=True):
    items = [hair, 'eyebrow007', 'toigo_fisherman_sweater', 'toigo_long_full_skirt', 'toigo_mj_cloth_shoes'] + (['aethelraed_unraed_cloche_hat'] if hat else [])
    return _mk(name, seed, skin='skin_old_caucasian_female.jpg' if old > 0.6 else 'skin_young_caucasian_female.jpg', eyes='eye_brown.jpg', age={'young': 1 - old, 'old': old}, weight=0.55, muscle=0.4, height=0.4,
               items=items, tints={'toigo_fisherman_sweater': T(top), 'toigo_long_full_skirt': T(skirt, flat=0.8), 'aethelraed_unraed_cloche_hat': T((0.2, 0.18, 0.16), flat=0.9),
                                   'toigo_mj_cloth_shoes': T((0.1, 0.1, 0.1))}, **FEMALE)


def gentleman(name='gent', seed=8, black=False):
    return _mk(name, seed, hats=[(props.tophat(), -0.06, (0.05, 0, 0))], skin='skin_young_caucasian_male.jpg', eyes='eye_blue.jpg', age={'young': 0.7, 'old': 0.3}, weight=0.6, muscle=0.5, height=0.6,
               items=['short01', 'eyebrow008', 'beard_goatee', 'male_elegantsuit01', 'shoes02'], tints={'male_elegantsuit01': T((0.5, 0.5, 0.5) if black else (1, 1, 1), sat=1.0)}, **MALE)


def snatcher():
    return _mk('snatcher', 9, skin='skin_middleage_caucasian_male.jpg', eyes='eye_grey.jpg',
               age={'young': 0.6, 'old': 0.4}, weight=0.7, muscle=0.75, height=0.6,
               items=['eyebrow009', 'rehmanpolanski_beard_viking', 'male_casualsuit05', 'shoes03', 'fedora01'],
               tints={'male_casualsuit05': T((0.3, 0.3, 0.34), flat=0.4, val=1.5), 'fedora01': T((0.15, 0.15, 0.16)), 'shoes03': T((0.2, 0.17, 0.14)), 'rehmanpolanski_beard_viking': T((0.4, 0.35, 0.3), sat=0.3)},
               details={'head/head-square': 0.5}, **MALE)


def plague_collector(name='collector', seed=10):
    return _mk(name, seed, skin='skin_middleage_caucasian_male.jpg', eyes='eye_grey.jpg', skin_bump=0.5, age={'young': 0.5, 'old': 0.5}, weight=0.25, muscle=0.5, height=0.55,
               items=['eyebrow010', 'beard_short', 'donitz_monk_robe', 'donitz_monk_robe_hood', 'rehmanpolanski_viking_boots'],
               tints={'donitz_monk_robe': T((0.55, 0.45, 0.35), sat=0.3), 'donitz_monk_robe_hood': T((0.55, 0.45, 0.35), sat=0.3), 'beard_short': DARKHAIR},
               details={'head/head-rectangular': 0.6, 'cheek/l-cheek-bones-incr': 0.8, 'cheek/r-cheek-bones-incr': 0.8, 'nose/nose-hump-incr': 0.5}, **MALE)


def prince():
    return _mk('prince', 11, hats=[(props.crown(), -0.035, (0.1, 0, 0))], skin='skin_young_caucasian_male.jpg', eyes='eye_blue.jpg', age={'child': 0.85, 'young': 0.15}, weight=0.6, muscle=0.4, height=0.5,
               items=['short01', 'eyebrow001', 'rehmanpolanski_viking_tunic', 'rehmanpolanski_viking_pants', 'rehmanpolanski_viking_boots'],
               tints={'rehmanpolanski_viking_tunic': T((0.75, 0.1, 0.12), flat=0.35, val=1.3), 'rehmanpolanski_viking_pants': T((0.9, 0.85, 0.7), flat=0.5, val=1.3),
                      'rehmanpolanski_viking_boots': T((0.25, 0.12, 0.08)), 'short01': T((1.0, 0.85, 0.6), sat=0.8, val=1.5)},
               details={'head/head-round': 0.6}, **MALE)


def whipping_boy():
    return _mk('boy', 12, skin='skin_young_caucasian_male.jpg', eyes='eye_brown.jpg', age={'child': 0.85, 'young': 0.15}, weight=0.3, muscle=0.4, height=0.5,
               items=['cortu_short_messy_hair', 'eyebrow002', 'elvs_crude_t-shirt_male', 'rehmanpolanski_viking_pants'],
               tints={'elvs_crude_t-shirt_male': T((0.6, 0.55, 0.45)), 'rehmanpolanski_viking_pants': T((0.4, 0.3, 0.22), flat=0.3), 'cortu_short_messy_hair': T((0.5, 0.35, 0.25), sat=0.6)},
               details={'head/head-oval': 0.5}, **MALE)


def tutor():
    return _mk('tutor', 13, skin='skin_old_caucasian_male.jpg', eyes='eye_grey.jpg', skin_bump=0.6, age={'old': 0.7, 'young': 0.3}, weight=0.5, muscle=0.5, height=0.7,
               items=['short02', 'eyebrow011', 'rehmanpolanski_beard_viking', 'ours_sorcerer_robe', 'shoes02'],
               tints={'ours_sorcerer_robe': T((0.12, 0.11, 0.13), flat=0.97), 'short02': GREY, 'rehmanpolanski_beard_viking': GREY, 'eyebrow011': GREY},
               details={'head/head-rectangular': 0.6, 'nose/nose-hump-incr': 0.7, 'nose/nose-point-down': 0.5}, **MALE)
