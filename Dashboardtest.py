import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import defaultdict

st.set_page_config(page_title="Petrol Dashboard", layout="wide")

# ─── 1) Initialize login state ─────────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""

# ─── 2) Show login form if not logged in ──────────────────────────────────
if not st.session_state.logged_in:
    with st.form("login_form"):
        st.write("## Please log in")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            creds = st.secrets["credentials"]  # expects TOML like:
                                              # [credentials]
                                              # user1 = "hash_or_pwd"
            if username in creds and creds[username] == password:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success(f"Welcome, {username}!")
            else:
                st.error("Invalid credentials. Please try again")
    # Stop here and show only the form until success
    st.stop()

# ─── 3) Logged-in dashboard ─────────────────────────────────────────────────
st.sidebar.success(f"👋 Hello, {st.session_state.user}")
st.title("Petrol Dashboard")

# ─── 4) Persistent file uploader ─────────────────────────────────────────────
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

uploaded = st.file_uploader("Upload the Excel file", type=["xlsx"])
if uploaded:
    st.session_state.uploaded_file = uploaded

if not st.session_state.uploaded_file:
    st.info("Please upload the Excel file to proceed.")
    st.stop()

# ─── 5) Data processing ─────────────────────────────────────────────────────
df = pd.read_excel(st.session_state.uploaded_file, sheet_name="Data")
df = df.melt(id_vars=["Date"], var_name="Series", value_name="Value")
df["Date"] = pd.to_datetime(df["Date"])

# ─── 6) Sidebar filters ────────────────────────────────────────────────────
st.sidebar.header("Filter Data:")
all_series   = df["Series"].unique()
selected     = st.sidebar.multiselect("Series (LHS):", all_series, default=all_series)
rhs_series   = st.sidebar.multiselect("Series (RHS):", selected)
third_series = st.sidebar.multiselect("Series (3rd axis):", selected)
fourth_series= st.sidebar.multiselect("Series (4th axis):", selected)

start_date = st.sidebar.date_input("Start Date", value=df["Date"].min())
end_date   = st.sidebar.date_input("End Date",   value=df["Date"].max())
start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

filtered = df.query(
    "Series in @selected and Date >= @start_date and Date <= @end_date"
)
st.dataframe(filtered)

# ─── 7) Build & show Plotly chart ──────────────────────────────────────────
fig = go.Figure()

def is_percent(s): return "%" in s or "rate" in s.lower()
fmt_map = {s: ("percent" if is_percent(s) else "rands") for s in df["Series"].unique()}

axis_map = defaultdict(list)
for s in selected:
    if s in fourth_series: ax = "y4"
    elif s in third_series: ax = "y3"
    elif s in rhs_series:   ax = "y2"
    else:                   ax = "y1"
    axis_map[ax].append(fmt_map[s])

tickfmt, tickpre = {}, {}
for ax, fmts in axis_map.items():
    if all(f=="percent" for f in fmts):
        tickfmt[ax], tickpre[ax] = ",.0%", ""
    elif all(f=="rands" for f in fmts):
        tickfmt[ax], tickpre[ax] = ",.0f", "R"
    else:
        tickfmt[ax], tickpre[ax] = ",.0f", "R "

for s in selected:
    series_data = filtered[filtered["Series"] == s]
    if s in fourth_series:
        ax, name = "y4", f"{s} (4th)"
    elif s in third_series:
        ax, name = "y3", f"{s} (3rd)"
    elif s in rhs_series:
        ax, name = "y2", f"{s} (RHS)"
    else:
        ax, name = "y1", s

    fig.add_trace(go.Scatter(
        x=series_data["Date"],
        y=series_data["Value"],
        mode="lines",
        name=name,
        yaxis=ax
    ))

fig.update_layout(
    title=f"Petrol: {' vs '.join(selected)}",
    xaxis=dict(title="Date"),
    yaxis = dict(tickformat=tickfmt.get("y1"),  tickprefix=tickpre.get("y1")),
    yaxis2=dict(overlaying="y", side="right", showgrid=False,
                tickformat=tickfmt.get("y2"), tickprefix=tickpre.get("y2")),
    yaxis3=dict(overlaying="y", side="left",  showgrid=False,
                tickformat=tickfmt.get("y3"), tickprefix=tickpre.get("y3")),
    yaxis4=dict(overlaying="y", side="right", showgrid=False,
                tickformat=tickfmt.get("y4"), tickprefix=tickpre.get("y4")),
    template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)

