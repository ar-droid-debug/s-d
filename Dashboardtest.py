import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit_authenticator as stauth
from collections import defaultdict

# Page configuration
st.set_page_config(page_title="Petrol Dashboard", layout="wide")

# 1) Load credentials from Streamlit Secrets into a mutable dict
credentials = {
    "usernames": {
        user: {"name": info["name"], "password": info["password"]}
        for user, info in st.secrets["credentials"]["usernames"].items()
    }
}
cookie_name = st.secrets["cookie"]["name"]
key = st.secrets["cookie"]["key"]
cookie_expiry_days = int(st.secrets["cookie"]["expiry_days"])

# 2) Initialize authenticator
authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    key,
    cookie_expiry_days,
)

# 3) Show login form and capture result
login_result = authenticator.login(location="main")
if not login_result:
    # No submission yet
    st.warning("Please enter your username and password.")
    st.stop()

name, auth_status, username = login_result

# 4) Check authentication status
if not auth_status:
    st.error("❌ Invalid username or password.")
    st.stop()

# 5) Authenticated: show logout and sidebar welcome
authenticator.logout("Logout", "sidebar")
st.sidebar.success(f"Welcome, {name}!")

# 6) Persistent file upload
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

uploaded = st.file_uploader("Upload the Excel file", type=["xlsx"])
if uploaded:
    st.session_state.uploaded_file = uploaded

if not st.session_state.uploaded_file:
    st.info("Please upload the Excel file to proceed.")
    st.stop()

# 7) Data processing
_df = pd.read_excel(st.session_state.uploaded_file, sheet_name="Data")
df = _df.melt(id_vars=["Date"], var_name="Series", value_name="Value")
df["Date"] = pd.to_datetime(df["Date"])
st.dataframe(df)

# 8) Sidebar filters
st.sidebar.header("Filter Data")
all_series = df["Series"].unique()
selected = st.sidebar.multiselect("Series (LHS)", all_series, default=all_series)
rhs_series = st.sidebar.multiselect("Series (RHS)", selected)
third_series = st.sidebar.multiselect("Series (3rd axis)", selected)
fourth_series = st.sidebar.multiselect("Series (4th axis)", selected)
start_date = st.sidebar.date_input("Start Date", value=df["Date"].min())
end_date = st.sidebar.date_input("End Date", value=df["Date"].max())
start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)
filtered_df = df.query(
    "Series in @selected and Date >= @start_date and Date <= @end_date"
)
st.dataframe(filtered_df)

# 9) Plotly chart
fig = go.Figure()
for s in selected:
    data = filtered_df[filtered_df["Series"] == s]
    if s in fourth_series:
        axis, label = 'y4', f"{s} (4th)"
    elif s in third_series:
        axis, label = 'y3', f"{s} (3rd)"
    elif s in rhs_series:
        axis, label = 'y2', f"{s} (RHS)"
    else:
        axis, label = 'y1', s
    fig.add_trace(go.Scatter(x=data["Date"], y=data["Value"], mode='lines', name=label, yaxis=axis))

# dynamic axis formatting
def is_percent(x): return '%' in x or 'rate' in x.lower()
format_map = {s: ('percent' if is_percent(s) else 'rands') for s in df['Series'].unique()}
axis_series_map = defaultdict(list)
for s in selected:
    ax = 'y1'
    if s in fourth_series: ax = 'y4'
    elif s in third_series: ax = 'y3'
    elif s in rhs_series: ax = 'y2'
    axis_series_map[ax].append(format_map[s])
tickfmt, tickpre = {}, {}
for ax, fmts in axis_series_map.items():
    if all(f=='percent' for f in fmts): tickfmt[ax], tickpre[ax] = ',.0%', ''
    elif all(f=='rands'  for f in fmts): tickfmt[ax], tickpre[ax] = ',.0f','R'
    else: tickfmt[ax], tickpre[ax] = ',.0f','R '
fig.update_layout(
    title=f"Petrol: {' vs '.join(selected)} [{start_date.year}-{end_date.year}]",
    xaxis=dict(title='Date'),
    yaxis = dict(tickformat=tickfmt.get('y1'), tickprefix=tickpre.get('y1')),
    yaxis2=dict(overlaying='y', side='right', showgrid=False, tickformat=tickfmt.get('y2'), tickprefix=tickpre.get('y2')),
    yaxis3=dict(overlaying='y', side='left',  showgrid=False, tickformat=tickfmt.get('y3'), tickprefix=tickpre.get('y3')),
    yaxis4=dict(overlaying='y', side='right', showgrid=False, tickformat=tickfmt.get('y4'), tickprefix=tickpre.get('y4')),
    template='plotly_dark', legend=dict(orientation='h', yanchor='bottom', y=-0.5, xanchor='right', x=1)
)
st.plotly_chart(fig, use_container_width=True)


