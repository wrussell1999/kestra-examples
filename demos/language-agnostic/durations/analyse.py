import json
from datetime import timedelta
import isodate

# Path to the JSON file
file_path = "make_data.json"

# Load the JSON data
with open(file_path, "r") as f:
    data = json.load(f)

# Navigate to the list of executions
executions = data["results"]

# Collect all durations for "transform" tasks
durations = []
for execution in executions:
    for task in execution.get("taskRunList", []):
        if task.get("taskId") == "python":
            duration_str = task.get("state", {}).get("duration")
            if duration_str:
                try:
                    duration = isodate.parse_duration(duration_str)
                    if isinstance(duration, timedelta):
                        durations.append(duration.total_seconds())
                except Exception as e:
                    print(f"Error parsing duration: {e}")

# Calculate the average duration
if durations:
    average_duration = sum(durations) / len(durations)
    print(f"Average duration for 'transform' task: {average_duration:.3f} seconds")
else:
    print("No 'transform' task durations found.")
