"""This module is used to test integration between the Habit class and a SQLite 3 database.

This test covers everything in the test_habit.py test, but with data from the database as opposed to within the pytest
fixture.
"""

import datetime

import pytest
import sqlite3

from habit import Habit
from test_habit import testing_data
import utils

start_date = utils.add_midnight(datetime.date.today() - datetime.timedelta(days=28))
iso_start_date = start_date.isoformat()

Habit.db_name = "test_db.db"
conn = sqlite3.connect(Habit.db_name)
cur = conn.cursor()


@pytest.fixture
def db_habit_metadata():
    yield [
        ('Take a walk', 'Daily', iso_start_date),
        ('Run', 'Weekly', iso_start_date),
        ('Read for 15 minutes', 'Daily', iso_start_date),
        ('Pay tuition', 'Monthly', datetime.datetime(year=2024, month=6, day=10)),
        ('Meditate', 'Weekly', iso_start_date)
    ]


def test_db_init(testing_data, db_habit_metadata):
    with conn:
        cur.execute("DROP TABLE Log")
        cur.execute("DROP TABLE Habit")

    Habit.initialize_db()

    with conn:
        cur.execute("DELETE FROM Habit")
        cur.execute("DELETE FROM Log")

        cur.executemany("INSERT INTO Habit Values (?, ?, ?)", db_habit_metadata)
        for dataset in testing_data.values():
            cur.executemany("INSERT INTO Log VALUES (?, ?, ?)", dataset)

    assert cur.execute("SELECT * FROM Habit").fetchall() != []
    assert cur.execute("SELECT * FROM Log").fetchall() != []


@pytest.fixture
def db_testing_habits():
    Walk = Habit('Take a walk', 'Daily', iso_start_date)
    Run = Habit('Run', 'Weekly', iso_start_date)
    Read = Habit('Read for 15 minutes', 'Daily', iso_start_date)
    Tuition = Habit('Pay tuition', 'Monthly', utils.add_midnight(datetime.datetime(2024, 6, 2, 0, 0, 0)))
    Meditate = Habit('Meditate', 'Weekly', iso_start_date)

    yield {
        'walk': Walk,
        'run': Run,
        'read': Read,
        'tuition': Tuition,
        'meditate': Meditate
    }


def test_habit_loading_and_creation(db_testing_habits):
    Walk = db_testing_habits['walk']
    Run = db_testing_habits['run']
    Read = db_testing_habits['read']

    # does the streak and fail count still get calculated right?
    assert Walk.streak == 27
    assert Run.fail_count == 1

    # and state?
    Walk.load_state()
    assert Walk.state == 'Ready'
    Read.load_state()
    assert Read.state == 'Broken'

    # does an initialized habit get written into the Habit table?
    Tea = Habit('Drink green tea', 'Daily', datetime.datetime.now().isoformat())
    Tea.save_to_db()
    assert cur.execute("SELECT * FROM Habit WHERE Name=?", ('Drink green tea',)).fetchone() != []


def test_habit_writing(db_testing_habits):
    Walk = db_testing_habits['walk']
    with conn:
        assert len(cur.execute("SELECT * FROM Log WHERE Name=?", (Walk.name,)).fetchall()) == 27
    assert Walk.streak == 27

    Walk.check_off()
    Walk.save_to_db()
    with conn:
        assert len(cur.execute("SELECT * FROM Log WHERE Name=?", (Walk.name,)).fetchall()) == 28
    assert Walk.streak == 28

    Walk.restart()
    Walk.save_to_db()
    with conn:
        assert cur.execute("SELECT Log_Type FROM Log WHERE Time=(SELECT MAX(Time) FROM Log) and Name=?",
                           (Walk.name,)).fetchone()[0] == 'Restart'
    Walk.load_state()
    Walk.parse_data()
    assert Walk.state == 'Unready'
    assert Walk.streak == 0
    assert Walk.longest_streak == 28
