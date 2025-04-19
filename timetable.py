import random

# Set up subjects with their names and weekly hours
subjects = {
    "AC": {"name": "Analog Circuits", "hours_per_week": 0},
    "ADC": {"name": "Analog and Digital Communication", "hours_per_week": 0},
    "EMTL": {"name": "Electromagnetic waves and transmission lines", "hours_per_week": 0},
    "CS": {"name": "Control Systems", "hours_per_week": 0},
    "CO": {"name": "Computer Organisation", "hours_per_week": 0},
    "IPR": {"name": "Intellectual Property Rights", "hours_per_week": 2},
    "FP": {"name": "Field Project", "hours_per_week": 2},
}

# Labs need fixed 3-hour blocks
labs = {
    "AC Lab": {"name":"Analog Circuits Lab","duration": 3},
    "ADC Lab": {"name":"Analog and Digital Communication Lab","duration": 3},
    "PPP Lab": {"name": "Python practice and programming Lab", "duration": 3},
}

# Define our days and time slots
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
periods = ["10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
           "01:40 PM - 02:40 PM", "02:40 PM - 03:40 PM", "03:40 PM - 04:40 PM"]

# Create an empty timetable
timetable = {day: {period: None for period in periods} for day in days}

# Figure out hours per subject
remaining_slots = (len(days) * len(periods)) - (sum(lab["duration"] for lab in labs.values()) + subjects["IPR"]["hours_per_week"] + subjects["FP"]["hours_per_week"])
hours_per_subject = remaining_slots // (len(subjects) - 2) # Excluding IPR and FP
remainder = remaining_slots % (len(subjects) - 2)

subject_hours = {}
subject_list = [sub for sub in subjects if sub not in ["IPR", "FP"]]
for i, subject in enumerate(subject_list):
    subjects[subject]["hours_per_week"] = hours_per_subject + (1 if i < remainder else 0)

# Track scheduled labs and special classes
labs_scheduled = {lab: False for lab in labs}
ipr_fp_scheduled = {"IPR": 0, "FP": 0}
subject_hours_scheduled = {sub: 0 for sub in subjects if sub not in ["IPR", "FP"]}

def is_valid_placement(day, period_index, item, current_timetable):
    """Check if we can place this class without breaking rules."""
    # No back-to-back classes for main subjects
    if item in subjects and item not in ["IPR", "FP"]:
        if period_index > 0 and current_timetable[day][periods[period_index - 1]] == item:
            return False
        if period_index < len(periods) - 1 and current_timetable[day][periods[period_index + 1]] == item:
            return False

    # Limit subjects to once per day if there's a lab
    if item in subjects and item not in ["IPR", "FP"]:
        lab_on_day = any(current_timetable[day][p] in labs for p in periods)
        subject_count_today = 0
        for period in periods:
            if current_timetable[day][period] == item:
                subject_count_today += 1
        if lab_on_day and subject_count_today >= 1:
            return False

    return True

def schedule_labs_ipr_fp(current_timetable):
    """Place labs and special classes, prioritizing late slots for IPR/FP."""
    available_days = list(days)
    random.shuffle(available_days)

    # Schedule labs first
    for lab_name, lab_info in labs.items():
        if not labs_scheduled[lab_name]:
            for day in available_days:
                # Try before lunch
                for start_period_index in range(3 - lab_info["duration"] + 1):
                    can_schedule = True
                    for i in range(lab_info["duration"]):
                        if current_timetable[day][periods[start_period_index + i]] is not None:
                            can_schedule = False
                            break
                    if can_schedule:
                        # Ensure no other lab or special class today
                        scheduled_today = [current_timetable[day][period] for period in periods if current_timetable[day][period] in labs or current_timetable[day][period] in ["IPR", "FP"]]
                        if not scheduled_today: # No other lab/IPR/FP on this day
                            for i in range(lab_info["duration"]):
                                current_timetable[day][periods[start_period_index + i]] = lab_name
                            labs_scheduled[lab_name] = True
                            break
                if labs_scheduled[lab_name]:
                    break
                # Try after lunch if needed
                if not labs_scheduled[lab_name]:
                    for start_period_index in range(3, 6 - lab_info["duration"] + 1):
                        can_schedule = True
                        for i in range(lab_info["duration"]):
                            if current_timetable[day][periods[start_period_index + i]] is not None:
                                can_schedule = False
                                break
                        if can_schedule:
                            # Ensure no other lab or special class today
                            scheduled_today = [current_timetable[day][period] for period in periods if current_timetable[day][period] in labs or current_timetable[day][period] in ["IPR", "FP"]]
                            if not scheduled_today: # No other lab/IPR/FP on this day
                                for i in range(lab_info["duration"]):
                                    current_timetable[day][periods[start_period_index + i]] = lab_name
                                labs_scheduled[lab_name] = True
                                break
                if labs_scheduled[lab_name]:
                    break
            if not labs_scheduled[lab_name]:
                print(f"Oops, couldn't fit {lab_name}")
                return False

    # Schedule IPR and FP, aiming for end of day
    ipr_fp_list = ["IPR", "FP"]
    for item in ipr_fp_list:
        while ipr_fp_scheduled[item] < subjects[item]["hours_per_week"]:
            scheduled = False
            random.shuffle(available_days)
            for day in available_days:
                # Try late slots first
                last_two_periods_indices = [4, 5] # Indices for 02:40-03:40 and 03:40-04:40
                random.shuffle(last_two_periods_indices)
                for period_index in last_two_periods_indices:
                    if current_timetable[day][periods[period_index]] is None and is_valid_placement(day, period_index, item, current_timetable) and not any(current_timetable[day][period] in labs for period in periods):
                        current_timetable[day][periods[period_index]] = item
                        ipr_fp_scheduled[item] += 1
                        scheduled = True
                        break
                if scheduled:
                    break
                # Try other slots if needed
                available_periods = [i for i, period in enumerate(periods) if current_timetable[day][period] is None and is_valid_placement(day, i, item, current_timetable) and not any(current_timetable[day][period] in labs for period in periods)]
                if available_periods:
                    period_index = random.choice(available_periods)
                    current_timetable[day][periods[period_index]] = item
                    ipr_fp_scheduled[item] += 1
                    scheduled = True
                    break
            if not scheduled:
                print(f"Hmm, couldn't schedule all {item} hours")
                return False
    return True

def schedule_subjects(current_timetable):
    """Fill in the main subjects, meeting their hour goals."""
    subject_list_schedule = [sub for sub, info in subjects.items() if sub not in ["IPR", "FP"]]
    all_scheduled = False
    attempts = 0
    max_attempts = 5000 
    stagnant_count = 0
    previous_timetable_state = None

    while not all_scheduled and attempts < max_attempts and stagnant_count < 200:
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
                           and is_valid_placement(day, i, sub, temp_timetable)
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
        print("Oh no, couldn't fit all subjects!")
        return False
    return True

# Start with labs and special classes
if schedule_labs_ipr_fp(timetable):
    # Then add main subjects
    schedule_subjects(timetable)

# Fill empty slots with Sports 
for day in days:
    for period in periods:
        if timetable[day][period] is None:
            timetable[day][period] = "Sports"

# --- Show the timetable ---
print("Timetable:")
print("-" * 80)
print(f"{'Day':<10}", end="")
for period in periods:
    print(f"{period:<20}", end="")
print()
print("-" * 80)
for day, day_schedule in timetable.items():
    print(f"{day:<10}", end="")
    for period in periods:
        subject = day_schedule[period]
        print(f"{subject if subject else '':<20}", end="")
    print()
print("-" * 80)