#!/usr/bin/python
"""
Initialize the mongodb database with training dates
"""
import sys
import json

from Database import Database
import constants as c


def main():
    """
    Initialize the mongodb database with possible training dates.
    The configuration file config.json needs the following structure:
    {
      "database-connect-string": "mongodb+srv://<your-connect-string>",
      "num_trainings": <int of how many trainings should be initialized in the db>
      "trainings": [
        {
            "weekday": <weekday_as_int>,
            "time": "HH:MM"
        },
        ...
      ],
    }
    The weekday is provided as int (where 0 means monday and 6 is sunday).
    In the trainings list you can provide dates and times of the week, where
    trainings are possible.
    The next num_trainings trainings are then initialized in the database
    """
    database = Database(c.CONFIG_FILE, False)

    with open(c.CONFIG_FILE, "r") as cfg:
        config = json.load(cfg)

    if "num_trainings" not in config:
        print(f"ERROR: Key \"num_trainings\" missing in config file {c.CONFIG_FILE}")
        sys.exit(1)

    database.create_trainings(config["num_trainings"])


if __name__ == "__main__":
    main()
