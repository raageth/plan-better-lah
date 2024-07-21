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
    # test_result_url = "https://nusmods.com/timetable/sem-2/share?CS1101S=TUT:02,REC:01,LEC:1&MA1521=TUT:22,LEC:2&MA1522=TUT:15,LEC:2&IS1108=TUT:08,LEC:1&GEA1000=TUT:D28"

    planner = ModPlanner(test_modules, load_test_file('s2_5m_positive.json'), 2, 10)
    url = planner.solve()
    # assert url == test_result_url
    assert url

def test_s1_8m_negative():
    """
    Test sem1, 8 mods, negative case
    """
    test_modules = ['CS1101S', 'MA1521', 'MA1522', 'IS1108', 'GEA1000', 'CS1231', 'CS2030', 'CS2040']
    test_result_url = ""

    planner = ModPlanner(test_modules, load_test_file('s1_8m_negative.json'), 1, 10)
    url = planner.solve()
    # assert url == test_result_url
    assert not url