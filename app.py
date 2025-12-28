import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title = 'Dashboard', layout = "wide")

@st.cache_data
def load_data():
    df = pd.read_excel(
        r"Financial_Samples.xlsx",
        parse_dates=["Date"]
    )
    return df


df = load_data()

st.sidebar.title("Filters")

country_filter = st.sidebar.multiselect(
    "Country",
    options=sorted(df["Country"].unique()),
    default=sorted(df["Country"].unique())
)
product_filter = st.sidebar.multiselect(
    "Product",
    options=sorted(df["Product"].unique()),
    default=sorted(df["Product"].unique())
)
segment_filter = st.sidebar.multiselect(
    "Segment",
    options=sorted(df["Segment"].unique()),
    default=sorted(df["Segment"].unique())
)
year_filter = st.sidebar.multiselect(
    "Year",
    options=sorted(df["Year"].unique()),
    default=sorted(df["Year"].unique())
)
filtered_df = df[
    (df["Country"].isin(country_filter)) &
    (df["Product"].isin(product_filter)) &
    (df["Segment"].isin(segment_filter)) &
    (df["Year"].isin(year_filter))
]



page = st.sidebar.radio(
    "Navigate",
    [
        "Executive Overview",
        "Product & Pricing",
        "Discount Impact",
        "Time Analysis",
        "Data Quality & Assumptions"
    ]
)

def compute_kpis(data):
    Sales = data["Gross Sales"].sum()
    Profit = data["Profit"].sum()
    units = data["Units Sold"].sum()

    margin = Profit/Sales if Sales !=0 else 0
    discount_ratio = (
        data["Discounts"].sum() / data["Gross Sales"].sum()
        if data["Gross Sales"].sum() != 0 else 0
    )
    return Sales,Profit,units,margin,discount_ratio

if page == "Executive Overview":

    st.title("Executive Overview")

    Sales, Profit, units, margin, discount_ratio = compute_kpis(filtered_df)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Sales", f"{Sales:,.0f}")
    col2.metric("Total Profit", f"{Profit:,.0f}")
    col3.metric("Units Sold", f"{units:,.0f}")
    col4.metric("Avg Margin", f"{margin:.2%}")
    col5.metric("% Revenue Discounted", f"{discount_ratio:.2%}")

    monthly = (
    filtered_df
    .groupby(filtered_df["Date"].dt.to_period("M"))
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum")
    )
    .reset_index())


    monthly["Date"] = monthly["Date"].astype(str)

    
    fig = px.line(
        monthly,
        x="Date",
        y=["Sales", "Profit"],
        markers=True,
        title="Monthly Sales & Profit"
    )
    st.plotly_chart(fig, use_container_width=True)

    profit_product = (
        filtered_df
        .groupby("Product")["Profit"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    fig2 = px.bar(
        profit_product,
        x="Product",
        y="Profit",
        title="Profit by Product"
    )
    st.plotly_chart(fig2, use_container_width=True)

elif page == "Product & Pricing":
    st.title("Product & Pricing Analysis")

    price_filter = st.multiselect(
        "Sale Price",
        options=sorted(filtered_df["Sale Price"].unique()),
        default=sorted(filtered_df["Sale Price"].unique())
    )

    pricing_df = filtered_df[filtered_df["Sale Price"].isin(price_filter)]
    
    fig = px.scatter(
        pricing_df,
        x="Sale Price",
        y="Profit",
        color="Product",
        title="Profit Distribution Across Sale Prices"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.scatter(
        pricing_df,
        x="Sale Price",
        y="Units Sold",
        color="Product",
        title="Units Sold vs Sale Price"
    )
    st.plotly_chart(fig2, use_container_width=True)

elif page == "Discount Impact":

    st.title("Discount Impact Analysis")
    
    fig = px.scatter(
        filtered_df,
        x="Discounts",
        y="Units Sold",
        color="Discount Band",
        title="Discounts vs Units Sold"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    fig2 = px.scatter(
        filtered_df,
        x="Discounts",
        y="Profit",
        color="Discount Band",
        title="Discounts vs Profit"
    )
    st.plotly_chart(fig2, use_container_width=True)

    profit_discount = (
        filtered_df
        .groupby("Discount Band")["Profit"]
        .sum()
        .reset_index()
    )

    fig3 = px.bar(
        profit_discount,
        x="Discount Band",
        y="Profit",
        title="Total Profit by Discount Band"
    )
    st.plotly_chart(fig3, use_container_width=True)

elif page == "Time Analysis":

    st.title("Time-Based Performance")

    monthly = (
    filtered_df
    .groupby(filtered_df["Date"].dt.to_period("M"))
    .agg(
        Sales=("Sales", "sum"),
        Profit=("Profit", "sum"),
        Units_Sold=("Units Sold", "sum")
    )
    .reset_index())

# Convert Period → Timestamp for plotting
    monthly["Date"] = monthly["Date"].dt.to_timestamp()


    
    fig = px.line(
        monthly,
        x="Date",
        y="Sales",
        title="Monthly Sales Trend"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig2 = px.line(
        monthly,
        x="Date",
        y="Profit",
        title="Monthly Profit Trend"
    )
    st.plotly_chart(fig2, use_container_width=True) 

elif page == "Data Quality & Assumptions":
    st.title("Data Quality & Assumptions")

    st.markdown("""
    ### Key Assumptions (Validated via EDA)

    - Dataset is **scenario-based aggregated data**, not transactions
    - **Profit is derived**:  
      `Profit = Gross Sales - Discounts - COGS`
    - **Manufacturing Price is constant per product**
    - **Sale Price is discrete** (7 fixed levels per product)
    - **Discount Band does NOT uniquely define price**
    - Missing Discount Band = **No Discount Applied**
    """)

    st.markdown("### Profit Formula Verification")

    diff = (
        filtered_df["Gross Sales"]
        - filtered_df["Discounts"]
        - filtered_df["COGS"]
        - filtered_df["Profit"]
    )

    st.write(diff.describe())

    if (diff.abs() > 1e-9).sum() > 0:
        st.warning("Minor floating-point deviations detected (expected).")
    else:
        st.success("Profit formula holds exactly.")

print(filtered_df.columns)

