#!/usr/bin/env python3
"""Generate a clean, editable DOCX for InsightPulse Proposal V3.1."""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


OUT = Path("/Users/rmtariq/Downloads/InsightPulse_Proposal_Strategik_2026_V3.1_Singapore_AI_Clinic_CLEAN_EDITABLE.docx")

NAVY = RGBColor(0, 51, 102)
GREEN = RGBColor(21, 128, 61)
SLATE = RGBColor(30, 41, 59)
GREY = RGBColor(100, 116, 139)


def set_run(run, *, bold=False, size=10, color=None):
    run.bold = bold
    run.font.name = "Arial"
    run.font.size = Pt(size)
    if color:
        run.font.color.rgb = color


def add_title(doc: Document):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("PROPOSAL PERKONGSIAN STRATEGIK\n")
    set_run(r, bold=True, size=20, color=NAVY)
    r = p.add_run("InsightPulse AI Platform\n")
    set_run(r, bold=True, size=16, color=GREEN)
    r = p.add_run("Penyelesaian Kecerdasan Buatan untuk Ekosistem PMKS Malaysia")
    set_run(r, size=12, color=SLATE)
    doc.add_paragraph()
    for label, val in [
        ("Dikemukakan kepada", "Agensi Pembiayaan & Pembangunan Usahawan Malaysia"),
        ("Dikemukakan oleh", "Fiscal Digest Sdn Bhd"),
        ("Tarikh", "Julai 2026"),
        ("Versi", "3.1 — SULIT"),
    ]:
        p = doc.add_paragraph()
        r = p.add_run(f"{label}: ")
        set_run(r, bold=True, size=10, color=NAVY)
        r = p.add_run(val)
        set_run(r, size=10)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('"Memantau. Memahami. Memperkasa Usahawan Malaysia."')
    set_run(r, bold=True, size=11, color=GREEN)
    doc.add_page_break()


def h1(doc, text):
    p = doc.add_heading(text, level=1)
    for r in p.runs:
        set_run(r, bold=True, size=15, color=NAVY)


def h2(doc, text):
    p = doc.add_heading(text, level=2)
    for r in p.runs:
        set_run(r, bold=True, size=12, color=GREEN)


def para(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.08
    for r in p.runs:
        set_run(r, size=10, color=SLATE)
    return p


def bullet(doc, text):
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    for r in p.runs:
        set_run(r, size=10, color=SLATE)


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    hdr = table.rows[0].cells
    for i, head in enumerate(headers):
        hdr[i].text = head
        hdr[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        for p in hdr[i].paragraphs:
            for r in p.runs:
                set_run(r, bold=True, size=9, color=NAVY)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            cells[i].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            for p in cells[i].paragraphs:
                p.paragraph_format.space_after = Pt(1)
                for r in p.runs:
                    set_run(r, size=8.5, color=SLATE)
    if widths:
        for row in table.rows:
            for idx, w in enumerate(widths):
                row.cells[idx].width = Inches(w)
    doc.add_paragraph()
    return table


def build_doc():
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.65)
    sec.bottom_margin = Inches(0.65)
    sec.left_margin = Inches(0.75)
    sec.right_margin = Inches(0.75)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)

    add_title(doc)

    h1(doc, "1. Ringkasan Eksekutif")
    para(doc, "InsightPulse ialah platform kecerdasan buatan (AI) tempatan Malaysia yang menyediakan pemantauan media sosial secara masa nyata, analitik sentimen, dan papan pemuka pintar untuk membantu Perusahaan Mikro, Kecil dan Sederhana (PMKS) memahami pelanggan, memperkukuh jenama dan membuat keputusan berasaskan data.")
    para(doc, "Melalui cadangan ini, InsightPulse menawarkan perkongsian strategik dengan agensi pembangunan usahawan utama di Malaysia sebagai Pembekal Penyelesaian Teknologi (TSP), rakan program pembangunan keusahawanan, serta alat pemantauan portfolio institusi.")
    h2(doc, "Nilai Utama InsightPulse kepada Ekosistem PMKS")
    for b in [
        "Membantu PMKS memahami sentimen pelanggan dan meningkatkan perkhidmatan pelanggan melalui AI.",
        "Memperkukuh jenama digital PMKS menerusi data dan strategi berasaskan bukti.",
        "Membekalkan agensi pembiaya dengan intelligence untuk pantau prestasi dan keupayaan client PMKS.",
        "Mengenal pasti industri dan sektor berisiko atau berpotensi tinggi secara automatik.",
        "Produk AI tempatan Malaysia — menyokong agenda kedaulatan digital dan teknologi Bumiputera.",
    ]:
        bullet(doc, b)

    h1(doc, "2. Latar Belakang InsightPulse")
    h2(doc, "2.1 Profil Syarikat")
    add_table(doc, ["Perkara", "Maklumat"], [
        ["Nama Syarikat", "FISCAL DIGEST SDN. BHD."],
        ["Lokasi", "Cyberjaya, Selangor Darul Ehsan, Malaysia"],
        ["Bidang Teras", "AI Social Listening, Analitik Sentimen, Business Intelligence"],
        ["Teknologi Utama", "Large Language Models (LLM), NLP Bahasa Melayu/Inggeris, FastAPI, Dashboard Interaktif"],
        ["Platform Sosial / E-Dagang / Web", "X (Twitter), Facebook, TikTok, Instagram, Threads, News dan platform berkaitan"],
        ["Pasaran Sasaran", "PMKS Malaysia, Institusi Kewangan, Agensi Kerajaan"],
        ["Model Perniagaan", "SaaS — Langganan Bulanan & Pakej Institusi"],
    ], [2.0, 4.8])
    h2(doc, "2.2 Keupayaan Teknikal")
    add_table(doc, ["Ciri / Modul", "Penerangan"], [
        ["Pemantauan Masa Nyata", "Memantau platform media sosial dan e-dagang untuk mengesan sebutan jenama, trend industri dan maklum balas pelanggan."],
        ["Analitik Sentimen AI", "Model NLP khusus Bahasa Melayu dan Inggeris untuk memahami konteks, sarkasme dan slanga tempatan."],
        ["Dashboard / Laporan PMKS Pintar", "Papan pemuka mudah difahami agar usahawan boleh membaca data dan mengambil tindakan segera."],
        ["Pemantauan Pesaing", "Bandingkan prestasi jenama PMKS berbanding pesaing dalam industri yang sama."],
        ["Laporan Industri Automatik", "Jana laporan trend industri mengikut sektor secara berkala."],
        ["Portfolio Intelligence", "Dashboard khas untuk institusi pantau kesihatan digital dan reputasi portfolio client PMKS."],
        ["Alert & Notifikasi", "Makluman segera apabila berlaku krisis reputasi, sentimen negatif mendadak atau peluang viral."],
        ["Integrasi API", "Boleh disambungkan dengan CRM, sistem penilaian kredit dan portal usahawan."],
    ], [2.2, 4.6])

    h1(doc, "3. Peta Agensi Sasaran & Nilai InsightPulse")
    add_table(doc, ["Agensi / Institusi", "Fokus Utama", "Nilai InsightPulse", "Mod Kerjasama"], [
        ["MDEC", "Digitalisasi & Ekosistem Teknologi Malaysia", "TSP bertauliah — SME client boleh claim Geran Digital PMKS sehingga RM5,000.", "Daftar sebagai TSP MDEC"],
        ["SME Bank", "Pembiayaan & Pembangunan Keupayaan PMKS", "Dashboard portfolio — pantau reputasi digital dan prestasi borrower PMKS.", "Strategic Tech Partner"],
        ["PUNB", "Pemerkasaan Usahawan Bumiputera", "Analitik industri untuk kenal pasti sektor trending bagi usahawan Bumiputera.", "Program Pembangunan Usahawan"],
        ["MARA", "Pendidikan & Keusahawanan Bumiputera", "Alat pemantauan jenama untuk usahawan MARA & program GTG.", "Rakan Program Usahawan"],
        ["TEKUN Nasional", "Pembiayaan Mikro Usahawan Grassroot", "Dashboard mudah untuk usahawan mikro pantau reputasi dan sentimen pelanggan.", "Program Digitalisasi Usahawan"],
        ["Amanah Ikhtiar Malaysia", "Pembiayaan Wanita & B40", "Alat pemasaran digital berasaskan data untuk Sahabat AIM meningkatkan jualan.", "Program Pembangunan Kapasiti"],
        ["SME Corp Malaysia", "Dasar & Pembangunan Ekosistem PMKS", "Data industri dan benchmark untuk dasar pembangunan PMKS kebangsaan.", "Rakan Data Intelligence"],
        ["Agrobank", "Pembiayaan Agro & Makanan", "Pantau sentimen produk agro-makanan di media sosial dan marketplace.", "TSP / Tech Partner"],
        ["BSN", "Perbankan Inklusif & Pembiayaan Mikro", "Platform AI untuk perkasa usahawan PMKS BSN dalam pemasaran digital dan jualan online.", "Program Peningkatan Kapasiti"],
    ], [1.25, 1.55, 2.55, 1.45])

    h1(doc, "4. Model Perkongsian yang Dicadangkan")
    h2(doc, "4.1 Mod A — InsightPulse sebagai TSP Bertauliah")
    for b in [
        "PMKS client agensi boleh menggunakan geran 50% untuk melanggan InsightPulse.",
        "Agensi boleh mengesyorkan InsightPulse sebagai alat digitalisasi kepada PMKS binaan.",
        "InsightPulse bertindak sebagai vendor sah dalam ekosistem program bantuan kerajaan.",
        "Memudahkan onboarding PMKS baharu yang belum mampu melanggan tanpa subsidi.",
    ]:
        bullet(doc, b)
    h2(doc, "4.2 Mod B — Platform Pemantauan Portfolio Institusi")
    for b in [
        "Dashboard portfolio menunjukkan kesihatan digital setiap client PMKS.",
        "Agensi boleh mengenal pasti awal PMKS yang berdepan risiko reputasi atau kehilangan pelanggan.",
        "Kenal pasti PMKS berprestasi tinggi untuk program naik taraf atau pembiayaan lanjutan.",
        "Data boleh diintegrasikan dengan sistem penilaian kredit atau profiling sedia ada.",
    ]:
        bullet(doc, b)
    h2(doc, "4.3 Mod C — Program Pembangunan Keusahawanan")
    for b in [
        "Bengkel Bina Jenama Digital dengan AI — hands-on untuk usahawan PMKS.",
        "Slot taklimat dalam Sesi Bincang Niaga, seminar usahawan dan program agensi.",
        "Demo langsung platform InsightPulse kepada peserta program.",
        "Modul e-learning pemasaran digital berasaskan data.",
    ]:
        bullet(doc, b)
    para(doc, "Ringkasan: Mod A = TSP; Mod B = portfolio intelligence; Mod C = rakan bengkel dan pembangunan kapasiti. Ketiga-tiga mod boleh berjalan serentak.")

    h1(doc, "5. Struktur Harga & Pakej")
    add_table(doc, ["Perkara", "Pelan Asas", "Pelan Profesional", "Pelan Institusi"], [
        ["Sasaran", "PMKS Kecil", "PMKS Sederhana", "Agensi / Bank / DFI"],
        ["Harga Bulanan", "RM650", "RM2,100", "Harga Khas Institusi"],
        ["Pemantauan Media Sosial", "1 platform", "3+ platform", "Multi-platform"],
        ["Analitik Sentimen AI", "✓", "✓", "✓"],
        ["Dashboard Industri", "—", "✓", "✓"],
        ["Portfolio Monitoring", "—", "—", "✓"],
        ["Laporan Custom", "—", "✓", "✓"],
        ["API Integration", "—", "—", "✓"],
        ["Sokongan Dedikasi", "—", "—", "✓"],
    ], [1.8, 1.5, 1.7, 1.7])

    h1(doc, "6. Faedah & Impak Jangkaan")
    h2(doc, "6.1 Faedah kepada PMKS")
    for b in [
        "Mengurangkan kos kajian pasaran melalui data sentimen pelanggan masa nyata.",
        "Meningkatkan jualan melalui strategi pemasaran disokong data.",
        "Mengesan krisis reputasi awal sebelum menjadi isu besar.",
        "Memahami tren industri dan peluang pasaran yang belum diterokai.",
        "Meningkatkan keyakinan usahawan membuat keputusan berasaskan fakta.",
    ]:
        bullet(doc, b)
    h2(doc, "6.2 Faedah kepada Agensi & Institusi")
    for b in [
        "Pemantauan portfolio yang lebih cekap — satu paparan untuk ratusan client PMKS.",
        "Pengesanan awal PMKS berisiko sebelum berlaku kemungkiran atau penutupan perniagaan.",
        "Data industri berasaskan AI untuk menyokong program dan dasar.",
        "Meningkatkan kadar kejayaan PMKS binaan melalui data literacy.",
        "Memperkukuh imej agensi sebagai pelopor digitalisasi PMKS.",
        "Memenuhi KPI digitalisasi PMKS yang disasarkan kementerian.",
    ]:
        bullet(doc, b)

    h2(doc, "6.3 Penjajaran dengan Agenda Nasional")
    add_table(doc, ["Agenda Nasional", "Bagaimana InsightPulse Menyokong"], [
        ["Pelan Induk PMKS 2030", "Menyokong sasaran digitalisasi PMKS dan peningkatan produktiviti berasaskan teknologi."],
        ["Malaysia MADANI — Ekonomi", "Memperkasa usahawan Bumiputera dan B40 melalui akses kepada alat AI mampu milik."],
        ["Dasar Industri Baru 4.0 (NIMP)", "Mempercepat penggunaan AI dalam operasi perniagaan PMKS."],
        ["Strategi Digital Nasional", "Meningkatkan literasi digital PMKS dan penggunaan data dalam perniagaan."],
        ["PowerUp10K KUSKOP", "Melengkapkan program pembiayaan dengan alat untuk pastikan PMKS berjaya menggunakan modal."],
        ["SME SRF BNM", "Menambah nilai kepada PMKS penerima pembiayaan dengan sokongan intelligence."],
    ], [2.2, 4.6])

    h2(doc, "6.4 Pemerhatian Pasaran: Singapore AI Discovery Clinic")
    para(doc, "Singapura melalui Singapore Artificial Intelligence Association (SAIA) dilaporkan melancarkan AI Discovery Clinic sebagai pendekatan baharu untuk membantu SME mengenal pasti bagaimana AI boleh digunakan dalam operasi sebenar. Pendekatan ini tidak bermula dengan geran atau pembelian tool, tetapi dengan diagnosis pain point, pemetaan use case dan cadangan tindakan.")
    para(doc, "Isyarat pasaran ini penting: rantau ini sedang bergerak daripada model “beli software dahulu” kepada model diagnose dahulu, bina use case, kemudian deploy penyelesaian. Ini selari dengan cara InsightPulse mahu dibawa ke ekosistem PMKS Malaysia.")
    add_table(doc, ["Model AI Discovery Clinic", "Kedudukan InsightPulse"], [
        ["Advisory / diagnosis: Expert bantu SME kenal pasti masalah sebenar seperti invoice, customer query, lead generation, pemasaran, reputasi atau workflow.", "Advisory + platform sebenar: selepas diagnosis, SME boleh terus menggunakan dashboard live, social listening, sentiment analysis dan laporan tindakan."],
        ["Use case mapping: hasil utama ialah cadangan use case AI yang sesuai dengan pain point SME.", "Use case + execution layer: InsightPulse menterjemah use case kepada monitoring sebenar — brand mention, competitor signal, customer feedback, risiko reputasi dan peluang viral."],
        ["Tiada platform nasional khusus: model clinic berfungsi sebagai front-end advisory kepada ekosistem.", "Platform Malaysia-ready: InsightPulse boleh menjadi enjin teknologi di belakang program seumpama AI Discovery Clinic Malaysia untuk PMKS dan agensi."],
    ], [3.25, 3.55])
    h2(doc, "Strategic Play untuk Malaysia")
    for b in [
        "Jangan compete dengan konsep clinic — InsightPulse melengkapkan model itu sebagai platform selepas diagnosis.",
        "Positioning baharu: AI Discovery + Live Intelligence Platform untuk PMKS Malaysia.",
        "Untuk agensi: bukan hanya bengkel AI, tetapi sistem untuk pantau outcome selepas program.",
        "Untuk SME: mula dengan satu pain point sebenar, kemudian deploy dashboard yang boleh diukur.",
        "Untuk Fiscal / InsightPulse: masuk sebagai TSP, rakan clinic dan enjin analytics.",
    ]:
        bullet(doc, b)
    h2(doc, "Cadangan Program Tambahan: AI Discovery + InsightPulse Pilot")
    add_table(doc, ["Komponen", "Output"], [
        ["Sesi diagnosis 60–90 minit bersama PMKS", "Pain point sebenar + AI use case priority."],
        ["Setup InsightPulse dashboard mini", "Pantau brand, pelanggan, pesaing dan isu industri."],
        ["Laporan tindakan 30 hari", "Senarai tindakan pemasaran, reputasi dan pelanggan."],
        ["Portfolio view untuk agensi", "Agensi boleh ukur adoption, risiko dan outcome PMKS."],
    ], [3.0, 3.8])
    para(doc, "Kesimpulan: Jika Malaysia mengadaptasi model AI Discovery Clinic seperti Singapura, InsightPulse boleh diposisikan sebagai platform rujukan tempatan yang menukar sesi diagnosis kepada tindakan data-driven dan dashboard yang boleh dipantau oleh PMKS serta agensi.")

    h1(doc, "7. Pelan Pelaksanaan")
    add_table(doc, ["Fasa", "Tempoh", "Aktiviti Utama", "Output"], [
        ["Fasa 1", "1 Bulan", "Pembentangan proposal, perbincangan MOU/LOI, pengesahan keperluan teknikal agensi.", "LOI / MOU ditandatangani"],
        ["Fasa 2", "1 Bulan", "Integrasi API jika perlu, persediaan dashboard institusi, latihan pegawai agensi, co-branding.", "Dashboard institusi live"],
        ["Fasa 3", "2–4 Minggu", "Pelancaran program, Sesi Bincang Niaga pertama bersama agensi, onboarding PMKS pilot.", "Program berlancaran"],
        ["Fasa 4", "6 Bulan", "Pengembangan ke lebih banyak PMKS, integrasi latihan agensi, kajian impak dan laporan.", "Laporan impak 6 bulan"],
    ], [1.0, 1.2, 3.4, 1.3])

    h1(doc, "8. Sokongan yang Diperlukan daripada Agensi")
    for b in [
        "Pengiktirafan status sebagai TSP / Rakan Teknologi Bertauliah agensi.",
        "Akses program untuk menyertai bengkel, Sesi Bincang Niaga dan seminar usahawan.",
        "Rujukan PMKS binaan agensi kepada InsightPulse sebagai alat digitalisasi.",
        "Perkongsian data agregat tanpa PII untuk penambahbaikan model AI.",
        "Co-branding dengan agensi rakan dalam bahan pemasaran dan platform.",
        "Kelulusan kajian rintis 1 hingga 3 bulan bersama kumpulan PMKS binaan agensi.",
    ]:
        bullet(doc, b)

    h1(doc, "9. Kelebihan Daya Saing InsightPulse")
    for b in [
        "Platform tempatan Malaysia — memahami budaya, bahasa dan pasaran Malaysia.",
        "Model AI dilatih khusus untuk Bahasa Melayu termasuk slanga, dialek dan code-switching.",
        "Kos lebih rendah berbanding platform global seperti Brandwatch, Meltwater atau Sprinklr.",
        "Sokongan pelanggan dalam Bahasa Malaysia.",
        "Data disimpan dalam Malaysia — pematuhan PDPA dan data sovereignty.",
        "Syarikat Bumiputera — sejajar agenda pemerkasaan teknologi Bumiputera.",
        "Boleh customize mengikut keperluan agensi — bukan produk one-size-fits-all.",
    ]:
        bullet(doc, b)

    h1(doc, "10. Penutup & Jemputan Tindakan")
    para(doc, "Kejayaan PMKS Malaysia bukan sekadar bergantung kepada modal kewangan tetapi kepada keupayaan memahami pasaran, pelanggan dan persaingan dengan tepat. Di sinilah AI dan data menjadi penyama rata yang berkuasa.")
    para(doc, "Melalui perkongsian strategik ini, Fiscal dan agensi rakan dapat bersama-sama membina ekosistem PMKS yang lebih kuat, lebih celik data dan lebih berdaya saing.")
    h2(doc, "Tindakan Seterusnya")
    for b in [
        "Hubungi Fiscal untuk perbincangan awal tanpa komitmen.",
        "Fiscal bersedia untuk demo langsung platform kepada pasukan agensi.",
        "LOI boleh dimeterai sebagai permulaan kerjasama formal.",
        "Kajian rintis percuma selama 1 bulan boleh dimulakan selepas persetujuan.",
    ]:
        bullet(doc, b)
    h2(doc, "Hubungi Kami")
    para(doc, "Fiscal Digest Sdn Bhd | Cyberjaya, Selangor Darul Ehsan")
    para(doc, "Email: rmtariq@gmail.com; rmtariq@fiscald.com | Web: www.insightpulse.my")
    para(doc, "Dokumen ini adalah SULIT dan hanya untuk kegunaan agensi yang ditujukan sahaja.")

    for section in doc.sections:
        footer = section.footer.paragraphs[0]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = footer.add_run("InsightPulse | Proposal Perkongsian Strategik 2026 | SULIT")
        set_run(run, size=8, color=GREY)

    doc.save(str(OUT))


if __name__ == "__main__":
    build_doc()
    print(f"Saved: {OUT}")
