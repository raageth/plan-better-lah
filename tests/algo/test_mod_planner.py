import unittest
import json
import os
from algo.mod_planner import ModPlanner

class TestModPlanner(unittest.TestCase):
    def setUp(self):
        pass

    def test_s2_5m_positive(self):
        """
        Test sem2, 5 mods, positive case
        """

        test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000']
        with open(os.path.join(os.path.dirname(__file__), '..', 'testcases', 's2_5m_positive.json'), 'r') as f:
            test_mod_info = json.load(f)
        test_result_url = "https://nusmods.com/timetable/sem-2/share?CS1101S=TUT:06,REC:02,LEC:1&MA1521=TUT:16,LEC:1&MA1522=TUT:7,LEC:1&IS1108=TUT:16,LEC:1&GEA1000=TUT:D54"
        
        planner = ModPlanner(test_modules, test_mod_info, 2)
        url = planner.solve()
        self.assertEqual(url, test_result_url)
    
    def test_s1_8m_negative(self):
        """
        Test sem1, 8 mods, negative case
        """

        test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000', 'CS1231', 'CS2030', 'CS2040']
        with open(os.path.join(os.path.dirname(__file__), '..', 'testcases', 's1_8m_negative.json'), 'r') as f:
            test_mod_info = json.load(f)
        test_result_url = ""
        
        planner = ModPlanner(test_modules, test_mod_info, 1)
        url = planner.solve()
        self.assertEqual(url, test_result_url)

if __name__ == '__main__':
    unittest.main()