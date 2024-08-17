"""This module is responsible for testing the functionality of the habit class.
Two fixtures are used: testing_data for habit data, and testing_habits to load habit instances using that data."""

import datetime

import pytest

from habit import Habit
import utils

Habit.db_name = "test_db.db"

start_date = utils.add_midnight(datetime.date.today() - datetime.timedelta(days=28))
iso_start_date = start_date.isoformat()


@pytest.fixture
def testing_data():
    walk_example_data = [
        ('Take a walk', datetime.datetime.now() - datetime.timedelta(days=i), 'Success') for i in range(1, 28)
    ]

    run_example_data = [
        ('Run', start_date + datetime.timedelta(days=7), 'Success'),
        ('Run', start_date + datetime.timedelta(days=14), 'Success'),
        ('Run', start_date + datetime.timedelta(days=21), 'Failure'),
        ('Run', start_date + datetime.timedelta(days=21), 'Restart')
    ]

    read_15_minutes_data = [
        ('Read for 15 minutes', start_date + datetime.timedelta(days=i), 'Success') for i in range(1, 9)
    ]
    read_15_minutes_data += [
        ('Read for 15 minutes', start_date + datetime.timedelta(days=13), 'Failure'),
        ('Read for 15 minutes', start_date + datetime.timedelta(days=13), 'Restart')
    ]
    read_15_minutes_data += [
        ('Read for 15 minutes', start_date + datetime.timedelta(days=i), 'Success') for i in range(14, 27)
    ]

    tuition_example_data = [
        ('Pay tuition', utils.add_midnight(datetime.date.today() - datetime.timedelta(days=31)), 'Success')
    ]

    meditate_example_data = [
        ('Meditate', start_date + datetime.timedelta(days=i), 'Success') for i in range(0, 28, 7)
    ]

    yield {
        'walk': walk_example_data,
        'run': run_example_data,
        'read': read_15_minutes_data,
        'tuition': tuition_example_data,
        'meditate': meditate_example_data
    }


@pytest.fixture
def testing_habits(testing_data):
    Walk = Habit('Take a walk', 'Daily', iso_start_date, data=testing_data['walk'])
    Run = Habit('Run', 'Weekly', iso_start_date, data=testing_data['run'])
    Read = Habit('Read for 15 minutes', 'Daily', iso_start_date, data=testing_data['read'])
    Tuition = Habit('Pay tuition', 'Monthly', utils.add_midnight(datetime.datetime(2024, 6, 2, 0, 0, 0)),
                    data=testing_data['tuition'])
    Meditate = Habit('Meditate', 'Weekly', iso_start_date, data=testing_data['meditate'])

    yield {
        'walk': Walk,
        'run': Run,
        'read': Read,
        'tuition': Tuition,
        'meditate': Meditate
    }


def test_streak_calculation(testing_habits):
    assert testing_habits['walk'].streak == 27
    assert testing_habits['walk'].longest_streak == 27


def test_state_calculation(testing_habits):
    for habit in ['walk', 'read']:
        testing_habits[habit].load_state()

    assert testing_habits['walk'].state == 'Ready'
    assert testing_habits['read'].state == 'Broken'


def test_check_off_and_restart(testing_habits):
    habit = testing_habits['walk']
    habit.check_off()

    assert habit.streak == 28
    assert habit.state == 'Unready'

    testing_habits['walk'].restart()
    assert testing_habits['walk'].streak == 0
    assert testing_habits['walk'].longest_streak == 28
    assert habit.state == 'Unready'


def test_fail_tracking(testing_habits):
    assert testing_habits['run'].fail_count == 1
    assert testing_habits['read'].fail_count == 1

    assert testing_habits['run'].last_fail == start_date + datetime.timedelta(days=21)
    assert testing_habits['read'].last_fail == start_date + datetime.timedelta(days=13)
