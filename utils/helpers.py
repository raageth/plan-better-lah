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
        'Workshop': 'WS',
        'Tutorial Type 2': 'TUT2',
    }

    return lesson_types[lesson_type]