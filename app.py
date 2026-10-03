
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="GameScope Pro | Video Game Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #0b1020, #111a30);
    color: #f1f5f9;
}
[data-testid="stSidebar"] {
    background-color: #10182b;
}
.block-container {
    padding-top: 1.5rem;
}
.hero {
    padding: 25px;
    border-radius: 18px;
    background: linear-gradient(110deg, #172554, #312e81, #164e63);
    margin-bottom: 22px;
}
.hero h1 {
    color: white;
    font-size: 38px;
    margin-bottom: 5px;
}
.hero p {
    color: #dbeafe;
    font-size: 16px;
}
[data-testid="stMetric"] {
    background: #172238;
    border: 1px solid #293751;
    padding: 18px;
    border-radius: 14px;
}
[data-testid="stMetricLabel"] {
    color: #b8c5dc;
}
[data-testid="stMetricValue"] {
    color: #ffffff;
}
.section-title {
    font-size: 23px;
    font-weight: 700;
    margin-top: 22px;
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# LOAD CLEANED DATASET
# --------------------------------------------------
@st.cache_data
def load_data():
    file_path = Path(__file__).parent / "cleaned_video_game_sales.csv"

    if not file_path.exists():
        raise FileNotFoundError(
            "cleaned_video_game_sales.csv was not found."
        )

    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    numeric_columns = [
        "Rank", "Year", "NA_Sales", "EU_Sales",
        "JP_Sales", "Other_Sales", "Global_Sales",
        "Game_Age_2026"
    ]

    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Name", "Platform", "Genre", "Publisher"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unknown").astype(str)

    return df


try:
    df = load_data()
except Exception as e:
    st.error(f"Unable to load dataset: {e}")
    st.info(
        "Keep app.py and cleaned_video_game_sales.csv "
        "inside the same project folder."
    )
    st.stop()

# --------------------------------------------------
# VALIDATE REQUIRED COLUMNS
# --------------------------------------------------
required_columns = [
    "Name", "Platform", "Year", "Genre",
    "Publisher", "Global_Sales"
]

missing_columns = [
    col for col in required_columns if col not in df.columns
]

if missing_columns:
    st.error(f"Missing required columns: {missing_columns}")
    st.write("Available columns:", list(df.columns))
    st.stop()

# --------------------------------------------------
# HEADER
# --------------------------------------------------
st.markdown("""
<div class="hero">
    <h1>🎮 GameScope Pro</h1>
    <p>
        Interactive Video Game Sales Intelligence Dashboard
        <br>
        Explore games, platforms, genres and worldwide sales.
    </p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.title("🎛️ Dashboard Controls")
st.sidebar.caption("Customize your dataset view")

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Release Year")

valid_years = df["Year"].dropna()

if not valid_years.empty:
    min_year = int(valid_years.min())
    max_year = int(valid_years.max())

    if min_year < max_year:
        year_range = st.sidebar.slider(
            "Select year range",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
            key="filter_release_year"
        )
    else:
        year_range = (min_year, max_year)
else:
    year_range = None

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Game Filters")

genres = sorted(df["Genre"].dropna().unique().tolist())
platforms = sorted(df["Platform"].dropna().unique().tolist())
publishers = sorted(df["Publisher"].dropna().unique().tolist())

selected_genres = st.sidebar.multiselect(
    "Select genres",
    options=genres,
    default=genres,
    key="filter_genres"
)

selected_platforms = st.sidebar.multiselect(
    "Select platforms",
    options=platforms,
    default=platforms,
    key="filter_platforms"
)

selected_publishers = st.sidebar.multiselect(
    "Select publishers",
    options=publishers,
    default=publishers,
    key="filter_publishers"
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔎 Search")

search_query = st.sidebar.text_input(
    "Search game title",
    placeholder="e.g. Mario, GTA",
    key="filter_game_search"
)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------
filtered_df = df.copy()

if year_range is not None:
    filtered_df = filtered_df[
        filtered_df["Year"].between(
            year_range[0], year_range[1]
        )
    ]

filtered_df = filtered_df[
    filtered_df["Genre"].isin(selected_genres)
    & filtered_df["Platform"].isin(selected_platforms)
    & filtered_df["Publisher"].isin(selected_publishers)
]

if search_query.strip():
    filtered_df = filtered_df[
        filtered_df["Name"].str.contains(
            search_query.strip(),
            case=False,
            na=False,
            regex=False
        )
    ]

# --------------------------------------------------
# KPI CARDS
# --------------------------------------------------
st.markdown('<div class="section-title">📊 Sales Overview</div>',
            unsafe_allow_html=True)

total_games = len(filtered_df)
total_sales = filtered_df["Global_Sales"].sum()
total_platforms = filtered_df["Platform"].nunique()
total_genres = filtered_df["Genre"].nunique()

if not filtered_df.empty:
    top_game = filtered_df.loc[
        filtered_df["Global_Sales"].idxmax(), "Name"
    ]
    average_sales = filtered_df["Global_Sales"].mean()
else:
    top_game = "N/A"
    average_sales = 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("🎮 Games", f"{total_games:,}")
k2.metric("🌍 Global Sales", f"{total_sales:,.2f}M")
k3.metric("🕹️ Platforms", f"{total_platforms:,}")
k4.metric("🎯 Genres", f"{total_genres:,}")

st.caption(
    f"Average global sales per game: {average_sales:.2f} million"
)

if filtered_df.empty:
    st.warning(
        "No games match your filters. Change the sidebar selections."
    )
    st.stop()

# --------------------------------------------------
# TABS
# --------------------------------------------------
overview_tab, genre_tab, platform_tab, explorer_tab = st.tabs([
    "🏠 Overview",
    "🎯 Genre Analysis",
    "🕹️ Platform Analysis",
    "🔍 Game Explorer"
])

# --------------------------------------------------
# OVERVIEW TAB
# --------------------------------------------------
with overview_tab:

    left, right = st.columns(2)

    with left:
        st.subheader("📈 Global Sales by Release Year")

        yearly = (
            filtered_df.dropna(subset=["Year"])
            .groupby("Year", as_index=False)["Global_Sales"]
            .sum()
            .sort_values("Year")
        )

        if not yearly.empty:
            yearly["Year"] = yearly["Year"].astype(int)

            fig = px.area(
                yearly,
                x="Year",
                y="Global_Sales",
                markers=True,
                title="Worldwide Sales Trend",
                labels={
                    "Global_Sales": "Global Sales (millions)",
                    "Year": "Release Year"
                }
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No valid release-year data available.")

    with right:
        st.subheader("🏆 Top 10 Best-Selling Games")

        top_games = (
            filtered_df.groupby("Name", as_index=False)
            ["Global_Sales"].sum()
            .nlargest(10, "Global_Sales")
            .sort_values("Global_Sales")
        )

        fig = px.bar(
            top_games,
            x="Global_Sales",
            y="Name",
            orientation="h",
            title="Games Ranked by Global Sales",
            labels={
                "Global_Sales": "Global Sales (millions)",
                "Name": "Game"
            },
            text_auto=".2f"
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("🌎 Regional Sales Distribution")

    region_columns = [
        "NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"
    ]
    available_regions = [
        col for col in region_columns if col in filtered_df.columns
    ]

    if available_regions:
        region_names = {
            "NA_Sales": "North America",
            "EU_Sales": "Europe",
            "JP_Sales": "Japan",
            "Other_Sales": "Other Regions"
        }

        regional = pd.DataFrame({
            "Region": [
                region_names[col] for col in available_regions
            ],
            "Sales": [
                filtered_df[col].sum() for col in available_regions
            ]
        })

        fig = px.pie(
            regional,
            names="Region",
            values="Sales",
            hole=0.55,
            title="Share of Regional Sales",
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("✨ Quick Insight")

    st.write(
        f"Within the current selection, **{top_game}** "
        f"has the highest individual global sales."
    )

# --------------------------------------------------
# GENRE ANALYSIS TAB
# --------------------------------------------------
with genre_tab:

    st.subheader("🎯 Compare Sales Across Genres")

    genre_sales = (
        filtered_df.groupby("Genre", as_index=False)
        .agg(
            Global_Sales=("Global_Sales", "sum"),
            Game_Count=("Name", "count")
        )
        .sort_values("Global_Sales", ascending=False)
    )

    fig = px.bar(
        genre_sales,
        x="Genre",
        y="Global_Sales",
        color="Global_Sales",
        title="Total Global Sales by Genre",
        labels={"Global_Sales": "Global Sales (millions)"},
        text_auto=".2f",
        color_continuous_scale="Viridis"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.scatter(
        genre_sales,
        x="Game_Count",
        y="Global_Sales",
        size="Global_Sales",
        color="Genre",
        hover_name="Genre",
        title="Number of Games vs Total Sales",
        labels={
            "Game_Count": "Number of Games",
            "Global_Sales": "Global Sales (millions)"
        }
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(genre_sales, use_container_width=True)

# --------------------------------------------------
# PLATFORM ANALYSIS TAB
# --------------------------------------------------
with platform_tab:

    st.subheader("🕹️ Platform Performance")

    platform_sales = (
        filtered_df.groupby("Platform", as_index=False)
        .agg(
            Global_Sales=("Global_Sales", "sum"),
            Game_Count=("Name", "count")
        )
        .sort_values("Global_Sales", ascending=False)
    )

    top_n = st.slider(
        "Number of platforms to display",
        min_value=5,
        max_value=max(5, min(30, len(platform_sales))),
        value=min(10, max(5, len(platform_sales))),
        key="platform_top_n"
    )

    platform_chart = platform_sales.head(top_n)

    fig = px.bar(
        platform_chart.sort_values("Global_Sales"),
        x="Global_Sales",
        y="Platform",
        orientation="h",
        color="Global_Sales",
        title=f"Top {top_n} Platforms by Global Sales",
        labels={"Global_Sales": "Global Sales (millions)"},
        text_auto=".2f",
        color_continuous_scale="Plasma"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📋 Platform Statistics")
    st.dataframe(platform_sales, use_container_width=True)

# --------------------------------------------------
# GAME EXPLORER TAB
# --------------------------------------------------
with explorer_tab:

    st.subheader("🔍 Explore Your Games")

    sort_by = st.selectbox(
        "Sort games by",
        options=[
            "Global_Sales",
            "Year",
            "Name",
            "NA_Sales",
            "EU_Sales",
            "JP_Sales"
        ],
        index=0,
        key="game_sort_column"
    )

    ascending = st.checkbox(
        "Sort ascending",
        value=False,
        key="game_sort_ascending"
    )

    display_df = filtered_df.sort_values(
        sort_by,
        ascending=ascending,
        na_position="last"
    )

    st.caption(f"Showing {len(display_df):,} matching records.")

    st.dataframe(
        display_df,
        use_container_width=True,
        height=450
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="📥 Download Filtered Dataset",
        data=csv_data,
        file_name="filtered_video_game_sales.csv",
        mime="text/csv",
        key="download_filtered_csv"
    )

# --------------------------------------------------
# FOOTER
# --------------------------------------------------
st.markdown("---")
st.markdown(
    "<center>🎮 GameScope Pro | Foundation of Data Science"
    " | Built with Streamlit, Pandas and Plotly</center>",
    unsafe_allow_html=True
)
