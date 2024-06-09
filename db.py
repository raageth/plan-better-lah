import logging
import requests
from utils.keys import MONGO_CONN_STRING
from utils.helpers import day_to_int, shorten_lesson_type
from pymongo import MongoClient
from pprint import pprint
import json
import pdb

class DBClient:
    def __init__(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        acad_year = '2023-2024'
        self.base_url = f'https://api.nusmods.com/v2/{acad_year}/%s.json'
        self.mongo_client = MongoClient(f'{MONGO_CONN_STRING}')
        self.db = self.mongo_client.nusmods
        self.collection = self.db.module_info 

    def check_valid_mod(self, mod_id: str, semester: str) -> bool:
        resp = self.collection.find_one({'mod_id': mod_id, f'semester_data.{semester}': {'$exists': True}})
        if resp:
            return True
        else:
            return False
    
    def get_mod_info(self, mod_id: str, semester: str) -> dict:
        # No need error handling for resp as check_valid_mod is called before this
        resp = self.collection.find_one({'mod_id': mod_id})
        mod_info = resp['semester_data'][semester]
        return mod_info

    def _get_modules(self) -> list:
        url = self.base_url % 'moduleList'
        data = requests.get(url).json()
        module_list = [mod['moduleCode'] for mod in data]
        return module_list

    def _get_module_info(self, module_code: str) -> dict:
        url = self.base_url % f'modules/{module_code}'
        data = requests.get(url).json()
        module_info = {
            'mod_id': module_code,
            'mod_name': data['title'],
            'semester_data': {}
        }
        for sem_data in data['semesterData']:
            semester = str(sem_data['semester'])
            module_info['semester_data'][semester] = {}
            for timetable in sem_data['timetable']:
                # lesson_data -> dict
                lesson_type = shorten_lesson_type(timetable['lessonType'])
                class_no = timetable['classNo']

                lesson_data = module_info['semester_data'][semester].get(lesson_type, {})
                module_info['semester_data'][semester][lesson_type] = lesson_data

                class_data = lesson_data.get(class_no, [])
                class_data.append({
                    'class_no': timetable['classNo'],
                    'day': day_to_int(timetable['day']),
                    'start_time': timetable['startTime'],
                    'end_time': timetable['endTime'],
                })
                module_info['semester_data'][semester][lesson_type][class_no] = class_data
    
        return module_info

    def insert_module_info(self) -> None:
        # transaction should be atomic
        mod_id_list = self._get_modules()
        insert_list = []
        for mod_id in mod_id_list:
            module_info = self._get_module_info(mod_id)
            insert_list.append(module_info)
        
        result = self.collection.insert_many(insert_list).inserted_ids
        self.logger.info(f'{len(result)} rows inserted')

if __name__ == "__main__":
    client = DBClient()
    t = client.get_mod_info('CE3102', '2')
    