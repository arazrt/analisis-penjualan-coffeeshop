import io
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ----------------------------------------------------------------------------
# Konfigurasi
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Coffee Shop Sales",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded", # Diubah agar sidebar filter langsung terlihat
)

FILE_NAME = "coffee-shop-sales-revenue.csv"
KOLOM_WAJIB = {
    "transaction_id", "transaction_date", "transaction_time", "transaction_qty",
    "store_id", "store_location", "product_id", "unit_price",
    "product_category", "product_type", "product_detail",
}
HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

# Palet dashboard gelap
TEAL = "#01B8AA"
GELAP = "#8bcac5"
KUNING = "#F2C80F"
MERAH = "#ff7b72"
ABU = "#aab4c0"
FONT = "Segoe UI, -apple-system, system-ui, sans-serif"

DIM = {
    "month": ("month_label", "x"),
    "store": ("store_location", "y"),
    "category": ("product_category", "y"),
    "hour": ("hour", "x"),
}
NAMA_DIM = {"month": "Bulan", "store": "Toko", "category": "Kategori", "hour": "Jam"}

CSS = f"""
<style>
.stApp {{ background: #0e1117; color: #f0f3f6; font-family: {FONT}; }}
.block-container {{ padding-top: 2rem; padding-bottom: 2rem; max-width: 1600px; }}
footer {{ visibility: hidden; }}
header[data-testid="stHeader"] {{ background: transparent; }}

[data-testid="stVerticalBlockBorderWrapper"] {{
    border: 1px solid #303a46 !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.22) !important;
    background-color: #161b22 !important;
}}

.hdr {{ background: #161b22; color: #f0f3f6; padding: 20px 24px; border-radius: 8px;
       border: 1px solid #303a46; border-left: 8px solid {TEAL};
       box-shadow: 0 4px 12px rgba(0,0,0,0.22); margin-bottom: 16px; }}
.hdr-title {{ font-size: 1.8rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.5px; }}
.hdr-sub {{ font-size: 0.9rem; color: {ABU}; margin-top: 4px; }}

.vt {{ font-size: 1.05rem; font-weight: 600; color: #f0f3f6; margin: 0 0 2px 2px; }}
.vs {{ font-size: 0.8rem; color: {ABU}; margin: 0 0 12px 2px; }}

.kpi-container {{ display: flex; gap: 1rem; margin-bottom: 1rem; }}
.kpi {{ flex: 1; background: #1c232d; border: 1px solid #303a46; border-radius: 8px; padding: 16px 20px;
       box-shadow: 0 4px 12px rgba(0,0,0,0.18); border-top: 4px solid {TEAL}; }}
.kpi-label {{ font-size: 0.85rem; font-weight: 500; color: #aab4c0; text-transform: uppercase; letter-spacing: 0.5px; }}
.kpi-value {{ font-size: 2.2rem; font-weight: 700; color: #f0f3f6; line-height: 1.3; margin: 4px 0; }}
.kpi-delta {{ font-size: 0.85rem; font-weight: 500; display: flex; align-items: center; gap: 4px; }}
.up {{ color: #7ee787; background: #173323; padding: 2px 8px; border-radius: 12px; }}
.down {{ color: #ff938a; background: #3a2024; padding: 2px 8px; border-radius: 12px; }}
.flat {{ color: {ABU}; }}

.chip {{ display: inline-block; background: #12302f; border: 1px solid {TEAL}; color: #76e3d8;
        border-radius: 16px; padding: 4px 12px; margin: 0 8px 8px 0; font-size: 0.85rem; font-weight: 500; }}
.chip-none {{ color: {ABU}; font-size: 0.85rem; font-style: italic; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
CFG = {"displayModeBar": False}

# ----------------------------------------------------------------------------
# Data (Sama dengan sumber asli)
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner="Memuat dan menyiapkan data...")
def muat_data(mentah: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(mentah), sep="|")
    kurang = KOLOM_WAJIB - set(df.columns)
    if kurang:
        raise ValueError(f"Kolom berikut tidak ditemukan: {', '.join(sorted(kurang))}")

    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["hour"] = pd.to_datetime(df["transaction_time"], format="%H:%M:%S").dt.hour
    df["revenue"] = df["transaction_qty"] * df["unit_price"]
    df["month"] = df["transaction_date"].dt.to_period("M").dt.to_timestamp()
    df["month_label"] = df["month"].dt.strftime("%b %Y")
    df["weekday"] = pd.Categorical(
        df["transaction_date"].dt.dayofweek.map(dict(enumerate(HARI))),
        categories=HARI, ordered=True,
    )
    return df

def ambil_sumber() -> bytes | None:
    for p in (Path(__file__).parent / FILE_NAME, Path(__file__).parent / "data" / FILE_NAME):
        if p.exists():
            return p.read_bytes()
    st.warning(f"File `{FILE_NAME}` tidak ditemukan. Unggah file CSV (pemisah `|`).")
    unggahan = st.file_uploader("File CSV", type="csv")
    return unggahan.getvalue() if unggahan else None

mentah = ambil_sumber()
if mentah is None: st.stop()
try:
    data = muat_data(mentah)
except Exception as e:
    st.error(f"Data tidak bisa dibaca. {e}")
    st.stop()

# ----------------------------------------------------------------------------
# State & Filter 
# ----------------------------------------------------------------------------
if "xf" not in st.session_state: st.session_state.xf = {d: [] for d in DIM}
if "reset_n" not in st.session_state: st.session_state.reset_n = 0

def reset_filter() -> None:
    st.session_state.xf = {d: [] for d in DIM}
    st.session_state.reset_n += 1

def nilai_dari_titik(titik: list, dim: str, sumbu: str) -> list:
    nilai = [int(t.get(sumbu)) if dim == "hour" else t.get(sumbu) for t in titik if t.get(sumbu) is not None]
    return list(dict.fromkeys(nilai))

def sinkron(dim: str, kunci: str, sumbu: str) -> None:
    try: titik = st.session_state[kunci]["selection"]["points"]
    except Exception: titik = []
    st.session_state.xf[dim] = nilai_dari_titik(titik, dim, sumbu)

def terapkan(frame: pd.DataFrame, kecuali: str | None = None) -> pd.DataFrame:
    for d, (kolom, _) in DIM.items():
        pilih = st.session_state.xf[d]
        if d != kecuali and pilih: frame = frame[frame[kolom].isin(pilih)]
    return frame

# ----------------------------------------------------------------------------
# Sidebar Slicer (Dipindahkan ke Sidebar ala Power BI)
# ----------------------------------------------------------------------------
tgl_min, tgl_maks = data["transaction_date"].min().date(), data["transaction_date"].max().date()
daftar_toko = sorted(data["store_location"].unique())
daftar_kategori = data.groupby("product_category")["revenue"].sum().sort_values(ascending=False).index.tolist()
jam_min, jam_maks = int(data["hour"].min()), int(data["hour"].max())

with st.sidebar:
    st.markdown("### 🎛️ Filter Panel")
    rentang = st.date_input("Rentang Tanggal", value=(tgl_min, tgl_maks), min_value=tgl_min, max_value=tgl_maks)
    toko_dipilih = st.multiselect("Lokasi Toko", daftar_toko, default=daftar_toko)
    kategori_dipilih = st.multiselect("Kategori Produk", daftar_kategori, default=daftar_kategori)
    jam_dipilih = st.slider("Jam Operasional", jam_min, jam_maks, (jam_min, jam_maks))
    
    st.markdown("---")
    st.caption(f"Total Toko: {data['store_location'].nunique()} | Mata uang: USD")

if not isinstance(rentang, (tuple, list)) or len(rentang) != 2: st.stop()

base = data[
    data["transaction_date"].between(pd.Timestamp(rentang[0]), pd.Timestamp(rentang[1]))
    & data["store_location"].isin(toko_dipilih)
    & data["product_category"].isin(kategori_dipilih)
    & data["hour"].between(*jam_dipilih)
]

if base.empty:
    st.warning("Tidak ada data untuk kombinasi filter ini.")
    st.stop()

for d, (kolom, _) in DIM.items():
    ada = set(base[kolom].unique())
    st.session_state.xf[d] = [v for v in st.session_state.xf[d] if v in ada]

df = terapkan(base)
if df.empty:
    st.warning("Kombinasi klik grafik ini tidak memiliki data.")
    st.stop()

# ----------------------------------------------------------------------------
# Header Utama & Indikator Filter Aktif
# ----------------------------------------------------------------------------
st.markdown(
    f"""<div class="hdr">
        <div class="hdr-title">☕ Performa Penjualan Coffee Shop</div>
        <div class="hdr-sub">Periode Analisis: {tgl_min:%d %b %Y} - {tgl_maks:%d %b %Y}</div>
    </div>""", unsafe_allow_html=True
)

c_chip, c_reset = st.columns([6, 2])
aktif = [f"{NAMA_DIM[d]}: {', '.join(map(str, v))}" for d, v in st.session_state.xf.items() if v]
if aktif:
    c_chip.markdown("".join(f'<span class="chip">{a}</span>' for a in aktif), unsafe_allow_html=True)
else:
    c_chip.markdown('<span class="chip-none">💡 Klik batang pada grafik untuk melihat rincian spesifik (Cross-filtering).</span>', unsafe_allow_html=True)
c_reset.button(
    "Reset Filter",
    icon="🔄",
    help="Hapus semua filter yang dipilih lewat grafik",
    on_click=reset_filter,
    disabled=not aktif,
    use_container_width=True,
)
st.write("")

# ----------------------------------------------------------------------------
# Kartu KPI (Flexbox Layout)
# ----------------------------------------------------------------------------
bln = df.groupby("month", as_index=False).agg(
    revenue=("revenue", "sum"), lines=("transaction_id", "count"),
    qty=("transaction_qty", "sum"), hari=("transaction_date", "nunique")
).sort_values("month")
bln["per_hari"], bln["per_line"] = bln["revenue"] / bln["hari"], bln["revenue"] / bln["lines"]

delta_ok = False
if len(bln) >= 2:
    akhir, sebelum = bln.iloc[-1], bln.iloc[-2]
    delta_ok = (akhir["hari"] == akhir["month"].days_in_month and sebelum["hari"] == sebelum["month"].days_in_month)

def kartu(label: str, nilai: str, kolom: str) -> str:
    if delta_ok and sebelum[kolom] != 0:
        d = akhir[kolom] / sebelum[kolom] - 1
        kelas = "up" if d > 0.0005 else "down" if d < -0.0005 else "flat"
        panah = "▲" if d > 0.0005 else "▼" if d < -0.0005 else "■"
        delta = f'<div class="kpi-delta"><span class="{kelas}">{panah} {abs(d) * 100:.1f}%</span> vs bulan lalu</div>'
    else: delta = '<div class="kpi-delta flat">&nbsp;</div>'
    return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{nilai}</div>{delta}</div>'

kpi_html = f"""<div class="kpi-container">
    {kartu("Total Pendapatan", f"${df['revenue'].sum():,.0f}", "revenue")}
    {kartu("Total Transaksi", f"{len(df):,}", "lines")}
    {kartu("Item Terjual", f"{int(df['transaction_qty'].sum()):,}", "qty")}
    {kartu("Rata-rata Harian", f"${df['revenue'].sum() / df['transaction_date'].nunique():,.0f}", "per_hari")}
</div>"""
st.markdown(kpi_html, unsafe_allow_html=True)
st.write("")

# ----------------------------------------------------------------------------
# Fungsi Visual (Transparan untuk menyatu dengan Card)
# ----------------------------------------------------------------------------
def dasar(fig: go.Figure, tinggi: int, legenda: bool = False) -> go.Figure:
    fig.update_layout(
        height=tinggi, margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", # Latar transparan
        font=dict(family=FONT, size=12, color="#e6edf3"),
        showlegend=legenda, bargap=0.2,
        hoverlabel=dict(bgcolor="#1c232d", font_size=12, bordercolor="#485462",
                        font=dict(color="#f0f3f6")),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
    )
    fig.update_xaxes(showgrid=False, linecolor="#485462", automargin=True,
                     tickfont=dict(color="#c9d1d9"), title_font=dict(color="#c9d1d9"))
    fig.update_yaxes(gridcolor="#28313c", zeroline=False, automargin=True,
                     tickfont=dict(color="#c9d1d9"), title_font=dict(color="#c9d1d9"))
    return fig

def opasitas(nilai, pilih): return [1.0 if (not pilih or v in pilih) else 0.25 for v in nilai]

def judul(teks: str, sub: str = ""): st.markdown(f'<div class="vt">{teks}</div><div class="vs">{sub}</div>', unsafe_allow_html=True)

def tampil(fig, nama, dim=None):
    if dim is None:
        st.plotly_chart(fig, key=f"{nama}_{st.session_state.reset_n}", config=CFG, use_container_width=True)
    else:
        kunci, sumbu = f"{nama}_{st.session_state.reset_n}", DIM[dim][1]
        st.plotly_chart(fig, key=kunci, config=CFG, use_container_width=True,
                        on_select=lambda d=dim, kk=kunci, s=sumbu: sinkron(d, kk, s), selection_mode="points")

def batang_horizontal(frame, kolom, dim, tinggi):
    g = frame.groupby(kolom, as_index=False)["revenue"].sum().sort_values("revenue")
    fig = go.Figure(go.Bar(
        x=g["revenue"], y=g[kolom], orientation="h", marker=dict(color=TEAL, opacity=opasitas(g[kolom], st.session_state.xf[dim]),
        line=dict(color="rgba(0,0,0,0)", width=0)), text=[f"${v / 1000:,.1f}K" for v in g["revenue"]], textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>Pendapatan: $%{x:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(visible=False, range=[0, g["revenue"].max() * 1.25])
    fig.update_yaxes(showgrid=False)
    return dasar(fig, tinggi)

# ----------------------------------------------------------------------------
# Tata Letak (Grid Layout)
# ----------------------------------------------------------------------------
r1a, r1b = st.columns([6, 4])

with r1a:
    with st.container(border=True):
        judul("Tren Pendapatan Bulanan", "Perbandingan total volume vs rata-rata harian")
        d = terapkan(base, "month")
        m = d.groupby(["month", "month_label"], as_index=False).agg(revenue=("revenue", "sum"), hari=("transaction_date", "nunique")).sort_values("month")
        m["per_hari"] = m["revenue"] / m["hari"]
        fig = go.Figure()
        fig.add_bar(x=m["month_label"], y=m["revenue"], name="Total Pendapatan", marker=dict(color=TEAL, opacity=opasitas(m["month_label"], st.session_state.xf["month"])))
        fig.add_scatter(x=m["month_label"], y=m["per_hari"], name="Rata-rata Harian", yaxis="y2", mode="lines+markers", line=dict(color=GELAP, width=3), marker=dict(size=8))
        fig = dasar(fig, 320, legenda=True)
        fig.update_yaxes(tickprefix="$", tickformat=",.0f", range=[0, m["revenue"].max() * 1.2])
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, tickprefix="$", range=[0, m["per_hari"].max() * 1.5]))
        tampil(fig, "g_bulan", "month")

with r1b:
    with st.container(border=True):
        judul("Pendapatan per Toko", "Berdasarkan lokasi cabang")
        tampil(batang_horizontal(terapkan(base, "store"), "store_location", "store", 320), "g_toko", "store")

r2a, r2b, r2c = st.columns(3)
with r2a:
    with st.container(border=True):
        judul("Distribusi Kategori", "Kontribusi per kategori produk")
        tampil(batang_horizontal(terapkan(base, "category"), "product_category", "category", 340), "g_kategori", "category")
with r2b:
    with st.container(border=True):
        judul("Lalu Lintas Jam Operasional", "Total pendapatan per jam")
        d = terapkan(base, "hour")
        g = d.groupby("hour", as_index=False)["revenue"].sum()
        fig = go.Figure(go.Bar(x=g["hour"], y=g["revenue"], marker=dict(color=TEAL, opacity=opasitas(g["hour"], st.session_state.xf["hour"]))))
        fig = dasar(fig, 340)
        fig.update_xaxes(dtick=1, title="Jam")
        fig.update_yaxes(tickprefix="$")
        tampil(fig, "g_jam", "hour")
with r2c:
    with st.container(border=True):
        judul("10 Produk Terlaris", "Pemeringkatan berdasarkan total nilai")
        top = df.groupby("product_detail", as_index=False)["revenue"].sum().nlargest(10, "revenue").sort_values("revenue")
        fig = go.Figure(go.Bar(x=top["revenue"], y=top["product_detail"], orientation="h", marker_color=GELAP, text=[f"${v / 1000:,.1f}K" for v in top["revenue"]], textposition="outside"))
        fig = dasar(fig, 340)
        fig.update_xaxes(visible=False, range=[0, top["revenue"].max() * 1.3])
        fig.update_yaxes(showgrid=False)
        tampil(fig, "g_top")

# ----------------------------------------------------------------------------
# Matriks Data & Detail
# ----------------------------------------------------------------------------
with st.container(border=True):
    judul("Matriks Rincian Produk", "Tabel interaktif - klik header untuk mengurutkan data")
    tabel = df.groupby(["product_category", "product_detail"], as_index=False).agg(
        harga=("unit_price", "first"), qty=("transaction_qty", "sum"), revenue=("revenue", "sum")
    ).sort_values("revenue", ascending=False)
    tabel["porsi"] = tabel["revenue"] / tabel["revenue"].sum() * 100
    st.dataframe(
        tabel, hide_index=True, height=340, use_container_width=True,
        column_order=["product_category", "product_detail", "harga", "qty", "revenue", "porsi"],
        column_config={
            "product_category": "Kategori", "product_detail": "Produk",
            "harga": st.column_config.NumberColumn("Harga Unit", format="$%.2f"),
            "qty": st.column_config.NumberColumn("Volume Terjual", format="%d"),
            "revenue": st.column_config.ProgressColumn("Pendapatan", format="$%.0f", min_value=0, max_value=float(tabel["revenue"].max())),
            "porsi": st.column_config.NumberColumn("Kontribusi (%)", format="%.1f"),
        }
    )