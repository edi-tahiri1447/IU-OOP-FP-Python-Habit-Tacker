# Habit Tracker App & Habit Class

A simple habit tracker application that allows you to enter habits you would like to keep yourself accountable for.
Supports daily, weekly and monthly habits, and provides extensive analytical capabilities, allowing you to look deep into your own behavior through an interactive and straightforward GUI powered by Tkinter.

Also contains the Habit class module, which is the central feature of the project. Designed to be used with a SQLite3 database.

## Features

- Creation and storage of habit data
- Tkinter GUI that is easy to use and navigate
- Data analytics; every detail is visible to the user
- Habit class module
- Thoroughly documented code

## Installation

```shell
pip install -r requirements.txt
```

## Usage

### Running the habit tracker

Run main.py and the GUI will open, allowing you to use the app.

### Creating a new habit

In the habit tracker, habit creation is very straightforward: simply press the "Add Habit" button, enter the habit name and periodicity, and confirm by pressing "Create New Habit."

If you're using the habit class for your own project, keep in mind that there are two ways to instantiate a habit object:

1. With predefined data (data list is passed as a parameter when initializing class instance). This is used for the unit test, for example, as it allows the class to be used without a SQLite database.
2. Without predefined data. This is what is used in the habit tracker app. Not passing a 
data list while instantiating a habit makes it search in the linked database: first for metadata (Habit table) and then for data (Log table).

### Checking-off, deleting or restarting an existing habit

In the habit tracker, all of these actions are done by pressing the respective button while having the habit selected.

If you're using the habit class for your own project, simply call the respective method for each of them. If you're using the habit class with a SQLite database, remember to use the method save_to_db to save your changes.

### Viewing habit analytics

In the habit tracker, there are a lot of analytics to be seen. Press the "Show Analytics" button and the app will open a new window where you can see all of your habits grouped by periodicity.

You can also select an individual habit and view the detailed history of every action.

You will also see all of your longest-running habits, and the habits you have broken the most throughout their history.

If you're using the habit class, you can access the history of the habit through the habit.data attribute, and parse the list directly in Python. You can also do it through SQL, if you're using the database functionality. 

## Testing

All files related to testing can be found inside the "test" directory.

First run the test_habit.py unit test.

Then, run the test_db_integration.py integration test.

After that you may run the tracker_test.py script, which will open an identical copy of the habit tracker itself; except this one is connected to the test database and filled with five predefined habits and four weeks of tracking data.