import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit_authenticator as stauth
from collections import defaultdict

st.set_page_config(page_title="Petrol Dashboard", layout="wide")

# --- Secure login setup ---
credentials = {
    "usernames": {k: dict(v) for k, v in st.secrets["credentials"]["usernames"].items()}
}
cookie_name = st.secrets["cookie"]["name"]
key = st.secrets["cookie"]["key"]
cookie_expiry_days = int(st.secrets["cookie"]["expiry_days"])

authenticator = stauth.Authenticate(credentials, cookie_name, key, cookie_expiry_days)

# --- Login form ---
name, authentication_status, username = authenticator.login(location='main')

# Persist authentication in session state
if authentication_status:
    st.session_state["authenticated"] = True
elif authentication_status is False:
    st.session_state["authenticated"] = False
    st.error("Invalid username or password")
elif authentication_status is None and "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
    st.warning("Please log in")

# --- Show dashboard if authenticated ---
if st.session_state.get("authenticated"):
    st.success(f"Welcome {name}!")

    # --- Persistent file upload ---
    if "uploaded_file" not in st.session_state:
        st.session_state.uploaded_file = None

    uploaded_excel = st.file_uploader("Upload the Excel file", type=["xlsx"])
    if uploaded_excel is not None:
        st.session_state.uploaded_file = uploaded_excel

    # --- Only show dashboard if file is uploaded ---
    if st.session_state.uploaded_file:
        df = pd.read_excel(st.session_state.uploaded_file, sheet_name="Data")
        df = df.melt(id_vars=['Date'], var_name='Series', value_name='Value')
        df['Date'] = pd.to_datetime(df['Date'])
        st.dataframe(df)

        # --- Sidebar Filters ---
        st.sidebar.header("Filter Data:")
        selected_series = st.sidebar.multiselect(
            'Choose Relevant Series:',
            df['Series'].unique(),
            default=df['Series'].unique()
        )
        rhs_series = st.sidebar.multiselect('Secondary Axis:', selected_series)
        third_series = st.sidebar.multiselect('Third Axis (LHS):', selected_series)
        fourth_series = st.sidebar.multiselect('Fourth Axis (RHS):', selected_series)

        start_date = st.sidebar.date_input('Select Start Date', value=df['Date'].min())
        end_date = st.sidebar.date_input('Select End Date', value=df['Date'].max())
        start_date, end_date = pd.to_datetime(start_date), pd.to_datetime(end_date)

        # --- Filtered dataframe ---
        series_name = '<b> vs </b>'.join(selected_series)
        start_year, end_year = start_date.year, end_date.year
        filtered_df = df.query(
            "Series == @selected_series & Date >= @start_date & Date <= @end_date"
        )
        st.dataframe(filtered_df)

        # --- Plotly Chart ---
        st.title("Petrol Dashboard")
        fig_petrol_2 = go.Figure()

        # Add series dynamically with axis assignment
        for series in selected_series:
            series_data = filtered_df[filtered_df['Series'] == series]
            if series in fourth_series:
                axis, label = 'y4', f"{series} (Fourth)"
            elif series in third_series:
                axis, label = 'y3', f"{series} (Third)"
            elif series in rhs_series:
                axis, label = 'y2', f"{series} (RHS)"
            else:
                axis, label = 'y1', series

            fig_petrol_2.add_trace(go.Scatter(
                x=series_data['Date'],
                y=series_data['Value'],
                mode='lines',
                name=label,
                yaxis=axis
            ))

        # Axis formatting
        def is_percent(name): return '%' in name or 'rate' in name.lower()
        format_map = {s: 'percent' if is_percent(s) else 'rands' for s in df['Series'].unique()}

        axis_series_map = defaultdict(list)
        for series in selected_series:
            if series in fourth_series: axis = 'y4'
            elif series in third_series: axis = 'y3'
            elif series in rhs_series: axis = 'y2'
            else: axis = 'y1'
            axis_series_map[axis].append(format_map.get(series, 'rands'))

        axis_tickformat, axis_tickprefix = {}, {}
        for axis, formats in axis_series_map.items():
            if all(f == 'percent' for f in formats):
                axis_tickformat[axis] = ',.0%'; axis_tickprefix[axis] = ''
            elif all(f == 'rands' for f in formats):
                axis_tickformat[axis] = ',.0f'; axis_tickprefix[axis] = 'R'
            else:
                axis_tickformat[axis] = ',.0f'; axis_tickprefix[axis] = 'R '

        # Chart layout
        fig_petrol_2.update_layout(
            title=f"{series_name} [{start_year}-{end_year}]",
            xaxis=dict(title='Date'),
            yaxis=dict(tickformat=axis_tickformat.get('y1'), tickprefix=axis_tickprefix.get('y1')),
            yaxis2=dict(overlaying='y', side='right', showgrid=False,
                        tickformat=axis_tickformat.get('y2'), tickprefix=axis_tickprefix.get('y2')),
            yaxis3=dict(overlaying='y', side='left', showgrid=False,
                        tickformat=axis_tickformat.get('y3'), tickprefix=axis_tickprefix.get('y3')),
            yaxis4=dict(overlaying='y', side='right', showgrid=False,
                        tickformat=axis_tickformat.get('y4'), tickprefix=axis_tickprefix.get('y4')),
            template='plotly_dark',
            legend=dict(orientation='h', yanchor='bottom', y=-0.5, xanchor='right', x=1)
        )
        st.plotly_chart(fig_petrol_2)
    else:
        st.info("Please upload an Excel file to see the dashboard.")
else:
    st.warning("Please log in")





