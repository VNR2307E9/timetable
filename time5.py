import random
import pandas as pd
import subprocess
import platform
import os
from collections import defaultdict

def get_inputs():
    """Get inputs for classes, subjects, labs, and faculty."""
    # Get number of classes and their names
    n_classes = int(input("Enter number of classes: "))
    class_names = []
    for i in range(n_classes):
        class_name = input(f"Enter name of class {i+1}: ")
        class_names.append(class_name)

    # Get subjects
    subjects = {}
    print("\n--- Enter subject details ---")
    n_subs = int(input("No. of regular subjects: "))
    for i in range(n_subs):
        s_name = input(f"Regular subject {i+1} short name: ").upper()
        full_name = input(f"Full name of {s_name}: ")
        while True:
            try:
                hrs = int(input(f"Classes per week for {s_name}: "))
                if hrs >= 0:
                    subjects[s_name] = {"name": full_name, "hrs_wk": hrs, "type": "regular", "faculty": ""}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    # Get non-credential subjects
    n_nc = int(input("No. of non-credential subjects: "))
    for i in range(n_nc):
        nc_name = input(f"Non-credential subject {i+1} short name: ").upper()
        full_name = input(f"Full name of {nc_name}: ")
        while True:
            try:
                hrs = int(input(f"Classes per week for {nc_name}: "))
                if hrs >= 0:
                    subjects[nc_name] = {"name": full_name, "hrs_wk": hrs, "type": "non-credential", "faculty": ""}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    # Get project subjects
    n_proj = int(input("No. of project subjects: "))
    for i in range(n_proj):
        p_name = input(f"Project subject {i+1} short name: ").upper()
        full_name = input(f"Full name of {p_name}: ")
        while True:
            try:
                hrs = int(input(f"Classes per week for {p_name}: "))
                if hrs >= 0:
                    subjects[p_name] = {"name": full_name, "hrs_wk": hrs, "type": "project", "faculty": ""}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    # Get labs
    labs = {}
    n_labs = int(input("No. of labs: "))
    for i in range(n_labs):
        lab_name = input(f"Lab {i+1} short name: ").upper()
        full_name = input(f"Full name of {lab_name}: ")
        labs[lab_name] = {"name": full_name, "dur": 3, "faculty": ""}

    # Get faculty details
    faculty = {}
    faculty_classes = defaultdict(list)
    print("\n--- Enter faculty details ---")
    n_faculty = int(input("No. of faculty members: "))
    for i in range(n_faculty):
        f_name = input(f"Faculty {i+1} name: ")
        faculty[f_name] = {"subjects": [], "classes": []}
        
        # Subjects they teach
        n_subj = int(input(f"No. of subjects taught by {f_name}: "))
        for j in range(n_subj):
            subj = input(f"Subject {j+1} taught by {f_name} (short name): ").upper()
            if subj in subjects:
                subjects[subj]["faculty"] = f_name
                faculty[f_name]["subjects"].append(subj)
            elif subj in labs:
                labs[subj]["faculty"] = f_name
                faculty[f_name]["subjects"].append(subj)
            else:
                print(f"Subject/lab {subj} not found in the list.")
        
        # Classes they teach
        n_cls = int(input(f"No. of classes taught by {f_name}: "))
        for j in range(n_cls):
            cls = input(f"Class {j+1} taught by {f_name}: ")
            if cls in class_names:
                faculty[f_name]["classes"].append(cls)
                faculty_classes[f_name].append(cls)

    return class_names, subjects, labs, faculty, faculty_classes

def valid_slot(class_name, day, idx, item, global_tt, labs, subs, class_names, faculty, faculty_classes):
    """Check if item can be placed at given time slot for the class."""
    periods = list(global_tt[class_name][day].keys())
    
    # Check for consecutive subject periods within the same class
    if item in subs:
        if idx > 0 and global_tt[class_name][day][periods[idx - 1]] == item:
            return False
        if idx < len(periods) - 1 and global_tt[class_name][day][periods[idx + 1]] == item:
            return False
        has_lab = any(global_tt[class_name][day][p] in labs for p in periods)
        sub_count = sum(1 for p in periods if global_tt[class_name][day][p] == item)
        if has_lab and sub_count >= 1:
            return False
    
    # Check faculty availability
    faculty_name = subs[item]["faculty"] if item in subs else labs[item]["faculty"]
    if faculty_name:
        for other_class in faculty_classes[faculty_name]:
            if other_class != class_name:
                if global_tt[other_class][day][periods[idx]]:
                    return False

    return True

def sched_labs(global_tt, labs, class_names, faculty, faculty_classes):
    """Schedule labs for all classes."""
    days = list(global_tt[class_names[0]].keys())
    periods = list(global_tt[class_names[0]][days[0]].keys())
    lab_done = {class_name: {lab: False for lab in labs} for class_name in class_names}
    avail_days = days.copy()

    for class_name in class_names:
        random.shuffle(avail_days)
        for lab, info in labs.items():
            if not lab_done[class_name][lab]:
                for day in avail_days:
                    for start in range(3 - info["dur"] + 1):
                        can_sched = True
                        for i in range(info["dur"]):
                            if global_tt[class_name][day][periods[start + i]]:
                                can_sched = False
                                break
                            faculty_name = labs[lab]["faculty"]
                            for other_class in faculty_classes[faculty_name]:
                                if other_class != class_name and global_tt[other_class][day][periods[start + i]]:
                                    can_sched = False
                                    break
                        if can_sched and not any(global_tt[class_name][day][p] in labs for p in periods):
                            for i in range(info["dur"]):
                                global_tt[class_name][day][periods[start + i]] = lab
                            lab_done[class_name][lab] = True
                            break
                    if lab_done[class_name][lab]:
                        break
                    if not lab_done[class_name][lab]:
                        for start in range(3, 6 - info["dur"] + 1):
                            can_sched = True
                            for i in range(info["dur"]):
                                if global_tt[class_name][day][periods[start + i]]:
                                    can_sched = False
                                    break
                                faculty_name = labs[lab]["faculty"]
                                for other_class in faculty_classes[faculty_name]:
                                    if other_class != class_name and global_tt[other_class][day][periods[start + i]]:
                                        can_sched = False
                                        break
                            if can_sched and not any(global_tt[class_name][day][p] in labs for p in periods):
                                for i in range(info["dur"]):
                                    global_tt[class_name][day][periods[start + i]] = lab
                                lab_done[class_name][lab] = True
                                break
                    if lab_done[class_name][lab]:
                        break
                if not lab_done[class_name][lab]:
                    print(f"Warning: Couldn't schedule lab {lab} for {class_name}")
                    return False
    return True

def sched_subs(global_tt, subs, labs, class_names, faculty, faculty_classes):
    """Schedule subjects for all classes."""
    days = list(global_tt[class_names[0]].keys())
    periods = list(global_tt[class_names[0]][days[0]].keys())
    sub_list = list(subs.keys())
    sub_hrs = {class_name: {s: 0 for s in sub_list} for class_name in class_names}
    done = False
    tries = 0
    max_tries = 40000
    stall = 0
    prev_global_tt = None
    last_two_periods_indices = [4, 5]

    while not done and tries < max_tries and stall < 2000:
        tries += 1
        temp_global_tt = {
            class_name: {d: day.copy() for d, day in global_tt[class_name].items()}
            for class_name in class_names
        }
        temp_hrs = {class_name: {s: 0 for s in sub_list} for class_name in class_names}
        ok = True

        # Schedule non-credential and project subjects in the last two periods
        for class_name in class_names:
            for d in days:
                random.shuffle(last_two_periods_indices)
                for i in last_two_periods_indices:
                    p = periods[i]
                    if not temp_global_tt[class_name][d][p]:
                        nc_proj_avail = [
                            s for s in sub_list
                            if subs[s]["type"] in ["non-credential", "project"]
                            and temp_hrs[class_name][s] < subs[s]["hrs_wk"]
                            and valid_slot(class_name, d, i, s, temp_global_tt, labs, subs, class_names, faculty, faculty_classes)
                        ]
                        if nc_proj_avail:
                            s = random.choice(nc_proj_avail)
                            temp_global_tt[class_name][d][p] = s
                            temp_hrs[class_name][s] += 1

        # Schedule regular subjects
        for class_name in class_names:
            for d in days:
                for i, p in enumerate(periods):
                    if not temp_global_tt[class_name][d][p]:
                        reg_avail = [
                            s for s in sub_list
                            if subs[s]["type"] == "regular"
                            and temp_hrs[class_name][s] < subs[s]["hrs_wk"]
                            and valid_slot(class_name, d, i, s, temp_global_tt, labs, subs, class_names, faculty, faculty_classes)
                        ]
                        if reg_avail:
                            s = random.choice(reg_avail)
                            temp_global_tt[class_name][d][p] = s
                            temp_hrs[class_name][s] += 1

        # Check if all subjects are scheduled
        all_scheduled = True
        for class_name in class_names:
            if not all(temp_hrs[class_name][s] == subs[s]["hrs_wk"] for s in sub_list):
                all_scheduled = False
                break

        if all_scheduled:
            for class_name in class_names:
                global_tt[class_name].update(temp_global_tt[class_name])
            done = True
        elif temp_global_tt == prev_global_tt:
            stall += 1
        else:
            stall = 0
            prev_global_tt = {
                class_name: {d: day.copy() for d, day in temp_global_tt[class_name].items()}
                for class_name in class_names
            }

    if not done:
        print("Warning: Couldn't schedule all subjects for all classes.")
        return False
    return True

def fill_sports(global_tt, class_names):
    """Fill empty slots with 'Sports' for each class."""
    days = list(global_tt[class_names[0]].keys())
    periods = list(global_tt[class_names[0]][days[0]].keys())
    for class_name in class_names:
        for d in days:
            for p in periods:
                if not global_tt[class_name][d][p]:
                    global_tt[class_name][d][p] = "Sports"

def generate_faculty_timetables(global_tt, faculty, class_names):
    """Generate timetables for each faculty member."""
    days = list(global_tt[class_names[0]].keys())
    periods = list(global_tt[class_names[0]][days[0]].keys())
    faculty_timetables = {}
    
    for f_name, f_info in faculty.items():
        faculty_tt = {d: {p: "" for p in periods} for d in days}
        for class_name in f_info["classes"]:
            for d in days:
                for p in periods:
                    if global_tt[class_name][d][p] in f_info["subjects"]:
                        faculty_tt[d][p] = f"{global_tt[class_name][d][p]} ({class_name})"
        faculty_timetables[f_name] = pd.DataFrame.from_dict(faculty_tt, orient='index', columns=periods)
        faculty_timetables[f_name].index.name = 'Day'
    
    return faculty_timetables

def create_subject_details_df(subjects, labs):
    """Create a DataFrame for subject details without room numbers."""
    data = []
    for code, info in subjects.items():
        data.append([code, info["name"], info["faculty"], ""])
    for code, info in labs.items():
        data.append([code, info["name"], info["faculty"], ""])
    
    return pd.DataFrame(data, columns=["Course Code", "Name of the Course (Short)", 
                                     "Name of the Course Coordinator (Faculty)", 
                                     "Category of the Course / Activity"])

if __name__ == "__main__":
    class_names, subjects, labs, faculty, faculty_classes = get_inputs()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = ["10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
               "01:40 PM - 02:40 PM", "02:40 PM - 03:40 PM", "03:40 PM - 04:40 PM"]

    # Initialize global timetable for all classes
    global_timetable = {
        class_name: {d: {p: None for p in periods} for d in days}
        for class_name in class_names
    }

    timetable_data = {}
    faculty_timetable_data = {}
    subject_details = create_subject_details_df(subjects, labs)

    if sched_labs(global_timetable, labs, class_names, faculty, faculty_classes):
        if sched_subs(global_timetable, subjects, labs, class_names, faculty, faculty_classes):
            fill_sports(global_timetable, class_names)
            
            # Generate class timetables
            for class_name in class_names:
                timetable_data[class_name] = pd.DataFrame.from_dict(
                    global_timetable[class_name], orient='index', columns=periods
                )
                timetable_data[class_name].index.name = 'Day'
            
            # Generate faculty timetables
            faculty_timetable_data = generate_faculty_timetables(global_timetable, faculty, class_names)
        else:
            print("Subject scheduling failed.")
            for class_name in class_names:
                timetable_data[class_name] = pd.DataFrame()
    else:
        print("Lab scheduling failed.")
        for class_name in class_names:
            timetable_data[class_name] = pd.DataFrame()

    excel_filename = "timetables.xlsx"
    try:
        with pd.ExcelWriter(excel_filename) as writer:
            # Write class timetables
            for class_name, df in timetable_data.items():
                df.to_excel(writer, sheet_name=f"Class_{class_name}")
            
            # Write faculty timetables
            for f_name, df in faculty_timetable_data.items():
                df.to_excel(writer, sheet_name=f"Faculty_{f_name}")
            
            # Write subject details
            subject_details.to_excel(writer, sheet_name="Subject_Details", index=False)

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
    for class_name, df in sorted(timetable_data.items()):
        print(f"\n--- {class_name} ---")
        if not df.empty:
            print(df.to_string())
        else:
            print("Scheduling failed for this class.")
    
    for f_name, df in sorted(faculty_timetable_data.items()):
        print(f"\n--- Faculty: {f_name} ---")
        if not df.empty:
            print(df.to_string())
        else:
            print("Scheduling failed for this faculty.")
    
    print("\n--- Subject Details ---")
    print(subject_details.to_string())