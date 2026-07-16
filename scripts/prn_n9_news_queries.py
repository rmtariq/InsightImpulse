"""PRN N9 — Google News RSS query packs (percuma, tiada API key)."""
from __future__ import annotations

from typing import Any, Dict, List

# community: melayu | islam | cina | india | ekonomi | umum | lain
# Semua query melalui Google News RSS — $0 kos

QUERY_PACK: Dict[str, List[Dict[str, Any]]] = {
    "umum": [
        {"id": "BM1", "lang": "bm", "community": "umum", "query": '"PRN Negeri Sembilan" OR "pilihan raya negeri sembilan" when:30d'},
        {"id": "BM5", "lang": "bm", "community": "umum", "query": 'SPR OR penamaan OR mengundi "Negeri Sembilan" when:30d'},
        {"id": "BM4", "lang": "bm", "community": "umum", "query": 'PAS OR PN OR UMNO OR "Pakatan Harapan" "Negeri Sembilan" when:30d'},
        {"id": "ED3", "lang": "en", "community": "umum", "query": 'site:theedgemalaysia.com "Negeri Sembilan" PRN when:30d'},
        {"id": "ED4", "lang": "en", "community": "umum", "query": '"The Edge Malaysia" "Negeri Sembilan" when:30d'},
    ],
    "melayu": [
        {"id": "MY1", "lang": "bm", "community": "melayu", "query": 'Bernama OR "Astro Awani" OR Utusan OR "Berita Harian" "Negeri Sembilan" PRN when:30d'},
        {"id": "MY2", "lang": "bm", "community": "melayu", "query": 'Malaysiakini OR "Free Malaysia Today" OR "The Star" "Negeri Sembilan" when:30d'},
        {"id": "MY3", "lang": "bm", "community": "melayu", "query": 'site:utusan.com.my "Negeri Sembilan" when:30d'},
        {"id": "MY4", "lang": "bm", "community": "melayu", "query": 'site:bharian.com.my "Negeri Sembilan" when:30d'},
        {"id": "MY5", "lang": "bm", "community": "melayu", "query": 'site:sinarharian.com.my "Negeri Sembilan" when:30d'},
        {"id": "MY6", "lang": "bm", "community": "melayu", "query": 'FELDA OR getah OR RISDA OR "Felda Serting" "Negeri Sembilan" when:30d'},
    ],
    "islam": [
        {"id": "IS1", "lang": "bm", "community": "islam", "query": 'site:harakahdaily.net "Negeri Sembilan" when:30d'},
        {"id": "IS2", "lang": "bm", "community": "islam", "query": 'masjid OR pondok OR tahfiz OR JAKIM "Negeri Sembilan" when:30d'},
        {"id": "IS3", "lang": "bm", "community": "islam", "query": 'PAS OR "Parti Islam" OR "Bulan Sabit" "Negeri Sembilan" when:30d'},
        {"id": "IS4", "lang": "bm", "community": "islam", "query": 'site:astroawani.com Islam OR halal "Negeri Sembilan" when:30d'},
    ],
    "cina": [
        {"id": "CN1", "lang": "cina", "community": "cina", "query": 'site:n9.chinapress.com.my when:30d'},
        {"id": "CN2", "lang": "cina", "community": "cina", "query": 'site:chinapress.com.my 森美兰 OR 芙蓉 when:30d'},
        {"id": "CN3", "lang": "cina", "community": "cina", "query": 'site:sinchew.com.my 森美兰 OR 芙蓉 OR 马口 when:30d'},
        {"id": "CN4", "lang": "cina", "community": "cina", "query": 'site:orientaldaily.com.my 森美兰 OR "Negeri Sembilan" when:30d'},
        {"id": "CN5", "lang": "cina", "community": "cina", "query": 'site:nanyang.com 森美兰 OR Seremban when:30d'},
        {"id": "CN6", "lang": "cina", "community": "cina", "query": 'site:kwongwah.com.my 森美兰 when:30d'},
        {"id": "CN7", "lang": "cina", "community": "cina", "query": 'site:guangming.com.my 森美兰 when:30d'},
        {"id": "CN8", "lang": "cina", "community": "cina", "query": '"星洲日报" OR "中国报" PRN 森美兰 when:30d'},
        {"id": "CN9", "lang": "cina", "community": "cina", "query": '"pengundi Cina" OR "komuniti Cina" "Negeri Sembilan" PRN when:30d'},
        {"id": "CN10", "lang": "cina", "community": "cina", "query": 'DAP OR "Pakatan Harapan" "Negeri Sembilan" PRN when:30d'},
    ],
    "india": [
        {"id": "IN1", "lang": "tamil", "community": "india", "query": 'site:malaysiannanban.com "Negeri Sembilan" when:30d'},
        {"id": "IN2", "lang": "tamil", "community": "india", "query": 'site:makkalosai.com "Negeri Sembilan" when:30d'},
        {"id": "IN3", "lang": "tamil", "community": "india", "query": '"Makkal Osai" OR "Malaysia Nanban" Tamil "Negeri Sembilan" when:30d'},
        {"id": "IN4", "lang": "tamil", "community": "india", "query": '"pengundi India" OR "komuniti India" OR MIC "Negeri Sembilan" when:30d'},
        {"id": "IN5", "lang": "tamil", "community": "india", "query": 'Seremban OR Nilai OR Bahau Indian community when:30d'},
        {"id": "IN6", "lang": "tamil", "community": "india", "query": 'site:makkalosai.com.my Tamil Malaysia when:14d'},
        {"id": "IN7", "lang": "tamil", "community": "india", "query": 'MIC OR "Malaysian Indian" OR Hindu temple Seremban when:30d'},
        {"id": "IN8", "lang": "tamil", "community": "india", "query": '"Gunasekaren" OR "V. Gunasekaran" Negeri Sembilan when:30d'},
    ],
    "lain": [
        {"id": "OT1", "lang": "bm", "community": "lain", "query": '"Orang Asli" OR "Kampung Orang Asli" "Negeri Sembilan" when:30d'},
        {"id": "OT2", "lang": "bm", "community": "lain", "query": 'Sikh OR Gurdwara OR punjabi Malaysia when:30d'},
        {"id": "OT3", "lang": "bm", "community": "lain", "query": 'Eurasian OR Kristian OR gereja "Negeri Sembilan" when:30d'},
    ],
    "ekonomi": [
        {"id": "EC1", "lang": "ekonomi", "community": "ekonomi", "query": 'kos sara hidup OR inflasi OR "harga barang" "Negeri Sembilan" when:30d'},
        {"id": "EC2", "lang": "ekonomi", "community": "ekonomi", "query": 'ekonomi OR pelaburan OR "SME" OR "kos hidup" Seremban OR Nilai OR "Port Dickson" when:30d'},
        {"id": "EC3", "lang": "ekonomi", "community": "ekonomi", "query": 'BNM OR OPR OR ringgit OR "belanjawan" Malaysia when:14d'},
        {"id": "ED1", "lang": "en", "community": "ekonomi", "query": 'site:theedgemalaysia.com "Negeri Sembilan" when:30d'},
        {"id": "ED2", "lang": "en", "community": "ekonomi", "query": 'site:theedgemalaysia.com ringgit OR OPR OR pelaburan OR ekonomi when:14d'},
    ],
}

COMMUNITY_LABELS = {
    "umum": "Umum / PRN",
    "melayu": "Komuniti Melayu",
    "islam": "Islam / PAS / Harakah",
    "cina": "Komuniti Cina",
    "india": "Komuniti India / Tamil",
    "lain": "Lain-lain (OA, Sikh, dll.)",
    "ekonomi": "Ekonomi & Kos Hidup",
}


def all_queries() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for items in QUERY_PACK.values():
        out.extend(items)
    return out
