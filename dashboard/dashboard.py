from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# Konfigurasi halaman dan tema visual
st.set_page_config(page_title="Dashboard Bike Sharing", page_icon="🚲", layout="wide")

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams.update({
    "figure.dpi": 110,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titleweight": "bold",
    "axes.titlesize": 12,
})
BLUE, ORANGE, GREY, DARK = "#2F6DB5", "#E8833A", "#9AA5B1", "#1B3A5C"

DATA_DIR = Path(__file__).parent

WEATHER_ORDER = ["Clear", "Mist/Cloudy", "Light Rain/Snow"]
SEASON_ORDER = ["Winter", "Spring", "Summer", "Fall"]
SEGMENT_ORDER = ["Dini hari (00-05)", "Rush pagi (06-09)", "Siang (10-15)", "Rush sore (16-19)", "Malam (20-23)"]
DAYTYPES = ["Hari Kerja", "Akhir Pekan/Libur"]
LEVEL_ORDER = ["Rendah (< 2.000)", "Sedang (2.000-3.999)", "Tinggi (4.000-5.999)", "Sangat tinggi (>= 6.000)"]
BIN_ORDER = {
    "temp_bin": ["< 10 C", "10-20 C", "20-30 C", "> 30 C"],
    "hum_bin": ["< 40%", "40-60%", "60-80%", "> 80%"],
    "wind_bin": ["< 10", "10-20", "> 20"],
}
BIN_TITLE = {
    "temp_bin": "Suhu (derajat Celsius)",
    "hum_bin": "Kelembapan",
    "wind_bin": "Kecepatan angin (skala asli)",
}
MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]


# Load data
@st.cache_data
def load_data():
    hour_df = pd.read_csv(DATA_DIR / "main_data.csv", parse_dates=["dteday"])
    day_df = pd.read_csv(DATA_DIR / "day_data.csv", parse_dates=["dteday"])
    return hour_df, day_df


hour_all, day_all = load_data()

# Sidebar: filter rentang tanggal
min_date, max_date = day_all["dteday"].min().date(), day_all["dteday"].max().date()

with st.sidebar:
    st.title("🚲 Bike Sharing")
    selected = st.date_input(
        "Rentang tanggal",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        help="Filter berlaku untuk ringkasan, Pola Jam, Cuaca & Musim, dan Analisis Lanjutan. "
             "Tab Pertumbuhan selalu membandingkan 2011 vs 2012 secara penuh.",
    )
    st.markdown("---")

if isinstance(selected, (list, tuple)):
    if len(selected) == 2:
        start_date, end_date = selected
    elif len(selected) == 1:
        start_date = end_date = selected[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = selected

start_ts, end_ts = pd.Timestamp(start_date), pd.Timestamp(end_date)
hour_df = hour_all[(hour_all["dteday"] >= start_ts) & (hour_all["dteday"] <= end_ts)]
day_df = day_all[(day_all["dteday"] >= start_ts) & (day_all["dteday"] <= end_ts)]

# Header dan KPI
st.title("Dashboard Analisis Bike Sharing")
st.caption(f"Periode ditampilkan: {start_date:%d %b %Y} sampai {end_date:%d %b %Y} ({len(day_df)} hari)")

if day_df.empty:
    st.warning("Tidak ada data pada rentang tanggal yang dipilih.")
    st.stop()

total_rent = int(day_df["cnt"].sum())
avg_daily = day_df["cnt"].mean()
reg_share = day_df["registered"].sum() / day_df["cnt"].sum() * 100
busiest_day = day_df.loc[day_df["cnt"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total penyewaan", f"{total_rent:,}")
k2.metric("Rata-rata per hari", f"{avg_daily:,.0f}")
k3.metric("Porsi pengguna registered", f"{reg_share:.1f}%")
k4.metric("Hari tersibuk", f"{busiest_day['dteday']:%d %b %Y}", f"{int(busiest_day['cnt']):,} sewa")

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Pola Jam", "Cuaca & Musim", "Pertumbuhan", "Analisis Lanjutan", "Kesimpulan"]
)


# Tab 1: Pola jam (Pertanyaan 1)
with tab1:
    st.subheader("Pada jam berapa penyewaan memuncak: hari kerja vs akhir pekan/libur?")

    hourly = hour_df.groupby(["daytype", "hr"])["cnt"].mean().unstack(0).reindex(range(24))
    fig, ax = plt.subplots(figsize=(11, 4.8))
    for dtype, color in zip(DAYTYPES, [BLUE, ORANGE]):
        if dtype in hourly.columns and hourly[dtype].notna().any():
            ax.plot(hourly.index, hourly[dtype], marker="o", ms=4, lw=2.3, color=color, label=dtype)

    ax.axvspan(6, 9, color=GREY, alpha=0.12)
    ax.axvspan(16, 19, color=GREY, alpha=0.12, label="Jam sibuk (06-09 & 16-19)")

    peak_text = []
    if "Hari Kerja" in hourly.columns and hourly["Hari Kerja"].notna().any():
        wk = hourly["Hari Kerja"]
        for part, dx in [(wk.iloc[:12], -1.8), (wk.iloc[12:], 1.6)]:
            h, v = part.idxmax(), part.max()
            ax.annotate(f"{h:02d}.00 | {v:.0f}", xy=(h, v), xytext=(h + dx, v + 0.1 * np.nanmax(wk.values)),
                        ha="center", fontsize=9.5, fontweight="bold", color=BLUE,
                        arrowprops=dict(arrowstyle="-", color=BLUE, lw=1))
        peak_text.append(f"**Hari kerja** memuncak pukul {wk.iloc[:12].idxmax():02d}.00 dan {wk.iloc[12:].idxmax():02d}.00")
    if "Akhir Pekan/Libur" in hourly.columns and hourly["Akhir Pekan/Libur"].notna().any():
        we = hourly["Akhir Pekan/Libur"]
        h, v = we.idxmax(), we.max()
        ax.annotate(f"{h:02d}.00 | {v:.0f}", xy=(h, v), xytext=(h, v + 0.1 * np.nanmax(we.values)),
                    ha="center", fontsize=9.5, fontweight="bold", color=ORANGE,
                    arrowprops=dict(arrowstyle="-", color=ORANGE, lw=1))
        peak_text.append(f"**akhir pekan/libur** memuncak pukul {h:02d}.00")

    ax.set_xticks(range(24))
    ax.set_xlim(-0.5, 23.5)
    ymax = np.nanmax(hourly.values) if np.isfinite(hourly.values).any() else 1
    ax.set_ylim(0, ymax * 1.28)
    ax.set_xlabel("Jam dalam sehari")
    ax.set_ylabel("Rata-rata penyewaan per jam")
    ax.set_title("Rata-rata penyewaan per jam berdasarkan jenis hari")
    ax.legend(frameon=False, loc="upper center", ncol=3)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

    work = hour_df[hour_df["daytype"] == "Hari Kerja"]
    if len(work) and work["cnt"].sum() > 0:
        rush = work.loc[work["hr"].isin([6, 7, 8, 9, 16, 17, 18, 19]), "cnt"].sum() / work["cnt"].sum() * 100
        peak_text.append(f"jam sibuk menyumbang **{rush:.1f}%** penyewaan hari kerja")
    if peak_text:
        st.info("; ".join(peak_text) + ".")


# Tab 2: Cuaca dan musim (Pertanyaan 2)
with tab2:
    st.subheader("Seberapa besar cuaca menekan penyewaan harian, dan di musim apa paling terasa?")

    weather_stats = (
        day_df.groupby("weather")["cnt"].agg(rata_rata="mean", jumlah_hari="count").reindex(WEATHER_ORDER).dropna()
    )
    season_weather = (
        day_df.pivot_table(index="season_label", columns="weather", values="cnt", aggfunc="mean")
        .reindex(index=SEASON_ORDER, columns=WEATHER_ORDER)
    )

    c1, c2 = st.columns([1, 1.25])
    with c1:
        fig, ax = plt.subplots(figsize=(5.6, 4.8))
        colors = {"Clear": BLUE, "Mist/Cloudy": "#7FA8D9", "Light Rain/Snow": ORANGE}
        base = weather_stats["rata_rata"].get("Clear", np.nan)
        bars = ax.bar(weather_stats.index, weather_stats["rata_rata"],
                      color=[colors[w] for w in weather_stats.index], width=0.6)
        for bar, (w, row) in zip(bars, weather_stats.iterrows()):
            label = f"{row['rata_rata']:,.0f}"
            if w != "Clear" and np.isfinite(base):
                label += f"\n({(row['rata_rata'] / base - 1) * 100:+.1f}%)"
            label += f"\nn = {int(row['jumlah_hari'])} hari"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 60, label,
                    ha="center", va="bottom", fontsize=9)
        ax.set_ylim(0, weather_stats["rata_rata"].max() * 1.35)
        ax.set_ylabel("Rata-rata penyewaan per hari")
        ax.set_xlabel("")
        ax.set_title("Rata-rata penyewaan harian per cuaca")
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

    with c2:
        fig, ax = plt.subplots(figsize=(7, 4.8))
        sns.heatmap(season_weather, annot=True, fmt=",.0f", cmap="Blues", linewidths=1, linecolor="white",
                    cbar_kws={"label": "Rata-rata penyewaan per hari"}, ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_title("Rata-rata penyewaan harian: musim x cuaca")
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)

    if "Clear" in weather_stats.index and len(weather_stats) > 1:
        parts = [
            f"**{w}** {(weather_stats.loc[w, 'rata_rata'] / base - 1) * 100:+.1f}% dibanding cuaca cerah"
            for w in weather_stats.index if w != "Clear"
        ]
        st.info("Selisih rata-rata penyewaan harian: " + "; ".join(parts) + ".")



# Tab 3: Pertumbuhan YoY (Pertanyaan 3) - tidak terpengaruh filter tanggal
with tab3:
    st.subheader("Berapa pertumbuhan penyewaan 2012 dibanding 2011, dan segmen mana yang lebih cepat tumbuh?")
    st.caption("Bagian ini tidak terpengaruh filter tanggal karena membandingkan dua tahun penuh.")

    monthly = day_all.pivot_table(index="month_name", columns="year", values="cnt", aggfunc="sum").reindex(MONTH_ORDER)
    monthly["growth"] = (monthly[2012] / monthly[2011] - 1) * 100
    users = day_all.groupby("year")[["casual", "registered"]].sum()
    growth_user = (users.loc[2012] / users.loc[2011] - 1) * 100
    total = day_all.groupby("year")["cnt"].sum()
    total_growth = (total[2012] / total[2011] - 1) * 100

    m1, m2, m3 = st.columns(3)
    m1.metric("Total penyewaan 2012", f"{total[2012]:,}", f"{total_growth:+.1f}% vs 2011")
    m2.metric("Pertumbuhan registered", f"{growth_user['registered']:+.1f}%")
    m3.metric("Pertumbuhan casual", f"{growth_user['casual']:+.1f}%")

    c1, c2 = st.columns([1.6, 1])
    with c1:
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        ax.plot(MONTH_ORDER, monthly[2011], marker="o", lw=2.3, color=GREY, label="2011")
        ax.plot(MONTH_ORDER, monthly[2012], marker="o", lw=2.3, color=BLUE, label="2012")
        for m, v, g in zip(MONTH_ORDER, monthly[2012], monthly["growth"]):
            ax.annotate(f"+{g:.0f}%", xy=(m, v), xytext=(0, 9), textcoords="offset points", ha="center",
                        fontsize=8, color=BLUE,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x / 1000:.0f}rb"))
        ax.set_ylim(0, monthly[2012].max() * 1.18)
        ax.set_ylabel("Total penyewaan per bulan")
        ax.set_title("Total penyewaan bulanan: 2011 vs 2012")
        ax.legend(frameon=False, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)
    with c2:
        fig, ax = plt.subplots(figsize=(5, 4.8))
        x = np.arange(2)
        w = 0.36
        ax.bar(x - w / 2, users.loc[2011, ["casual", "registered"]], w, color=GREY, label="2011")
        ax.bar(x + w / 2, users.loc[2012, ["casual", "registered"]], w, color=BLUE, label="2012")
        for i, seg in enumerate(["casual", "registered"]):
            ax.text(i + w / 2, users.loc[2012, seg] + 25000, f"+{growth_user[seg]:.0f}%",
                    ha="center", fontweight="bold", color=BLUE)
        ax.set_xticks(x)
        ax.set_xticklabels(["Casual", "Registered"])
        ax.set_yticks([0, 500000, 1000000, 1500000, 2000000])
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v / 1e6:.1f} jt"))
        ax.set_ylim(0, 2000000)
        ax.set_ylabel("Total penyewaan per tahun")
        ax.set_title("Casual vs registered")
        ax.legend(frameon=False, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig, clear_figure=True)



# Tab 4: Analisis lanjutan (manual grouping & binning)
with tab4:
    st.subheader("Analisis lanjutan: manual grouping dan binning")

    st.markdown("**1. Segmen waktu dalam sehari (manual grouping)**")
    seg_total = hour_df.pivot_table(index="segment", columns="daytype", values="cnt", aggfunc="sum")
    seg_total = seg_total.reindex(index=SEGMENT_ORDER, columns=[d for d in DAYTYPES if d in seg_total.columns]).fillna(0)
    seg_share = seg_total / seg_total.sum() * 100

    seg_colors = ["#C9D3DE", BLUE, "#9FBFE3", DARK, GREY]
    fig, ax = plt.subplots(figsize=(11, 3.4))
    left = np.zeros(len(seg_share.columns))
    for seg, color in zip(SEGMENT_ORDER, seg_colors):
        vals = seg_share.loc[seg].values
        ax.barh(seg_share.columns, vals, left=left, color=color, edgecolor="white", label=seg)
        for i, (l, v) in enumerate(zip(left, vals)):
            if v >= 4:
                ax.text(l + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=10,
                        color="white" if color in (BLUE, DARK, GREY) else "black")
        left += vals
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_xlabel("Porsi total penyewaan (%)")
    ax.set_title("Porsi penyewaan per segmen waktu")
    ax.legend(ncol=5, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.3), fontsize=9)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

    st.markdown("**2. Kondisi cuaca per interval (binning)**")
    var = st.radio(
        "Pilih variabel",
        options=list(BIN_ORDER.keys()),
        format_func=lambda k: BIN_TITLE[k],
        horizontal=True,
    )
    res = (
        day_df.groupby(var, observed=True)["cnt"].agg(rata_rata="mean", jumlah_hari="count")
        .reindex(BIN_ORDER[var]).dropna()
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    best = res["rata_rata"].idxmax()
    bars = ax.bar(res.index, res["rata_rata"], color=[BLUE if i == best else GREY for i in res.index], width=0.65)
    for bar, n in zip(bars, res["jumlah_hari"]):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 60,
                f"{bar.get_height():,.0f}\n(n={int(n)})", ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, res["rata_rata"].max() * 1.25)
    ax.set_xlabel(BIN_TITLE[var])
    ax.set_ylabel("Rata-rata penyewaan per hari")
    ax.set_title(f"Rata-rata penyewaan harian berdasarkan {BIN_TITLE[var].split(' (')[0].lower()}")
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)

    st.markdown("**3. Tingkat permintaan harian per musim (binning)**")
    level_season = pd.crosstab(day_df["season_label"], day_df["demand_level"]).reindex(
        index=[s for s in SEASON_ORDER if s in day_df["season_label"].unique()], columns=LEVEL_ORDER, fill_value=0
    )
    level_share = level_season.div(level_season.sum(axis=1), axis=0) * 100
    lvl_colors = ["#D9534F", "#F0AD4E", "#7FA8D9", DARK]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    left = np.zeros(len(level_share))
    for lvl, color in zip(LEVEL_ORDER, lvl_colors):
        vals = level_share[lvl].values
        ax.barh(level_share.index, vals, left=left, color=color, edgecolor="white", label=lvl)
        for i, (l, v) in enumerate(zip(left, vals)):
            if v >= 6:
                ax.text(l + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=9.5,
                        color="black" if color in ("#F0AD4E", "#7FA8D9") else "white")
        left += vals
    ax.set_xlim(0, 100)
    ax.invert_yaxis()
    ax.set_xlabel("Porsi hari (%)")
    ax.set_title("Sebaran tingkat permintaan harian per musim")
    ax.legend(ncol=2, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=9)
    plt.tight_layout()
    st.pyplot(fig, clear_figure=True)
    st.caption("Pola ini bersifat asosiasi, bukan bukti sebab-akibat.")


# Tab 5: Kesimpulan
with tab5:
    st.subheader("Kesimpulan dan rekomendasi (seluruh periode 2011-2012)")
    st.markdown(
        """
**Pertanyaan 1 - Pola jam.** Hari kerja memuncak pukul 08.00 (sekitar 473 sewa/jam) dan 17.00 (sekitar 524 sewa/jam); jam sibuk
menyumbang sekitar 60% penyewaan hari kerja. Akhir pekan/libur memuncak pukul 13.00 (sekitar 373 sewa/jam), dengan sekitar 47% penyewaan terjadi pukul 10-15.

**Pertanyaan 2 - Cuaca dan musim.** Dibanding cuaca cerah (sekitar 4.877 sewa/hari), penyewaan turun sekitar 17% saat berkabut/berawan
dan sekitar 63% saat hujan/salju ringan. Dampak relatif terbesar terjadi pada musim Spring.

**Pertanyaan 3 - Pertumbuhan.** Total penyewaan 2012 tumbuh sekitar 64,9% dibanding 2011. Pengguna registered (+68%) tumbuh lebih cepat dari casual (+51%).

**Rekomendasi action item**
- Redistribusi armada berbasis jam: isi stok di area komuter sebelum jam sibuk dan lakukan perawatan pada dini hari.
- Arahkan armada dan promo casual ke area rekreasi pukul 10-15 pada akhir pekan dan hari libur.
- Sesuaikan sebaran armada dan jadwal perawatan dengan prakiraan cuaca, terutama pada musim Spring.
- Prioritaskan retensi pengguna registered dan siapkan penawaran konversi langganan untuk pengguna casual.
        """
    )
