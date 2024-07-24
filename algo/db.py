import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import requests
from utils.keys import MONGO_CONN_STRING
from utils.helpers import day_to_int, shorten_lesson_type, check_block_timings
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
        acad_year = '2024-2025'
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
        data = requests.get(url=url).json()       
        module_list = [mod['moduleCode'] for mod in data]
        return module_list

    def _get_module_info(self, module_code: str) -> dict:
        url = self.base_url % f'modules/{module_code}'
        # handle api resp
        data = requests.get(url=url).json()
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
            self.logger.info(f'Retrieved module info for {mod_id}')
            insert_list.append(module_info)
        
        result = self.collection.insert_many(insert_list).inserted_ids
        self.logger.info(f'{len(result)} rows inserted')
    
    def refresh_module_info(self) -> None:
        resp = self.collection.delete_many({})
        self.logger.info(f'{resp.deleted_count} rows deleted')
        self.insert_module_info()

    def draw_module_info(self, modules: list, semester: str) -> list:
        mod_info = []
        for module in modules:
            mod_info.append(self.get_mod_info(module, semester))
        return mod_info

    #old version
    def draw_filtered_module_info(self, modules: list, semester: str, blocked_days: list, timings: dict) -> list:
        mod_info = []
        for module in modules:
            mod_info.append(self.get_mod_info(module, semester))

        blocked_timings = {}
        for key in timings:
            if timings[key]:
                blocked_timings[day_to_int(key)] = timings[key]

        unique_mod_info = self.module_days_filtered(mod_info, blocked_days, blocked_timings)
        #print(unique_mod_info)
        return unique_mod_info
    
    def module_days_filtered(self, mod_info: list, blocked_days: list, blocked_timings: dict) -> list:
        if blocked_days or blocked_timings:
            filtered_mod_info = []
            for mod in mod_info:
                filtered_info = {}
                for lesson_type, class_info in mod.items():
                    filtered_classes = {}

                    for lesson_no, lesson_info in class_info.items():
                        is_blocked = False
                        for item in lesson_info:
                            if item['day'] in blocked_days or check_block_timings(item, blocked_timings):
                                is_blocked = True
                                break
                        if not is_blocked:
                            filtered_classes[lesson_no] = lesson_info

                    filtered_info[lesson_type] = filtered_classes

                filtered_mod_info.append(filtered_info)

            return filtered_mod_info
        
        return mod_info

    def create_testcase(self, modules: list, semester: str, blocked_days: list, result: str) -> None:
        """
        Generates testcases

        result: positive / negative
        """
        mod_info = self.draw_module_info(modules, semester, blocked_days)
        with open(os.path.join(os.path.dirname(__file__), '..', 'tests', 'testcases', f's{semester}_{len(modules)}m_{result}.json'), 'w') as f:
            json.dump(mod_info, f)
        self.logger.info(f'Testcase for {semester} {len(modules)} modules created')

if __name__ == "__main__":
    pass
    
    