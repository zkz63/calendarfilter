import streamlit as st
import pandas as pd
from icalendar import Calendar
from datetime import datetime, timedelta
import re

# --- Function to parse ICS into DataFrame ---
def ics_to_df(ics_content):
    cal = Calendar.from_ical(ics_content)
    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            summary = component.get('summary')
            location = component.get('location')
            description = component.get('description')
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt
            
            # Convert datetime/date objects to strings
            start = dtstart.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dtstart, datetime) else str(dtstart)
            end = dtend.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dtend, datetime) else str(dtend)
            
            events.append({
                "subject": summary,
                "start": start,
                "end": end,
                "location": location if location else "",
                "description": description if description else ""
            })
    return pd.DataFrame(events)

# --- Function to filter groups ---
def filter_groups(df, allowed_groups):
    group_pattern = r'\b([CD]-\d{1,3})\b'

    def keep_event(subject):
        if not subject:
            return False
        found_groups = re.findall(group_pattern, str(subject))
        return any(group in allowed_groups for group in found_groups)

    return df[df["subject"].apply(keep_event)]

# --- Streamlit Interface ---
st.title("Calendar Filter App")

uploaded_file = st.file_uploader("Upload your .ics calendar file", type=["ics"])

group_input = st.text_input("Enter allowed group(s), comma-separated (e.g., C-110, D-23):")

if uploaded_file and group_input:
    ics_content = uploaded_file.read().decode("utf-8")
    df = ics_to_df(ics_content)

    allowed_groups = [group.strip() for group in group_input.split(",")]
    filtered_df = filter_groups(df, allowed_groups)

    st.success(f"{len(filtered_df)} events matched your group filters.")
    st.dataframe(filtered_df)

    csv_data = filtered_df.to_csv(index=False)
    st.download_button("Download filtered CSV", csv_data, "filtered_calendar.csv", "text/csv")