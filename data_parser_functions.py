import re
import sqlite3
import sys
from prettytable import prettytable


class PrecipitationData:
    def __init__(self, x, y, month, year, data):
        self.x = x
        self.y = y
        self.month = month
        self.year = year
        self.data = data


def user_input():
    target, sort_by = "", ""
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.lower().capitalize() in field_names or arg == "none":
                sort_by = arg
            else:
                target = arg
    if target == "":
        target = input("Enter the file name: ")
    return target, sort_by


def open_file(target):
    try:
        file = open(target, "r")
        lines = file.readlines()
        file.close()
    except FileNotFoundError:
        print(f"File '{target}' not found")
        sys.exit(1)
    return lines


def get_start_year(str):
    regex = re.compile(r"(\d{4})-(\d{4})")
    match = regex.search(str)
    if match:
        return int(match.group(1))
    else:
        return None


def parse_file_header(lines):
    metadata = {}
    # [Long=-180.00, 180.00] [Lati= -90.00,  90.00] [Grid X,Y= 720, 360]
    # [Boxes=   67420] [Years=1991-2000] [Multi=    0.1000] [Missing=-999]
    count = 0
    metafound = False
    for line in lines:
        regex = re.compile(r"\[(.*?)\]")
        matches = regex.findall(line)
        if matches:
            for match in matches:
                key, value = match.split("=")
                metadata[key.strip()] = value.strip()
            metafound = True
        if metafound and not matches:
            break
        count = count + 1
    return metadata, count


def parse_data(lines, start_year, header_length):
    parsed_data, problematic_data = [], []
    index, year_index = 0, start_year
    x, y = 0, 0
    # For testing
    escape = 0
    for line in lines[header_length:]:
        if new_line_reference in line:
            # print(index)
            year_index = start_year
            # Extract xy from grid reference
            x = int(line.split()[1].replace(',', ''))
            y = int(line.split()[2])
            escape += 1
        else:
            core_data = line.split()
            month = 1
            # Sanity check on data
            # (it should have 12 (months) for each line)
            if len(core_data) != 12:
                print(f"Error: {len(core_data)}")
                problematic_data.append(PrecipitationData(
                    x, y, month, year_index, core_data))
            for i in range(len(core_data)):
                parsed_data.append(
                    PrecipitationData(
                        x, y, month, year_index, int(core_data[i])
                    )
                )
                month += 1
            year_index += 1
        index += 1
        if escape > 5:
            break
    return parsed_data, problematic_data


def write_to_sql_db(data):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data (
                x INTEGER,
                y INTEGER,
                month INTEGER,
                year INTEGER,
                data INTEGER)''')
    for item in data:
        c.execute(
            "SELECT * FROM data WHERE x=? AND y=? AND month=? AND year=?",
            (item.x, item.y, item.month, item.year)
        )
        if c.fetchone() is None:
            c.execute(
                (
                    "INSERT INTO data (x, y, month, year, data) "
                    "VALUES (?, ?, ?, ?, ?)"
                ),
                (item.x, item.y, item.month, item.year, item.data)
            )
    conn.commit()
    conn.close()


def table_generation(parsed_data):
    table = prettytable.PrettyTable()
    table.field_names = field_names
    table.align = "l"
    for item in parsed_data:
        table.add_row([
            item.x,
            item.y,
            f"1/{item.month}/{item.year}",
            item.data
        ])
    return table


field_names = ["Xref", "Yref", "Date", "Value"]
new_line_reference = "Grid-ref"
