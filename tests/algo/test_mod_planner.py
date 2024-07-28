import pytest
import json
import os
from algo.mod_planner import ModPlanner
from ortools.sat.python import cp_model

def load_test_file(file_name):
    with open(os.path.join(os.path.dirname(__file__), '..', 'testcases', file_name), 'r') as f:
        return json.load(f)

def test_s2_5m_positive():
    """
    Test sem2, 5 mods, positive case
    """
    test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000']
    test_blocked_timings = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    test_result_url = "https://nusmods.com/timetable/sem-2/share?CS1101S=TUT:01,REC:02,LEC:1&MA1521=TUT:5,LEC:2&MA1522=TUT:18,LEC:2&IS1108=LEC:2,TUT:10&GEA1000=TUT:D25"
    test_mod_info = load_test_file('s2_5m_positive.json')
    planner = ModPlanner(test_modules, test_mod_info, 2, 24, test_blocked_timings, test_mod_info)
    (url, best_info, errormsg) = planner.solve()
    assert url

def test_s1_8m_negative():
    """
    Test sem1, 8 mods, negative case
    """
    test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000', 'CS1231', 'CS2030', 'CS2040']
    test_blocked_timings = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    test_result_url = ""
    test_mod_info = load_test_file('s1_8m_negative.json')
    planner = ModPlanner(test_modules, test_mod_info, 1, 6, test_blocked_timings, test_mod_info)
    (url, best_info, errormsg) = planner.solve()
    assert not url