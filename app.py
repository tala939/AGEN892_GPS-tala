import pandas as pd
import folium
import streamlit as st
 
# Set the page layout to wide (full width)
st.set_page_config(layout="wide")
with open("./income_map.html", "r", encoding="utf-8") as f:
    map_html = f.read()
 
# Add a title for the page
st.title("State Income Map through the US")
st.components.v1.html(map_html, height=600, width=0,scrolling=True)
 
# ---------- Sidebar: data input ----------
st.sidebar.header("Data")
st.sidebar.write("Upload a CSV with columns: state, county, income_2015, income_1989")
uploaded = st.sidebar.file_uploader("Upload counties CSV", type=["csv"])
 
def load_counties_df(file_obj: io.BytesIO | str) -> pd.DataFrame:
    df = pd.read_csv(file_obj)
    # Normalize expected columns
    colmap = {}
    cols = {c.lower(): c for c in df.columns}
    needed = {
        "state": {"state", "stname", "state_name"},
        "county": {"county", "name", "county_name"},
        "income_2015": {"income_2015", "median_2015", "medianincome2015", "income2015"},
        "income_1989": {"income_1989", "median_1989", "medianincome1989", "income1989"},
    }
    for need, alts in needed.items():
        found = next((cols[a] for a in alts if a in cols), None)
        if found:
            colmap[found] = need
    df = df.rename(columns=colmap)
 
    missing = [c for c in ["state", "county", "income_2015", "income_1989"] if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")
 
    # Coerce numerics
    for c in ["income_2015", "income_1989"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
 
    return df
 
counties_df = None
if uploaded is not None:
    counties_df = load_counties_df(uploaded)
elif os.path.exists("counties.csv"):
    counties_df = load_counties_df("counties.csv")
 
# ---------- Layout: map (left) + stats/table (right) ----------
left, right = st.columns([3, 2], gap="large")
 
with left:
    st.subheader("Interactive Map")
    st.caption(f"Loaded from: `{map_path}`")
    st.components.v1.html(map_html, height=600, width=0, scrolling=True)
 
with right:
    st.subheader("County Income Explorer")
 
    if counties_df is None:
        st.info(
            "Upload a counties CSV in the sidebar (or place **counties.csv** in the working directory)."
        )
    else:
        # Build state select options
        states = sorted([s for s in counties_df["state"].dropna().astype(str).unique()])
        if not states:
            st.warning("No states found in the data.")
        else:
            chosen = st.selectbox("Choose a state", states, index=0)
 
            sub = counties_df[counties_df["state"].astype(str) == str(chosen)].copy()
 
            # Stats (medians)
            med_2015 = float(np.nanmedian(sub["income_2015"])) if len(sub) else np.nan
            med_1989 = float(np.nanmedian(sub["income_1989"])) if len(sub) else np.nan
            n_counties = int(len(sub))
 
            c1, c2, c3 = st.columns(3)
            c1.metric("# Counties", f"{n_counties}")
            c2.metric("County Median (2015)", f"${med_2015:,.0f}" if not np.isnan(med_2015) else "–")
            c3.metric("County Median (1989)", f"${med_1989:,.0f}" if not np.isnan(med_1989) else "–")
 
            # Table + % change
            sub["% Change 1989→2015"] = (sub["income_2015"] - sub["income_1989"]) / sub["income_1989"] * 100.0
            table = sub.rename(
                columns={
                    "county": "County",
                    "income_1989": "Income 1989 (USD)",
                    "income_2015": "Income 2015 (USD)",
                }
            )[["County", "Income 1989 (USD)", "Income 2015 (USD)", "% Change 1989→2015"]]
 
            st.dataframe(table.sort_values("Income 2015 (USD)", ascending=False), use_container_width=True)
 
            # Download filtered view
            st.download_button(
                "Download table as CSV",
                table.to_csv(index=False).encode("utf-8"),
                file_name=f"{chosen.replace(' ', '_').lower()}_county_incomes.csv",
                mime="text/csv",
            )
 
# Optional footer notes
with st.expander("Notes"):
    st.write(
        """
        - The interactive map on the left is the Folium HTML you saved.
        - If you're in Colab, make sure your Google Drive is mounted before running Streamlit:
            from google.colab import drive
            drive.mount('/content/drive')
        """
    )
