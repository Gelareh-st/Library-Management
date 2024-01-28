# import pyodbc

# connection_string = ("Driver={ODBC Driver 17 for SQL Server};"
#                     "Server=DESKTOP-H42O97C;"
#                     "Database=mydata;"
#                     "Trusted_Connection=yes;")

# connection = pyodbc.connect(connection_string)

# # Create a cursor
# cursor = connection.cursor()

# # Execute SQL queries
# cursor.execute("SELECT * FROM mytable1")
# rows = cursor.fetchall()
# m=0
# # Print the results
# for row in rows:
#     print(row)

# # Close the cursor and connection
# cursor.close()
# connection.close()


for i in range(1,4):
    for j in range(1,11):
        print(f"INSERT INTO addresses (floor_number, corridor_letter, shelf_number) VALUES ({i}, 'D', {j});")