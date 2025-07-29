from icalendar import Calendar
import pandas as pd
import re
from pathlib import Path
from typing import List

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

            # Format datetime objects to strings
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
    group_pattern = r'\b([CD]-\d{1,3})\b'

    def keep_event(subject: str) -> bool:
        if not subject:
            return False
        found_groups = re.findall(group_pattern, str(subject))
        return any(group in allowed_groups for group in found_groups)

    return df[df["subject"].apply(keep_event)]

def main() -> None:
    input_ics = Path("MCCalendarIds.ics")  # Your ICS filename here
    output_csv = Path("filtered_calendar.csv")
    allowed_groups = ["C-110", "D-23"]    # Your groups to keep here

    print(f"Reading calendar from '{input_ics}'...")
    df = ics_to_df(input_ics)

    print(f"Filtering events for groups: {allowed_groups} ...")
    filtered_df = filter_groups(df, allowed_groups)

    filtered_df.to_csv(output_csv, index=False)
    print(f"Done! Filtered {len(filtered_df)} events. Saved to '{output_csv.resolve()}'")

if __name__ == "__main__":
    main()