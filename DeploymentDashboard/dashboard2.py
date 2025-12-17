import streamlit as st
import pandas as pd
import plotly.express as px

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sales Performance Dashboard", layout="wide")

# =========================
# LOAD CSS
# =========================
def load_css(path: str):
    with open(path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# pastikan file ini ada: styles/theme.css
load_css("styles/theme.css")

# =========================
# THEME + GLOBAL CSS POLISH
# =========================
THEME = {
    "accent": "#6a1b6a",   # ungu
    "border": "#b95aa3",   # pink-ungu
    "text":   "#3b0a2f",
    "apps":   "#6a1b6a",
    "erp":    "#b95aa3",
    "blank":  "#999999",
}

# palette selaras untuk donut/pie
PIE_COLORS = [
    "#6a1b6a", "#8a2d7c", "#b95aa3", "#d98cc7", "#f0b7dd",
    "#5a2a6e", "#7b3b88", "#a455a7", "#c97dc2", "#efb3d9",
    "#4a1f52", "#9b4aa2", "#d16bbd", "#f4c2e2"
]

st.markdown(
    """
    <style>
      /* center KPI cards */
      [data-testid="stMetricLabel"] {text-align:center !important; width:100%;}
      [data-testid="stMetricValue"] {text-align:center !important; width:100%;}
      [data-testid="stMetricDelta"] {text-align:center !important; width:100%;}

      /* centered section title helper (for non-plotly sections like tables) */
      .center-subtitle{
        text-align:center;
        font-weight:900;
        font-size:22px;
        color:#6a1b6a;
        margin: 16px 0 10px 0;
      }

      .center-title{
        text-align:center;
        font-weight:900;
        font-size:28px;
        color:#6a1b6a;
        margin: 8px 0 12px 0;
      }
    </style>
    """,
    unsafe_allow_html=True
)

def apply_plot_theme(fig, title: str):
    """Bikin judul chart center + bold + warna selaras tema"""
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5, xanchor="center",
            font=dict(family="Poppins, Segoe UI, Arial", size=22, color=THEME["accent"])
        ),
        font=dict(family="Poppins, Segoe UI, Arial", size=14, color=THEME["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.35)",
        legend=dict(
            bgcolor="rgba(255,255,255,0.35)",
            bordercolor="rgba(185,90,163,0.6)",
            borderwidth=1
        ),
        margin=dict(l=30, r=30, t=90, b=30),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(185,90,163,0.25)", zeroline=False)
    return fig

# =========================
# CONST
# =========================
MONTH_ORDER = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
MONTH_MAP = {m.lower(): i for i, m in enumerate(MONTH_ORDER, start=1)}

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    sales = pd.read_csv("data/SalesInvoice.csv")
    rfm = pd.read_csv("data/RFMCurrent.csv")
    return sales, rfm

sales_df, rfm_df = load_data()

# =========================
# SIDEBAR FILTER (simple slicer + select all)
# =========================
st.sidebar.header("Filter")

all_branches = sorted(sales_df["Branch"].dropna().unique().tolist())
select_all_branch = st.sidebar.checkbox("Select all branches", value=True)

branch_filter = st.sidebar.multiselect(
    "Branch",
    options=all_branches,
    default=all_branches if select_all_branch else all_branches[:3]
)

raw_months = sales_df["Month"].dropna().astype(str).str.strip().unique().tolist()
all_months = [m for m in MONTH_ORDER if m in raw_months] if raw_months else []
if not all_months:
    all_months = sorted(raw_months)

select_all_month = st.sidebar.checkbox("Select all months", value=True)

month_filter = st.sidebar.multiselect(
    "Month",
    options=all_months,
    default=all_months if select_all_month else all_months
)

filtered_df = sales_df[
    (sales_df["Branch"].isin(branch_filter)) &
    (sales_df["Month"].isin(month_filter))
].copy()

# =========================
# HEADER + LOGO (logo_upn dulu, lalu logo_kmb)
# =========================
colL, colM, colR = st.columns([1.2, 7.6, 1.2], vertical_alignment="center")

with colL:
    st.image("assets/logo_upn.png", width=110)

with colM:
    st.markdown(
        """
        <div class="center-title">
          Customer and Sales Performance Analysis Dashboard for Haircare Products
        </div>
        <div style="text-align:center; font-size:14px; font-weight:700; color:#6b2b5f;">
          Steffany Marcellia Witanto • PT Kreatif Maju Bersama
        </div>
        """,
        unsafe_allow_html=True
    )

with colR:
    st.image("assets/logo_kmb.png", width=110)

st.markdown(
    "<hr style='border:0; height:2px; background:#b95aa3; margin:10px 0 14px 0;'>",
    unsafe_allow_html=True
)

# =========================
# KPI
# =========================
filtered_df["Grand Total (Company Currency)"] = pd.to_numeric(
    filtered_df["Grand Total (Company Currency)"], errors="coerce"
).fillna(0)

filtered_df["Quantity"] = pd.to_numeric(
    filtered_df["Quantity"], errors="coerce"
).fillna(0)

kpi_df = filtered_df.copy()
kpi_df["product_clean"] = (
    kpi_df["Item Name (Sales Invoice Item)"]
    .astype(str).str.strip().str.lower()
)

unique_products = kpi_df["product_clean"].nunique()
total_revenue = filtered_df["Grand Total (Company Currency)"].sum()
total_customers = filtered_df["Customer"].nunique()
sales_volume = filtered_df["Quantity"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Revenue", f"{total_revenue:,.0f}")
c2.metric("Total Customers", total_customers)
c3.metric("Unique Products", unique_products)
c4.metric("Sales Volume", f"{sales_volume:,.0f}")

# ======================================================
# PREP TREND DF
# ======================================================
trend_df = filtered_df.copy()

trend_df["Month_label"] = trend_df["Month"].astype(str).str.strip()
trend_df.loc[
    trend_df["Month"].isna()
    | (trend_df["Month_label"] == "")
    | (trend_df["Month_label"].str.lower() == "nan"),
    "Month_label"
] = "(blank)"

trend_df["Month_clean"] = trend_df["Month_label"].astype(str).str.strip().str.lower()

alias = {
    "sept": "september", "sep": "september",
    "oct": "october", "okt": "october", "oktober": "october",
    "nov": "november",
    "agustus": "august",
    "desember": "december", "des": "december"
}
trend_df["Month_clean"] = trend_df["Month_clean"].replace(alias)

trend_df["Month_order_from_name"] = trend_df["Month_clean"].map(MONTH_MAP)

if "MonthNumber" in trend_df.columns:
    trend_df["MonthNumber_num"] = pd.to_numeric(trend_df["MonthNumber"], errors="coerce")
    trend_df["Month_order"] = trend_df["MonthNumber_num"].fillna(trend_df["Month_order_from_name"])
else:
    trend_df["Month_order"] = trend_df["Month_order_from_name"]

trend_df.loc[trend_df["Month_clean"] == "(blank)", "Month_order"] = 13
trend_df["Month_order"] = trend_df["Month_order"].fillna(99)

trend_df["Month_label"] = trend_df["Month_clean"].apply(
    lambda x: x.title() if x in MONTH_MAP else "(blank)" if x == "(blank)" else x.title()
)

# Source clean
if "Source" in trend_df.columns:
    trend_df["Source_clean"] = trend_df["Source"].fillna("").astype(str).str.strip()
else:
    trend_df["Source_clean"] = ""

trend_df.loc[trend_df["Source_clean"] == "", "Source_clean"] = "(blank)"
trend_df["Source_clean"] = trend_df["Source_clean"].astype(str).str.strip()
trend_df["Source_clean"] = trend_df["Source_clean"].str.lower().replace({
    "apps": "Apps",
    "app": "Apps",
    "erp": "ERP",
    "(blank)": "(blank)"
})

# ======================================================
# 1) SALES TREND
# ======================================================
sales_trend = (
    trend_df
    .groupby(["Month_order", "Month_label"], as_index=False)
    .agg(Total_Revenue=("Grand Total (Company Currency)", "sum"))
    .sort_values("Month_order")
)

fig_sales_trend = px.line(
    sales_trend,
    x="Month_label",
    y="Total_Revenue",
    markers=True
)
fig_sales_trend.update_traces(line=dict(color=THEME["accent"]), marker=dict(color=THEME["accent"]))
fig_sales_trend.update_layout(
    xaxis_title="Month",
    yaxis_title="Total Revenue",
    xaxis=dict(categoryorder="array", categoryarray=sales_trend["Month_label"]),
)
fig_sales_trend = apply_plot_theme(fig_sales_trend, "Sales Trend")
st.plotly_chart(fig_sales_trend, use_container_width=True)

# ======================================================
# 2) MONTHLY REVENUE SHARE BY SALES CHANNEL (%)
# ======================================================
channel_share = (
    trend_df
    .groupby(["Month_order", "Month_label", "Source_clean"], as_index=False)
    .agg(Total_Revenue=("Grand Total (Company Currency)", "sum"))
    .sort_values("Month_order")
)

channel_share["Revenue_Share"] = (
    channel_share.groupby("Month_label")["Total_Revenue"]
    .transform(lambda x: x / x.sum())
)

fig_share = px.bar(
    channel_share,
    x="Month_label",
    y="Revenue_Share",
    color="Source_clean",
    barmode="stack",
    text_auto=".0%",
    color_discrete_map={
        "Apps": THEME["apps"],
        "ERP": THEME["erp"],
        "(blank)": THEME["blank"]
    }
)
fig_share.update_layout(
    xaxis_title="Month",
    yaxis_title="Revenue Share",
    yaxis_tickformat=".0%",
    xaxis=dict(categoryorder="array", categoryarray=sales_trend["Month_label"]),
    legend_title_text="Source",
)
fig_share = apply_plot_theme(fig_share, "Monthly Revenue Share by Sales Channel (%)")
st.plotly_chart(fig_share, use_container_width=True)

# ======================================================
# 3) TOP 5 BEST SELLER PRODUCTS (force ungu)
# ======================================================
top_products = (
    filtered_df
    .groupby("Item Name (Sales Invoice Item)")["Quantity"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)

fig_product = px.bar(
    top_products,
    x="Quantity",
    y="Item Name (Sales Invoice Item)",
    orientation="h"
)
fig_product.update_traces(marker_color=THEME["accent"])
fig_product.update_layout(
    xaxis_title="Quantity",
    yaxis_title="Product",
    yaxis=dict(categoryorder="total ascending")
)
fig_product = apply_plot_theme(fig_product, "Top 5 Best Seller Products")
st.plotly_chart(fig_product, use_container_width=True)

# ======================================================
# 4) BRANCH PERFORMANCE (DONUT theme colors)
# ======================================================
branch_perf = (
    filtered_df
    .groupby("Branch")["Grand Total (Company Currency)"]
    .sum()
    .reset_index()
    .sort_values("Grand Total (Company Currency)", ascending=False)
)

fig_branch = px.pie(
    branch_perf,
    values="Grand Total (Company Currency)",
    names="Branch",
    hole=0.55
)

fig_branch.update_traces(
    marker=dict(
        colors=PIE_COLORS,
        line=dict(color="rgba(255,255,255,0.7)", width=1)
    ),
    textposition="inside",
    textinfo="percent"
)

fig_branch = apply_plot_theme(fig_branch, "Branch Performance")
st.plotly_chart(fig_branch, use_container_width=True)

# ======================================================
# 5) BRANCH SUMMARY TABLE (center title)
# ======================================================
st.markdown("<div class='center-subtitle'>Branch Summary</div>", unsafe_allow_html=True)

branch_summary = (
    filtered_df
    .groupby("Branch")
    .agg(
        Total_Revenue=("Grand Total (Company Currency)", "sum"),
        Total_Transactions=("ID", "count"),
        Total_Customers=("Customer", "nunique"),
        Average_Transaction_Value=("Grand Total (Company Currency)", "mean")
    )
    .reset_index()
    .sort_values("Total_Revenue", ascending=False)
    .reset_index(drop=True)
)

branch_summary.insert(0, "No", range(1, len(branch_summary) + 1))
st.dataframe(branch_summary, use_container_width=True)

# ======================================================
# 6) CUSTOMER SEGMENTATION (force ungu)
# ======================================================
rfm_segment = (
    rfm_df
    .groupby("Segment_Name_Current")["Customer"]
    .count()
    .reset_index(name="Total_Customers")
    .sort_values("Total_Customers", ascending=False)
)

fig_rfm = px.bar(
    rfm_segment,
    x="Segment_Name_Current",
    y="Total_Customers"
)
fig_rfm.update_traces(marker_color=THEME["accent"])
fig_rfm.update_layout(xaxis_title="Segment", yaxis_title="Total Customers")
fig_rfm = apply_plot_theme(fig_rfm, "Customer Segmentation")
st.plotly_chart(fig_rfm, use_container_width=True)

# ======================================================
# 7) HIGHEST SPENDERS (force ungu)
# ======================================================
top_spenders = (
    filtered_df
    .groupby("Customer")["Grand Total (Company Currency)"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)

fig_spender = px.bar(
    top_spenders,
    x="Grand Total (Company Currency)",
    y="Customer",
    orientation="h"
)
fig_spender.update_traces(marker_color=THEME["accent"])
fig_spender.update_layout(
    xaxis_title="Total Spending",
    yaxis_title="Customer",
    yaxis=dict(categoryorder="total ascending")
)
fig_spender = apply_plot_theme(fig_spender, "Highest Spenders (Top 5 Customers)")
st.plotly_chart(fig_spender, use_container_width=True)

