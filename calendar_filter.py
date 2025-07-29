from icalendar import Calendar
import pandas as pd
import re
from pathlib import Path
from typing import List

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
            return False
        found_groups = extract_all_groups(subject)
        print(f"Subject: {subject} -> Groups found: {found_groups}")
        return any(group in allowed_set for group in found_groups)

    filtered = df[df["subject"].apply(keep_event)]
    print(f"Filtered {len(filtered)} events out of {len(df)} total")
    return filtered

def main() -> None:
    input_ics = Path("MCCalendarIds.ics")
    output_csv = Path("filtered_calendar.csv")
    allowed_groups = ["C110", "D23"]

    print(f"Reading calendar from '{input_ics}'...")
    df = ics_to_df(input_ics)

    print(f"Filtering events for groups: {allowed_groups} ...")
    filtered_df = filter_groups(df, allowed_groups)

    if filtered_df is None:
        print("filter_groups returned None! This should not happen.")
        return

    filtered_df.to_csv(output_csv, index=False)
    print(f"Done! Filtered {len(filtered_df)} events. Saved to '{output_csv.resolve()}'")

if __name__ == "__main__":
    main()