from icalendar import Calendar
import pandas as pd
import re
from pathlib import Path
from typing import List
from datetime import datetime

print("starting filter")

def extract_all_groups(summary):
    groups = set()

    # Match single groups like C110 or D23
    singles = re.findall(r'\b[CD]\d{2,3}\b', summary)
    groups.update(singles)

    # Match group ranges like C101–C114 or D15-D28
    ranges = re.findall(r'([CD])(\d{2,3})[–-]([CD])?(\d{2,3})', summary)
    for prefix1, start, prefix2, end in ranges:
        prefix = prefix1  # Use first prefix if second missing
        start = int(start)
        end = int(end)
        for i in range(start, end + 1):
            groups.add(f"{prefix}{i}")

    return groups

def ics_to_df(ics_path: Path) -> pd.DataFrame:
    with ics_path.open('rb') as file:
        cal = Calendar.from_ical(file.read())

    events = []
    for component in cal.walk():
        if component.name == "VEVENT":
            summary = component.get('summary')
            location = component.get('location') or ""
            description = component.get('description') or ""
            dtstart = component.get('dtstart').dt
            dtend = component.get('dtend').dt

            start = dtstart.strftime("%Y-%m-%d %H:%M:%S") if hasattr(dtstart, "strftime") else str(dtstart)
            end = dtend.strftime("%Y-%m-%d %H:%M:%S") if hasattr(dtend, "strftime") else str(dtend)

            events.append({
                "subject": summary,
                "start": start,
                "end": end,
                "location": location,
                "description": description
            })

    return pd.DataFrame(events)

def filter_groups(df: pd.DataFrame, allowed_groups: List[str]) -> pd.DataFrame:
    allowed_set = set(allowed_groups)

    def keep_event(subject: str) -> bool:
        if not subject:
            return True  # Keep events with no subject just in case
        found_groups = extract_all_groups(subject)
        if not found_groups:
            return True  # Keep non-group events
        return any(group in allowed_set for group in found_groups)  # Only keep if at least one group matches

    filtered = df[df["subject"].apply(keep_event)]
    print(f"Filtered {len(filtered)} events out of {len(df)} total")
    return filtered

def to_google_calendar_csv(df: pd.DataFrame) -> pd.DataFrame:
    def parse_dt(dt_str):
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    starts = df['start'].apply(parse_dt)
    ends = df['end'].apply(parse_dt)

    gcal_df = pd.DataFrame({
        "Subject": df["subject"].fillna(""),
        "Start Date": starts.dt.strftime("%m/%d/%Y"),
        "Start Time": starts.dt.strftime("%I:%M:%S %p"),
        "End Date": ends.dt.strftime("%m/%d/%Y"),
        "End Time": ends.dt.strftime("%I:%M:%S %p"),
        "All Day Event": "False",
        "Description": df["description"].fillna(""),
        "Location": df["location"].fillna("")
    })

    return gcal_df

def main() -> None:
    input_ics = Path("MCCalendarIds.ics")
    output_csv = Path("filtered_calendar_gcal.csv")
    allowed_groups = ["C110", "D23"]

    print(f"Reading calendar from '{input_ics}'...")
    df = ics_to_df(input_ics)

    print(f"Filtering events for groups: {allowed_groups} ...")
    filtered_df = filter_groups(df, allowed_groups)

    if filtered_df is None or filtered_df.empty:
        print("No matching events found.")
        return

    gcal_df = to_google_calendar_csv(filtered_df)
    gcal_df.to_csv(output_csv, index=False)
    print(f"Done! Filtered {len(filtered_df)} events. Saved Google Calendar CSV to '{output_csv.resolve()}'")

if __name__ == "__main__":
    main()