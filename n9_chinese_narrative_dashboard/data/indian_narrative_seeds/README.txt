INDIAN NARRATIVE CRAWL SEED PACKAGE
Prepared: 2026-06-16
Coverage: Negeri Sembilan, Melaka and Johor

FILES
00_crawl_allocation.csv - target percentages and crawl operating rules
01_facebook_pages_groups_tempatan.csv - location-based Facebook discovery seeds
02_tiktok_tempatan_komen.csv - TikTok search terms and hashtag seeds
03_media_tamil_dan_komen.csv - verified/identified Tamil media sources
04_ngo_sjkt_kuil_persatuan.csv - NGO, temple and 152 SJKT records
05_wakil_rakyat_agensi_rasmi.csv - official agencies and seat-based representative discovery
06_youtube_forum_berita_umum.csv - supplemental video/forum/news sources
07_location_keywords.csv - location aliases for search and geolocation normalisation
08_issue_keywords_multilingual.csv - Malay, English, Tamil and mixed-language issue terms
09_crawler_output_schema.csv - minimum normalized output fields

COUNTS
- Facebook discovery seeds: 96
- TikTok discovery seeds: 24
- Tamil media sources: 12
- NGO/SJKT/temple rows: 155
- SJKT official dataset rows: 152
- Official/representative rows: 40
- YouTube/forum/news rows: 9
- Location clusters: 24
- Issue categories: 16

IMPORTANT
- Rows marked discovery_seed are queries, not verified accounts. Resolve and verify URLs before production crawling.
- Do not infer ethnicity from personal names. Segment by language/content/source context.
- Aggregate map output to town/district/state; do not expose exact personal locations.
- Respect platform terms, robots rules, API limits and applicable privacy law.
- KPM SJKT school data is from the official January 2020 school list and should be refreshed when a newer official roster becomes available.
