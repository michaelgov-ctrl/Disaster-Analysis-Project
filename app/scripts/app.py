import matplotlib.pyplot as plt
from pathlib import Path
import sqlite3
import sys

def print_rows(rows):
    # helper to print query responses
    if not rows:
        print("No results found.")
        return

    for row in rows:
        print(row)

def get_int(prompt, default=None):
    # helper to process user input to an integer
    value = input(prompt).strip()

    if value == "":
        return default

    try:
        return int(value)
    except ValueError:
        print("Please enter a valid number.")
        return get_int(prompt, default) # a little recursion as a treat ( ͡° ͜ʖ ͡°)

class App:
    """
    Application class for the disaster analysis REPL.

    This class manages the database connection, runs SQL queries,
    displays query results, and creates charts from the disaster data.
    """

    def __init__(self, dbpath):
        """
        Initialize the application with the path to the SQLite database.

        Validates the SQLite connection and sets the
        applications min and max year.
        """

        self.dbpath = dbpath
        self.min_year = 0
        self.max_year = 0
        self.limit = 10
        
        if not self.dbpath.exists():
            raise FileNotFoundError(f"Database not found: {self.dbpath}")

        try:
            with self.connect() as conn:
                self.min_year, self.max_year = self.db_year_range()
        except sqlite3.Error as e:
            raise RuntimeError(f"Could not connect to database: {e}")

    def connect(self):
        """
        Convenience wrapper for sqlite connection
        """

        return sqlite3.connect(self.dbpath)

    def disasters_by_year(self, start_year=None, end_year=None):
        """
        Return the number of disaster declarations for each year
        time sliced by start_year and end_year.
        """

        query = """
        SELECT 
            fy_declared AS year,
            COUNT(*) AS disaster_count
        FROM disasters
        WHERE fy_declared BETWEEN ? AND ?
        GROUP BY fy_declared
        ORDER BY fy_declared;
        """

        with self.connect() as conn:
            return conn.execute(query, (start_year, end_year)).fetchall()

    def disasters_by_state(self, start_year=None, end_year=None, limit=None):
        """
        Return disaster counts grouped by state, limited,
        and time sliced by start_year and end_year.
        """

        query = """
        SELECT 
            s.state_code,
            COUNT(*) AS disaster_count
        FROM disasters d
        JOIN states s ON d.state_id = s.state_id
        WHERE d.fy_declared BETWEEN ? AND ?
        GROUP BY s.state_code
        ORDER BY disaster_count DESC
        LIMIT ?;
        """

        with self.connect() as conn:
            return conn.execute(query, (start_year, end_year, limit)).fetchall()

    def disasters_by_type(self, start_year=None, end_year=None):
        """
        Return disaster counts grouped by incident type.
        """

        query = """
        SELECT 
            it.incident_type,
            COUNT(*) AS disaster_count
        FROM disasters d
        JOIN incident_types it ON d.incident_type_id = it.incident_type_id
        WHERE d.fy_declared BETWEEN ? AND ?
        GROUP BY it.incident_type
        ORDER BY disaster_count DESC;
        """

        with self.connect() as conn:
            return conn.execute(query, (start_year, end_year)).fetchall()

    def search_disasters(self, state=None, year=None, incident_type=None):
        """
        Search disaster declarations using optional state, year,
        and incident_type filters.
        """

        query = """
        SELECT
            d.disaster_id,
            d.declaration_title,
            d.declaration_type,
            d.declaration_date,
            d.fy_declared,
            s.state_code,
            it.incident_type
        FROM disasters d
        JOIN states s ON d.state_id = s.state_id
        JOIN incident_types it ON d.incident_type_id = it.incident_type_id
        WHERE 1 = 1
        """

        params = []

        if state is not None:
            query += " AND s.state_code = ?"
            params.append(state.upper())

        if year is not None:
            query += " AND d.fy_declared = ?"
            params.append(year)

        if incident_type is not None:
            query += " AND it.incident_type = ?"
            params.append(incident_type)

        query += " ORDER BY d.declaration_date DESC;"

        with self.connect() as conn:
            return conn.execute(query, params).fetchall()
    

    def chart_disasters_by_year(self, start_year=None, end_year=None):
        """
        Generate a simple chart of time sliced disasters by year.
        """

        rows = self.disasters_by_year(start_year, end_year)

        years = [row[0] for row in rows]
        counts = [row[1] for row in rows]

        plt.figure(figsize=(10, 5))
        plt.plot(years, counts, marker="o")
        plt.title(f"Declared Disasters by Year ({start_year}-{end_year})")
        plt.xlabel("Year")
        plt.ylabel("Number of Disasters")
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def chart_top_states(self, start_year=None, end_year=None, limit=None):
        """
        Generate a chart of the states with the most disasters.
        """

        rows = self.disasters_by_state(start_year, end_year, limit)

        states = [row[0] for row in rows]
        counts = [row[1] for row in rows]

        plt.figure(figsize=(10, 5))
        plt.bar(states, counts)
        plt.title(f"Top {limit} States by Disaster Count ({start_year}-{end_year})")
        plt.xlabel("State")
        plt.ylabel("Number of Disasters")
        plt.tight_layout()
        plt.show()

    def db_year_range(self):
        """
        Convenience function to populate the application with
        min and max years.
        """

        query = """
        SELECT
            MIN(fy_declared),
            MAX(fy_declared)
        FROM disasters;
        """

        with self.connect() as conn:
            return conn.execute(query).fetchone()

    def REPL(self):
        """
        Run a Read Evaluate Print Loop(REPL) to allow iterative querying of disaster data.
        The REPL displays a menu, asks the user to choose an option andperforms the appropriate action.
        """

        helptext = """
Disaster Analysis CLI

1. Show disasters by year
2. Show top states by disaster count
3. Show disasters by type
4. Search disasters
5. Chart disasters by year
6. Chart top states
7. Exit
"""
        startyeartext = f"Start year [default {self.min_year}]: "
        endyeartext = f"End year [default {self.max_year}]: "
        limittext = f"Limit [default {self.limit}]: "

        while True:
            print(helptext)

            selection = input("Choose an option: ").strip()
            match selection:
                case "1":
                    # Show disasters by year
                    start_year = get_int(startyeartext, self.min_year)
                    end_year = get_int(endyeartext, self.max_year)

                    rows = self.disasters_by_year(start_year, end_year)

                    print("\nYear | Count")
                    print("------------")
                    for year, count in rows:
                        print(f"{year} | {count}")

                case "2":
                    # Show top states by disaster count
                    start_year = get_int(startyeartext, self.min_year)
                    end_year = get_int(endyeartext, self.max_year)
                    limit = get_int(limittext, self.limit)

                    rows = self.disasters_by_state(start_year, end_year, limit)

                    print("\nState | Count")
                    print("-------------")
                    for state, count in rows:
                        print(f"{state} | {count}")

                case "3":
                    # Show disasters by type
                    start_year = get_int(startyeartext, self.min_year)
                    end_year = get_int(endyeartext, self.max_year)

                    rows = self.disasters_by_type(start_year, end_year)

                    print("\nIncident Type | Count")
                    print("---------------------")
                    for incident_type, count in rows:
                        print(f"{incident_type} | {count}")

                case "4":
                    # Search disasters
                    state = input("State code [default all]: ").strip()
                    year = get_int("Year [default all]: ", None)
                    incident_type = input("Incident type [default all]: ").strip()

                    if state == "":
                        state = None

                    if incident_type == "":
                        incident_type = None

                    rows = self.search_disasters(
                        state=state,
                        year=year,
                        incident_type=incident_type,
                    )

                    print("\nSearch Results")
                    print("--------------")
                    for row in rows:
                        print(row)

                case "5":
                    # Chart disasters by year
                    start_year = get_int(startyeartext, self.min_year)
                    end_year = get_int(endyeartext, self.max_year)

                    self.chart_disasters_by_year(start_year, end_year)

                case "6":
                    # Chart top states
                    start_year = get_int(startyeartext, self.min_year)
                    end_year = get_int(endyeartext, self.max_year)
                    limit = get_int(limittext, self.limit)

                    self.chart_top_states(start_year, end_year, limit)

                case "7":
                    # Exit
                    print("Goodbye.")
                    break

                case _:
                    # Invalid choice
                    print("Invalid choice. Please choose 1-7.")

def main(dbpath):
    App(dbpath).REPL()

if __name__ == "__main__":
    dbpath = Path("disasters.db")
    if len(sys.argv) > 1:
        dbpath = Path(sys.argv[1])
    main(dbpath)