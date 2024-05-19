import logging
import requests
from supabase import create_client, Client
from keys import DB_PASSWORD, DB_URL, DB_API_KEY

def day_to_int(day: str) -> int:
    days = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5
    }
    return days[day]

def get_modules(url: str) -> list:
    url = url % 'moduleList'
    data = requests.get(url).json()
    module_list = [mod['moduleCode'] for mod in data]
    return module_list

def get_module_info(url: str, module_code: str) -> list:
    url = url % f'modules/{module_code}'
    data = requests.get(url).json()
    module_info = []
    for sem_data in data['semesterData']:
        semester = int(sem_data['semester'])
        for lesson_data in sem_data['timetable']:
            # lesson_data -> dict
            tmp = {
                # TODO: format start_time and end_time
                'mod_id': module_code,
                'semester': semester,
                'class_id': lesson_data['classNo'],
                'lesson_type': lesson_data['lessonType'],
                'day': day_to_int(lesson_data['day']),
                'start_time': lesson_data['startTime'],
                'end_time': lesson_data['endTime'],
                'venue': lesson_data['venue'],
                'size': lesson_data['size']
            }
            module_info.append(tmp)
    return module_info

def upsert_db(db: Client, table: str, data: list) -> None:
    d, count = db.table(table).upsert(data).execute()
    row_cnt = len(d[1])
    logger.info(f'{row_cnt} rows inserted into {table} table')
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    db = create_client(DB_URL, DB_API_KEY)

    acad_year = '2023-2024'
    url = f'https://api.nusmods.com/v2/{acad_year}/%s.json'

    module_list = get_modules(url)
    data = []

    for module in module_list[:5]:
        module_info = get_module_info(url, module)
        data.extend(module_info)
    
    upsert_db(db, 'modules', {'id': 'test', 'title': 'test'})