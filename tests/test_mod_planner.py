import unittest
from algo.mod_planner import ModPlanner

class TestModPlanner(unittest.TestCase):
    def setUp(self):
        self.test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000']
        self.test_mod_info = [
            {'TUT': {'05': [{'day': 1, 'start_time': '1400', 'end_time': '1600'}], '04': [{'day': 2, 'start_time': '1200', 'end_time': '1400'}], '06': [{'day': 2, 'start_time': '1400', 'end_time': '1600'}], '02': [{'day': 2, 'start_time': '1000', 'end_time': '1200'}]}, 
            'REC': {'02': [{'day': 4, 'start_time': '1100', 'end_time': '1200'}], '01': [{'day': 4, 'start_time': '1000', 'end_time': '1100'}]}, 
            'LEC': {'1': [{'day': 3, 'start_time': '1200', 'end_time': '1400'}]}}, 
            {'TUT': {'19': [{'day': 4, 'start_time': '1200', 'end_time': '1300'}], '20': [{'day': 4, 'start_time': '1300', 'end_time': '1400'}], '7': [{'day': 2, 'start_time': '0900', 'end_time': '1000'}], 
            '16': [{'day': 4, 'start_time': '0900', 'end_time': '1000'}], '17': [{'day': 4, 'start_time': '1000', 'end_time': '1100'}], '18': [{'day': 4, 'start_time': '1100', 'end_time': '1200'}], 
            '21': [{'day': 5, 'start_time': '1400', 'end_time': '1500'}], '22': [{'day': 5, 'start_time': '1500', 'end_time': '1600'}], '24': [{'day': 5, 'start_time': '1700', 'end_time': '1800'}], 
            '8': [{'day': 2, 'start_time': '1400', 'end_time': '1500'}], '9': [{'day': 2, 'start_time': '1500', 'end_time': '1600'}], '11': [{'day': 2, 'start_time': '1700', 'end_time': '1800'}], 
            '12': [{'day': 3, 'start_time': '0900', 'end_time': '1000'}], '13': [{'day': 3, 'start_time': '1000', 'end_time': '1100'}], '15': [{'day': 3, 'start_time': '1300', 'end_time': '1400'}], 
            '1': [{'day': 1, 'start_time': '0900', 'end_time': '1000'}], '2': [{'day': 1, 'start_time': '1000', 'end_time': '1100'}], '3': [{'day': 1, 'start_time': '1100', 'end_time': '1200'}], 
            '4': [{'day': 1, 'start_time': '1200', 'end_time': '1300'}], '5': [{'day': 1, 'start_time': '1600', 'end_time': '1700'}], '6': [{'day': 1, 'start_time': '1700', 'end_time': '1800'}], 
            '10': [{'day': 2, 'start_time': '1600', 'end_time': '1700'}], '23': [{'day': 5, 'start_time': '1600', 'end_time': '1700'}], '14': [{'day': 3, 'start_time': '1200', 'end_time': '1300'}]}, 
            'LEC': {'2': [{'day': 4, 'start_time': '1400', 'end_time': '1600'}, {'day': 1, 'start_time': '1400', 'end_time': '1600'}], 
            '1': [{'day': 5, 'start_time': '1000', 'end_time': '1200'}, {'day': 2, 'start_time': '1000', 'end_time': '1200'}]}}, 
            {'TUT': {'2': [{'day': 1, 'start_time': '1200', 'end_time': '1300'}], '3': [{'day': 1, 'start_time': '1400', 'end_time': '1500'}], '7': [{'day': 2, 'start_time': '1300', 'end_time': '1400'}], 
            '5': [{'day': 2, 'start_time': '1100', 'end_time': '1200'}], '8': [{'day': 2, 'start_time': '1400', 'end_time': '1500'}], '10': [{'day': 3, 'start_time': '0900', 'end_time': '1000'}], 
            '11': [{'day': 3, 'start_time': '1000', 'end_time': '1100'}], '17': [{'day': 5, 'start_time': '1000', 'end_time': '1100'}], '18': [{'day': 5, 'start_time': '1100', 'end_time': '1200'}], 
            '13': [{'day': 3, 'start_time': '1200', 'end_time': '1300'}], '14': [{'day': 3, 'start_time': '1300', 'end_time': '1400'}], '15': [{'day': 4, 'start_time': '1200', 'end_time': '1300'}], 
            '16': [{'day': 4, 'start_time': '1300', 'end_time': '1400'}], '1': [{'day': 1, 'start_time': '1100', 'end_time': '1200'}], '4': [{'day': 1, 'start_time': '1500', 'end_time': '1600'}], 
            '6': [{'day': 2, 'start_time': '1200', 'end_time': '1300'}], '9': [{'day': 2, 'start_time': '1500', 'end_time': '1600'}], '12': [{'day': 3, 'start_time': '1100', 'end_time': '1200'}]}, 
            'LEC': {'2': [{'day': 2, 'start_time': '0800', 'end_time': '1000'}, {'day': 4, 'start_time': '0800', 'end_time': '1000'}], 
            '1': [{'day': 1, 'start_time': '1600', 'end_time': '1800'}, {'day': 4, 'start_time': '1600', 'end_time': '1800'}]}}, 
            {'TUT': {'13': [{'day': 3, 'start_time': '1300', 'end_time': '1500'}], '14': [{'day': 3, 'start_time': '1400', 'end_time': '1600'}], '06': [{'day': 1, 'start_time': '1400', 'end_time': '1600'}], 
            '11': [{'day': 3, 'start_time': '1100', 'end_time': '1300'}], '01': [{'day': 1, 'start_time': '0900', 'end_time': '1100'}], '02': [{'day': 1, 'start_time': '1000', 'end_time': '1200'}], 
            '25': [{'day': 3, 'start_time': '0900', 'end_time': '1100'}], '26': [{'day': 3, 'start_time': '1500', 'end_time': '1700'}], '05': [{'day': 1, 'start_time': '1300', 'end_time': '1500'}], 
            '08': [{'day': 1, 'start_time': '1600', 'end_time': '1800'}], '10': [{'day': 3, 'start_time': '1000', 'end_time': '1200'}], '20': [{'day': 1, 'start_time': '1500', 'end_time': '1700'}], 
            '04': [{'day': 1, 'start_time': '1200', 'end_time': '1400'}], '12': [{'day': 3, 'start_time': '1200', 'end_time': '1400'}], '16': [{'day': 3, 'start_time': '1600', 'end_time': '1800'}]}, 
            'LEC': {'1': [{'day': 5, 'start_time': '1200', 'end_time': '1400'}]}}, 
            {'TUT': {'D20': [{'day': 4, 'start_time': '1500', 'end_time': '1800'}], 'D26': [{'day': 3, 'start_time': '0900', 'end_time': '1200'}], 'D28': [{'day': 3, 'start_time': '1500', 'end_time': '1800'}], 
            'E19': [{'day': 1, 'start_time': '0900', 'end_time': '1200'}], 'D14': [{'day': 2, 'start_time': '1500', 'end_time': '1800'}], 'D32': [{'day': 5, 'start_time': '1200', 'end_time': '1500'}], 
            'D54': [{'day': 5, 'start_time': '1500', 'end_time': '1800'}], 'D05': [{'day': 3, 'start_time': '1200', 'end_time': '1500'}], 'E22': [{'day': 2, 'start_time': '0900', 'end_time': '1200'}], 
            'E23': [{'day': 2, 'start_time': '1200', 'end_time': '1500'}], 'E03': [{'day': 1, 'start_time': '1500', 'end_time': '1800'}], 'D30': [{'day': 4, 'start_time': '1200', 'end_time': '1500'}], 
            'D29': [{'day': 4, 'start_time': '0900', 'end_time': '1200'}], 'E08': [{'day': 1, 'start_time': '1200', 'end_time': '1500'}]}}
        ]
        self.test_result_url = "https://nusmods.com/timetable/sem-2/share?CS1101S=TUT:06,REC:02,LEC:1&MA1521=TUT:16,LEC:1&MA1522=TUT:7,LEC:1&IS1108=TUT:16,LEC:1&GEA1000=TUT:D54"

    def test_plan(self):
        planner = ModPlanner(self.test_modules, self.test_mod_info, 2)
        url = planner.solve()
        self.assertEqual(url, self.test_result_url)

if __name__ == '__main__':
    unittest.main()