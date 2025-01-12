import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import plotly.express as px

# Load Excel data
@st.cache_data
def load_excel_data(file_path):
    try:
        if file_path.endswith('.xlsx'):
            return pd.read_excel(file_path, engine='openpyxl')
        else:
            raise ValueError("Unsupported file format. Please use .xlsx files.")
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
    except Exception as e:
        st.error(f"Failed to load data: {e}")
    return pd.DataFrame()

# Fetch the next row based on the timestamp
def fetch_next_row(df, timestamp):
    """Fetch the next row based on a timestamp."""
    return df[df['Date and Time'] == timestamp]

# Create a gauge chart
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

    fig.update_layout(
        width=450,
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor=background_color,
        plot_bgcolor=background_color
    )
    return fig

# Create a line chart
def create_real_time_line_chart(data, x_col, y_col, title):
    if x_col not in data or y_col not in data:
        return px.line()  # Return an empty figure if columns are missing

    # Determine high and low points
    max_value = data[y_col].max()
    min_value = data[y_col].min()
    max_point = data.loc[data[y_col].idxmax()]
    min_point = data.loc[data[y_col].idxmin()]

    # Create the line chart
    fig = px.line(
        data,
        x=x_col,
        y=y_col,
        title=title,
        markers=True,  # Enable markers for each data point
    )

    # Add annotations for the high and low points
    fig.add_annotation(
        x=max_point[x_col],
        y=max_value,
        text=f"High: {max_value:.2f}",
        showarrow=True,
        arrowhead=2,
        ax=20,
        ay=-40,
        font=dict(color="green", size=12),
        arrowcolor="green",
    )
    fig.add_annotation(
        x=min_point[x_col],
        y=min_value,
        text=f"Low: {min_value:.2f}",
        showarrow=True,
        arrowhead=2,
        ax=-20,
        ay=40,
        font=dict(color="red", size=12),
        arrowcolor="red",
    )

    # Customize the layout for better visualization
    fig.update_traces(
        line=dict(width=2, color="blue"),  # Customize line color and width
        marker=dict(size=8, symbol='circle', color="blue")  # Customize marker size and style
    )
    fig.update_layout(
        width=800,
        height=450,
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis_title=x_col,
        yaxis_title=y_col,
        hovermode="x unified",  # Show hover information for x-axis
    )
    return fig


# Create a grouped bar chart for totalizer values
def create_grouped_bar_chart(data, x_col, y_cols, title):
    fig = go.Figure()
    for y_col in y_cols:
        fig.add_trace(go.Bar(
            x=data[x_col],
            y=data[y_col],
            name=y_col
        ))
    fig.update_layout(
        barmode='group',
        title=title,
        xaxis_title=x_col,
        yaxis_title="Values",
        width=700,
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig

# Display metrics (Updated)
def display_metrics(df, timestamps_list, flow_values, total_values):
    gauge_columns = st.columns(7)
    gauge_placeholders = [col.empty() for col in gauge_columns]
    totalizer_bar_columns = st.columns(7)
    totalizer_bar_placeholders = [col.empty() for col in totalizer_bar_columns]
    line_chart_placeholder = st.empty()
    grouped_bar_chart_placeholder = st.empty()  # Placeholder for the grouped bar chart

    displayed_data = pd.DataFrame()

    for timestamp in timestamps_list:
        new_row = fetch_next_row(df, timestamp)
        displayed_data = pd.concat([displayed_data, new_row], ignore_index=True)

        if not new_row.empty:
            # Update gauge charts
            for i, (col_name, max_value) in enumerate(flow_values):
                value = float(new_row.iloc[0].get(col_name, 0))
                with gauge_placeholders[i]:
                    st.plotly_chart(
                        create_single_gauge_chart(value, col_name, max_value),
                        use_container_width=True,
                        key=f"gauge_{timestamp}_{i}"
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
                    showlegend=False
                )
                with totalizer_bar_placeholders[i]:
                    st.plotly_chart(
                        bar_chart,
                        use_container_width=True,
                        key=f"bar_{timestamp}_{i}"
                    )

            # Update the line chart
            line_chart = create_real_time_line_chart(
                displayed_data,
                x_col="Date and Time",
                y_col=flow_values[0][0],
                title="Flow Rates Over Time"
            )
            line_chart_placeholder.plotly_chart(
                line_chart,
                use_container_width=True,
                key=f"line_chart_{timestamp}"
            )

            # Update the grouped bar chart
            grouped_bar_chart = create_grouped_bar_chart(
                displayed_data,
                x_col="Date and Time",
                y_cols=[col_name for col_name, _ in total_values],
                title="Flow Rates Grouped by Timestamp"
            )
            grouped_bar_chart_placeholder.plotly_chart(
                grouped_bar_chart,
                use_container_width=True,
                key=f"grouped_bar_chart_{timestamp}"
            )

        else:
            st.warning(f"No data found for timestamp: {timestamp}")

        time.sleep(15)


# Streamlit app configuration
st.set_page_config(page_title="Water Works Dashboard", layout="wide")

# Sidebar navigation
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

# Page logic
if st.session_state.active_page == "New RPH":
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>New RPH Page</h1>", unsafe_allow_html=True)
    NEW_RPH_FILE = "https://github.com/Adi0604/Water_Works/raw/refs/heads/main/NEW_RPH_Overview_Flow_DetailsReport%20(1).xlsx"  # Replace with your file path
    data = load_excel_data(NEW_RPH_FILE)
    if not data.empty:
        timestamps_list = data['Date and Time'].drop_duplicates().tolist()
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
        display_metrics(data, timestamps_list, flow_values, total_values)

elif st.session_state.active_page == "Old RPH":
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>Old RPH Page</h1>", unsafe_allow_html=True)
    OLD_RPH_FILE = "https://github.com/Adi0604/Water_Works/raw/refs/heads/main/Old_rph.xlsx"  # Replace with your file path
    data = load_excel_data(OLD_RPH_FILE)
    if not data.empty:
        timestamps_list = data['Date and Time'].drop_duplicates().tolist()
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
        display_metrics(data, timestamps_list, flow_values, total_values)
