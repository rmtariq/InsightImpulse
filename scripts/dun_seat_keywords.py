#!/usr/bin/env python3
"""Safe per-DUN keyword lists — elak false match (Kota→Kota Baharu, Johor→semua Johor)."""
from __future__ import annotations

import re
from typing import Any

# Perkataan terlalu generik / sering muncul dalam teks lain negeri
GENERIC_PARTS = frozenset({
    "johor", "bukit", "tanjung", "sungai", "parit", "pasir", "raja", "mahkota", "kota",
    "bandar", "pekan", "kampung", "taman", "felda", "pusat", "kawasan", "menanti",
    "nilai", "labu", "paloh", "gemas", "linggi", "tenang", "rompin", "permai", "batu",
    "seri", "sri", "ulu", "baru", "lama", "jaya", "iskandar", "pontian", "skudai",
    "senai", "kempas", "permas", "machap", "rengit", "kukup", "endau", "panti",
    "sedili", "benut", "gambir", "bekok", "tenggaroh", "semarang", "semarah",
    "medan", "balang", "nanas", "sebatang", "layang", "jeram", "naning", "kepong",
    "kepayang", "pinang", "tanjung", "surat", "wangsa", "larkin", "stulang", "perling",
    "chennah", "palong", "temiang", "lobak", "rahang", "mambau", "chembong", "rantau",
    "chuah", "lukut", "repah", "tampin", "gemencheh", "jementah", "pemanis", "kemelah",
    "bentayan", "semarang", "kahang", "penawar", "buloh", "kasap", "maharani", "mengkibol",
})

# Nama kerusi 1 perkataan — perlukan konteks DUN / kod
AMBIGUOUS_SEAT_NAMES = frozenset({
    "kota", "labu", "paloh", "nilai", "tiram", "tenang", "gemas", "linggi", "lobak",
    "pilah", "johol", "chuah", "lukut", "repah", "tampin", "endau", "panti", "sedili",
    "benut", "gambir", "bekok", "rengit", "kukup", "machap", "permas", "kempas",
    "skudai", "senai", "larkin", "stulang", "perling", "tangkak", "serom", "semarah",
    "semarang", "kahang", "penawar", "jementah", "pemanis", "kemelah", "bentayan",
})

# Override manual — kurator (lebih dipercayai daripada auto-split)
N9_SEAT_KEYWORDS: dict[str, list[str]] = {
    "N01": ["chennah", "kampung chennah", "n01"],
    "N02": ["pertang", "simpang pertang", "n02"],
    "N03": ["sungai lui", "sg lui", "sg. lui", "n03"],
    "N04": ["klawang", "kuala klawang", "n04"],
    "N05": ["serting", "bandar baru serting", "n05"],
    "N06": ["palong", "pusat bandar palong", "n06"],
    "N07": ["jeram padang", "n07"],
    "N08": ["bahau", "n08"],
    "N09": ["lenggeng", "n09"],
    "N10": ["nilai", "bandar baru nilai", "dun nilai", "n10"],
    "N11": ["lobak", "kampung lobak", "dun lobak", "n11"],
    "N12": ["temiang", "jalan temiang", "n12"],
    "N13": ["sikamat", "n13"],
    "N14": ["ampangan", "bandar baru ampangan", "n14"],
    "N15": ["juasseh", "n15"],
    "N16": ["seri menanti", "n16"],
    "N17": ["senaling", "pekan senaling", "n17"],
    "N18": ["kuala pilah", "dun pilah", "n18"],
    "N19": ["johol", "dun johol", "n19"],
    "N20": ["labu", "dun labu", "n20"],
    "N21": ["bukit kepayang", "kepayang", "n21"],
    "N22": ["rahang", "n22"],
    "N23": ["mambau", "n23"],
    "N24": ["seremban jaya", "taman seremban jaya", "n24"],
    "N25": ["paroi", "senawang", "n25"],
    "N26": ["chembong", "rembau chembong", "n26"],
    "N27": ["rantau", "n27"],
    "N28": ["seremban kota", "dun kota", "kerusi kota", "n28"],
    "N29": ["chuah", "bukit pelandok", "n29"],
    "N30": ["lukut", "n30"],
    "N31": ["bagan pinang", "port dickson", "si rusa", "teluk kemang", "n31"],
    "N32": ["linggi", "dun linggi", "n32"],
    "N33": ["sri tanjung", "dun sri tanjung", "n33"],
    "N34": ["gemas", "dun gemas", "n34"],
    "N35": ["gemencheh", "n35"],
    "N36": ["repah", "dun repah", "tampin", "n36"],
}

JOHOR_SEAT_KEYWORDS: dict[str, list[str]] = {
    "N01": ["buloh kasap", "pekan buloh kasap", "n01"],
    "N02": ["jementah", "pekan jementah", "n02"],
    "N03": ["pemanis", "felda pemanis", "n03"],
    "N04": ["kemelah", "felda kemelah", "n04"],
    "N05": ["tenang", "kampung tenang", "dun tenang", "n05"],
    "N06": ["bekok", "pekan bekok", "dun bekok", "n06"],
    "N07": ["bukit kepong", "pekan bukit kepong", "n07"],
    "N08": ["bukit pasir", "pekan bukit pasir", "n08"],
    "N09": ["gambir", "bukit gambir", "dun gambir", "n09"],
    "N10": ["tangkak", "bandar tangkak", "dun tangkak", "n10"],
    "N11": ["serom", "pekan serom", "dun serom", "n11"],
    "N12": ["bentayan", "bandar muar", "dun bentayan", "n12"],
    "N13": ["simpang jeram", "n13"],
    "N14": ["bukit naning", "n14"],
    "N15": ["maharani", "bandar maharani", "n15"],
    "N16": ["sungai balang", "pekan sungai balang", "n16"],
    "N17": ["semarah", "pekan semarah", "n17"],
    "N18": ["sri medan", "pekan sri medan", "n18"],
    "N19": ["yong peng", "bandar yong peng", "n19"],
    "N20": ["semarang", "pekan semarang", "n20"],
    "N21": ["parit yaani", "pekan parit yaani", "n21"],
    "N22": ["parit raja", "pekan parit raja", "n22"],
    "N23": ["penggaram", "bandar penggaram", "batu pahat", "n23"],
    "N24": ["senggarang", "pekan senggarang", "n24"],
    "N25": ["rengit", "pekan rengit", "dun rengit", "n25"],
    "N26": ["machap", "pekan machap", "dun machap", "n26"],
    "N27": ["layang-layang", "layang layang", "pekan layang", "n27"],
    "N28": ["mengkibol", "kluang barat", "dun mengkibol", "n28"],
    "N29": ["mahkota", "bandar kluang", "dun mahkota", "n29"],
    "N30": ["paloh", "pekan paloh", "dun paloh", "n30"],
    "N31": ["kahang", "pekan kahang", "dun kahang", "n31"],
    "N32": ["endau", "pekan endau", "dun endau", "n32"],
    "N33": ["tenggaroh", "felda tenggaroh", "n33"],
    "N34": ["panti", "kawasan panti", "dun panti", "n34"],
    "N35": ["pasir raja", "kampung pasir raja", "n35"],
    "N36": ["sedili", "sedili besar", "n36"],
    "N37": ["johor lama", "kampung johor lama", "n37"],
    "N38": ["penawar", "bandar penawar", "dun penawar", "n38"],
    "N39": ["tanjung surat", "n39"],
    "N40": ["tiram", "ulu tiram", "dun tiram", "n40"],
    "N41": ["puteri wangsa", "bandar puteri wangsa", "n41"],
    "N42": ["johor jaya", "taman johor jaya", "n42"],
    "N43": ["permas", "permas jaya", "bandar baru permas", "n43"],
    "N44": ["larkin", "dun larkin", "n44"],
    "N45": ["stulang", "dun stulang", "n45"],
    "N46": ["perling", "taman perling", "dun perling", "n46"],
    "N47": ["kempas", "dun kempas", "n47"],
    "N48": ["skudai", "bandar skudai", "dun skudai", "n48"],
    "N49": ["kota iskandar", "n49"],
    "N50": ["bukit permai", "dun bukit permai", "kulai", "n50"],
    "N51": ["bukit batu", "dun bukit batu", "n51"],
    "N52": ["senai", "bandar senai", "dun senai", "n52"],
    "N53": ["benut", "pekan benut", "dun benut", "n53"],
    "N54": ["pulai sebatang", "n54"],
    "N55": ["pekan nanas", "n55"],
    "N56": ["kukup", "pekan kukup", "dun kukup", "n56"],
}

CROSS_KOTA_NOISE = re.compile(
    r"kota\s*baharu|kota\s*kinabalu|kota\s*tinggi|kota\s*marudu|kota\s*belud",
    re.I,
)

DUN_CONTEXT = re.compile(
    r"\b(dun|kerusi|prn|calon|adun|pilihan\s*raya)\b",
    re.I,
)

STATE_CONTEXT = {
    "N9": re.compile(r"negeri\s*sembilan|seremban|prn\s*n9|\bn9\b", re.I),
    "JOHOR": re.compile(r"\bjohor\b|prn\s*johor|jdt\b", re.I),
}


def norm_code(code: str) -> str:
    if not code:
        return ""
    s = str(code).strip().upper().replace(" ", "")
    m = re.match(r"N\.?0*(\d+)", s)
    return f"N{int(m.group(1)):02d}" if m else s


def _dedupe(kws: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for k in kws:
        k = k.strip().lower()
        if k and k not in seen:
            seen.add(k)
            out.append(k)
    return out


def build_seat_keywords(seat: dict[str, Any], state_key: str = "N9") -> list[str]:
    """Build safe keywords — default to curated tables."""
    code = norm_code(seat.get("id") or seat.get("code") or "")
    st = "JOHOR" if str(state_key).upper() in ("JOHOR", "JDT") else "N9"
    table = JOHOR_SEAT_KEYWORDS if st == "JOHOR" else N9_SEAT_KEYWORDS
    if code in table:
        return list(table[code])

    name = (seat.get("name") or "").strip().lower()
    kws = [name, code.lower(), f"n.{code[1:].lower()}"] if code and name else []
    if " " in name:
        for part in name.split():
            if len(part) >= 5 and part not in GENERIC_PARTS:
                kws.append(part)
    return _dedupe(kws)


def keywords_for_state(seats: list[dict], state_key: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    table = JOHOR_SEAT_KEYWORDS if state_key.upper() == "JOHOR" else N9_SEAT_KEYWORDS
    for seat in seats:
        code = norm_code(seat.get("id") or seat.get("code") or "")
        if not code:
            continue
        out[code] = table.get(code) or build_seat_keywords(seat, state_key)
    return out


def _ambiguous_name_match(text: str, kw: str, code: str, state_key: str) -> bool:
    if kw not in AMBIGUOUS_SEAT_NAMES:
        return True
    st = "JOHOR" if state_key.upper() == "JOHOR" else "N9"
    ctx = STATE_CONTEXT.get(st)
    if re.search(rf"\b{re.escape(code.lower())}\b|n\.{code[1:].lower()}\b", text, re.I):
        return True
    if DUN_CONTEXT.search(text) and re.search(rf"\b{re.escape(kw)}\b", text, re.I):
        return True
    if ctx and ctx.search(text) and re.search(rf"\b{re.escape(kw)}\b", text, re.I):
        # Require longer phrase when possible
        return len(kw) >= 6 or f"dun {kw}" in text.lower()
    return False


DUN_CODE_IN_TEXT = re.compile(r"\bN\.?\s*0?[1-9][0-9]?\b", re.I)


def _count_dun_codes(text: str) -> int:
    return len(set(m.group(0).upper().replace(".", "").replace(" ", "") for m in DUN_CODE_IN_TEXT.finditer(text or "")))


def row_matches_seat(text: str, code: str, keywords: list[str], state_key: str = "N9") -> bool:
    """Match post to DUN — reject cross-state noise & generic partial hits."""
    t = text.lower()
    st = "JOHOR" if state_key.upper() == "JOHOR" else "N9"

    dotted = f"n.{code[1:].lower()}" if code.lower().startswith("n") and len(code) > 1 else code.lower()
    has_code = bool(
        re.search(rf"\b{re.escape(code.lower())}\b", t)
        or re.search(rf"\b{re.escape(dotted)}\b", t)
    )
    if _count_dun_codes(text) >= 4 and not has_code:
        return False

    if CROSS_KOTA_NOISE.search(t):
        seat_ctx = re.search(
            rf"\b{re.escape(code.lower())}\b|n\.{re.escape(code[1:].lower())}\b",
            t,
            re.I,
        )
        state_ctx = STATE_CONTEXT.get(st)
        if not seat_ctx and not (state_ctx and state_ctx.search(t) and DUN_CONTEXT.search(t)):
            return False

    if has_code:
        return True

    for kw in keywords:
        if len(kw) <= 3:
            continue
        if kw in GENERIC_PARTS:
            continue
        if not re.search(rf"\b{re.escape(kw)}\b", t):
            continue
        if not _ambiguous_name_match(t, kw, code, st):
            continue
        # Multi-word keywords are trusted
        if " " in kw or len(kw) >= 8:
            return True
        if DUN_CONTEXT.search(t) or STATE_CONTEXT.get(st, re.compile("$^")).search(t):
            return True
    return False
