import random
import pandas as pd
import subprocess
import platform
import os

def get_common_inputs():
    """Get common subjects and labs for both classes from user."""
    subjects = {}
    print("\n--- Enter common details for both classes ---")
    n_subs = int(input("No. of regular subjects: "))
    for i in range(n_subs):
        s_name = input(f"Regular subject {i+1} name (short): ").upper()
        while True:
            try:
                hrs = int(input(f"Classes per week for {s_name}: "))
                if hrs >= 0:
                    subjects[s_name] = {"name": input(f"Full name of {s_name}: "), "hrs_wk": hrs, "type": "regular"}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    n_nc = int(input("No. of non-credential subjects: "))
    for i in range(n_nc):
        nc_name = input(f"Non-credential subject {i+1} name (short): ").upper()
        while True:
            try:
                hrs = int(input(f"Classes per week for {nc_name}: "))
                if hrs >= 0:
                    subjects[nc_name] = {"name": input(f"Full name of {nc_name}: "), "hrs_wk": hrs, "type": "non-credential"}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    n_proj = int(input("No. of project subjects: "))
    for i in range(n_proj):
        p_name = input(f"Project subject {i+1} name (short): ").upper()
        while True:
            try:
                hrs = int(input(f"Classes per week for {p_name}: "))
                if hrs >= 0:
                    subjects[p_name] = {"name": input(f"Full name of {p_name}: "), "hrs_wk": hrs, "type": "project"}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    labs = {}
    n_labs = int(input("No. of labs: "))
    for i in range(n_labs):
        lab_name = input(f"Lab {i+1} name: ")
        labs[lab_name] = {"dur": 3}

    return subjects, labs

def valid_slot(day, idx, item, tt, labs, subs):
    """Check if item can be placed at given time."""
    if item in subs:
        if idx > 0 and tt[day][periods[idx - 1]] == item:
            return False
        if idx < len(periods) - 1 and tt[day][periods[idx + 1]] == item:
            return False
        has_lab = any(tt[day][p] in labs for p in periods)
        sub_count = sum(1 for p in periods if tt[day][p] == item)
        if has_lab and sub_count >= 1:
            return False
    return True

def sched_labs(tt, labs):
    """Schedule labs."""
    days = list(tt.keys())
    periods = list(tt[days[0]].keys())
    lab_done = {lab: False for lab in labs}
    avail_days = days.copy()
    random.shuffle(avail_days)

    for lab, info in labs.items():
        if not lab_done[lab]:
            for day in avail_days:
                for start in range(3 - info["dur"] + 1):
                    can_sched = True
                    for i in range(info["dur"]):
                        if tt[day][periods[start + i]]:
                            can_sched = False
                            break
                    if can_sched and not any(tt[day][p] in labs for p in periods):
                        for i in range(info["dur"]):
                            tt[day][periods[start + i]] = lab
                        lab_done[lab] = True
                        break
                if lab_done[lab]:
                    break
                if not lab_done[lab]:
                    for start in range(3, 6 - info["dur"] + 1):
                        can_sched = True
                        for i in range(info["dur"]):
                            if tt[day][periods[start + i]]:
                                can_sched = False
                                break
                        if can_sched and not any(tt[day][p] in labs for p in periods):
                            for i in range(info["dur"]):
                                tt[day][periods[start + i]] = lab
                            lab_done[lab] = True
                            break
                if lab_done[lab]:
                    break
            if not lab_done[lab]:
                print(f"Warning: Couldn't schedule lab {lab}")
                return False
    return True

def sched_subs(tt, subs, labs):
    """Schedule subjects, prioritizing non-credential and project in last two periods."""
    days = list(tt.keys())
    periods = list(tt[days[0]].keys())
    sub_list = list(subs.keys())
    sub_hrs = {s: 0 for s in sub_list}
    done = False
    tries = 0
    max_tries = 40000  # Increased tries
    stall = 0
    prev_tt = None
    last_two_periods_indices = [4, 5]

    while not done and tries < max_tries and stall < 2000:
        tries += 1
        random.shuffle(sub_list)
        temp_tt = {d: day.copy() for d, day in tt.items()}
        temp_hrs = {s: 0 for s in sub_list}
        ok = True

        # First, try to schedule non-credential and project in the last two periods
        for d in days:
            random.shuffle(last_two_periods_indices)
            for i in last_two_periods_indices:
                p = periods[i]
                if not temp_tt[d][p]:
                    nc_proj_avail = [s for s in sub_list if subs[s]["type"] in ["non-credential", "project"] and temp_hrs[s] < subs[s]["hrs_wk"] and valid_slot(d, i, s, temp_tt, labs, subs)]
                    if nc_proj_avail:
                        s = random.choice(nc_proj_avail)
                        temp_tt[d][p] = s
                        temp_hrs[s] += 1

        # Then schedule the rest
        for d in days:
            for i, p in enumerate(periods):
                if not temp_tt[d][p]:
                    reg_avail = [s for s in sub_list if subs[s]["type"] == "regular" and temp_hrs[s] < subs[s]["hrs_wk"] and valid_slot(d, i, s, temp_tt, labs, subs)]
                    if reg_avail:
                        s = random.choice(reg_avail)
                        temp_tt[d][p] = s
                        temp_hrs[s] += 1

        if all(temp_hrs[s] == subs[s]["hrs_wk"] for s in sub_list):
            tt.update(temp_tt)
            done = True
        elif temp_tt == prev_tt:
            stall += 1
        else:
            stall = 0
            prev_tt = temp_tt.copy()

    if not done:
        print("Warning: Couldn't schedule all subjects.")
        return False
    return True

def fill_sports(tt):
    """Fill empty slots with 'Sports'."""
    days = list(tt.keys())
    periods = list(tt[days[0]].keys())
    for d in days:
        for p in periods:
            if not tt[d][p]:
                tt[d][p] = "Sports"

if __name__ == "__main__":
    common_subjects, common_labs = get_common_inputs()
    timetable_data = {}
    class_names = ["Class 1", "Class 2"]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = ["10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
               "01:40 PM - 02:40 PM", "02:40 PM - 03:40 PM", "03:40 PM - 04:40 PM"]

    for class_name in class_names:
        timetable = {d: {p: None for p in periods} for d in days}
        labs_for_class = common_labs.copy() # Use a copy for each class
        subjects_for_class = common_subjects.copy() # Use a copy for each class

        if sched_labs(timetable, labs_for_class):
            if sched_subs(timetable, subjects_for_class, labs_for_class): # Pass labs_for_class here
                fill_sports(timetable)
                timetable_data[class_name] = pd.DataFrame.from_dict(timetable, orient='index', columns=periods)
                timetable_data[class_name].index.name = 'Day'
            else:
                print(f"Scheduling failed for {class_name}")
                timetable_data[class_name] = pd.DataFrame() # Empty DataFrame on failure
        else:
            print(f"Lab scheduling failed for {class_name}")
            timetable_data[class_name] = pd.DataFrame() # Empty DataFrame on failure

    excel_filename = "timetable.xlsx"
    try:
        with pd.ExcelWriter(excel_filename) as writer:
            for class_name, df in timetable_data.items():
                df.to_excel(writer, sheet_name=class_name)
        print(f"Timetables saved to {excel_filename}")

        sys = platform.system()
        if sys == "Darwin":
            subprocess.run(["open", excel_filename])
        elif sys == "Windows":
            os.startfile(excel_filename)
        elif sys == "Linux":
            subprocess.run(["xdg-open", excel_filename])
        else:
            print(f"Can't open {excel_filename} on this OS.")

    except Exception as e:
        print(f"Error saving to Excel: {e}")

    print("\nTimetables (in console):")
    for class_name, df in timetable_data.items():
        print(f"\n--- {class_name} ---")
        if not df.empty:
            print(df.to_string())
        else:
            print("Scheduling failed for this class.")