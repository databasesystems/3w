import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import calendar


# Initialize session state for selected date
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")

def init_db():
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            sugar REAL,
            salt REAL,
            flour REAL
        )
    ''')
    conn.commit()
    conn.close()
    return "Database initialized"

def save_to_db(sugar, salt, flour, date_str=None):
    """
    Save values to the database for a specific date.
    If date_str is None, use current date.
    """
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    
    # If no date provided, use current date
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    # Check if a record for this date already exists
    c.execute("""
        SELECT id FROM measurements 
        WHERE date(timestamp) = ?
    """, (date_str,))
    
    existing_record = c.fetchone()
    
    if existing_record:
        # Update existing record
        c.execute("""
            UPDATE measurements 
            SET sugar = ?, salt = ?, flour = ?
            WHERE date(timestamp) = ?
        """, (sugar, salt, flour, date_str))
    else:
        # Create new record with specific date
        c.execute("""
            INSERT INTO measurements (sugar, salt, flour, timestamp) 
            VALUES (?, ?, ?, ?)
        """, (sugar, salt, flour, date_str))
    
    conn.commit()
    conn.close()

def get_daily_averages():
    conn = sqlite3.connect('3whites.db')
    df = pd.read_sql_query('''
        SELECT 
            date(timestamp) as date,
            AVG(sugar) as sugar,
            AVG(salt) as salt,
            AVG(flour) as flour
        FROM measurements
        GROUP BY date(timestamp)
        ORDER BY date
    ''', conn)
    conn.close()
    return df

def get_average_for_day(date_str):
    """
    Get the average of sugar, salt, and flour for a specific day.
    This is used for coloring the calendar.
    """
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    
    c.execute("""
        SELECT (sugar + salt + flour) / 3 
        FROM measurements 
        WHERE date(timestamp) = ?
    """, (date_str,))
    
    result = c.fetchone()
    conn.close()
    
    return result[0] if result else None

def display_calendar_table():
    # Initialize session state for selected date if not exists
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")
        
    st.subheader(f" {datetime.now().strftime('%B %Y')}")

    # Add a legend with exact calendar colors and black text
    st.markdown(
        """
        <div style="font-size: 0.85em; margin: -5px 0 15px 0; text-align: center;">
            <span style="background-color: #c8e6c9; color: black; padding: 0 8px; border-radius: 3px;">Good job!</span> &nbsp;&nbsp; 
            <span style="background-color: #fff9c4; color: black; padding: 0 8px; border-radius: 3px;">Be aware</span> &nbsp;&nbsp; 
            <span style="background-color: #ffcdd2; color: black; padding: 0 8px; border-radius: 3px;">You are overdoing it</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Get daily data from database
    conn = sqlite3.connect('3whites.db')
    daily_data = pd.read_sql_query('''
        SELECT 
            date(timestamp) as date,
            sugar,
            salt,
            flour
        FROM measurements
        ORDER BY date
    ''', conn)
    conn.close()
    
    # Convert daily_data dates to strings for comparison
    if not daily_data.empty:
        daily_data['date'] = pd.to_datetime(daily_data['date'])
        daily_data['date_str'] = daily_data['date'].dt.strftime('%Y-%m-%d')
    
    # Get current month and year
    now = datetime.now()
    year, month = now.year, now.month
    
    # Get month calendar
    cal = calendar.monthcalendar(year, month)
    
    # Check URL parameter for date selection
    if "date" in st.query_params:
        date_param = st.query_params["date"]
        if date_param != st.session_state.selected_date:
            st.session_state.selected_date = date_param
            st.rerun()
    
    # Build HTML table for calendar
    html = """
    <style>
    .calendar-table {
        width: 100%;
        table-layout: fixed;
        border-collapse: separate;
        border-spacing: 2px;
    }
    .calendar-table th {
        text-align: center;
        padding: 5px;
        font-weight: bold;
    }
    .calendar-table td {
        text-align: center;
        padding: 5px;
        border-radius: 5px;
        height: 30px;
    }
    .calendar-table a {
        text-decoration: none;
        color: black;
        display: block;
        width: 100%;
        height: 100%;
    }
    .calendar-table a:hover {
        font-weight: bold;
    }
    .selected-date {
        border: 2px solid #333;
        font-weight: bold;
    }
    </style>
    <table class="calendar-table">
      <thead>
        <tr>
          <th>M</th>
          <th>T</th>
          <th>W</th>
          <th>T</th>
          <th>F</th>
          <th>S</th>
          <th>S</th>
        </tr>
      </thead>
      <tbody>
    """
    
    # Add calendar days to table
    for week in cal:
        html += "<tr>"
        for day in week:
            if day == 0:
                # Empty cell
                html += "<td></td>"
            else:
                # Format the date string
                date_str = f"{year}-{month:02d}-{day:02d}"
                
                # Check if this is the selected date
                selected_class = " selected-date" if date_str == st.session_state.selected_date else ""
                
                # Check if we have data for this day
                if not daily_data.empty and date_str in daily_data['date_str'].values:
                    # Get data for this day
                    day_data = daily_data[daily_data['date_str'] == date_str]
                    sugar_val = day_data['sugar'].values[0]
                    salt_val = day_data['salt'].values[0]
                    flour_val = day_data['flour'].values[0]
                    
                    # Calculate average
                    avg_val = (sugar_val + salt_val + flour_val) / 3
                    
                    # Determine color based on average
                    if avg_val < 3:
                        bg_color = "#c8e6c9"  # Light green
                    elif avg_val < 4:
                        bg_color = "#fff9c4"  # Light yellow
                    else:
                        bg_color = "#ffcdd2"  # Light red
                    
                    # Add colored day cell with clickable link
                    html += f'<td class="{selected_class}" style="background-color:{bg_color};"><a href="?date={date_str}">{day}</a></td>'
                else:
                    # Add regular day cell with clickable link
                    html += f'<td class="{selected_class}" style="background-color:#f5f5f5;"><a href="?date={date_str}">{day}</a></td>'
        
        html += "</tr>"
    
    html += """
      </tbody>
    </table>
    """
    
    # Display the HTML table
    st.markdown(html, unsafe_allow_html=True)

def get_today_record():
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if a record for today exists
    c.execute("""
        SELECT sugar, salt, flour 
        FROM measurements 
        WHERE date(timestamp) = ?
    """, (today,))
    
    record = c.fetchone()
    conn.close()
    
    if record:
        return {"sugar": record[0], "salt": record[1], "flour": record[2]}
    else:
        return {"sugar": 5.0, "salt": 5.0, "flour": 5.0}



def add_footer():
    # Add a divider
    st.divider()
    
    # Get current year
    current_year = datetime.now().year
    
    # Create footer with copyright text
    st.markdown(
        f"""
        <div style="text-align: left; color: #888; padding: 10px 0;">
        Developed by databasesystems.info
        <br> © {current_year} All rights reserved.
        </div>
        """, 
        unsafe_allow_html=True
    )

def get_record_for_date(date_str):
    """
    Get the sugar, salt, flour values for a specific date.
    If no record exists, return default values.
    """
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    
    # Check if a record for the selected date exists
    c.execute("""
        SELECT sugar, salt, flour 
        FROM measurements 
        WHERE date(timestamp) = ?
    """, (date_str,))
    
    record = c.fetchone()
    conn.close()
    
    if record:
        return {"sugar": record[0], "salt": record[1], "flour": record[2]}
    else:
        return {"sugar": 5.0, "salt": 5.0, "flour": 5.0}  # Default values

def main():
    st.title("🍚 3 whites tracker")

    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
    
    # Initialize session state for selected date if not exists
    if 'selected_date' not in st.session_state:
        st.session_state.selected_date = datetime.now().strftime("%Y-%m-%d")
    
    # Check URL parameter for date selection
    if "date" in st.query_params:
        date_param = st.query_params["date"]
        if date_param != st.session_state.selected_date:
            st.session_state.selected_date = date_param
            st.rerun()
    
    # Get record for selected date
    selected_date = st.session_state.selected_date
    record = get_record_for_date(selected_date)
    
    # Format the selected date for display
    selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
    formatted_date = selected_date_obj.strftime("%A, %B %d, %Y")
    
    # Simple sliders with values for the selected date
    st.subheader("Intake Values")
    st.write(f"Values for: **{formatted_date}**")
    
    st.divider()
    sugar = st.slider("🍬 Sugar", 1.0, 10.0, record["sugar"], 0.01)
    salt = st.slider("🧂Salt", 1.0, 10.0, record["salt"], 0.01)
    flour = st.slider("🍞 Flour", 1.0, 10.0, record["flour"], 0.01)
    
    # Save button
    if st.button("Save Values"):
        try:
            save_to_db(sugar, salt, flour, selected_date)
            st.success("Values saved successfully!")
            st.rerun()  # Refresh to update the calendar colors
        except Exception as e:
            st.error(f"Save error: {str(e)}")
    
    st.divider()
    
    # Display calendar
    display_calendar_table()
    
    # Add footer
    add_footer()

if __name__ == "__main__":
    main()

