import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit_authenticator as stauth

st.set_page_config(page_title="Petrol Dashboard", layout="wide")

credentials = {
    "usernames": st.secrets["credentials"]["usernames"]
}
cookie_name = st.secrets["cookie"]["name"]
key = st.secrets["cookie"]["key"]
cookie_expiry_days= int(st.secrets["cookie"]["expiry_days"])

authenticator = stauth.Authenticate(
    credentials,
    cookie_name,
    key,
    cookie_expiry_days
)

login_result = authenticator.login(location='main')

if login_result:
    name, authentication_status, username = login_result
    if authentication_status:
        st.success(f"Welcome {name}!")
    elif authentication_status is False:
        st.error("invalid username or password")
    else:
        st.warning("Please login")
        
    if "upload_file" not in st.session_state:
        st.session_state.uploadedfile = None


        uploaded_excel = st.file_uploader("Upload the excel file", type=["xlsx"])

        if uploaded_excel is not None:
            st.session_state.uploaded_file = uploaded_excel

        if st.session_state.uploaded_file:   
            df=pd.read_excel(uploaded_excel,sheet_name="Data")
            df= df.melt(id_vars=['Date'], var_name='Series', value_name='Value')
            df['Date'] = pd.to_datetime(df['Date'])
            st.dataframe(df)
            
        # else: 
        #     st.info("Please upload the Excel file.")
elif authentication_status is False:
            st.error("Invalid username or password.") 
else:
            st.warning("Please log in")          

        #Create a sidebar for user to filter through data:
            st.sidebar.header("Filter Data:")
            selected_series = st.sidebar.multiselect('Choose Relevant Series:',df['Series'].unique(),default=df['Series'].unique())
            rhs_series = st.sidebar.multiselect('Choose Series to plot on Secondary Axis:',selected_series)
            third_series = st.sidebar.multiselect('Choose Series to plot on a Third Axis(LHS):', selected_series)
            fourth_series = st.sidebar.multiselect('Choose Series to plot on Fourth Axis(RHS):',selected_series)

            start_date = st.sidebar.date_input('Select Start Date', value=df['Date'].min())
            end_date = st.sidebar.date_input('Select End Date', value=df['Date'].max())

            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)

            series_name = '<b> vs </b>'.join(selected_series) #to dynamically adjust chart title
            start_year= start_date.year
            end_year = end_date.year

            filtered_df = df.query(
                " Series == @selected_series & Date >= @start_date & Date <= @end_date "

            )
            st.dataframe(filtered_df)


            #MainPage for graphs:
            st.title("Petrol Dashboard")
            st.markdown("##")


            fig_petrol_2 = go.Figure()

            # Add series dynamically after allowing user to select on which axis they would like to display the series
            for series in selected_series:
                series_data = filtered_df[filtered_df['Series'] == series]
            
                if series in fourth_series:
                    axis = 'y4'
                    label = f"{series} (Fourth)"
                elif series in third_series:
                    axis= 'y3'
                    label= f"{series} (Third)"
                elif series in rhs_series:
                    axis = 'y2'
                    label= f"{series} (RHS)"
                else:
                    axis = 'y1'
                    label= f"{series}"
            
                fig_petrol_2.add_trace(go.Scatter(
                    x=series_data['Date'],
                    y=series_data['Value'],
                    mode='lines',
                    name=label,
                    yaxis=axis
                ))

            #Making the Y Axes more Dynamic (i.e anticipate for % or Rand value):

            def is_percent(series_name):
                return '%' in series_name or 'rate' in series_name.lower()

            format_map = {s: 'percent' if is_percent(s) else 'rands' for s in df['Series'].unique()}

            from collections import defaultdict

            # Create a mapping from axis to the list of series formats
            axis_series_map = defaultdict(list)

            for series in selected_series:
                # Assign to axis
                if series in fourth_series:
                    axis = 'y4'
                elif series in third_series:
                    axis = 'y3'
                elif series in rhs_series:
                    axis = 'y2'
                else:
                    axis = 'y1'
                axis_series_map[axis].append(format_map.get(series, 'rands'))
            axis_tickformat = {}
            axis_tickprefix = {}

            for axis, formats in axis_series_map.items():
                if all(f == 'percent' for f in formats):
                    axis_tickformat[axis] = ',.0%'
                    axis_tickprefix[axis] = ''
                elif all(f == 'rands' for f in formats):
                    axis_tickformat[axis] = ',.0f'
                    axis_tickprefix[axis] = 'R'
                else:
                    # Mixed formats: default to Rands (or add custom logic or a warning)
                    axis_tickformat[axis] = ',.0f'
                    axis_tickprefix[axis] = 'R '


            # Layout with three y-axes:
            fig_petrol_2.update_layout(
                title=f"{series_name} [{start_year}- {end_year}]",
                xaxis=dict(title='Date'),
                yaxis=dict(
                    tickformat= axis_tickformat.get('y1'),
                    tickprefix = axis_tickprefix.get('y1'),
                ),
                yaxis2=dict(
                    overlaying='y',
                    side='right',
                    anchor= 'free',
                    autoshift= True,
                    showgrid=False,
                    tickformat = axis_tickformat.get('y2'),  #adjusting for format of axis depending on series selected
                    tickprefix = axis_tickprefix.get('y2'),  #adjusting for the prefix for the axis to show "R" for Rands if Rand Value shown as opposed to % value
                ),
                yaxis3=dict(
                    overlaying = 'y',
                    side = 'left',
                    anchor = 'free',
                    autoshift = True,
                    showgrid = False,
                    tickformat = axis_tickformat.get('y3'),
                    tickprefix = axis_tickprefix.get('y3'),
                ),
                yaxis4=dict(
                    overlaying = 'y',
                    side = 'right',
                    anchor = 'free',
                    autoshift =True,
                showgrid=False,
                tickformat = axis_tickformat.get('y4'),
                tickprefix= axis_tickprefix.get('y4'),
                ),
                template='plotly_dark',
                legend=dict(orientation='h', yanchor='bottom', y=-0.5 , xanchor='right', x=1)
            )
            st.plotly_chart(fig_petrol_2)










