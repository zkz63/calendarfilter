import streamlit as st
import pandas as pd
from icalendar import Calendar
from datetime import datetime
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

            start = dtstart.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dtstart, datetime) else str(dtstart)
            end = dtend.strftime("%Y-%m-%d %H:%M:%S") if isinstance(dtend, datetime) else str(dtend)

            events.append({
                "subject": summary or "",
                "start": start,
                "end": end,
                "location": location or "",
                "description": description or ""
            })
    return pd.DataFrame(events)

# --- Helper to extract all group codes from text, including ranges ---
def extract_all_groups(text):
    if not text:
        return set()

    single_group_pattern = r'\b([CD](?:0?\d{1,2}|1[01][0-4]))\b'
    range_pattern = r'\b([CD])(\d{1,3})[–-]([CD])?(\d{1,3})\b'

    groups = set(re.findall(single_group_pattern, text, flags=re.IGNORECASE))

    for match in re.finditer(range_pattern, text, flags=re.IGNORECASE):
        prefix1, start_num, prefix2, end_num = match.groups()
        prefix2 = prefix2 or prefix1
        if prefix1.upper() != prefix2.upper():
            continue
        for i in range(int(start_num), int(end_num) + 1):
            groups.add(f"{prefix1.upper()}{i}")

    return groups

# --- Function to filter groups ---
def filter_groups(df, allowed_groups):
    allowed_groups = set(g.upper() for g in allowed_groups)

    def keep_event(subject):
        found_groups = extract_all_groups(subject)
        return any(group.upper() in allowed_groups for group in found_groups)

    return df[df["subject"].apply(keep_event)]

# --- Streamlit Interface ---
st.title("Calendar Filter App")

uploaded_file = st.file_uploader("Upload your .ics calendar file", type=["ics"])
group_input = st.text_input("Enter allowed group(s), comma-separated (e.g., C110, D23):")

if uploaded_file and group_input:
    ics_content = uploaded_file.read().decode("utf-8")
    df = ics_to_df(ics_content)

    allowed_groups = [group.strip().upper() for group in group_input.split(",") if group.strip()]
    filtered_df = filter_groups(df, allowed_groups)

    st.success(f"{len(filtered_df)} events matched your group filters.")
    st.dataframe(filtered_df)

    csv_data = filtered_df.to_csv(index=False)
    st.download_button("Download filtered CSV", csv_data, "filtered_calendar.csv", "text/csv")