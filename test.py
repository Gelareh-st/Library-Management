import pyodbc

connection_string = ("Driver={ODBC Driver 17 for SQL Server};"
                    "Server=DESKTOP-H42O97C;"
                    "Database=mydata;"
                    "Trusted_Connection=yes;")

connection = pyodbc.connect(connection_string)

# Create a cursor
cursor = connection.cursor()

# Execute SQL queries
cursor.execute("SELECT * FROM mytable1")
rows = cursor.fetchall()
m=0
# Print the results
for row in rows:
    print(row)

# Close the cursor and connection
cursor.close()
connection.close()


