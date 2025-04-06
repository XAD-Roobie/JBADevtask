import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from data_parser_functions import write_to_sql_db, PrecipitationData
from data_parser_functions import (
    user_input,
    open_file,
    get_start_year,
    parse_file_header,
    parse_data,
    table_generation,
)


class TestUserInput(unittest.TestCase):
    @patch('builtins.input', return_value="test_file.txt")
    @patch('sys.argv', new=["script_name"])
    def test_user_input_with_no_arguments(self, mock_input):
        target, sort_by = user_input()
        self.assertEqual(target, "test_file.txt")
        self.assertEqual(sort_by, "")

    @patch('sys.argv', new=["script_name", "test_file.txt"])
    def test_user_input_with_file_argument(self):
        target, sort_by = user_input()
        self.assertEqual(target, "test_file.txt")
        self.assertEqual(sort_by, "")

    @patch('sys.argv', new=["script_name", "test_file.txt", "none"])
    def test_user_input_with_sort_by_none(self):
        target, sort_by = user_input()
        self.assertEqual(target, "test_file.txt")
        self.assertEqual(sort_by, "none")

    @patch('sys.argv', new=["script_name", "test_file.txt", "none"])
    def test_user_input_with_file_and_sort_by(self):
        target, sort_by = user_input()
        self.assertEqual(target, "test_file.txt")
        self.assertEqual(sort_by, "none")

    @patch('sys.argv', new=["script_name", "test_file.txt", "invalid_sort"])
    def test_user_input_with_invalid_sort_by(self):
        target, sort_by = user_input()
        self.assertEqual(target, "invalid_sort")
        self.assertEqual(sort_by, "")


class TestOpenFile(unittest.TestCase):
    @patch(
        'builtins.open',
        new_callable=unittest.mock.mock_open,
        read_data="line1\nline2\nline3\n"
    )
    def test_open_file_success(self, mock_open):
        lines = open_file("test_file.txt")
        self.assertEqual(lines, ["line1\n", "line2\n", "line3\n"])
        mock_open.assert_called_once_with("test_file.txt", "r")

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_open_file_not_found(self, mock_open):
        with self.assertRaises(SystemExit):
            open_file("non_existent_file.txt")


class TestGetStartYear(unittest.TestCase):
    def test_get_start_year_valid_range(self):
        self.assertEqual(get_start_year("Years=1991-2000"), 1991)

    def test_get_start_year_no_range(self):
        self.assertIsNone(get_start_year("Years="))

    def test_get_start_year_invalid_format(self):
        self.assertIsNone(get_start_year("Years=1991/2000"))

    def test_get_start_year_partial_range(self):
        self.assertIsNone(get_start_year("Years=1991-"))

    def test_get_start_year_non_numeric(self):
        self.assertIsNone(get_start_year("Years=abcd-efgh"))

    def test_get_start_year_extra_text(self):
        self.assertEqual(
            get_start_year("Some text Years=1985-1995 more text"), 1985
        )


class TestParseFileHeader(unittest.TestCase):
    def test_parse_file_header_with_valid_metadata(self):
        lines = [
            ("[Long=-180.00, 180.00] [Lati= -90.00,  90.00] "
             "[Grid X,Y= 720, 360]"),
            "[Boxes=   67420] [Years=1991-2000] "
            "[Multi=    0.1000] [Missing=-999]",
            "Some other line"
        ]
        expected_metadata = {
            "Long": "-180.00, 180.00",
            "Lati": "-90.00,  90.00",
            "Grid X,Y": "720, 360",
            "Boxes": "67420",
            "Years": "1991-2000",
            "Multi": "0.1000",
            "Missing": "-999"
        }
        metadata, count = parse_file_header(lines)
        self.assertEqual(metadata, expected_metadata)
        self.assertEqual(count, 2)

    def test_parse_file_header_with_no_metadata(self):
        lines = [
            "Some random line",
            "Another random line"
        ]
        metadata, count = parse_file_header(lines)
        self.assertEqual(metadata, {})
        self.assertEqual(count, 2)

    def test_parse_file_header_with_partial_metadata(self):
        lines = [
            "[Long=-180.00, 180.00] [Lati= -90.00,  90.00]",
            "Some other line"
        ]
        expected_metadata = {
            "Long": "-180.00, 180.00",
            "Lati": "-90.00,  90.00"
        }
        metadata, count = parse_file_header(lines)
        self.assertEqual(metadata, expected_metadata)
        self.assertEqual(count, 1)

    def test_parse_file_header_with_empty_lines(self):
        lines = []
        metadata, count = parse_file_header(lines)
        self.assertEqual(metadata, {})
        self.assertEqual(count, 0)


class TestParseData(unittest.TestCase):
    def test_parse_data_with_valid_data(self):
        lines = [
            "Header line 1",
            "Header line 2",
            "Grid-ref 1, 2",
            "10 20 30 40 50 60 70 80 90 100 110 120",
            "Grid-ref 3, 4",
            "15 25 35 45 55 65 75 85 95 105 115 125"
        ]
        start_year = 2000
        header_length = 2
        parsed_data, problematic_data = parse_data(
            lines, start_year, header_length
        )

        self.assertEqual(len(parsed_data), 24)
        self.assertEqual(len(problematic_data), 0)

        self.assertEqual(parsed_data[0].x, 1)
        self.assertEqual(parsed_data[0].y, 2)
        self.assertEqual(parsed_data[0].month, 1)
        self.assertEqual(parsed_data[0].year, 2000)
        self.assertEqual(parsed_data[0].data, 10)

        self.assertEqual(parsed_data[12].x, 3)
        self.assertEqual(parsed_data[12].y, 4)
        self.assertEqual(parsed_data[12].month, 1)
        self.assertEqual(parsed_data[12].year, 2000)
        self.assertEqual(parsed_data[12].data, 15)

    def test_parse_data_with_problematic_data(self):
        lines = [
            "Header line 1",
            "Header line 2",
            "Grid-ref 1, 2",
            "10 20 30 40 50 60 70 80 90 100 110",
            "Grid-ref 3, 4",
            "15 25 35 45 55 65 75 85 95 105 115 125"
        ]
        start_year = 2000
        header_length = 2
        parsed_data, problematic_data = parse_data(
            lines, start_year, header_length
        )

        self.assertEqual(len(parsed_data), 23)
        self.assertEqual(len(problematic_data), 1)

        self.assertEqual(problematic_data[0].x, 1)
        self.assertEqual(problematic_data[0].y, 2)
        self.assertEqual(problematic_data[0].year, 2000)
        self.assertEqual(
            problematic_data[0].data,
            [
                "10", "20", "30", "40", "50", "60",
                "70", "80", "90", "100", "110"
            ]
        )

    def test_parse_data_with_empty_lines(self):
        lines = [
            "Header line 1",
            "Header line 2"
        ]
        start_year = 2000
        header_length = 2
        parsed_data, problematic_data = parse_data(
            lines, start_year, header_length
        )

        self.assertEqual(len(parsed_data), 0)
        self.assertEqual(len(problematic_data), 0)

    def test_parse_data_with_escape_limit(self):
        lines = [
            "Header line 1",
            "Header line 2",
            "Grid-ref 1, 2",
            "10 20 30 40 50 60 70 80 90 100 110 120",
            "Grid-ref 3, 4",
            "15 25 35 45 55 65 75 85 95 105 115 125",
            "Grid-ref 5, 6",
            "20 30 40 50 60 70 80 90 100 110 120 130",
            "Grid-ref 7, 8",
            "25 35 45 55 65 75 85 95 105 115 125 135",
            "Grid-ref 9, 10",
            "30 40 50 60 70 80 90 100 110 120 130 140",
            "Grid-ref 11, 12",
            "35 45 55 65 75 85 95 105 115 125 135 145"
        ]
        start_year = 2000
        header_length = 2
        parsed_data, problematic_data = parse_data(
            lines, start_year, header_length
        )

        self.assertEqual(len(parsed_data), 60)
        self.assertEqual(len(problematic_data), 0)

    def test_parse_data_with_invalid_grid_reference(self):
        lines = [
            "Header line 1",
            "Header line 2",
            "Invalid Grid-ref",
            "10 20 30 40 50 60 70 80 90 100 110 120"
        ]
        start_year = 2000
        header_length = 2
        with self.assertRaises(ValueError):
            parse_data(lines, start_year, header_length)


class TestWriteToSqlDb(TestCase):
    @patch('sqlite3.connect')
    def test_write_to_sql_db_inserts_data(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        data = [
            PrecipitationData(1, 2, 1, 2000, 100),
            PrecipitationData(1, 2, 2, 2000, 200),
        ]

        write_to_sql_db(data)

        mock_cursor.execute.assert_any_call(
            '''CREATE TABLE IF NOT EXISTS data (
                x INTEGER,
                y INTEGER,
                month INTEGER,
                year INTEGER,
                data INTEGER)'''
        )

        self.assertEqual(mock_cursor.execute.call_count, 3)
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM data WHERE x=? AND y=? AND month=? AND year=?",
            (1, 2, 1, 2000)
        )

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('sqlite3.connect')
    def test_write_to_sql_db_skips_existing_data(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.side_effect = [True, None]

        data = [
            PrecipitationData(1, 2, 1, 2000, 100),
            PrecipitationData(1, 2, 2, 2000, 200),
        ]

        write_to_sql_db(data)

        self.assertEqual(mock_cursor.execute.call_count, 4)
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM data WHERE x=? AND y=? AND month=? AND year=?",
            (1, 2, 1, 2000)
        )
        mock_cursor.execute.assert_any_call(
            "SELECT * FROM data WHERE x=? AND y=? AND month=? AND year=?",
            (1, 2, 2, 2000)
        )
        mock_cursor.execute.assert_any_call(
            (
                "INSERT INTO data (x, y, month, year, data) "
                "VALUES (?, ?, ?, ?, ?)"
            ),
            (1, 2, 2, 2000, 200)
        )

        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()


class TestTableGeneration(unittest.TestCase):
    def test_table_generation_with_valid_data(self):
        parsed_data = [
            PrecipitationData(1, 2, 1, 2000, 100),
            PrecipitationData(3, 4, 2, 2001, 200),
        ]
        table = table_generation(parsed_data)

        self.assertEqual(table.field_names, ["Xref", "Yref", "Date", "Value"])

        rows = table._rows
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], [1, 2, "1/1/2000", 100])
        self.assertEqual(rows[1], [3, 4, "1/2/2001", 200])

    def test_table_generation_with_empty_data(self):
        parsed_data = []
        table = table_generation(parsed_data)

        self.assertEqual(table.field_names, ["Xref", "Yref", "Date", "Value"])

        rows = table._rows
        self.assertEqual(len(rows), 0)


if __name__ == "__main__":
    unittest.main()
