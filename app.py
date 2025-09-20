import pandas as pd
import streamlit as st
import os

# ---------- Page setup ----------
st.set_page_config(layout="wide", page_title="State Income Map through the US")

# Use one variable everywhere for the map file
MAP_PATH = "income_map.html"

# ---------- Load the saved Folium map HTML ----------
map_html = None
if os.path.exists(MAP_PATH):
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        map_html = f.read()
else:
    st.warning(f"Map file not found at `{MAP_PATH}`. Place the generated HTML next to app.py.")

# ---------- Title + (optional) map render at top ----------
st.title("State Income Map through the US")

# If you want the map also at the top, keep this; otherwise remove it.
if map_html:
    st.components.v1.html(map_html, height=600, scrolling=True)

# ---------- Load county income data (from GitHub) ----------
DATA_URL = "https://raw.githubusercontent.com/pri-data/50-states/master/data/income-counties-states-national.csv"

@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, dtype={"fips": str})
    df["income-2015"] = pd.to_numeric(df.get("income-2015"), errors="coerce")
    df["income-1989"] = pd.to_numeric(df.get("income-1989"), errors="coerce")
    df = df.rename(columns={"state": "State", "county": "County"})
    return df

df = load_data(DATA_URL)

# ---------- Sidebar controls ----------
st.sidebar.header("Controls")
states = sorted(df["State"].dropna().astype(str).unique().tolist())
chosen = st.sidebar.selectbox("Choose a state", states, index=0 if states else None)

# ---------- Layout: Map (left) + Explorer (right) ----------
left, right = st.columns([3, 2], gap="large")

with left:
    st.subheader("Interactive Map")
    st.caption(f"Loaded from: `{MAP_PATH}`")
    if map_html:
        st.components.v1.html(map_html, height=650, scrolling=True)
    else:
        st.info("Map HTML not found yet. Generate it and save as income_map.html.")

with right:
    st.subheader("County Income Explorer")
    if not states:
        st.info("No data loaded.")
    else:
        sub = df[df["State"] == chosen].copy()

        # Medians + counts
        med_2015 = sub["income-2015"].median(skipna=True)
        med_1989 = sub["income-1989"].median(skipna=True)
        n_counties = len(sub)

        c1, c2, c3 = st.columns(3)
        c1.metric("# Counties", f"{n_counties}")
        c2.metric("County Median (2015)", f"${med_2015:,.0f}" if pd.notna(med_2015) else "–")
        c3.metric("County Median (1989)", f"${med_1989:,.0f}" if pd.notna(med_1989) else "–")

        # Table (+ % change)
        sub["Income 1989 (USD)"] = sub["income-1989"]
        sub["Income 2015 (USD)"] = sub["income-2015"]
        sub["% Change 1989→2015"] = (
            (sub["income-2015"] - sub["income-1989"]) / sub["income-1989"] * 100.0
        )

        table = sub[["County", "Income 1989 (USD)", "Income 2015 (USD)", "% Change 1989→2015"]] \
                  .sort_values("Income 2015 (USD)", ascending=False)

        st.dataframe(table, use_container_width=True)

        st.download_button(
            "Download table as CSV",
            table.to_csv(index=False).encode("utf-8"),
            file_name=f"{chosen.lower().replace(' ', '_')}_county_incomes.csv",
            mime="text/csv",
        )
