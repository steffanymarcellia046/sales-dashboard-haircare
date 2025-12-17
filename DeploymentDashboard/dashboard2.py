import streamlit as st
import pandas as pd
import plotly.express as px
import os

# =====================================================
# CONFIG
# =====================================================
st.set_page_config(
    page_title="Sales Performance Dashboard",
    layout="wide"
)

# =====================================================
# PATH SETUP (CLOUD SAFE)
# =====================================================
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSET_DIR = os.path.join(BASE_DIR, "assets")
STYLE_DIR = os.path.join(BASE_DIR, "styles")

# =====================================================
# LOAD CSS
# =====================================================
def load_css(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css(os.path.join(STYLE_DIR, "theme.css"))

# =====================================================
# THEME
# =====================================================
THEME = {
    "accent": "#6a1b6a",
    "border": "#b95aa3",
    "text": "#3b0a2f",
    "apps": "#6a1b6a",
    "erp": "#b95aa3",
    "blank": "#999999",
}

PIE_COLORS = [
    "#6a1b6a", "#8a2d7c", "#b95aa3", "#d98cc7", "#f0b7dd",
    "#5a2a6e", "#7b3b88", "#a455a7", "#c97dc2", "#efb3d9",
    "#4a1f52", "#9b4aa2", "#d16bbd", "#f4c2e2"
]

# =====================================================
# GLOBAL STYLE
# =====================================================
st.markdown(
    """
    <style>
    .center-title{
        text-align:center;
        font-weight:900;
        font-size:28px;
        color:#6a1b6a;
        margin: 8px 0;
    }
    .center-subtitle{
        text-align:center;
        font-weight:800;
        font-size:22px;
        color:#6a1b6a;
        margin: 16px 0 10px 0;
    }
    [data-testid="stMetricLabel"],
    [data-testid="stMetricValue"]{
        text-align:center !important;
        width:100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def apply_plot_theme(fig, title):
    fig.update_layout(
        title=dict(
            text=f"<b>{title}</b>",
            x=0.5,
            xanchor="center",
            font=dict(size=22, color=THEME["accent"])
        ),
        font=dict(color=THEME["text"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.35)",
        margin=dict(l=30, r=30, t=90, b=30)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(185,90,163,0.25)")
    return fig

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    sales = pd.read_csv(os.path.join(DATA_DIR, "SalesInvoice.csv"))
    rfm = pd.read_csv(os.path.join(DATA_DIR, "RFMCurrent.csv"))
    return sales, rfm

sales_df, rfm_df = load_data()

# =====================================================
# SIDEBAR FILTER
# =====================================================
st.sidebar.header("Filter")

branches = sorted(sales_df["Branch"].dropna().unique())
select_all_branch = st.sidebar.checkbox("Select all branches", True)

branch_filter = st.sidebar.multiselect(
    "Branch",
    branches,
    default=branches if select_all_branch else branches[:3]
)

months = sales_df["Month"].dropna().astype(str).unique().tolist()
select_all_month = st.sidebar.checkbox("Select all months", True)

month_filter = st.sidebar.multiselect(
    "Month",
    months,
    default=months if select_all_month else months
)

filtered_df = sales_df[
    (sales_df["Branch"].isin(branch_filter)) &
    (sales_df["Month"].isin(month_filter))
].copy()

# =====================================================
# HEADER
# =====================================================
c1, c2, c3 = st.columns([1.2, 7.6, 1.2])
with c1:
    st.image(os.path.join(ASSET_DIR, "logo_upn.png"), width=110)
with c2:
    st.markdown(
        """
        <div class="center-title">
        Customer and Sales Performance Analysis Dashboard for Haircare Products
        </div>
        <div style="text-align:center;font-size:14px;font-weight:700;">
        Steffany Marcellia Witanto • PT Kreatif Maju Bersama
        </div>
        """,
        unsafe_allow_html=True
    )
with c3:
    st.image(os.path.join(ASSET_DIR, "logo_kmb.png"), width=110)

st.markdown("<hr>", unsafe_allow_html=True)

# =====================================================
# KPI
# =====================================================
filtered_df["Grand Total (Company Currency)"] = pd.to_numeric(
    filtered_df["Grand Total (Company Currency)"], errors="coerce"
).fillna(0)

filtered_df["Quantity"] = pd.to_numeric(
    filtered_df["Quantity"], errors="coerce"
).fillna(0)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"{filtered_df['Grand Total (Company Currency)'].sum():,.0f}")
k2.metric("Total Customers", filtered_df["Customer"].nunique())
k3.metric("Unique Products", filtered_df["Item Name (Sales Invoice Item)"].nunique())
k4.metric("Sales Volume", f"{filtered_df['Quantity'].sum():,.0f}")

# =====================================================
# SALES TREND
# =====================================================
trend = (
    filtered_df.groupby("Month", as_index=False)
    .agg(Total_Revenue=("Grand Total (Company Currency)", "sum"))
)

fig = px.line(trend, x="Month", y="Total_Revenue", markers=True)
fig.update_traces(line_color=THEME["accent"])
fig = apply_plot_theme(fig, "Sales Trend")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# MONTHLY SHARE
# =====================================================
share = (
    filtered_df.groupby(["Month", "Source"], as_index=False)
    .agg(Total_Revenue=("Grand Total (Company Currency)", "sum"))
)

share["Revenue_Share"] = share.groupby("Month")["Total_Revenue"].transform(lambda x: x / x.sum())

fig = px.bar(
    share,
    x="Month",
    y="Revenue_Share",
    color="Source",
    barmode="stack",
    text_auto=".0%",
    color_discrete_map={
        "Apps": THEME["apps"],
        "ERP": THEME["erp"]
    }
)
fig = apply_plot_theme(fig, "Monthly Revenue Share by Sales Channel (%)")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# TOP PRODUCTS
# =====================================================
top_products = (
    filtered_df.groupby("Item Name (Sales Invoice Item)")["Quantity"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)

fig = px.bar(
    top_products,
    x="Quantity",
    y="Item Name (Sales Invoice Item)",
    orientation="h"
)
fig.update_traces(marker_color=THEME["accent"])
fig = apply_plot_theme(fig, "Top 5 Best Seller Products")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# BRANCH PERFORMANCE (DONUT)
# =====================================================
branch_perf = (
    filtered_df.groupby("Branch")["Grand Total (Company Currency)"]
    .sum()
    .reset_index()
)

fig = px.pie(
    branch_perf,
    values="Grand Total (Company Currency)",
    names="Branch",
    hole=0.55,
    color_discrete_sequence=PIE_COLORS
)
fig = apply_plot_theme(fig, "Branch Performance")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# BRANCH SUMMARY
# =====================================================
st.markdown("<div class='center-subtitle'>Branch Summary</div>", unsafe_allow_html=True)

summary = (
    filtered_df.groupby("Branch")
    .agg(
        Total_Revenue=("Grand Total (Company Currency)", "sum"),
        Total_Transactions=("ID", "count"),
        Total_Customers=("Customer", "nunique"),
        Avg_Transaction_Value=("Grand Total (Company Currency)", "mean")
    )
    .reset_index()
)

summary.insert(0, "No", range(1, len(summary) + 1))
st.dataframe(summary, use_container_width=True)

# =====================================================
# CUSTOMER SEGMENTATION
# =====================================================
segment = (
    rfm_df.groupby("Segment_Name_Current")["Customer"]
    .count()
    .reset_index(name="Total_Customers")
)

fig = px.bar(segment, x="Segment_Name_Current", y="Total_Customers")
fig.update_traces(marker_color=THEME["accent"])
fig = apply_plot_theme(fig, "Customer Segmentation")
st.plotly_chart(fig, use_container_width=True)

# =====================================================
# HIGHEST SPENDERS
# =====================================================
spender = (
    filtered_df.groupby("Customer")["Grand Total (Company Currency)"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
    .reset_index()
)

fig = px.bar(
    spender,
    x="Grand Total (Company Currency)",
    y="Customer",
    orientation="h"
)
fig.update_traces(marker_color=THEME["accent"])
fig = apply_plot_theme(fig, "Highest Spenders (Top 5 Customers)")
st.plotly_chart(fig, use_container_width=True)
