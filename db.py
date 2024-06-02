import logging
import requests
from supabase import create_client, Client
from utils.keys import DB_PASSWORD, DB_URL, DB_API_KEY
from utils.helpers import day_to_int
import pdb

class SupabaseClient:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)
        acad_year = '2023-2024'
        self.base_url = f'https://api.nusmods.com/v2/{acad_year}/%s.json'
        self.db = create_client(DB_URL, DB_API_KEY)

    def check_valid_mod(self, mod_id: str, semester: str) -> bool:
        # TODO: Error handling for resp
        resp = self.db.table('modules').select('id').eq('id', mod_id).execute()
        if resp.data:
            return True
        else:
            return False

    def _get_modules(self) -> list:
        url = self.base_url % 'moduleList'
        data = requests.get(url).json()
        module_list = [mod['moduleCode'] for mod in data]
        return module_list

    def _get_module_info(self, module_code: str) -> list:
        url = self.base_url % f'modules/{module_code}'
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
                    'lesson_type': lesson_data['lessonType'],
                    'class_id': lesson_data['classNo'],
                    'day': day_to_int(lesson_data['day']),
                    'start_time': lesson_data['startTime'],
                    'end_time': lesson_data['endTime'],
                    'venue': lesson_data['venue'],
                    'size': lesson_data['size']
                }
                module_info.append(tmp)
        return module_info

    def _upsert(self, table: str, data: list) -> None:
        d, count = self.db.table(table).upsert(data).execute()
        row_cnt = len(d[1])
        self.logger.info(f'{row_cnt} rows inserted into {table} table')

if __name__ == "__main__":
    client = SupabaseClient()
    print(client.check_valid_mod('CS1101s'))