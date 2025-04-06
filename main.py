import data_parser_functions as dpf

new_line_reference = "Grid-ref"
target = ""
sort_by = ""

lines = []
# Command line arguments
target, sort_by = dpf.user_input()

# Try open file
data = dpf.open_file(target)

# Open raw file
# Parse the header
metadata, header_length = dpf.parse_file_header(data)

parsed_data, problematic_data = dpf.parse_data(
    data, dpf.get_start_year(metadata["Years"]), header_length)

if problematic_data:
    print("Found problems with some data")
    for item in problematic_data:
        print(
            f"X: {item.x}, Y: {item.y}, Year: {item.year}, "
            f"Data: {item.data}"
        )


# Dump the data to sqllite db
dpf.write_to_sql_db(parsed_data)

table = dpf.table_generation(parsed_data)

print("Data has been parsed with {} rows".format(len(parsed_data)))
print("Header Data")
print(metadata)
if sort_by == "":
    sort_by = input(
        "Sort by (Xref, Yref, Date, Value, none): ")

sort_by = sort_by.lower()
if sort_by == "none" or sort_by == "":
    print(table)
else:
    # Sorting is pretty basic using package sorters,
    # could be improved with additional code
    if sort_by in ["xref", "yref", "date", "value"]:
        print(table.get_string(sortby=sort_by.capitalize()))
    else:
        print(f"Invalid sort option. '{sort_by}'")
