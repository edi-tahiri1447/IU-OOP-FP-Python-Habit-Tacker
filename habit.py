import datetime

import sqlite3
import dateutil.parser

import utils


class Habit:
    """
    This is the habit class, which is the central part of the habit tracker.
    A habit is a task which must be "checked-off" every given period. The user can establish a streak if the habit is
    checked-off for multiple periods in a row.

    A period can be every day, every calendar week, or every calendar month.

    If a period passes without the habit having been checked-off, the habit is broken.

    Each Habit instance can be initialized with a predefined log, but is by default bound to a database with two tables:
    Habits, where class instances are stored, and
    Log, where check-off dates, breakage dates, and restart dates are stored.

    Attributes:
        db_name (string) (Class attribute):
        This is the name of the SQLite database the habits read and write to.
        Please make sure to overwrite the Habit.db_name and connect it to your own database file before use.

        name (string):
        The name of the habit. In the SQLite 3 setting, this has to be unique (as it is used as the primary key
        of the Habits table) and cannot exceed 32 characters due to database design.

        period (string):
        The periodicity of the habit. Is either 'Daily', 'Weekly' or 'Monthly.'
        Defines state loading (described below.)

        start_date (datetime.date):
        The start date of the habit. Is stored as a datetime string in the DB, then parsed into a datetime.datetime
        object upon loading.
        Can be passed as a string, a datetime.date (time defaults to midnight) or datetime.datetime object.

        data (list):
        Optional; if omitted, Habit instance will draw from the database Log table by querying where the name matches.

        The main data structure of the class. List of tuples of three: name (str), time (datetime), and log type (str).
        Keeps track of the interactions that the habit has undergone and is used to derive all the attributes below.

        last_success (datetime.date):
        The date of the last check-off ('Success' entry).
        Is used to calculate habit state.

        last_restart (datetime.date):
        The date of the last restart ('Restart' entry).

        last_fail (datetime.date):
        The date of the last habit break ('Failure' entry).

        fail_count (int):
        The amount of times a user has broken a habit.

        streak (int):
        The length of the current consecutive chain of check-offs. The streak is calculated by looping through the data
        list, incrementing one for each success, and resetting at a failure or a restart.

        streaks (list):
        A list of all the streaks that have existed for the habit.

        longest_streak (int):
        The longest historic streak, taken as the max value of the streaks list.

        state (string):
        Designed to be loaded during program execution through load_state() method.

        Can either be 'Ready', 'Unready' or 'Broken' depending on how much many periods have passed between
        the last check-off/start and the day of program execution.

        Controls when a user can check-off a habit, and determines whether a habit has been broken.
    """
    db_name = ""

    def __init__(self, name: str, period: str, start_date: str, data=None):
        """
        Initializes Habit class.

        Args:
        name (string): checked for length here based on database design. Default application allows only names up to 32 chars.
        period (string): has to be 'Daily', 'Weekly' or 'Monthly', otherwise exception is raised.
        start_date (string, datetime.date or datetime.datetime): converted into datetime.date regardless of input.
        data (list): Predefined data can be passed here.
        """

        if len(name) > 32:
            raise ValueError("Please make sure the name is 32 characters or fewer!")
        else:
            self.name = name

        if period in ['Daily', 'Weekly', 'Monthly']:
            self.period = period
        else:
            raise ValueError("Please make sure the periodicity is either daily, weekly or monthly!")

        if type(start_date) == str:
            self.start_date = dateutil.parser.isoparse(start_date)
        elif type(start_date) == datetime.date:
            self.start_date = utils.add_midnight(start_date, datetime.min.time())
        elif type(start_date) == datetime.datetime:
            self.start_date = start_date
        else:
            raise ValueError("Please make sure that the supplied start date is either an ISO-Format datetime string or a datetime datetime/date object!")

        if data is not None:
            self.data = sorted(data, key=lambda x: x[1])
        elif data is None:
            self.data = []
            with sqlite3.connect(self.db_name) as conn:
                cur = conn.cursor()
                # load date from SQLite database into data list
                for row in cur.execute("SELECT * FROM Log WHERE Name=? ORDER BY Time ASC", (self.name,)).fetchall():
                    self.data.append((row[0], dateutil.parser.isoparse(row[1]), row[2]))

        self.parse_data()
        self.load_state()

    def parse_data(self):
        """
        Loops through the data list and (re)loads the parameters that are derived from it.

        Updates streak, list of streaks, last_success, last_restart, last_fail and fail_count
        """

        self.streak = 0
        self.streaks = []
        self.longest_streak = 0
        self.fail_count = 0

        self.last_success = None
        self.last_fail = None
        self.last_restart = None

        # loop through the data list
        for row in self.data:
            match row[2]:
                case 'Success':
                    # increment streak, update last_success
                    self.streak += 1

                    self.last_success = row[1]
                case 'Restart':
                    # take streak up until this point, append into list of streak values, then reset
                    self.streaks.append(self.streak)
                    self.streak = 0

                    self.last_restart = row[1]
                case 'Failure':
                    # same as with restart, except also increment fail_count and update last_fail
                    self.streaks.append(self.streak)
                    self.streak = 0

                    self.fail_count += 1
                    self.last_fail = row[1]
        # if done looping without any resets, load streak into list regardless
        self.streaks.append(self.streak)

        if self.streaks:
            self.longest_streak = max(self.streaks)
        else:
            self.longest_streak = 0

    def load_state(self):
        """
        Loads state.

        First, declares a 'compare_time' with which to compare the current time.
        compare_time is either last_success or last_restart (whichever is more recent.)
        If both are missing (like with a newly-created habit), take start_date instead.

        Second, declares a method to calculate the 'differential' between the two times
        depending on the habit periodicity:

        with daily periodicity, the datetime timedelta functionality is used to return the difference in days;
        with weekly periodicity, both times' calendar week are compared.
        with monthly periodicity, both times' calendar months are compared.

        Usage of calendar weeks and calendar months also take into consideration any year difference (see utils module.)

        Depending on the final value of the differential, the state attribute is finally declared.
        If the declared state is 'Broken', the habit is broken, and a 'Failure' record is created if the most recent
        record is not already a 'Failure'.
        """

        if self.last_success is None and self.last_restart is None:
            compare_time = self.start_date
        else:
            compare_time = max((self.last_success if self.last_success is not None else datetime.datetime.min),
                               (self.last_restart if self.last_restart is not None else datetime.datetime.min))

        match self.period:
            case 'Daily':
                differential = int((datetime.date.today() - compare_time.date()).days)
            case 'Weekly':
                differential = utils.diff_of_cw(datetime.datetime.now(), compare_time)
            case 'Monthly':
                differential = utils.diff_of_cm(datetime.datetime.now(), compare_time)

        if differential == 1:
            self.state = 'Ready'
        elif differential < 1:
            self.state = 'Unready'
        elif differential > 1:
            self.state = 'Broken'

            if self.data == [] or self.data[-1][2] != 'Failure':
                self.data.append((self.name, datetime.datetime.now(), 'Failure'))

        self.parse_data()

    def check_off(self):
        """
        Inserts a "Success" record for the habit into the Log table.
        """

        self.data.append((self.name, datetime.datetime.now(), 'Success'))

        self.parse_data()
        self.load_state()

    def restart(self):
        """
        Inserts a "Restart" record for the habit into the log table.
        """

        self.data.append((self.name, datetime.datetime.now(), 'Restart'))

        self.parse_data()
        self.load_state()

    @classmethod
    def initialize_db(cls):
        """
        Class method to establish the necessary tables (and connection between them) inside the database file.
        """

        with sqlite3.connect(cls.db_name) as conn:
            cur = conn.cursor()
            cur.execute("""CREATE TABLE IF NOT EXISTS Habit (
            Name VARCHAR(32) PRIMARY KEY,
            Period VARCHAR(7),
            Start_Date DATETIME
            )""")
            cur.execute("""CREATE TABLE IF NOT EXISTS Log (
            Name VARCHAR(32),
            Time DATETIME,
            Log_Type VARCHAR(7),
            PRIMARY KEY(Name, Time, Log_Type),
            FOREIGN KEY(Name) REFERENCES Habits(NAME)
            )""")

    def delete_from_db(self):
        """
        Wipes the habit off of the database, deleting its entries from both tables.
        """
        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM Habit WHERE Name=?",
                              (self.name,))
            cur.execute("DELETE FROM Log WHERE Name=?",
                              (self.name,))

    def save_to_db(self):
        """
        Updates database by replacing the Log entries in the DB with the contents of the Habit.data attribute.
        """

        with sqlite3.connect(self.db_name) as conn:
            cur = conn.cursor()
            # if habit does not exist in Habit table, enter it there
            if cur.execute("SELECT * FROM Habit WHERE Name=?", (self.name,)).fetchone() is None:
                cur.execute("INSERT INTO Habit VALUES (?, ?, ?)", (self.name, self.period, self.start_date))

            cur.execute("DELETE FROM Log WHERE Name=?", (self.name,))
            cur.executemany("INSERT INTO Log VALUES (?, ?, ?)", self.data)

    def __str__(self):
        return self.name
