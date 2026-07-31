"""Design tokens — colours, gradients, chart palette."""

PRIMARY = "#2563eb"
SECONDARY = "#7c3aed"
ACCENT = "#06b6d4"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
CRITICAL = "#ef4444"
NEUTRAL_BG = "#f8fafc"
NEUTRAL_CARD = "#ffffff"
NEUTRAL_TEXT = "#0f172a"
NEUTRAL_MUTED = "#64748b"

GRADIENTS = {
    "header": "linear-gradient(135deg, #2563eb 0%, #7c3aed 55%, #06b6d4 100%)",
    "exec": "linear-gradient(135deg, #eff6ff 0%, #f5f3ff 50%, #ecfeff 100%)",
    "chinese": "linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)",
    "indian": "linear-gradient(135deg, #f5f3ff 0%, #fef3c7 100%)",
    "cross": "linear-gradient(135deg, #ecfeff 0%, #dbeafe 100%)",
    "btn": "linear-gradient(135deg, #2563eb 0%, #06b6d4 100%)",
}

CHART_COLORS = ["#2563eb", "#7c3aed", "#06b6d4", "#f43f5e", "#f59e0b", "#22c55e", "#a855f7", "#64748b"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, system-ui, sans-serif", color="#334155", size=12),
    margin=dict(l=12, r=12, t=48, b=12),
    colorway=CHART_COLORS,
)

PLOTLY_CHART_CONFIG = {"displayModeBar": False, "responsive": True}

STATUS_BADGE = {
    "HIJAU": ("Stabil", "badge-success"),
    "KUNING": ("Perlu Perhatian", "badge-warning"),
    "JINGGA": ("Tindakan Diperlukan", "badge-orange"),
    "MERAH": ("Kritikal", "badge-critical"),
    "biru": ("Sedang Dilaksanakan", "badge-info"),
    "kelabu": ("Belum Bermula", "badge-neutral"),
    "selesai": ("Selesai", "badge-success"),
    "lewat": ("Lewat", "badge-late"),
}

PRIORITY_COLORS = {
    "P1": "#ef4444",
    "P2": "#f59e0b",
    "P3": "#2563eb",
    "Pantau": "#64748b",
}

# Approximate district centroids for map markers
DISTRICT_COORDS: dict[str, tuple[float, float]] = {
    "Seremban": (2.7297, 101.9381),
    "Jempol": (2.9100, 102.3900),
    "Jelebu": (2.9400, 102.0900),
    "Port Dickson": (2.5228, 101.7960),
    "Kuala Pilah": (2.7389, 102.2486),
    "Tampin": (2.4700, 102.2300),
    "Rembau": (2.5900, 102.0900),
    "Johor Bahru": (1.4927, 103.7414),
    "Skudai": (1.5378, 103.6574),
    "Kluang": (2.0305, 103.3200),
    "Batu Pahat": (1.8548, 102.9325),
    "Muar": (2.0442, 102.5689),
    "Melaka": (2.1896, 102.2501),
    "Alor Gajah": (2.3800, 102.2100),
    "Jasin": (2.3100, 102.4300),
}
