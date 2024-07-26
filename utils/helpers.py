import re

def day_to_int(day: str) -> int:
    """
    Convert day string to integer.
    """

    days = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
        'Sunday': 7
    }
    return days[day]

def int_to_days(day: str) -> int:
    """
    Convert integer to day string.
    """

    days = {
        1 : 'Monday',
        2 : 'Tuesday',
        3 : 'Wednesday',
        4 : 'Thursday',
        5 : 'Friday',
        6 : 'Saturday',
        7 : 'Sunday'
    }
    return days[day]

def user_days_to_array(input_str: str) -> list:
    days = re.split(r'[,\s]+', input_str)
    days = [day for day in days if day]
    days = list(set(days)) # get unique array
    days.sort()
    return days
    
def shorten_lesson_type(lesson_type: str) -> str:
    """ 
    Shorten the lesson type.
    """

    lesson_types = {
        'Lecture': 'LEC',
        'Laboratory': 'LAB',
        'Tutorial': 'TUT',
        'Seminar-Style Module Class': 'SEM',
        'Sectional Teaching': 'SEC',
        'Design Lecture': 'DLEC',
        'Mini-Project': '',
        'Recitation': 'REC',
        'Packaged Lecture': 'PLEC',
        'Packaged Tutorial': 'PTUT',
        'Packaged Laboratory': 'PLAB',
        'Workshop': 'WS',
        'Tutorial Type 2': 'TUT2',
    }

    return lesson_types[lesson_type]

def blockout_timings_cleaner(timings: list) -> dict:
    blocktimings = {}
    for i in range(6):
        blocktimings[int_to_days(i+1)] = []
    for slot in timings:
        blocktimings[slot[0]].append(slot[1])
    for key in blocktimings:
        blocktimings[key].sort()
    #Make timings more concise
    for day, timeslots in blocktimings.items():
        l = len(timeslots)
        if l <= 1:
            continue
        new_slots = []
        new_slots.append(timeslots[0])
        for idx in range(1, l):
            prev_timing = new_slots[-1]
            prev = prev_timing.split('-')
            next_timing = timeslots[idx]
            next = next_timing.split('-')
            #check if can combine slots
            if prev[1] == next[0]:
                new_time = prev[0] + '-' + next[1]
                new_slots[-1] = new_time
            else:
                new_slots.append(next_timing)
        blocktimings[day] = new_slots

    return blocktimings

def blocktimings_printer(timings: dict) -> str:
    s = ""
    for key, val in timings.items():
        if val:
            s += f"{key}: {val}\n" 
    return s

def blocked_time_merge(days: list, timings: dict) -> dict:
    merged_time = {}
    for day, timing in timings.items():
        int_day = day_to_int(day)
        if int_day in days:
            merged_time[int_day] = ['0000-2359']
        else:
            merged_time[int_day] = timing
    return merged_time

def check_block_timings(lesson_info: dict, blocked_slots: dict) -> bool:
    day = lesson_info['day']
    if day not in blocked_slots:
        return False
    timings_list = blocked_slots[day]
    lesson_start = int(lesson_info['start_time'])
    lesson_end = int(lesson_info['end_time'])
    for timing in timings_list:
        time = timing.split('-')
        start_block = int(time[0])
        end_block = int(time[1])
        #lesson starts in block
        if lesson_start < end_block and lesson_start >= start_block:
            return True
        #lesson ends in block
        elif lesson_end <= end_block and lesson_end > start_block:
            return True
        #lesson contains the full block
        elif lesson_start <= start_block and lesson_end >= end_block:
            return True
    return False

def parse_time(time_str):
    """Convert time in HHMM format to minutes since midnight."""
    hours = int(time_str[:2])
    minutes = int(time_str[2:])
    return hours * 60 + minutes

def format_time(minutes):
    """Convert minutes since midnight to HHMM format."""
    hours = minutes // 60
    minutes = minutes % 60
    return f'{hours:02d}{minutes:02d}'

def url_generator(modules: list, class_info: list, semester: str) -> str:
    mod_info = ""
    for i, module in enumerate(modules):
        mod_info += f"{module}="
        for classes in class_info[i]:
            mod_info += classes
        mod_info = mod_info[:-1] + '&'
    return f"https://nusmods.com/timetable/sem-{semester}/share?{mod_info[:-1]}"

def single_timeslot_filter(distinct_mod_info: list) -> list:
    filtered_info = []
    for module in distinct_mod_info:
        filtered_module = {}
        for class_type, class_info in module.items():
            if len(class_info) == 1:
                filtered_module[class_type] = class_info
        filtered_info.append(filtered_module)
    return filtered_info

def check_overlaps(module1_info, module2_info):
    overlaps = []
    for class_type1, lessons1 in module1_info.items():
        for times1 in lessons1.values():
            for class1 in times1:
                day1 = class1['day']
                start1 = parse_time(class1['start_time'])
                end1 = parse_time(class1['end_time'])
                for class_type2, lessons2 in module2_info.items():
                    for times2 in lessons2.values():
                        for class2 in times2:
                            day2 = class2['day']
                            start2 = parse_time(class2['start_time'])
                            end2 = parse_time(class2['end_time'])
                            # Check for any overlap
                            if day1 == day2 and start1 < end2 and start2 < end1:
                                overlaps.append({
                                    'module1': f"{class_type1}[{class1['class_no']}] on {int_to_days(day1)}, {class1['start_time']}-{class1['end_time']}",
                                    'module2': f"{class_type2}[{class2['class_no']}] on {int_to_days(day2)}, {class2['start_time']}-{class2['end_time']}"
                                })
    return overlaps
