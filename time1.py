import random
import pandas as pd

def get_dynamic_inputs():
    """Gets all subjects, labs, and their required hours dynamically from the user."""
    subjects = {}

    # Get regular subjects
    num_subjects = int(input("Enter the number of regular subjects: "))
    for i in range(num_subjects):
        subject_name = input(f"Enter regular subject {i+1} name (short form): ").upper()
        while True:
            try:
                hours = int(input(f"Enter the total number of classes for {subject_name} per week: "))
                if hours >= 0:
                    subjects[subject_name] = {"name": input(f"Enter the full name of {subject_name}: "), "hours_per_week": hours}
                    break
                else:
                    print("Please enter a non-negative number of classes.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    # Get non-credential subjects
    num_non_credential = int(input("Enter the number of non-credential subjects: "))
    for i in range(num_non_credential):
        nc_subject_name = input(f"Enter non-credential subject {i+1} name (short form): ").upper()
        while True:
            try:
                hours = int(input(f"Enter the total number of classes for {nc_subject_name} per week: "))
                if hours >= 0:
                    subjects[nc_subject_name] = {"name": input(f"Enter the full name of {nc_subject_name}: "), "hours_per_week": hours}
                    break
                else:
                    print("Please enter a non-negative number of classes.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    # Get project subjects
    num_project = int(input("Enter the number of project subjects: "))
    for i in range(num_project):
        project_name = input(f"Enter project subject {i+1} name (short form): ").upper()
        while True:
            try:
                hours = int(input(f"Enter the total number of classes for {project_name} per week: "))
                if hours >= 0:
                    subjects[project_name] = {"name": input(f"Enter the full name of {project_name}: "), "hours_per_week": hours}
                    break
                else:
                    print("Please enter a non-negative number of classes.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    labs = {}
    num_labs = int(input("Enter the number of labs: "))
    for i in range(num_labs):
        lab_name = input(f"Enter lab {i+1} name: ")
        labs[lab_name] = {"duration": 3}

    return subjects, labs

def is_valid_placement(day, period_index, item, current_timetable, labs, subjects):
    """Checks if placing an item at a given time is valid based on constraints."""
    if item in subjects:
        if period_index > 0 and current_timetable[day][periods[period_index - 1]] == item:
            return False
        if period_index < len(periods) - 1 and current_timetable[day][periods[period_index + 1]] == item:
            return False

        lab_on_day = any(current_timetable[day][p] in labs for p in periods)
        subject_count_today = 0
        for period in periods:
            if current_timetable[day][period] == item:
                subject_count_today += 1
        if lab_on_day and subject_count_today >= 1:
            return False
    return True

def schedule_labs(current_timetable, labs, subjects):
    """Attempts to schedule the labs."""
    days = list(current_timetable.keys())
    periods = list(current_timetable[days[0]].keys())
    labs_scheduled = {lab: False for lab in labs}
    available_days = list(days)
    random.shuffle(available_days)

    for lab_name, lab_info in labs.items():
        if not labs_scheduled[lab_name]:
            for day in available_days:
                # Try to schedule before lunch
                for start_period_index in range(3 - lab_info["duration"] + 1):
                    can_schedule = True
                    for i in range(lab_info["duration"]):
                        if current_timetable[day][periods[start_period_index + i]] is not None:
                            can_schedule = False
                            break
                    if can_schedule:
                        scheduled_today = [current_timetable[day][period] for period in periods if current_timetable[day][period] in labs]
                        if not scheduled_today:
                            for i in range(lab_info["duration"]):
                                current_timetable[day][periods[start_period_index + i]] = lab_name
                            labs_scheduled[lab_name] = True
                            break
                if labs_scheduled[lab_name]:
                    break
                # If not scheduled before lunch, try after lunch
                if not labs_scheduled[lab_name]:
                    for start_period_index in range(3, 6 - lab_info["duration"] + 1):
                        can_schedule = True
                        for i in range(lab_info["duration"]):
                            if current_timetable[day][periods[start_period_index + i]] is not None:
                                can_schedule = False
                                break
                        if can_schedule:
                            scheduled_today = [current_timetable[day][period] for period in periods if current_timetable[day][period] in labs]
                            if not scheduled_today:
                                for i in range(lab_info["duration"]):
                                    current_timetable[day][periods[start_period_index + i]] = lab_name
                                labs_scheduled[lab_name] = True
                                break
                if labs_scheduled[lab_name]:
                    break
            if not labs_scheduled[lab_name]:
                print(f"Warning: Could not schedule {lab_name}")
                return False
    return True

def schedule_subjects(current_timetable, subjects):
    """Attempts to schedule all subjects."""
    days = list(current_timetable.keys())
    periods = list(current_timetable[days[0]].keys())
    subject_list_schedule = list(subjects.keys())
    subject_hours_scheduled = {sub: 0 for sub in subject_list_schedule}
    all_scheduled = False
    attempts = 0
    max_attempts = 20000
    stagnant_count = 0
    previous_timetable_state = None

    while not all_scheduled and attempts < max_attempts and stagnant_count < 1000:
        attempts += 1
        random.shuffle(subject_list_schedule)
        temp_timetable = {day: day_schedule.copy() for day, day_schedule in current_timetable.items()}
        temp_subject_hours_scheduled = {sub: 0 for sub in subject_list_schedule}
        possible = True

        for day in days:
            for i, period in enumerate(periods):
                if temp_timetable[day][period] is None:
                    available_subjects = [
                        sub for sub in subject_list_schedule
                        if temp_subject_hours_scheduled[sub] < subjects[sub]["hours_per_week"]
                           and is_valid_placement(day, i, sub, temp_timetable, labs, subjects)
                    ]
                    if available_subjects:
                        subject_to_place = random.choice(available_subjects)
                        temp_timetable[day][period] = subject_to_place
                        temp_subject_hours_scheduled[subject_to_place] += 1

        if all(temp_subject_hours_scheduled[sub] == subjects[sub]["hours_per_week"] for sub in subject_list_schedule):
            current_timetable.update(temp_timetable)
            subject_hours_scheduled.update(temp_subject_hours_scheduled)
            all_scheduled = True
            break
        elif temp_timetable == previous_timetable_state:
            stagnant_count += 1
        else:
            stagnant_count = 0
            previous_timetable_state = temp_timetable.copy()

    if not all_scheduled:
        print("Warning: Could not schedule all subjects according to the constraints.")
        return False
    return True

# --- Main Execution ---
if __name__ == "__main__":
    subjects, labs = get_dynamic_inputs()

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = ["10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
               "01:40 PM - 02:40 PM", "02:40 PM - 03:40 PM", "03:40 PM - 04:40 PM"]

    timetable = {day: {period: None for period in periods} for day in days}

    if schedule_labs(timetable, labs, subjects):
        schedule_subjects(timetable, subjects)

    for day in days:
        for period in periods:
            if timetable[day][period] is None:
                timetable[day][period] = "Sports"

    # --- Output to Excel ---
    df = pd.DataFrame.from_dict(timetable, orient='index', columns=periods)
    df.index.name = 'Day'
    try:
        df.to_excel("timetable.xlsx", index=True)
        print("Timetable saved to timetable.xlsx")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

    print("\nGenerated Timetable (in console):")
    print("-" * (20 * len(periods) + 10))
    print(f"{'Day':<10}", end="")
    for period in periods:
        print(f"{period:<20}", end="")
    print()
    print("-" * (20 * len(periods) + 10))
    for day, day_schedule in timetable.items():
        print(f"{day:<10}", end="")
        for period in periods:
            subject = day_schedule[period]
            print(f"{subject if subject else '':<20}", end="")
        print()
    print("-" * (20 * len(periods) + 10))