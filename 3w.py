import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import calendar

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

def save_to_db(sugar, salt, flour):
    conn = sqlite3.connect('3whites.db')
    c = conn.cursor()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if a record for today already exists
    c.execute("SELECT id FROM measurements WHERE date(timestamp) = ?", (today,))
    existing_record = c.fetchone()
    
    if existing_record:
        # Update existing record
        c.execute("""
            UPDATE measurements 
            SET sugar = ?, salt = ?, flour = ?, timestamp = ?
            WHERE date(timestamp) = ?
        """, (sugar, salt, flour, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), today))
        message = "Today's record updated"
    else:
        # Insert new record
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO measurements (timestamp, sugar, salt, flour) VALUES (?, ?, ?, ?)",
                (timestamp, sugar, salt, flour))
        message = "New record created"
    
    conn.commit()
    conn.close()
    return message

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

def display_calendar_table():
    st.subheader(f" {datetime.now().strftime('%B %Y')}")
    
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
                    
                    # Add colored day cell
                    html += f'<td style="background-color:{bg_color};"><span style="color:black;">{day}</span></td>'
                else:
                    # Add regular day cell
                    html += f'<td style="background-color:#f5f5f5;"><span style="color:black;">{day}</span></td>'
        
        html += "</tr>"
    
    html += """
      </tbody>
    </table>
    """
    
    # Display the HTML table
    st.markdown(html, unsafe_allow_html=True)

def main():
    st.title("🍚 Starch Tracker")

    # Initialize database
    try:
        init_db()
    except Exception as e:
        st.error(f"Database error: {str(e)}")
    
    # Simple sliders
    st.subheader("Today's Intake")
    st.divider()
    sugar = st.slider("🍬 Sugar", 1.0, 10.0, 5.0, 0.01)
    salt = st.slider("🧂Salt", 1.0, 10.0, 5.0, 0.01)
    flour = st.slider("🍞 Flour", 1.0, 10.0, 5.0, 0.01)
    
    # Save button
    if st.button("Save Values"):
        try:
            save_to_db(sugar, salt, flour)
            st.success("Values saved successfully!")
            # Force a complete rerun of the app
            st.rerun()
        except Exception as e:
            st.error(f"Save error: {str(e)}")
        
    st.divider()
    
    # Display simple calendar
    display_calendar_table()
()
    
if __name__ == "__main__":
    main()