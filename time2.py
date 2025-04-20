import random
import pandas as pd
import subprocess
import platform
import os

def get_inputs():
    """Get subjects and labs from user."""
    subs = {}
    n_subs = int(input("No. of regular subjects: "))
    for i in range(n_subs):
        s_name = input(f"Regular subject {i+1} name (short): ").upper()
        while True:
            try:
                hrs = int(input(f"Classes per week for {s_name}: "))
                if hrs >= 0:
                    subs[s_name] = {"name": input(f"Full name of {s_name}: "), "hrs_wk": hrs}
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
                    subs[nc_name] = {"name": input(f"Full name of {nc_name}: "), "hrs_wk": hrs}
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
                    subs[p_name] = {"name": input(f"Full name of {p_name}: "), "hrs_wk": hrs}
                    break
                print("Enter non-negative number.")
            except ValueError:
                print("Enter a number.")

    labs = {}
    n_labs = int(input("No. of labs: "))
    for i in range(n_labs):
        lab_name = input(f"Lab {i+1} name: ")
        labs[lab_name] = {"dur": 3}

    return subs, labs

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

def sched_labs(tt, labs, subs):
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
                print(f"Warning: Couldn't schedule {lab}")
                return False
    return True

def sched_subs(tt, subs):
    """Schedule subjects."""
    days = list(tt.keys())
    periods = list(tt[days[0]].keys())
    sub_list = list(subs.keys())
    sub_hrs = {s: 0 for s in sub_list}
    done = False
    tries = 0
    max_tries = 20000
    stall = 0
    prev_tt = None

    while not done and tries < max_tries and stall < 1000:
        tries += 1
        random.shuffle(sub_list)
        temp_tt = {d: day.copy() for d, day in tt.items()}
        temp_hrs = {s: 0 for s in sub_list}
        ok = True

        for d in days:
            for i, p in enumerate(periods):
                if not temp_tt[d][p]:
                    avail = [s for s in sub_list if temp_hrs[s] < subs[s]["hrs_wk"] and valid_slot(d, i, s, temp_tt, labs, subs)]
                    if avail:
                        s = random.choice(avail)
                        temp_tt[d][p] = s
                        temp_hrs[s] += 1

        if all(temp_hrs[s] == subs[s]["hrs_wk"] for s in sub_list):
            tt.update(temp_tt)
            sub_hrs.update(temp_hrs)
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

if __name__ == "__main__":
    subs, labs = get_inputs()
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    periods = ["10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 01:00 PM",
               "01:40 PM - 02:40 PM", "02:40 PM - 03:40 PM", "03:40 PM - 04:40 PM"]
    tt = {d: {p: None for p in periods} for d in days}

    if sched_labs(tt, labs, subs):
        sched_subs(tt, subs)

    for d in days:
        for p in periods:
            if not tt[d][p]:
                tt[d][p] = "Sports"

    excel = "timetable.xlsx"
    df = pd.DataFrame.from_dict(tt, orient='index', columns=periods)
    df.index.name = 'Day'
    try:
        df.to_excel(excel, index=True)
        print(f"Saved to {excel}")
        sys = platform.system()
        if sys == "Darwin":
            subprocess.run(["open", excel])
        elif sys == "Windows":
            os.startfile(excel)
        elif sys == "Linux":
            subprocess.run(["xdg-open", excel])
        else:
            print(f"Can't open {excel} on this OS.")
    except Exception as e:
        print(f"Error saving to Excel: {e}")

    print("\nTimetable:")
    print("-" * (20 * len(periods) + 10))
    print(f"{'Day':<10}", end="")
    for p in periods:
        print(f"{p:<20}", end="")
    print()
    print("-" * (20 * len(periods) + 10))
    for d, sched in tt.items():
        print(f"{d:<10}", end="")
        for p in periods:
            s = sched[p]
            print(f"{s if s else '':<20}", end="")
        print()
    print("-" * (20 * len(periods) + 10))