import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit_authenticator as stauth
from collections import defaultdict

st.set_page_config(page_title="Petrol Dashboard", layout="wide")

# ——————————————————————————————————————————————
# 1️⃣ Load and prepare credentials
# ——————————————————————————————————————————————
credentials = {
    "usernames": {
        user: {"name": info["name"], "password": info["password"]}
        for user, info in st.secrets["credentials"]["usernames"].items()
    }
}
cookie_name        = st.secrets["cookie"]["name"]
key                = st.secrets["cookie"]["key"]
cookie_expiry_days = int(st.secrets["cookie"]["expiry_days"])

authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    key,
    cookie_expiry_days,
)

# ——————————————————————————————————————————————
# 2️⃣ Show login form and capture result
# ——————————————————————————————————————————————
login_result = authenticator.login(location="main")

# If still entering credentials, login_result is None → stop here (login UI remains)
if login_result is None:
    st.stop()

name, auth_status, username = login_result

# If login failed or not yet valid, stop (error/warning already shown by login())
if not auth_status:
    st.stop()

# ——————————————————————————————————————————————
# 3️⃣ At this point, user is authenticated
# ——————————————————————————————————————————————
# Offer logout
authenticator.logout("Logout", "sidebar")
st.sidebar.success(f"Welcome, {name}!")

# ——————————————————————————————————————————————
# 4️⃣ Persistent file uploader
# ——————————————————————————————————————————————
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

uploaded = st.file_uploader("Upload the Excel file", type=["xlsx"])
if uploaded:
    st.session_state.uploaded_file = uploaded

if not st.session_state.uploaded_file:
    st.info("Please upload the Excel file to proceed.")
    st.stop()

# ——————————————————————————————————————————————
# 5️⃣ Data processing
# ——————————————————————————————————————————————
df = pd.read_excel(st.session_state.uploaded_file, sheet_name="Data")
df = df.melt(id_vars=["Date"], var_name="Series", value_name="Value")
df["Date"] = pd.to_datetime(df["Date"])

# ——————————————————————————————————————————————
# 6️⃣ Sidebar filters
# ——————————————————————————————————————————————
st.sidebar.header("Filter Data")
all_series   = df["Series"].unique()
selected     = st.sidebar.multiselect("Series (LHS)", all_series, default=all_series)
rhs_series   = st.sidebar.multiselect("Series (RHS)", selected)
third_series = st.sidebar.multiselect("Series (3rd axis)", selected)
fourth_series= st.sidebar.multiselect("Series (4th axis)", selected)

start_date = st.sidebar.date_input("Start Date", value=df["Date"].min())
end_date   = st.sidebar.date_input("End Date",   value=df["Date"].max())
start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

filtered_df = df.query(
    "Series in @selected and Date >= @start_date and Date <= @end_date"
)

# ——————————————————————————————————————————————
# 7️⃣ Display filtered table
# ——————————————————————————————————————————————
st.dataframe(filtered_df)

# ——————————————————————————————————————————————
# 8️⃣ Build and show Plotly figure
# ——————————————————————————————————————————————
fig = go.Figure()
for s in selected:
    data = filtered_df[filtered_df["Series"] == s]
    if s in fourth_series:
        axis, name_label = "y4", f"{s} (4th)"
    elif s in third_series:
        axis, name_label = "y3", f"{s} (3rd)"
    elif s in rhs_series:
        axis, name_label = "y2", f"{s} (RHS)"
    else:
        axis, name_label = "y1", s

    fig.add_trace(go.Scatter(
        x=data["Date"], y=data["Value"],
        mode="lines", name=name_label, yaxis=axis
    ))

# Dynamic formatting map
def is_percent(x): return "%" in x or "rate" in x.lower()
fmt = {s: ("percent" if is_percent(s) else "rands") for s in df["Series"].unique()}

axis_map = defaultdict(list)
for s in selected:
    if s in fourth_series: axis_map["y4"].append(fmt[s])
    elif s in third_series:   axis_map["y3"].append(fmt[s])
    elif s in rhs_series:     axis_map["y2"].append(fmt[s])
    else:                     axis_map["y1"].append(fmt[s])

tickfmt, tickpre = {}, {}
for ax, fmts in axis_map.items():
    if all(f == "percent" for f in fmts):
        tickfmt[ax], tickpre[ax] = ",.0%", ""
    elif all(f == "rands" for f in fmts):
        tickfmt[ax], tickpre[ax] = ",.0f", "R"
    else:
        tickfmt[ax], tickpre[ax] = ",.0f", "R "

fig.update_layout(
    title=f"Petrol: {' vs '.join(selected)}",
    xaxis=dict(title="Date"),
    yaxis = dict(tickformat=tickfmt.get("y1"), tickprefix=tickpre.get("y1")),
    yaxis2= dict(overlaying="y", side="right", showgrid=False,
                 tickformat=tickfmt.get("y2"), tickprefix=tickpre.get("y2")),
    yaxis3= dict(overlaying="y", side="left",  showgrid=False,
                 tickformat=tickfmt.get("y3"), tickprefix=tickpre.get("y3")),
    yaxis4= dict(overlaying="y", side="right", showgrid=False,
                 tickformat=tickfmt.get("y4"), tickprefix=tickpre.get("y4")),
    template="plotly_dark",
    legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="right", x=1),
)

st.plotly_chart(fig, use_container_width=True)



