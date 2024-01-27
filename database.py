import pyodbc

def connect_to_database():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=DESKTOP-H42O97C;"
        "Database=library_database;"
        "Trusted_Connection=yes;"
    )
    connection = pyodbc.connect(connection_string)
    return connection

def create_cursor():
    connection = connect_to_database()
    cursor = connection.cursor()
    return cursor
