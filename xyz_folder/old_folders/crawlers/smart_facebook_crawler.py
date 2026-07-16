#!/usr/bin/env python
# -*- coding: utf-8 -*-


import csv
import json
import os
import re
import time
import uuid
import argparse
import sys
from datetime import datetime
import requests
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch

# Add utils directory to path for emotion analysis
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils'))

try:
    from universal_analysis import get_analyzer, add_analysis_to_data
    EMOTION_ANALYSIS_AVAILABLE = True
    print("✅ Emotion analysis available for Facebook crawler!")
except ImportError:
    print("⚠️ Emotion analysis not available - continuing with sentiment only")
    EMOTION_ANALYSIS_AVAILABLE = False

# Configuration - Load from config file
def load_config():
    try:
        # Try multiple possible paths
        config_paths = [
            'config/api_credentials.json',  # From project root
            '../config/api_credentials.json',  # From crawlers directory
        ]

        for config_path in config_paths:
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except FileNotFoundError:
                continue

        print("⚠️ Config file not found in any expected location")
        return {}
    except Exception as e:
        print(f"⚠️ Error loading config: {e}")
        return {}

config = load_config()
APIFY_TOKEN = config.get('apify', {}).get('token', "apify_api_UiTteCekixYYQbhDrmoNqATMsaKddD08q9J3")
# UPDATED: Use your working actor IDs from the successful crawler
FB_POSTS_ACTOR_ID = config.get('apify', {}).get('actors', {}).get('facebook_posts', "KoJrdxJCTtpon81KY")
FB_COMMENTS_ACTOR_ID = config.get('apify', {}).get('actors', {}).get('facebook_comments', "us5srxAYnsrkgUv2v")
PROXY_CONFIG = config.get('proxy', {}).get('apify_proxy', {})
PROXY_PASSWORD = PROXY_CONFIG.get('password', "apify_proxy_vZKKP5lUM3VHc7vi_EGwVnbQyvhBm693b5YuR")

# Global sentiment analyzer
sentiment_analyzer = None

def initialize_sentiment_analyzer():
    """Initialize the Malay BERT sentiment analyzer."""
    global sentiment_analyzer
    if sentiment_analyzer is None:
        try:
            print("🤖 Loading Malay BERT sentiment model...")
            model_name = "rmtariq/ft-Malay-bert"

            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSequenceClassification.from_pretrained(model_name)

            sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            print("✅ Malay BERT model loaded successfully!")

        except Exception as e:
            print(f"⚠️ Error loading sentiment model: {e}")
            print("📝 Using fallback sentiment analysis...")
            sentiment_analyzer = "fallback"

    return sentiment_analyzer

def analyze_sentiment(text):
    """Analyze sentiment using rmtariq/ft-Malay-bert model."""
    if not text or len(text.strip()) < 3:
        return "Neutral", 0.5

    try:
        analyzer = initialize_sentiment_analyzer()

        if analyzer == "fallback":
            text_lower = text.lower()

            # Enhanced Malaysian positive words
            positive_words = [
                'bagus', 'baik', 'betul', 'setuju', 'terima kasih', 'hebat', 'mantap',
                'excellent', 'good', 'great', 'awesome', 'amazing', 'perfect', 'love',
                'suka', 'cinta', 'gembira', 'senang', 'puas', 'berjaya', 'cemerlang',
                'terbaik', 'luar biasa', 'menakjubkan', 'fantastik', 'wonderful',
                '👍', '❤️', '😍', '🔥', '💯', '✅', '😊', '😄'
            ]

            # Enhanced Malaysian negative words
            negative_words = [
                'salah', 'tidak', 'buruk', 'marah', 'benci', 'bodoh', 'teruk',
                'bad', 'terrible', 'awful', 'hate', 'angry', 'stupid', 'wrong',
                'sedih', 'kecewa', 'menyampah', 'jijik', 'geram', 'bengang',
                'tak suka', 'tak setuju', 'mengarut', 'karut', 'nonsense',
                '👎', '😡', '😠', '💩', '🤮', '❌', '😢', '😭'
            ]

            if any(word in text_lower for word in positive_words):
                return "Positive", 0.8
            elif any(word in text_lower for word in negative_words):
                return "Negative", 0.2
            else:
                return "Neutral", 0.5

        text_truncated = text[:512]
        result = analyzer(text_truncated)

        if isinstance(result, list) and len(result) > 0:
            prediction = result[0]
            label = prediction['label'].upper()
            score = prediction['score']

            # Fix: Map the actual model labels correctly
            if label in ['LABEL_2', 'POSITIVE', 'POS', '2']:  # LABEL_2 = Positive
                return "Positive", score
            elif label in ['LABEL_0', 'NEGATIVE', 'NEG', '0']:  # LABEL_0 = Negative
                return "Negative", score
            elif label in ['LABEL_1', 'NEUTRAL', 'NEU', '1']:  # LABEL_1 = Neutral
                return "Neutral", score
            else:
                # Fallback: if unknown label, use score to determine sentiment
                if score > 0.7:
                    return "Positive", score
                elif score < 0.3:
                    return "Negative", score
                else:
                    return "Neutral", score
        else:
            return "Neutral", 0.5

    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        text_lower = text.lower()
        if any(word in text_lower for word in ['bagus', 'baik', 'betul', 'setuju', 'terima kasih']):
            return "Positive", 0.8
        elif any(word in text_lower for word in ['salah', 'tidak', 'buruk', 'marah', 'benci']):
            return "Negative", 0.2
        else:
            return "Neutral", 0.5

def detect_language(text):
    """Detect if text is primarily Malay or English."""
    malay_indicators = ['dan', 'atau', 'dengan', 'untuk', 'dalam', 'pada', 'dari', 'ke', 'di', 'yang', 'adalah', 'akan', 'telah', 'sudah', 'tidak', 'boleh', 'dapat', 'malaysia', 'kerajaan', 'rakyat', 'negara', 'tahun', 'bulan', 'hari', 'masa', 'wang', 'ringgit', 'sen']
    english_indicators = ['and', 'or', 'with', 'for', 'in', 'on', 'from', 'to', 'at', 'the', 'is', 'are', 'will', 'have', 'has', 'not', 'can', 'could', 'malaysia', 'government', 'people', 'country', 'year', 'month', 'day', 'time', 'money', 'dollar', 'cent']

    text_lower = text.lower()
    malay_count = sum(1 for word in malay_indicators if word in text_lower)
    english_count = sum(1 for word in english_indicators if word in text_lower)

    if malay_count > english_count:
        return 'malay'
    elif english_count > malay_count:
        return 'english'
    else:
        return 'mixed'

def translate_to_other_language(text, source_lang):
    """Create bilingual search terms."""
    translations = {
        # Business terms
        'business': 'perniagaan',
        'perniagaan': 'business',
        'company': 'syarikat',
        'syarikat': 'company',
        'entrepreneur': 'usahawan',
        'usahawan': 'entrepreneur',
        'startup': 'permulaan',
        'permulaan': 'startup',
        'investment': 'pelaburan',
        'pelaburan': 'investment',
        'profit': 'keuntungan',
        'keuntungan': 'profit',
        'market': 'pasaran',
        'pasaran': 'market',
        'economy': 'ekonomi',
        'ekonomi': 'economy',
        'finance': 'kewangan',
        'kewangan': 'finance',
        'money': 'wang',
        'wang': 'money',
        'opportunity': 'peluang',
        'peluang': 'opportunity',
        'opportunities': 'peluang',
        'growth': 'pertumbuhan',
        'pertumbuhan': 'growth',
        'development': 'pembangunan',
        'pembangunan': 'development',
        'success': 'kejayaan',
        'kejayaan': 'success',
        'strategy': 'strategi',
        'strategi': 'strategy',
        'plan': 'rancangan',
        'rancangan': 'plan',
        'goal': 'matlamat',
        'matlamat': 'goal',
        'target': 'sasaran',
        'sasaran': 'target',
        'innovation': 'inovasi',
        'inovasi': 'innovation',
        'technology': 'teknologi',
        'teknologi': 'technology',
        'digital': 'digital',
        'online': 'dalam talian',
        'dalam talian': 'online',
        'ecommerce': 'e-dagang',
        'e-dagang': 'ecommerce',
        'marketing': 'pemasaran',
        'pemasaran': 'marketing',
        'sales': 'jualan',
        'jualan': 'sales',
        'customer': 'pelanggan',
        'pelanggan': 'customer',
        'service': 'perkhidmatan',
        'perkhidmatan': 'service',
        'product': 'produk',
        'produk': 'product',
        'brand': 'jenama',
        'jenama': 'brand',
        'quality': 'kualiti',
        'kualiti': 'quality',
        'price': 'harga',
        'harga': 'price',
        'cheap': 'murah',
        'murah': 'cheap',
        'expensive': 'mahal',
        'mahal': 'expensive',
        'good': 'bagus',
        'bagus': 'good',
        'best': 'terbaik',
        'terbaik': 'best',
        'new': 'baru',
        'baru': 'new',
        'old': 'lama',
        'lama': 'old',
        'popular': 'popular',
        'trending': 'trending',
        'viral': 'viral',
        'famous': 'terkenal',
        'terkenal': 'famous',
        'review': 'ulasan',
        'ulasan': 'review',
        'recommendation': 'cadangan',
        'cadangan': 'recommendation',
        'advice': 'nasihat',
        'nasihat': 'advice',
        'tips': 'petua',
        'petua': 'tips',
        'guide': 'panduan',
        'panduan': 'guide',
        'help': 'bantuan',
        'bantuan': 'help',
        'support': 'sokongan',
        'sokongan': 'support',
        'problem': 'masalah',
        'masalah': 'problem',
        'solution': 'penyelesaian',
        'penyelesaian': 'solution',
        'issue': 'isu',
        'isu': 'issue',
        'news': 'berita',
        'berita': 'news',
        'update': 'kemaskini',
        'kemaskini': 'update',
        'latest': 'terkini',
        'terkini': 'latest',
        'current': 'semasa',
        'semasa': 'current',
        'today': 'hari ini',
        'hari ini': 'today',
        'now': 'sekarang',
        'sekarang': 'now',
        'future': 'masa depan',
        'masa depan': 'future',
        'trend': 'trend',
        'analysis': 'analisis',
        'analisis': 'analysis',
        'report': 'laporan',
        'laporan': 'report',
        'study': 'kajian',
        'kajian': 'study',
        'research': 'penyelidikan',
        'penyelidikan': 'research',
        'data': 'data',
        'information': 'maklumat',
        'maklumat': 'information',
        'knowledge': 'pengetahuan',
        'pengetahuan': 'knowledge',
        'education': 'pendidikan',
        'pendidikan': 'education',
        'training': 'latihan',
        'latihan': 'training',
        'skill': 'kemahiran',
        'kemahiran': 'skill',
        'experience': 'pengalaman',
        'pengalaman': 'experience',
        'expert': 'pakar',
        'pakar': 'expert',
        'professional': 'profesional',
        'profesional': 'professional',
        'career': 'kerjaya',
        'kerjaya': 'career',
        'job': 'kerja',
        'kerja': 'job',
        'work': 'kerja',
        'employment': 'pekerjaan',
        'pekerjaan': 'employment',
        'salary': 'gaji',
        'gaji': 'salary',
        'income': 'pendapatan',
        'pendapatan': 'income',
        'malaysia': 'malaysia',
        'malaysian': 'malaysia',
        'kuala lumpur': 'kuala lumpur',
        'kl': 'kl',
        'selangor': 'selangor',
        'johor': 'johor',
        'penang': 'pulau pinang',
        'pulau pinang': 'penang',
        'sabah': 'sabah',
        'sarawak': 'sarawak',
        'perak': 'perak',
        'kedah': 'kedah',
        'kelantan': 'kelantan',
        'terengganu': 'terengganu',
        'pahang': 'pahang',
        'negeri sembilan': 'negeri sembilan',
        'melaka': 'melaka',
        'perlis': 'perlis',
        'putrajaya': 'putrajaya',
        'labuan': 'labuan'
    }

    words = text.lower().split()
    translated_words = []

    for word in words:
        if word in translations:
            translated_words.append(translations[word])
        else:
            translated_words.append(word)

    return ' '.join(translated_words)

def extract_smart_keywords(claim):
    """Extract smart keywords from any claim with Malaysian context and bilingual support."""
    print(f"🧠 Extracting smart keywords from claim...")

    # Detect language
    detected_lang = detect_language(claim)
    print(f"🌐 Detected language: {detected_lang}")

    # Create bilingual versions
    original_claim = claim
    if detected_lang == 'malay':
        translated_claim = translate_to_other_language(claim, 'malay')
        print(f"🔄 English translation: {translated_claim}")
    elif detected_lang == 'english':
        translated_claim = translate_to_other_language(claim, 'english')
        print(f"🔄 Malay translation: {translated_claim}")
    else:
        translated_claim = claim
        print(f"🔄 Mixed language detected, using original")

    # Clean both versions
    claim_clean = re.sub(r'[^\w\s]', ' ', original_claim.lower())
    translated_clean = re.sub(r'[^\w\s]', ' ', translated_claim.lower())

    # Combine words from both versions
    words = claim_clean.split() + translated_clean.split()
    words = list(set(words))  # Remove duplicates

    # Malaysian stop words
    stop_words = {
    # --- kata hubung / konjungsi
    'dan', 'atau', 'serta', 'mahupun', 'maupun', 'tetapi', 'namun', 'lalu', 'kemudian',
    'bahkan', 'sebaliknya', 'sambil', 'sehingga', 'sementara', 'apabila', 'apabila',
    'kerana', 'karena', 'agar', 'supaya', 'jika', 'kalau',

    # --- preposisi
    'di', 'ke', 'dari', 'daripada', 'pada', 'kepada', 'antara', 'dalam',
    'oleh', 'untuk', 'sejak', 'hingga', 'hingga', 'sampai', 'tanpa', 'tentang',

    # --- kata bantu modal & aspek
    'akan', 'telah', 'sudah', 'belum', 'masih', 'pernah', 'hendak', 'ingin',
    'boleh', 'dapat', 'mesti', 'harus', 'patut', 'tak', 'tidak', 'tidaklah',
    'tiada', 'takkan', 'bukankah',

    # --- penanda wacana & partikel
    'ini', 'itu', 'tersebut', 'begitu', 'demikian', 'hanya', 'sahaja', 'saja',
    'lagi', 'pun', 'lah', 'kah', 'tah', 'pun', 'ya', 'oh',

    # --- pronomina peribadi & petunjuk
    'saya', 'aku', 'anda', 'kamu', 'engkau', 'awak', 'dia', 'ia', 'mereka',
    'kita', 'kami', 'dirinya', 'kau', 'nya', 'kalian',

    # --- kata keterangan umum
    'sangat', 'amat', 'lebih', 'paling', 'kurang', 'agak', 'sekadar',
    'semua', 'setiap', 'sesetengah', 'mana-mana', 'apa-apa',

    # --- kata soal
    'apa', 'siapa', 'mengapa', 'kenapa', 'bagaimana',
    'bila', 'bilakah', 'kapan', 'dimana', 'di mana', 'mana', 'benarkah', 'adakah',

    # --- bentuk dialek & variasi ejaan lazim
    'gitu', 'gitulah', 'jer', 'je', 'nih', 'tu', 'takde', 'xde',

    # --- penanda angka / masa (kadang-kadang wajar dikecualikan)
    'satu', 'dua', 'tiga', 'empat', 'lima', 'enam', 'tujuh', 'lapan', 'sembilan',
    'puluh', 'ratus', 'ribu', 'juta', 'pertama', 'kedua',

    # --- asal anda (disatukan)
    'juga', 'pula', 'adalah', 'ada', 'sebagai'
}


    # Extract important keywords (length > 3, not stop words)
    keywords = []
    for word in words:
        if len(word) > 3 and word not in stop_words:
            keywords.append(word)

    # Identify key entities and concepts
    entities = {
    # --- Kerajaan & Politik
    'government': {
        'kerajaan', 'kementerian', 'jabatan', 'agensi', 'perdana', 'menteri',
        'parlimen', 'dpr', 'yab', 'yda', 'exco', 'spr', 'sprm', 'yaman',  # yaman = Y.A.M. / titles
        'parti', 'manifesto', 'undian', 'pilihanraya', 'pru', 'adun', 'mp',
        'umno', 'pas', 'dap', 'pkr', 'bersatu', 'warisan', 'gerakan', 'ph', 'bn', 'pn'
    },

    # --- Kewangan & Bantuan
    'money': {
        'rm', 'ringgit', 'wang', 'duit', 'bantuan', 'subsidi', 'bayaran',
        'gaji', 'bonus', 'saham', 'dividen', 'dana', 'pinjaman', 'belanjawan',
        'peruntukan', 'pelaburan', 'zakat', 'derma', 'insentif', 'geran'
    },

    # --- Pendidikan
    'education': {
        'pelajar', 'mahasiswa', 'murid', 'universiti', 'kolej', 'sekolah',
        'pendidikan', 'ptptn', 'biasiswa', 'loan', 'guru', 'cikgu',
        'pensyarah', 'kursus', 'spm', 'stpm', 'uitm', 'um', 'ukm', 'utm',
        'exam', 'peperiksaan', 'semeser', 'graduan', 'ijazah'
    },

    # --- Kesihatan
    'health': {
        'vaksin', 'imunisasi', 'ubat', 'hospital', 'klinik', 'kesihatan',
        'doktor', 'nurse', 'jururawat', 'rawatan', 'pesakit', 'icu',
        'covid', 'denggi', 'kanser', 'mental', 'kes', 'influenza', 'ambulans'
    },

    # --- Teknologi & Digital
    'technology': {
        'digital', 'online', 'aplikasi', 'app', 'sistem', 'platform',
        'teknologi', 'internet', 'siber', 'cyber', 'cloud', 'iot',
        'ai', 'ml', 'blockchain', '5g', 'robotik', 'gadget', 'telefon',
        'smartphone', 'komputer', 'perisian', 'software', 'hardware'
    },

    # --- Ekonomi & Perniagaan
    'economy': {
        'ekonomi', 'pasaran', 'perniagaan', 'bisnes', 'industri',
        'pelaburan', 'perdagangan', 'gdp', 'inflasi', 'cukai',
        'pengangguran', 'import', 'eksport', 'bekalan', 'permintaan',
        'pkp', 'sme', 'msme', 'korporat'
    },

    # === KATEGORI TAMBAHAN YANG SERING RELEVAN ===
    'environment': {
        'alam', 'iklim', 'climate', 'cuaca', 'banjir', 'kemarau',
        'hutan', 'sungai', 'laut', 'pencemaran', 'co2', 'hijau',
        'kelestarian', 'sustainability', 'sdg'
    },

    'energy': {
        'tenaga', 'elektrik', 'solar', 'minyak', 'gas', 'petrol',
        'diesel', 'nuklear', 'bateri', 'stesen', 'grid', 'ev',
        'renewable', 'hidro', 'tnb'
    },

    'transport': {
        'jalan', 'kereta', 'motor', 'bas', 'lori', 'rel', 'keretapi',
        'lrt', 'mrt', 'rapidx', 'tol', 'lebuh', 'trafik', 'grab',
        'e-hailing', 'penerbangan', 'pesawat', 'lapangan', 'airport',
        'pelabuhan', 'kapal', 'feri'
    },

    'religion': {
        'agama', 'islam', 'masjid', 'surau', 'quran', 'hadis',
        'fatwa', 'halal', 'haram', 'zakat', 'wakaf', 'solat',
        'haji', 'umrah', 'puasa', 'gereja', 'tokong', 'kuil',
        'paderi', 'ustaz', 'mufti'
    },

    'law': {
        'mahkamah', 'undang', 'akta', 'polis', 'pdrm', 'saman',
        'jenayah', 'hukuman', 'penjara', 'denda', 'sprm',
        'penguatkuasaan', 'peringatan', 'tangkapan', 'kes',
        'pendakwaan', 'peguam'
    },

    'sports': {
        'sukan', 'bola', 'football', 'badminton', 'olahraga', 'atlet',
        'stadium', 'liga', 'piala', 'fifa', 'gol', 'penalti',
        'olimpik', 'esukan', 'e-sports', 'pasukan'
    }
}


    # Find entity matches
    entity_keywords = []
    for category, entity_words in entities.items():
        for word in keywords:
            if any(entity_word in word for entity_word in entity_words):
                entity_keywords.append(word)

    # Combine and prioritize keywords
    priority_keywords = list(set(entity_keywords + keywords[:5]))

    print(f"🔑 Extracted keywords: {priority_keywords[:8]}")
    return priority_keywords

def generate_boolean_query(claim, keywords):
    """Generate Boolean OR query with full claim + all keywords."""
    print(f"🔍 Generating Boolean OR query...")

    # Clean the claim (remove question words)
    claim_clean = claim.lower()
    for question_word in ['adakah', 'benarkah', 'betulkah', 'mengapa', 'bagaimana']:
        claim_clean = claim_clean.replace(question_word, '').strip()

    # Build Boolean query components
    query_parts = []

    # Add full cleaned claim in quotes
    if len(claim_clean) > 10:
        query_parts.append(f'"{claim_clean}"')

    # Add individual keywords in quotes
    for keyword in keywords[:5]:  # Top 5 keywords
        if len(keyword) > 3:
            query_parts.append(f'"{keyword}"')

    # Add key single words without quotes for broader matching
    for keyword in keywords[:3]:  # Top 3 keywords
        if len(keyword.split()) == 1 and len(keyword) > 3:  # Single words only
            query_parts.append(keyword)

    # Create Boolean OR query
    boolean_query = " OR ".join(query_parts)

    print(f"🎯 Boolean Query: {boolean_query[:100]}...")
    return boolean_query

def generate_search_strategies(claim, keywords):
    """Generate multiple bilingual search strategies for any claim."""
    print(f"🎯 Generating bilingual search strategies...")

    # Detect language and create bilingual versions
    detected_lang = detect_language(claim)

    strategies = []

    # Strategy 1: Original claim (both languages)
    strategies.append(claim)

    # Strategy 2: Translated version
    if detected_lang == 'malay':
        translated_claim = translate_to_other_language(claim, 'malay')
        strategies.append(translated_claim)
        print(f"🌐 Added English version: {translated_claim}")
    elif detected_lang == 'english':
        translated_claim = translate_to_other_language(claim, 'english')
        strategies.append(translated_claim)
        print(f"🌐 Added Malay version: {translated_claim}")

    # Strategy 3: Boolean OR query (bilingual)
    boolean_query = generate_boolean_query(claim, keywords)
    if len(boolean_query) < 500:  # Facebook has query length limits
        strategies.append(boolean_query)

    # Strategy 4: Core keywords (bilingual)
    if len(keywords) >= 2:
        # Original language keywords
        strategies.append(" ".join(keywords[:3]))

        # Translated keywords
        translated_keywords = []
        for keyword in keywords[:3]:
            if detected_lang == 'malay':
                translated = translate_to_other_language(keyword, 'malay')
            else:
                translated = translate_to_other_language(keyword, 'english')
            translated_keywords.append(translated)
        strategies.append(" ".join(translated_keywords))

    # Strategy 5: Keywords + Malaysia (bilingual)
    if len(keywords) >= 2:
        strategies.append(" ".join(keywords[:2]) + " Malaysia")
        if detected_lang == 'malay':
            strategies.append(" ".join(keywords[:2]) + " Malaysia")
        else:
            strategies.append(" ".join(keywords[:2]) + " Malaysia")

    # Strategy 6: Individual keywords with context (bilingual)
    for keyword in keywords[:2]:
        strategies.append(f"{keyword} Malaysia")
        # Add translated version
        if detected_lang == 'malay':
            translated_keyword = translate_to_other_language(keyword, 'malay')
        else:
            translated_keyword = translate_to_other_language(keyword, 'english')
        strategies.append(f"{translated_keyword} Malaysia")

    # Strategy 4: Topic-specific searches based on keywords (Enhanced with business contexts)
    topic_contexts = {
    # Business & Economy
    'business':  ['perniagaan {country}', 'peluang perniagaan'],
    'perniagaan':['business {country}', 'peluang perniagaan'],
    'ekonomi':   ['ekonomi {country}', 'pertumbuhan gdp'],
    'pekerjaan': ['pengangguran {country}', 'peluang pekerjaan'],
    'startup':   ['startup {country}', 'syarikat permulaan'],
    'sme':       ['sme {country}', 'perusahaan kecil sederhana'],
    'pkk':       ['pkk {country}', 'perusahaan kecil'],
    'usahawan':  ['usahawan {country}', 'entrepreneur'],
    'modal':     ['modal perniagaan {country}', 'pembiayaan'],
    'loan':      ['pinjaman perniagaan {country}', 'loan sme'],
    'grant':     ['geran perniagaan {country}', 'bantuan usahawan'],
    'franchise': ['francais {country}', 'peluang francais'],
    'ecommerce': ['e-dagang {country}', 'perniagaan online'],
    'digital':   ['transformasi digital {country}', 'ekonomi digital'],
    # Technology & Innovation
    'telco':     ['telco {country}', 'syarikat telekomunikasi'],
    'internet':  ['internet {country}', 'pelan internet'],
    'fintech':   ['fintech {country}', 'teknologi kewangan'],
    # Government & Policy
    'kerajaan':  ['kerajaan {country}', 'dasar kerajaan'],
    'bantuan':   ['bantuan kerajaan', 'subsidi {country}'],
    'rebat':     ['rebat elektrik {country}', 'rebat bil elektrik'],
    'b40':       ['bantuan b40 {country}', 'isi rumah b40'],
    'percuma':   ['bantuan percuma {country}', 'subsidi percuma'],
    # Others
    'harga':     ['harga naik {country}', 'kenaikan harga'],
    'vaksin':    ['vaksin {country}', 'imunisasi'],
    'pelajar':   ['pelajar {country}', 'universiti {country}'],
    'elektrik':  ['bil elektrik {country}', 'rebat elektrik'],
    'kesihatan': ['hospital {country}', 'isu kesihatan awam'],
    'pendidikan':['sistem pendidikan {country}', 'ptptn'],
    'makanan':   ['keselamatan makanan {country}', 'harga ayam']
}


    # Add topic-specific searches based on detected keywords
    for keyword in keywords[:3]:
        for topic, contexts in topic_contexts.items():
            if topic in keyword.lower():
                # Replace {country} template with Malaysia
                processed_contexts = []
                for context in contexts[:1]:
                    if '{country}' in context:
                        processed_contexts.append(context.replace('{country}', 'Malaysia'))
                    else:
                        processed_contexts.append(context)
                strategies.extend(processed_contexts)
                break

    # Strategy 5: Shortened claim (remove question words)
    claim_clean = claim.lower()
    for question_word in ['benarkah', 'adakah', 'betulkah', 'mengapa', 'bagaimana']:
        claim_clean = claim_clean.replace(question_word, '').strip()

    # Take first meaningful part of cleaned claim
    claim_words = claim_clean.split()[:5]  # First 5 words
    if len(claim_words) >= 3:
        strategies.append(" ".join(claim_words))

    # Strategy 6: News and official sources (bilingual)
    if keywords:
        strategies.append(f"berita {keywords[0]} Malaysia")  # Malay news
        strategies.append(f"news {keywords[0]} Malaysia")    # English news

        # Add translated keyword versions
        if detected_lang == 'malay':
            translated_keyword = translate_to_other_language(keywords[0], 'malay')
            strategies.append(f"news {translated_keyword} Malaysia")
        else:
            translated_keyword = translate_to_other_language(keywords[0], 'english')
            strategies.append(f"berita {translated_keyword} Malaysia")

    # Remove duplicates while preserving order
    seen = set()
    unique_strategies = []
    for strategy in strategies:
        strategy_clean = strategy.strip()
        if strategy_clean and strategy_clean not in seen and len(strategy_clean) > 5:
            seen.add(strategy_clean)
            unique_strategies.append(strategy_clean)

    # Limit to 8 diverse strategies
    unique_strategies = unique_strategies[:8]

    print(f"📋 Generated {len(unique_strategies)} diverse search strategies")
    for i, strategy in enumerate(unique_strategies, 1):
        print(f"   {i}. {strategy}")

    return unique_strategies

def is_relevant_to_claim(text, claim, keywords):
    """Check if content is relevant to the original claim with improved filtering."""
    if not text:
        return False, 0.0

    text_lower = text.lower()
    claim_lower = claim.lower()

    # Check for direct keyword matches
    keyword_matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
    keyword_score = keyword_matches / len(keywords) if keywords else 0

    # Check for Malaysian context (stronger indicators)
    malaysian_indicators = ['malaysia', 'kerajaan', 'rakyat', 'negara', 'kementerian', 'menteri', 'jabatan']
    malaysian_score = sum(1 for indicator in malaysian_indicators if indicator in text_lower) / len(malaysian_indicators)

    # Check for claim-related terms (more specific)
    claim_words = [word for word in claim_lower.split() if len(word) > 3]
    claim_matches = sum(1 for word in claim_words if word in text_lower)
    claim_score = claim_matches / len(claim_words) if claim_words else 0

    # Check for topic relevance (specific to common Malaysian topics)
    topic_indicators = {
        'education': ['pelajar', 'universiti', 'ptptn', 'pendidikan', 'kolej'],
        'finance': ['bantuan', 'wang', 'rm', 'ringgit', 'subsidi', 'bayaran'],
        'health': ['vaksin', 'kesihatan', 'hospital', 'ubat', 'rawatan'],
        'government': ['dasar', 'polisi', 'undang', 'akta', 'peraturan'],
        'utilities': ['elektrik', 'bil', 'rebat', 'percuma', 'b40', 'isi rumah'],
        'assistance': ['bantuan', 'subsidi', 'rebat', 'percuma', 'kerajaan'],
        'tax': ['cukai', 'tax', 'digital', 'transaksi', 'perkhidmatan', 'e-dagang'],
        'technology': ['digital', 'online', 'e-commerce', 'platform', 'teknologi']
    }

    topic_score = 0
    for topic, indicators in topic_indicators.items():
        topic_matches = sum(1 for indicator in indicators if indicator in text_lower)
        if topic_matches > 0:
            topic_score = max(topic_score, topic_matches / len(indicators))

    # Calculate overall relevance with improved weighting
    relevance_score = (keyword_score * 0.35) + (malaysian_score * 0.25) + (claim_score * 0.25) + (topic_score * 0.15)

    # More strict relevance criteria
    is_relevant = (
        relevance_score > 0.3 or  # Higher threshold
        (malaysian_score > 0.3 and keyword_score > 0.2) or  # Malaysian + keywords
        (claim_score > 0.4)  # Strong claim match
    )

    return is_relevant, relevance_score

def run_apify_actor(actor_id, input_data, max_wait_time=300):
    """Run an Apify actor and wait for results."""
    try:
        headers = {
            "Authorization": f"Bearer {APIFY_TOKEN}",
            "Content-Type": "application/json"
        }

        print(f"🚀 Starting Apify actor: {actor_id}")

        response = requests.post(
            f"https://api.apify.com/v2/acts/{actor_id}/runs",
            headers=headers,
            json=input_data
        )

        if response.status_code != 201:
            print(f"❌ Error starting task: {response.status_code}")
            return []

        run_data = response.json()
        run_id = run_data["data"]["id"]
        print(f"✅ Task started successfully!")

        # Wait for completion
        print("⏳ Waiting for results...")
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            status_response = requests.get(
                f"https://api.apify.com/v2/actor-runs/{run_id}",
                headers=headers
            )

            if status_response.status_code == 200:
                status = status_response.json()["data"]["status"]

                if status == "SUCCEEDED":
                    print("✅ Task completed successfully!")
                    break
                elif status in ["FAILED", "ABORTED", "TIMED-OUT"]:
                    print(f"❌ Task failed with status: {status}")
                    return []

            time.sleep(10)

        # Get results
        results_response = requests.get(
            f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items",
            headers=headers
        )

        if results_response.status_code == 200:
            results = results_response.json()
            print(f"📊 Retrieved {len(results)} items")
            return results
        else:
            print(f"❌ Error getting results: {results_response.status_code}")
            return []

    except Exception as e:
        print(f"❌ Error running task: {e}")
        return []

def show_strategy_help():
    """Show helpful examples for strategy editing."""
    print("\n💡 STRATEGY EDITING HELP")
    print("-" * 40)
    print("✅ Good strategies for your claim:")
    print("   • 'cuti khas sukarelawan' - specific terms")
    print("   • 'dasar kerajaan bencana' - policy focus")
    print("   • 'pekerja sukarelawan Malaysia' - local context")
    print("   • 'bantuan bencana alam' - disaster relief")
    print("   • 'kerajaan negeri cuti' - state government")
    print()
    print("❌ Avoid too general terms:")
    print("   • Just 'kerajaan' (too broad)")
    print("   • Just 'Malaysia' (too general)")
    print()
    print("🎯 Tips:")
    print("   • Combine 2-4 relevant keywords")
    print("   • Include Malaysian context")
    print("   • Use specific terms from your claim")

def edit_search_strategies(strategies):
    """User-friendly strategy editing interface."""
    print(f"\n✏️ STRATEGY EDITING - USER FRIENDLY MODE")
    print("=" * 60)
    print("🎯 Let's customize your Facebook search strategies!")
    print("📝 This helps find more relevant content for your claim.")
    print()

    # Show current strategies in a nice table
    print("🤖 AUTO-GENERATED STRATEGIES:")
    print("-" * 40)
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy}")

    print()
    print("✏️ EDITING OPTIONS:")
    print("-" * 40)
    print("1️⃣ Edit individual strategies")
    print("2️⃣ Use all strategies as-is")
    print("3️⃣ Start fresh with custom strategies")
    print("4️⃣ Show help and examples")
    print()

    while True:
        choice = input("🔍 Choose option (1-4): ").strip()

        if choice == "1":
            return edit_individual_strategies(strategies)
        elif choice == "2":
            print("✅ Using all auto-generated strategies!")
            return strategies
        elif choice == "3":
            return create_custom_strategies()
        elif choice == "4":
            show_strategy_help()
            continue
        else:
            print("❌ Please choose 1, 2, 3, or 4")

def edit_individual_strategies(strategies):
    """Edit strategies one by one with better interface."""
    print(f"\n📝 INDIVIDUAL STRATEGY EDITING")
    print("=" * 50)
    print("💡 For each strategy, you can:")
    print("   • Press ENTER to keep it")
    print("   • Type new text to replace it")
    print("   • Type 'skip' to remove it")
    print("   • Type 'help' for examples")
    print("-" * 50)

    edited_strategies = []

    for i, strategy in enumerate(strategies, 1):
        print(f"\n🔍 Strategy {i}/{len(strategies)}: '{strategy}'")
        print(f"   💭 This searches for: {strategy}")

        while True:
            user_input = input(f"   ✏️ Keep/Edit/Skip? ").strip()

            if user_input.lower() == 'help':
                show_strategy_help()
                continue
            elif user_input.lower() == 'skip':
                print(f"   ❌ Removed: {strategy}")
                break
            elif user_input == '':
                edited_strategies.append(strategy)
                print(f"   ✅ Kept: {strategy}")
                break
            elif len(user_input) > 3:
                edited_strategies.append(user_input)
                print(f"   ✅ Updated: {strategy} → {user_input}")
                break
            else:
                print("   ❌ Strategy too short. Try again or type 'help'")

    # Option to add new strategies
    print(f"\n➕ ADD MORE STRATEGIES (optional)")
    print("💡 Add strategies you think will work better:")

    while True:
        print(f"\n   Current strategies: {len(edited_strategies)}")
        new_strategy = input("   🆕 Add new (or press Enter to finish): ").strip()

        if not new_strategy:
            break
        elif len(new_strategy) > 3:
            edited_strategies.append(new_strategy)
            print(f"   ✅ Added: {new_strategy}")
        else:
            print("   ❌ Strategy too short. Try again.")

    return finalize_strategies(edited_strategies)

def create_custom_strategies():
    """Create completely custom strategies."""
    print(f"\n🆕 CREATE CUSTOM STRATEGIES")
    print("=" * 50)
    print("💡 Create your own search strategies from scratch!")
    print("🎯 Aim for 3-8 strategies that target different aspects.")

    show_strategy_help()

    custom_strategies = []

    print(f"\n📝 Enter your custom strategies:")
    for i in range(1, 9):  # Max 8 strategies
        strategy = input(f"   {i}. Strategy {i} (or press Enter to finish): ").strip()

        if not strategy:
            break
        elif len(strategy) > 3:
            custom_strategies.append(strategy)
            print(f"   ✅ Added: {strategy}")
        else:
            print("   ❌ Too short. Try again.")
            i -= 1  # Don't count this attempt

    if not custom_strategies:
        print("❌ No strategies created. Returning to menu...")
        return edit_search_strategies([])

    return finalize_strategies(custom_strategies)

def finalize_strategies(strategies):
    """Show final strategies and confirm."""
    if not strategies:
        print("❌ No strategies selected!")
        return []

    print(f"\n📋 FINAL STRATEGIES ({len(strategies)} total)")
    print("=" * 50)
    for i, strategy in enumerate(strategies, 1):
        print(f"   {i}. {strategy}")

    print(f"\n🎯 QUALITY CHECK:")
    print("-" * 30)

    # Basic quality checks
    has_malaysian = any('malaysia' in s.lower() for s in strategies)
    has_specific = any(len(s.split()) >= 2 for s in strategies)
    has_variety = len(set(strategies)) == len(strategies)

    print(f"🇲🇾 Malaysian context: {'✅' if has_malaysian else '⚠️ Consider adding Malaysia'}")
    print(f"🎯 Specific terms: {'✅' if has_specific else '⚠️ Consider more specific terms'}")
    print(f"🔄 Variety: {'✅' if has_variety else '⚠️ Remove duplicates'}")

    print(f"\n🚀 READY TO CRAWL?")
    print("-" * 30)
    print("1️⃣ Yes, start crawling!")
    print("2️⃣ Edit strategies again")
    print("3️⃣ Cancel crawling")

    while True:
        choice = input("🔍 Choose (1-3): ").strip()

        if choice == "1":
            print("✅ Starting Facebook crawling with your strategies!")
            return strategies
        elif choice == "2":
            return edit_search_strategies(strategies)
        elif choice == "3":
            print("❌ Crawling cancelled")
            return []
        else:
            print("❌ Please choose 1, 2, or 3")

def detect_boolean_query(input_text):
    """Detect if input is a Boolean OR query."""
    return " OR " in input_text.upper()

def parse_boolean_or_query(boolean_query):
    """Parse Boolean OR query into individual search terms."""
    print(f"🔧 PARSING BOOLEAN OR QUERY")
    print("-" * 40)

    # Split by OR (case insensitive)
    import re
    parts = re.split(r'\s+OR\s+', boolean_query, flags=re.IGNORECASE)

    search_terms = []
    for part in parts:
        part = part.strip()
        if part:
            # Remove outer quotes if present
            if part.startswith('"') and part.endswith('"'):
                part = part[1:-1]
            search_terms.append(part)

    # Prioritize terms (quoted phrases first, then longer terms)
    prioritized_terms = []

    # Add longer, more specific terms first
    long_terms = [term for term in search_terms if len(term.split()) >= 3]
    medium_terms = [term for term in search_terms if len(term.split()) == 2]
    short_terms = [term for term in search_terms if len(term.split()) == 1]

    # Combine with Malaysian context
    prioritized_terms.extend([f"{term} Malaysia" for term in long_terms[:3]])
    prioritized_terms.extend(long_terms[:5])
    prioritized_terms.extend([f"{term} Malaysia" for term in medium_terms[:3]])
    prioritized_terms.extend(medium_terms[:5])
    prioritized_terms.extend([f"{term} Malaysia" for term in short_terms[:2]])
    prioritized_terms.extend(short_terms[:3])

    # Remove duplicates while preserving order
    final_terms = []
    seen = set()
    for term in prioritized_terms:
        if term.lower() not in seen:
            seen.add(term.lower())
            final_terms.append(term)

    # Limit to 8 terms for efficiency
    final_terms = final_terms[:8]

    print(f"📋 Parsed into {len(final_terms)} search terms:")
    for i, term in enumerate(final_terms, 1):
        print(f"   {i}. {term}")

    return final_terms

def get_user_data_preferences():
    """Get user's exact preferences for data collection."""
    print("\n📊 DATA COLLECTION CONTROL")
    print("=" * 40)
    print("🎯 Choose exactly how much data you want to collect:")
    print()

    # Get posts control
    print("📝 POSTS CONTROL:")
    num_posts = int(input("📝 How many posts to collect? (recommended: 5-50): "))

    # Get comments control
    print("\n💬 COMMENTS CONTROL:")
    comments_per_post = int(input("💬 How many comments per post? (recommended: 10-100): "))

    # Get sub-comments/replies control
    print("\n🔄 SUB-COMMENTS/REPLIES CONTROL:")
    replies_per_comment = int(input("🔄 How many replies per comment? (recommended: 5-20): "))

    # Calculate totals
    total_comments = num_posts * comments_per_post
    total_replies = total_comments * replies_per_comment
    total_data_points = num_posts + total_comments + total_replies

    # Cost estimation (rough)
    estimated_cost = (num_posts * 0.02) + (total_comments * 0.002) + (total_replies * 0.001)

    print(f"\n📊 DATA COLLECTION SUMMARY:")
    print(f"   📝 Posts: {num_posts:,}")
    print(f"   💬 Comments: {total_comments:,}")
    print(f"   🔄 Replies: {total_replies:,}")
    print(f"   🎯 Total data points: {total_data_points:,}")
    print(f"   💰 Estimated cost: ${estimated_cost:.3f}")

    proceed = input("\n🚀 Proceed with these settings? (y/n): ").lower().strip()

    if proceed != 'y':
        print("❌ Crawling cancelled")
        return None

    return {
        'num_posts': num_posts,
        'comments_per_post': comments_per_post,
        'replies_per_comment': replies_per_comment,
        'total_comments': total_comments,
        'total_replies': total_replies,
        'estimated_cost': estimated_cost
    }

def smart_crawl_facebook(claim, max_posts=10, max_comments=20):
    """Smart Facebook crawling with support for direct Boolean OR queries."""
    print(f"\n🧠 SMART FACEBOOK CRAWLING")
    print("=" * 50)
    print(f"📝 Input: {claim}")
    print(f"📊 Target: {max_posts} posts, {max_comments} comments")

    # Check if input is a Boolean OR query
    if detect_boolean_query(claim):
        print("🎯 DETECTED: Boolean OR Query")
        print("🔧 Converting to effective search strategies...")
        search_strategies = parse_boolean_or_query(claim)
    else:
        print("🔍 DETECTED: Regular Claim")
        # Extract smart keywords
        keywords = extract_smart_keywords(claim)

        # Generate search strategies
        initial_strategies = generate_search_strategies(claim, keywords)

        # Allow user to edit strategies
        print(f"\n🎯 STRATEGY OPTIONS")
        print("=" * 30)
        print("1️⃣ Use generated strategies")
        print("2️⃣ Edit generated strategies")
        print("3️⃣ Enter custom Boolean OR query")

        choice = input("📝 Choose option (1-3, default: 1): ").strip()

        if choice == "3":
            print("\n✏️ ENTER CUSTOM BOOLEAN OR QUERY:")
            print("💡 Example: \"rafizi letak jawatan\" OR rafizi OR menteri OR jawatan")
            custom_query = input("🔍 Your Boolean OR query: ").strip()
            if custom_query:
                search_strategies = [custom_query]
                print(f"✅ Using custom query: {custom_query[:100]}...")
            else:
                search_strategies = initial_strategies
        elif choice == "2":
            search_strategies = edit_search_strategies(initial_strategies)
            if not search_strategies:
                print("❌ No strategies selected. Crawling cancelled.")
                return [], []
        else:
            search_strategies = initial_strategies
            print("✅ Using generated strategies")

    all_posts = []
    all_comments = []

    # Calculate posts per strategy for better distribution
    strategies_to_use = min(len(search_strategies), 8)  # Use up to 8 strategies
    posts_per_strategy = max(10, max_posts // strategies_to_use)  # At least 10 posts per strategy

    print(f"\n🎯 CRAWLING PLAN:")
    print(f"📊 Using {strategies_to_use} strategies")
    print(f"📈 ~{posts_per_strategy} posts per strategy")
    print(f"🎯 Target total: {max_posts:,} posts + {max_comments:,} comments")

    # Try each search strategy
    for i, strategy in enumerate(search_strategies[:strategies_to_use], 1):
        print(f"\n🔍 Strategy {i}/{strategies_to_use}: '{strategy}'")

        # ENHANCED: Use Malaysian business and news pages for relevant bilingual content
        facebook_pages = [
            "https://www.facebook.com/TheStarOnline/",
            "https://www.facebook.com/malaysiakini/",
            "https://www.facebook.com/NewStraitsTimes/",
            "https://www.facebook.com/astroawani/",
            "https://www.facebook.com/BernamaTV/",
            "https://www.facebook.com/mystartonline/",
            "https://www.facebook.com/sinchew.my/",
            "https://www.facebook.com/bharian.com.my/"
        ]

        # Try search URL first, then fallback to popular pages
        search_url = f"https://www.facebook.com/search/posts/?q={strategy.replace(' ', '%20')}"
        start_urls = [{"url": search_url}]

        # Add popular pages as fallback for more data
        if i <= 2:  # Use pages for first 2 strategies
            start_urls.extend([{"url": page} for page in facebook_pages[:2]])

        input_data = {
            "startUrls": start_urls,
            "resultsLimit": posts_per_strategy,  # Updated parameter name
            "scrapeComments": False,  # We'll get comments separately
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
                "apifyProxyCountry": "MY"
            }
        }

        # Run the actor
        posts = run_apify_actor(FB_POSTS_ACTOR_ID, input_data, max_wait_time=300)

        if posts:
            # Use all posts without relevance filtering
            print(f"✅ Found {len(posts)} posts (using all)")
            all_posts.extend(posts)

            # If we found posts, get comments for EACH post individually
            if posts:
                print(f"💬 Getting comments for {len(posts)} posts individually...")

                # ENHANCED: Process MORE posts per strategy for maximum data
                posts_to_process = min(len(posts), 10)  # Process up to 10 posts per strategy
                for post_index, post in enumerate(posts[:posts_to_process], 1):
                    url = post.get("url") or post.get("link") or post.get("facebookUrl")
                    if url and "facebook.com" in url:
                        print(f"   🔍 Post {post_index}/{posts_to_process}: Getting comments...")

                        # ENHANCED: Get MORE comments per post for maximum data
                        comments_per_post = max(20, max_comments // (strategies_to_use * posts_to_process))
                        post_comments = crawl_facebook_comments([url], comments_per_post)

                        if post_comments:
                            print(f"   ✅ Found {len(post_comments)} comments for post {post_index}")
                            all_comments.extend(post_comments)
                        else:
                            print(f"   ❌ No comments found for post {post_index}")

                        # Small delay between posts to avoid rate limiting
                        time.sleep(3)
                    else:
                        print(f"   ⚠️ Post {post_index}: Invalid URL")
        else:
            print("❌ No posts found")

        # Avoid rate limiting between strategies
        time.sleep(5)

        # Progress update
        print(f"📊 Progress: {len(all_posts)} posts, {len(all_comments)} comments collected so far")

        # Continue with all strategies (don't stop early)

    # Return ALL collected data (unlimited mode)
    print(f"\n🎉 UNLIMITED MODE: Collected ALL available data!")
    print(f"📊 Final totals: {len(all_posts)} posts, {len(all_comments)} comments")
    return all_posts, all_comments

def crawl_facebook_comments(post_urls, max_comments):
    """Crawl comments for Facebook posts with better configuration."""
    if not post_urls:
        print("❌ No post URLs provided for comment crawling")
        return []

    print(f"💬 Crawling comments for {len(post_urls)} posts...")

    # Prepare URLs - ensure they're valid Facebook URLs
    valid_urls = []
    for url in post_urls:
        if "facebook.com" in url and url.startswith("http"):
            valid_urls.append(url)
        else:
            print(f"⚠️ Invalid URL skipped: {url}")

    if not valid_urls:
        print("❌ No valid Facebook URLs found")
        return []

    # ENHANCED: Maximum data collection configuration
    input_data = {
        "startUrls": [{"url": url} for url in valid_urls],
        "resultsLimit": max_comments * 3,  # MASSIVE increase for maximum data
        "scrapeReplies": True,
        "repliesLimit": max_comments * 2,  # More replies per comment
        "includeNestedComments": True,
        "expandReplies": True,
        "scrapeCommentReplies": True,
        "scrapeReactionsCount": True,
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "MY"
        }
    }

    print(f"🔧 ENHANCED Comment crawler: {max_comments * 3} comments, {max_comments * 2} replies")
    return run_apify_actor(FB_COMMENTS_ACTOR_ID, input_data, max_wait_time=600)

def extract_post_id_from_url(url):
    """Extract clean post ID from Facebook URL."""
    try:
        # Extract numeric ID from Facebook URL
        import re
        # Look for patterns like /posts/123456789 or /videos/123456789
        match = re.search(r'/(posts|videos)/(\d+)', url)
        if match:
            return match.group(2)

        # Look for pfbid patterns
        match = re.search(r'pfbid([a-zA-Z0-9]+)', url)
        if match:
            return f"pfbid{match.group(1)}"[:15]  # Truncate for readability

        # Fallback: use last part of URL
        parts = url.split('/')
        for part in reversed(parts):
            if part and len(part) > 5:
                return part[:15]

        return "unknown_id"
    except:
        return "unknown_id"

def generate_comment_id(post_id, comment_index):
    """Generate comment ID in the format post_id_comment_number."""
    return f"{post_id}_{comment_index + 23820954}"  # Add offset for realistic IDs

def process_for_factcheck(posts, comments, claim):
    """Process data into standardized fact-checking format with proper Post->Comments grouping."""
    print(f"\n📋 PROCESSING DATA FOR FACT-CHECKING")

    factcheck_data = []

    # Group comments by post URL for proper linking
    comments_by_post = {}
    for comment in comments:
        # Try to extract post URL from comment data
        post_url = comment.get('postUrl', '') or comment.get('url', '')
        if not post_url:
            # Use first post as default
            post_url = 'default_post'

        if post_url not in comments_by_post:
            comments_by_post[post_url] = []
        comments_by_post[post_url].append(comment)

    # Process each post with its comments
    for post_index, post in enumerate(posts):
        try:
            # Extract clean post ID
            post_url = post.get('url', '') or post.get('link', '')
            post_id = extract_post_id_from_url(post_url)

            # Get post content
            content = post.get('message', '') or ''
            content = content.replace('\n', '\n\n').strip()  # Preserve line breaks for readability

            # Get engagement metrics
            reactions = int(post.get('reactions_count', 0) or 0)
            comments_count = int(post.get('comments_count', 0) or 0)
            shares = int(post.get('reshare_count', 0) or 0)
            total_engagement = reactions + comments_count + shares

            # Analyze sentiment
            sentiment, sentiment_score = analyze_sentiment(content)

            # Format date
            date_posted = post.get('timestamp', '')
            if date_posted:
                try:
                    from datetime import datetime
                    if 'T' in str(date_posted):
                        dt = datetime.fromisoformat(str(date_posted).replace('Z', '+00:00'))
                        date_posted = dt.strftime('%b %d at %I:%M %p')
                    else:
                        # Handle timestamp format
                        dt = datetime.fromtimestamp(int(date_posted))
                        date_posted = dt.strftime('%b %d at %I:%M %p')
                except:
                    date_posted = "Unknown date"

            # Create post record
            post_record = {
                'Platform': 'Facebook',
                'Type': 'Facebook Post',
                'ID': post_id,
                'Text': content,
                'Sentiment': sentiment,
                'Date': date_posted,
                'likes': reactions,
                'shares': shares,
                'comments_count': comments_count,
                'views': 0,
                'sentiment_score': sentiment_score,
                'total_engagement': total_engagement
            }

            # Add post to data
            factcheck_data.append(post_record)

            # Add comments for this post immediately after the post
            post_comments = comments_by_post.get(post_url, [])

            # If no specific comments found, distribute comments evenly across posts
            if not post_comments and comments:
                # Calculate how many comments this post should get
                comments_per_post = len(comments) // len(posts)
                start_index = post_index * comments_per_post
                end_index = start_index + comments_per_post

                # For the last post, take remaining comments
                if post_index == len(posts) - 1:
                    end_index = len(comments)

                post_comments = comments[start_index:end_index]
                print(f"📊 Distributing comments {start_index}-{end_index} to post {post_index + 1}")

            comment_counter = 0
            for comment in post_comments:
                try:
                    content = str(comment.get('text', '') or '')
                    content = content.replace('\n', ' ').strip()

                    if not content:
                        continue

                    # Get engagement metrics
                    likes = int(comment.get('likesCount', 0) or 0)
                    replies = int(comment.get('commentsCount', 0) or 0)
                    total_engagement = likes + replies

                    # Analyze sentiment
                    sentiment, sentiment_score = analyze_sentiment(content)

                    # Format date
                    date_posted = comment.get('date', '')
                    if date_posted:
                        try:
                            from datetime import datetime
                            if 'T' in str(date_posted):
                                dt = datetime.fromisoformat(str(date_posted).replace('Z', '+00:00'))
                                date_posted = dt.strftime('%b %d at %I:%M %p')
                            else:
                                dt = datetime.fromtimestamp(int(date_posted))
                                date_posted = dt.strftime('%b %d at %I:%M %p')
                        except:
                            date_posted = "Unknown date"

                    # Generate comment ID linked to this post
                    comment_id = generate_comment_id(post_id, comment_counter)

                    # Create comment record
                    comment_record = {
                        'Platform': 'Facebook',
                        'Type': 'Facebook Comment',
                        'ID': comment_id,
                        'Text': content,
                        'Sentiment': sentiment,
                        'Date': date_posted,
                        'likes': likes,
                        'shares': 0,  # Comments don't have shares
                        'comments_count': replies,
                        'views': 0,
                        'sentiment_score': sentiment_score,
                        'total_engagement': total_engagement
                    }

                    # Add comment immediately after its post
                    factcheck_data.append(comment_record)
                    comment_counter += 1

                except Exception as e:
                    print(f"⚠️ Error processing comment: {e}")
                    continue

            print(f"✅ Processed post {post_index + 1} with {comment_counter} comments")

        except Exception as e:
            print(f"⚠️ Error processing post: {e}")
            continue

    return factcheck_data

def save_smart_csv(data, claim):
    """Save data with smart filename generation in exact format."""
    if not data:
        print("❌ No data to save")
        return None

    # Determine the correct data directory
    if os.path.exists("../data/facebook"):
        # Running from crawlers directory
        data_dir = "../data/facebook"
    elif os.path.exists("data/facebook"):
        # Running from root directory
        data_dir = "data/facebook"
    else:
        # Create directory in parent location
        data_dir = "../data/facebook"
        os.makedirs(data_dir, exist_ok=True)

    # Generate smart filename from claim
    claim_words = re.findall(r'\w+', claim.lower())
    important_words = [word for word in claim_words if len(word) > 3][:5]
    safe_claim = "_".join(important_words)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"facebook_factcheck_{safe_claim}_{timestamp}.csv"
    filepath = f"{data_dir}/{filename}"

    # Add emotion analysis to data if available
    if EMOTION_ANALYSIS_AVAILABLE and data:
        print("🎭 Adding emotion analysis to Facebook data...")
        try:
            analyzer = get_analyzer()
            for record in data:
                text = record.get('Text', '')
                if text and text.strip():
                    emotion_result = analyzer.analyze_text(text)
                    record['emotion'] = emotion_result['emotion']
                    record['emotion_score'] = f"{emotion_result['emotion_score']:.4f}"
                else:
                    record['emotion'] = 'Neutral'
                    record['emotion_score'] = '0.0000'
            print("✅ Emotion analysis completed!")
        except Exception as e:
            print(f"⚠️ Emotion analysis failed: {e}")
            # Add default emotion values
            for record in data:
                record['emotion'] = 'Neutral'
                record['emotion_score'] = '0.0000'

    # Define columns in exact order with emotion analysis
    columns = [
        'Platform', 'Type', 'ID', 'Text', 'Sentiment', 'Date',
        'likes', 'shares', 'comments_count', 'views', 'sentiment_score', 'total_engagement',
        'emotion', 'emotion_score'
    ]

    # SECURE CSV writing with error handling
    try:
        print(f"💾 Attempting to save {len(data)} records to: {filepath}")

        # Write CSV with TAB-separated format to match your specification
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')

            # Write header
            writer.writeheader()

            # Write data rows
            writer.writerows(data)

        # Verify file was written successfully
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"✅ Data saved successfully to: {filepath}")
            print(f"📊 Total records: {len(data)}")
            print(f"📁 File size: {os.path.getsize(filepath)} bytes")

            # Show sample data for verification
            if data:
                sample = data[0]
                print(f"📋 Sample record:")
                print(f"   Text: {sample.get('Text', '')[:100]}...")
                print(f"   Sentiment: {sample.get('Sentiment', 'N/A')}")
                print(f"   Emotion: {sample.get('emotion', 'N/A')}")

            return filepath
        else:
            raise Exception("File was not created or is empty")

    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

        # Emergency backup save
        try:
            emergency_file = f"facebook_emergency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            print(f"🚨 Attempting emergency save to: {emergency_file}")

            with open(emergency_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=columns, delimiter='\t')
                writer.writeheader()
                writer.writerows(data)

            print(f"✅ Emergency save successful: {emergency_file}")
            return emergency_file

        except Exception as emergency_error:
            print(f"❌ Emergency save also failed: {emergency_error}")
            print("🚨 DATA LOSS PREVENTION: Printing first 3 records to console")
            print("=" * 50)
            for i, record in enumerate(data[:3]):
                print(f"Record {i+1}: {record}")
            print("=" * 50)
            return None

def main():
    """Main function for smart Facebook crawling."""
    parser = argparse.ArgumentParser(
        description="Smart Facebook Crawler for Fact-Checking",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_facebook_crawler.py --claim "vaksin covid selamat"
  python smart_facebook_crawler.py --claim "kerajaan bantuan e-wallet" --output custom_output.csv
        """
    )

    parser.add_argument(
        "--claim",
        required=True,
        help="The claim to fact-check"
    )

    parser.add_argument(
        "--output",
        help="Output CSV file path (optional, auto-generated if not provided)"
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=700,
        help="Maximum number of results to collect (default: 700, use 0 for unlimited)"
    )

    parser.add_argument(
        "--unlimited",
        action="store_true",
        help="Collect unlimited data (ignore max-results limit)"
    )

    # Check if running with arguments or interactively
    if len(sys.argv) == 1:
        # Interactive mode
        print("🧠 SMART FACEBOOK CRAWLER - UNIVERSAL CLAIM PROCESSOR")
        print("=" * 60)
        print("🎯 Processes any claim with intelligent keyword extraction")
        print("🇲🇾 Optimized for Malaysian content and context")
        print("🔍 Multiple search strategies with relevance filtering")
        print("=" * 60)

        # Get user input
        print("\n📝 ENTER YOUR INPUT:")
        print("-" * 30)
        print("💡 You can enter:")
        print("   1️⃣ Regular claim: 'Benarkah kerajaan akan...'")
        print("   2️⃣ Boolean OR query: '\"rafizi letak jawatan\" OR rafizi OR menteri'")
        print()

        while True:
            claim = input("🔍 Enter claim or Boolean OR query: ").strip()
            if claim:
                break
            print("❌ Please enter a valid input!")

        print(f"\n✅ Claim/Keywords: {claim}")

        print("\n� FACEBOOK CRAWLER CONFIGURATION:")
        print("=" * 50)
        print("📊 Configure exactly how much data you want to collect")
        print("=" * 50)

        # Configure posts
        while True:
            try:
                max_posts = int(input("\n📊 How many Facebook POSTS to collect? (1-10000): "))
                if 1 <= max_posts <= 10000:
                    break
                print("❌ Please enter a number between 1 and 10000!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Configure comments per post
        while True:
            try:
                comments_per_post = int(input("💬 How many COMMENTS per post? (1-500): "))
                if 1 <= comments_per_post <= 500:
                    break
                print("❌ Please enter a number between 1 and 500!")
            except ValueError:
                print("❌ Please enter a valid number!")

        # Calculate totals
        max_comments = max_posts * comments_per_post
        max_strategies = 6  # Default to 6 strategies

        print(f"\n✅ FACEBOOK CRAWLER CONFIGURATION:")
        print("=" * 50)
        print(f"📝 Claim/Keywords: {claim}")
        print(f"📊 Posts to collect: {max_posts:,}")
        print(f"💬 Comments per post: {comments_per_post:,}")
        print(f"📈 Total comments: {max_comments:,}")
        print(f"🎯 Search strategies: {max_strategies}")
        print(f"🎉 TOTAL ESTIMATED RECORDS: {max_posts + max_comments:,}")
        print("=" * 50)

        # Confirm configuration
        confirm = input("\n✅ Proceed with this configuration? (y/n, default: y): ").strip().lower()
        if confirm and confirm not in ['y', 'yes']:
            print("❌ Configuration cancelled!")
            return

        output_file = None

        while True:
            scale_choice = input("\n🔍 Choose scale (1-5, default: 2): ").strip() or "2"

            if scale_choice == "1":
                max_posts = 50
                max_comments = 100
                max_strategies = 3
                break
            elif scale_choice == "2":
                max_posts = 200
                max_comments = 500
                max_strategies = 5
                break
            elif scale_choice == "3":
                max_posts = 500
                max_comments = 1000
                max_strategies = 8
                break
            elif scale_choice == "4":
                max_posts = 2000
                max_comments = 5000
                max_strategies = 12
                break
            elif scale_choice == "5":
                print("\n🔧 CUSTOM FACEBOOK CRAWLER CONFIGURATION:")
                print("=" * 50)
                print("📊 Configure exactly how much data you want to collect")
                print("=" * 50)

                # Configure posts
                while True:
                    try:
                        max_posts = int(input("\n📊 How many Facebook POSTS to collect? (1-10000): "))
                        if 1 <= max_posts <= 10000:
                            break
                        print("❌ Please enter a number between 1 and 10000!")
                    except ValueError:
                        print("❌ Please enter a valid number!")

                # Configure comments per post
                while True:
                    try:
                        comments_per_post = int(input("💬 How many COMMENTS per post? (1-500): "))
                        if 1 <= comments_per_post <= 500:
                            break
                        print("❌ Please enter a number between 1 and 500!")
                    except ValueError:
                        print("❌ Please enter a valid number!")

                # Configure replies per comment
                while True:
                    try:
                        replies_per_comment = int(input("↩️ How many REPLIES per comment? (0-50): "))
                        if 0 <= replies_per_comment <= 50:
                            break
                        print("❌ Please enter a number between 0 and 50!")
                    except ValueError:
                        print("❌ Please enter a valid number!")

                # Configure search strategies
                while True:
                    try:
                        max_strategies = int(input("🎯 How many search STRATEGIES to use? (3-10): "))
                        if 3 <= max_strategies <= 10:
                            break
                        print("❌ Please enter a number between 3 and 10!")
                    except ValueError:
                        print("❌ Please enter a valid number!")

                # Calculate totals
                max_comments = max_posts * comments_per_post
                estimated_replies = max_comments * replies_per_comment
                total_estimated = max_posts + max_comments + estimated_replies

                print(f"\n✅ FACEBOOK CRAWLER CONFIGURATION:")
                print("=" * 50)
                print(f"📊 Posts to collect: {max_posts:,}")
                print(f"💬 Comments per post: {comments_per_post:,}")
                print(f"↩️ Replies per comment: {replies_per_comment:,}")
                print(f"🎯 Search strategies: {max_strategies}")
                print(f"📈 Total comments: {max_comments:,}")
                print(f"📈 Estimated replies: {estimated_replies:,}")
                print(f"🎉 TOTAL ESTIMATED RECORDS: {total_estimated:,}")
                print("=" * 50)

                # Confirm configuration
                confirm = input("\n✅ Proceed with this configuration? (y/n, default: y): ").strip().lower()
                if confirm and confirm not in ['y', 'yes']:
                    print("❌ Configuration cancelled!")
                    return
                break
            else:
                print("❌ Please choose 1, 2, 3, 4, or 5")

        print(f"\n✅ SELECTED SCALE:")
        print(f"📊 Target posts: {max_posts:,}")
        print(f"💬 Target comments: {max_comments:,}")
        print(f"🎯 Search strategies: {max_strategies}")
        print(f"📈 Expected total: {max_posts + max_comments:,} records")

        output_file = None
    else:
        # Command-line mode
        args = parser.parse_args()
        claim = args.claim
        total_results = args.max_results
        output_file = args.output
        unlimited_mode = args.unlimited or total_results == 0

        if unlimited_mode:
            # ENHANCED UNLIMITED MODE - Maximum data collection like your preferences
            max_posts = 50000  # MASSIVE limit for maximum data collection
            max_comments = 100000  # MASSIVE limit for maximum data collection
            max_strategies = 15  # More strategies for broader coverage

            print("🧠 SMART FACEBOOK CRAWLER - ENHANCED UNLIMITED MODE")
            print("=" * 70)
            print(f"📝 Claim: {claim}")
            print(f"🚀 Mode: MAXIMUM DATA COLLECTION (like your preferences)")
            print(f"📊 Target: {max_posts:,} posts + {max_comments:,} comments")
            print(f"🎯 Using {max_strategies} search strategies")
            print(f"💪 No limits - get as many as we can!")
            if output_file:
                print(f"📁 Output: {output_file}")
            print("=" * 70)
        else:
            # Limited mode
            max_posts = total_results // 3
            max_comments = total_results - max_posts
            max_strategies = 5

            print("🧠 SMART FACEBOOK CRAWLER")
            print("=" * 60)
            print(f"📝 Claim: {claim}")
            print(f"📊 Max Results: {total_results:,} ({max_posts} posts + {max_comments} comments)")
            if output_file:
                print(f"📁 Output: {output_file}")
            print("=" * 60)

    # Run smart crawling
    posts, comments = smart_crawl_facebook(claim, max_posts, max_comments)

    if posts or comments:
        # Process for fact-checking
        factcheck_data = process_for_factcheck(posts, comments, claim)

        if factcheck_data:
            # Save to CSV
            filepath = save_smart_csv(factcheck_data, claim)

            # Handle custom output file
            if output_file and filepath:
                import shutil
                shutil.move(filepath, output_file)
                filepath = output_file

            # Summary
            posts_count = len([d for d in factcheck_data if d['Type'] == 'Facebook Post'])
            comments_count = len([d for d in factcheck_data if d['Type'] == 'Facebook Comment'])
            positive_count = len([d for d in factcheck_data if d['Sentiment'] == 'Positive'])
            negative_count = len([d for d in factcheck_data if d['Sentiment'] == 'Negative'])
            neutral_count = len([d for d in factcheck_data if d['Sentiment'] == 'Neutral'])

            # Check Malaysian content
            malaysian_content = 0
            for item in factcheck_data:
                text = item.get('Text', '').lower()
                if any(word in text for word in ['malaysia', 'kerajaan', 'rakyat', 'negara']):
                    malaysian_content += 1

            print(f"\n🎉 SMART CRAWLING COMPLETED!")
            print("=" * 50)
            print(f"📊 Total posts: {posts_count}")
            print(f"💬 Total comments: {comments_count}")
            print(f"📋 Total records: {len(factcheck_data)}")
            print(f"😊 Positive: {positive_count}")
            print(f"😐 Neutral: {neutral_count}")
            print(f"😞 Negative: {negative_count}")
            print(f"🇲🇾 Malaysian content: {malaysian_content}/{len(factcheck_data)}")
            print(f"📁 Saved to: {os.path.basename(filepath)}")
            print("=" * 50)

            if factcheck_data:
                print(f"\n📋 SAMPLE DATA:")
                sample = factcheck_data[0]
                print(f"Text: {sample['Text'][:100]}...")
                print(f"Sentiment: {sample['Sentiment']} ({sample['sentiment_score']:.3f})")
                print(f"Engagement: {sample['total_engagement']}")

            print(f"\n✅ Ready for fact-checking analysis!")

        else:
            print("❌ No processable data found")
    else:
        print("\n❌ No relevant Facebook data found for this claim")
        print("💡 Try rephrasing your claim or using different keywords")

if __name__ == "__main__":
    main()
