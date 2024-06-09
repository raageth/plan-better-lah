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