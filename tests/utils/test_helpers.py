import pytest
from utils.helpers import *

def test_day_to_int():
    days_str = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_int = [1, 2, 3, 4, 5, 6, 7]
    for i in range(len(days_str)):
        assert day_to_int(days_str[i]) == days_int[i]

def test_int_to_days():
    days_str = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    days_int = [1, 2, 3, 4, 5, 6, 7]
    for i in range(len(days_str)):
        assert int_to_days(days_int[i]) == days_str[i]
    
def test_user_days_to_array():
    input_str = '3,4,1,2,5,6,7'
    days = ['1', '2', '3', '4', '5', '6', '7']
    assert user_days_to_array(input_str) == days

def test_parse_time():
    time_str = '0800'
    assert parse_time(time_str) == 480

    time_str = '0000'
    assert parse_time(time_str) == 0

def test_format_time():
    time_int = 480
    assert format_time(time_int) == '0800'

    time_int = 0
    assert format_time(time_int) == '0000'