import streamlit as st
import pandas as pd
import pyodbc
import time
import plotly.graph_objects as go
import plotly.express as px

# Database connection details
DRIVER_NAME = "ODBC Driver 17 for SQL Server"  
SERVER_NAME = "34.131.224.43,1433"             
DATABASE_NAME = "RPH-Old-New-Water"            
USERNAME = "sqlserver"                         
PASSWORD = "WaterWorks@123" 

# Establish database connection
@st.cache_resource
def get_db_connection():
    try:
        conn = pyodbc.connect(f"""
            DRIVER={{{DRIVER_NAME}}};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            UID={USERNAME};
            PWD={PASSWORD};
            Encrypt=yes;
            TrustServerCertificate=yes;
        """)
        return conn
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return None

# Fetch the next row of data for a given timestamp
def fetch_next_row(conn, table_name, timestamp):
    query = f"""
        SELECT * 
        FROM {table_name}
        WHERE [Date and Time] = '{timestamp}'
    """
    return pd.read_sql(query, conn)

# Format specific columns to avoid scientific notation
def format_dataframe(df):
    for col in df.select_dtypes(include=['float64', 'int64']).columns:
        df[col] = df[col].apply(lambda x: f"{x:,.2f}")  # Format as comma-separated values with 2 decimal places
    return df

# Create a real-time updating gauge chart
def create_single_gauge_chart(value, title, max_value=5000, 
                              bar_color="#009879", 
                              step_colors=["#f4f4f4", "#d9f4ff", "#0074d9"],
                              thresholds=None,
                              background_color="#28282B"):
    mid_value = max_value / 2
    high_value = max_value * 0.8

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': "darkgrey"},
            'bar': {'color': bar_color},
            'steps': [
                {'range': [0, mid_value], 'color': step_colors[0]},
                {'range': [mid_value, high_value], 'color': step_colors[1]},
                {'range': [high_value, max_value], 'color': step_colors[2]}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    percentage = (value / max_value) * 100
    fig.add_annotation(
        x=0.10, y=0.3, 
        text=f"{percentage:.1f}%", 
        showarrow=False, 
        font=dict(size=14, color="white")
    )

    fig.update_layout(
        width=450,
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor=background_color,
        plot_bgcolor=background_color
    )
    return fig

# Create a real-time line chart
def create_real_time_line_chart(data, x_col, y_col, title):
    fig = px.line(data, x=x_col, y=y_col, title=title)
    fig.update_layout(
        width=700,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Create a real-time pie chart
def create_real_time_pie_chart(data, values_col, names_col, title):
    fig = px.pie(data, values=values_col, names=names_col, title=title)
    fig.update_layout(
        width=500,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# Display gauges and other charts
def display_metrics(conn, table_name, timestamps_list, flow_values, total_values):
    # Create placeholders for gauges, bar charts, line chart, and pie chart
    gauge_columns = st.columns(7)
    gauge_placeholders = [col.empty() for col in gauge_columns]
    totalizer_bar_columns = st.columns(7)
    totalizer_bar_placeholders = [col.empty() for col in totalizer_bar_columns]
    line_chart_placeholder = st.empty()  # Placeholder for the line chart
    pie_chart_placeholder = st.empty()  # Placeholder for the pie chart

    displayed_data = pd.DataFrame()

    for timestamp in timestamps_list:
        # Fetch the new row based on the current timestamp
        new_row = fetch_next_row(conn, table_name, timestamp)
        displayed_data = pd.concat([displayed_data, new_row], ignore_index=True)
        displayed_data = format_dataframe(displayed_data)

        if not new_row.empty:
            # Update gauge charts
            for i, (col_name, max_value) in enumerate(flow_values):
                value = float(new_row.iloc[0].get(col_name, 0))
                with gauge_placeholders[i]:
                    st.plotly_chart(
                        create_single_gauge_chart(value, col_name, max_value),
                        use_container_width=True
                    )

            # Update bar charts
            for i, (col_name, max_value) in enumerate(total_values):
                value = float(new_row.iloc[0].get(col_name, 0))
                bar_chart = go.Figure(go.Bar(
                    x=[col_name],
                    y=[value],
                    marker_color='#0074d9',
                    name=col_name
                ))
                bar_chart.update_layout(
                    title=f"{col_name} Bar Chart",
                    xaxis_title="Totalizer",
                    yaxis_title="Value",
                    showlegend=False,
                    width=400,
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                with totalizer_bar_placeholders[i]:
                    st.plotly_chart(bar_chart, use_container_width=True)

            # Update the line chart
            line_chart = create_real_time_line_chart(
                displayed_data,
                x_col="Date and Time",
                y_col=flow_values[0][0],  # Assuming the first flow value column is used
                title="Flow Rates Over Time"
            )
            line_chart_placeholder.plotly_chart(line_chart, use_container_width=True)

            # Update the pie chart
            pie_chart = create_real_time_pie_chart(
                displayed_data,
                values_col=total_values[0][0],  # Assuming the first flow value column is used
                names_col="Date and Time",
                title="Flow Rate Distribution"
            )
            pie_chart_placeholder.plotly_chart(pie_chart, use_container_width=True)

        else:
            st.warning(f"No data found for timestamp: {timestamp}")

        time.sleep(1)


# Initialize Streamlit app
st.set_page_config(page_title="Water Works Dashboard", layout="wide")

# Sidebar for navigation
if "active_page" not in st.session_state:
    st.session_state.active_page = "New RPH"

def set_page(page):
    st.session_state.active_page = page

with st.sidebar:
    st.title("Water Works Navigation")
    st.markdown("---")
    page = st.radio(
        "Go to Page",
        ["New RPH", "Old RPH"],
        key="active_page",
        on_change=lambda: set_page(st.session_state.active_page)
    )

# Navigation logic
if st.session_state.active_page == "New RPH":
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>New RPH Page</h1>", unsafe_allow_html=True)
    conn = get_db_connection()
    if conn:
        timestamps_query = """
            SELECT DISTINCT [Date and Time] 
            FROM NEW_RPH_Overview_Flow_DetailsRe$
            ORDER BY [Date and Time]
        """
        try:
            timestamps_df = pd.read_sql(timestamps_query, conn)
            timestamps_list = timestamps_df['Date and Time'].tolist()

            flow_values = [
                ('MO 06 Flow Rate', 1000),
                ('MO 07 Flow Rate', 1000),
                ('MO 04 Flow Rate', 1000),
                ('MO 06 A Flow Rate', 1000),
                ('MO 07 A Flow Rate', 1000),
                ('10 MGD Flow Rate', 1000),
                ('OUTLET OF BARA TTP Flow Rate', 1000),
            ]

            total_values = [
                ('MO 06 Totalizer', 1000),
                ('MO 07 Totalizer', 1000),
                ('MO 04 Totalizer', 1000),
                ('MO 06 A Totalizer', 1000),
                ('MO 07 A Totalizer', 1000),
                ('10 MGD Totalizer', 1000),
                ('OUTLET OF BARA TTP Totalizer', 1000),
            ]

            display_metrics(conn, "NEW_RPH_Overview_Flow_DetailsRe$", timestamps_list, flow_values, total_values)
        except Exception as e:
            st.error(f"Error fetching timestamps: {e}")

elif st.session_state.active_page == "Old RPH":
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>Old RPH Page</h1>", unsafe_allow_html=True)
    conn = get_db_connection()
    if conn:
        timestamps_query = """
            SELECT DISTINCT [Date and Time] 
            FROM Old_Rph
            ORDER BY [Date and Time]
        """
        try:
            timestamps_df = pd.read_sql(timestamps_query, conn)
            timestamps_list = timestamps_df['Date and Time'].tolist()

            flow_values = [
                ('MO 03 A Flow Rate', 1000),
                ('MO 05 Flow Rate', 1000),
                ('MO 08 Flow Rate', 1000),
                ('MO 09 A Flow Rate', 1000),
                ('MO 09 B Flow Rate', 1000),
                ('MO 09 C Flow Rate', 1000),
            ]

            total_values = [
                ('MO 03 A Totalizer', 1000),
                ('MO 05 Totalizer', 1000),
                ('MO 08 Totalizer', 1000),
                ('MO 09 A Totalizer', 1000),
                ('MO 09 B Totalizer', 1000),
                ('MO 09 C Totalizer', 1000),
            ]

            display_metrics(conn, "Old_Rph", timestamps_list, flow_values, total_values)
        except Exception as e:
            st.error(f"Error fetching timestamps: {e}")
