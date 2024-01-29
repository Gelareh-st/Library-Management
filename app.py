from flask import Flask, render_template
from database import create_cursor
from flask import Flask, request, render_template, redirect, flash
import datetime
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)


@app.route('/')
def index():
    return render_template('index.html')
##############################################################################################################################################
# MEMBERS
##############################################################################################################################################


@app.route('/members', methods=['GET', 'POST'])
def members():
    order = 'id'
    search = ""
    if request.method == 'POST':
        order = request.form.get('orderby')
        search = request.form.get('search')
    query_string = f"""SELECT 
                   * 
                FROM 
                   members WHERE first_name LIKE '{search}%'
                OR 
                   last_name LIKE '{search}%'
                OR 
                   id LIKE '{search}'
                ORDER BY 
                   {order} """

    cursor = create_cursor()
    cursor.execute(query_string)
    rows = cursor.fetchall()

    return render_template('members.html', rows=rows, order=order, search=search)
##########################################################################################


@app.route('/profile/<int:user_id>')
def profile(user_id):
    today = datetime.date.today()
    cursor = create_cursor()
    cursor.execute("SELECT * FROM members WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.execute(
        "SELECT phone_number FROM phone_numbers WHERE member_id=?", (user_id,))
    numbers = cursor.fetchall()
    cursor.execute("""SELECT 
                    loans.id ,books.id, books.title, loans.loan_date, loans.due_date , loans.return_date
                FROM 
                    loans
                JOIN 
                    books ON loans.book_id = books.id
                WHERE 
                    loans.member_id=?;""", (user_id,))
    loans = cursor.fetchall()
    return render_template('profile.html', user=user, numbers=numbers, loans=loans, today=today)
##########################################################################################


@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    user_id = int(request.form['id'])
    cursor = create_cursor()
    cursor.execute(f"DELETE FROM members WHERE members.id={user_id}")
    cursor.commit()
    return redirect('/members')


##########################################################################################
@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    query_string = ""
    if request.method == 'POST':
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        ncode = int(request.form.get('ncode'))
        numbers = request.form.getlist('textInputs[]')
        query_string = f"""INSERT INTO members (first_name, last_name, national_code, registration_date) 
        VALUES ('{fname}', '{lname}', '{ncode}', CONVERT(date, GETDATE()))"""
        cursor = create_cursor()
        cursor.execute(query_string)
        cursor.connection.commit()

        for number in numbers:
            query_string = f"""
            INSERT INTO phone_numbers (member_id, phone_number)
            VALUES ((SELECT id FROM members WHERE national_code='{ncode}'), '{number}');"""
            cursor = create_cursor()
            cursor.execute(query_string)
            cursor.connection.commit()

        return redirect('/members')

    return render_template('add_member.html')

##########################################################################################


@app.route('/edit_member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    cursor = create_cursor()
    fname = cursor.execute(
        f"SELECT first_name FROM members WHERE members.id='{member_id}'").fetchone()[0]
    lname = cursor.execute(
        f"SELECT last_name FROM members WHERE members.id='{member_id}'").fetchone()[0]
    ncode = cursor.execute(
        f"SELECT national_code FROM members WHERE members.id='{member_id}'").fetchone()[0]
    numbers = cursor.execute(
        f"SELECT phone_number FROM phone_numbers WHERE phone_numbers.member_id='{member_id}'").fetchall()

    if request.method == 'POST':
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        ncode = int(request.form.get('ncode'))
        numbers = request.form.getlist('textInputs[]')
        query_string = f"""UPDATE members
                        SET first_name='{fname}',last_name='{lname}',national_code='{ncode}'
                        WHERE members.id={member_id} """
        cursor = create_cursor()
        cursor.execute(query_string)
        cursor.connection.commit()

        query_string = f"DELETE FROM phone_numbers WHERE phone_numbers.member_id={member_id};"
        cursor.execute(query_string)
        cursor.connection.commit()
        for number in numbers:
            if number != '0':
                query_string = f"""
                INSERT INTO phone_numbers (member_id, phone_number)
                VALUES ('{member_id}', '{number}');"""
                cursor.execute(query_string)
                cursor.connection.commit()

        return redirect(f"/profile/{member_id}")

    return render_template('edit_member.html', fname=fname, lname=lname, ncode=ncode, numbers=numbers, member_id=member_id)
##############################################################################################################################################
# BOOKS
##############################################################################################################################################


@app.route('/books', methods=['GET', 'POST'])
def books():
    order = 'id'
    search = ""
    if request.method == 'POST':
        order = request.form.get('orderby')
        search = request.form.get('search')
    query_string = f"""SELECT 
                    books.id, books.title, 
                    STRING_AGG(authors.name, ', ') AS authors, 
                    publishers.name , books.volume, books.publication_year, 
                    categories.name , 
                    CONCAT(addresses.floor_number, ',',
                      addresses.corridor_letter, ',', addresses.shelf_number) AS address, 
                    books.quantity
                FROM 
                    books
                JOIN 
                    publishers ON books.publisher_id = publishers.id
                JOIN 
                    categories ON books.category_id = categories.id
                JOIN 
                    addresses ON books.address_id = addresses.id
                JOIN 
                    book_authors ON books.id = book_authors.book_id
                JOIN 
                    authors ON book_authors.author_id = authors.id
                WHERE
                    books.title LIKE '{search}%'
                OR
                    publishers.name LIKE '{search}%'
                OR
                    books.volume LIKE '{search}%'
                OR
                    categories.name LIKE '{search}%'
                OR
                    authors.name LIKE '{search}%'                  
                GROUP BY 
                    books.id, 
                    books.title, 
                    publishers.name,
                    books.volume, 
                    books.publication_year, 
                    categories.name, 
                    CONCAT(addresses.floor_number, ',', addresses.corridor_letter, ',', addresses.shelf_number), 
                    books.quantity
                    ORDER BY {order};
                """
    cursor = create_cursor()
    cursor.execute(query_string)
    rows = cursor.fetchall()
    return render_template('books.html', rows=rows, order=order, search=search)
##########################################################################################


@app.route('/book/<int:book_id>')
def book(book_id):
    today = datetime.date.today()
    cursor = create_cursor()
    query_string = f"""SELECT 
                books.id, books.title, 
                STRING_AGG(authors.name, ', ') AS authors, 
                publishers.name , books.volume, books.publication_year, 
                categories.name , 
                CONCAT(addresses.floor_number, ',', addresses.corridor_letter,
                  ',', addresses.shelf_number) AS address, books.quantity
            FROM 
                books
            JOIN 
                publishers ON books.publisher_id = publishers.id
            JOIN 
                categories ON books.category_id = categories.id
            JOIN 
                addresses ON books.address_id = addresses.id
            JOIN 
                book_authors ON books.id = book_authors.book_id
            JOIN 
                authors ON book_authors.author_id = authors.id
            WHERE
                books.id={book_id}     
            GROUP BY 
                books.id, 
                books.title, 
                publishers.name,
                books.volume, 
                books.publication_year, 
                categories.name, 
                CONCAT(addresses.floor_number, ',', addresses.corridor_letter, ',',
                  addresses.shelf_number), books.quantity;
            """
    cursor.execute(query_string)
    book = cursor.fetchone()
    cursor.execute("""SELECT 
                    loans.id , members.id , members.first_name, members.last_name ,
                    loans.loan_date, loans.due_date , loans.return_date
                FROM 
                    loans
                JOIN 
                    members ON loans.member_id = members.id
                WHERE 
                    loans.book_id=?;""", (book_id,))
    loans = cursor.fetchall()
    return render_template('book.html', book=book, loans=loans, today=today)
##########################################################################################


@app.route('/delete_book', methods=['POST'])
def delete_book():
    book_id = int(request.form['id'])
    cursor = create_cursor()
    cursor.execute(f"DELETE FROM books WHERE books.id={book_id}")
    cursor.commit()
    return redirect('/books')
##########################################################################################


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    cursor = create_cursor()
    categories = cursor.execute(f"SELECT * FROM categories").fetchall()

    if request.method == 'POST':
        title = request.form.get('title')
        publisher = request.form.get('publisher')
        authors = request.form.getlist('textInputs[]')
        volume = int(request.form.get('volume'))
        publicationyear = int(request.form.get('year'))
        category_id = int(request.form.get('category'))
        floor = request.form.get('floor')
        corridor = request.form.get('corridor')
        shelf = request.form.get('shelf')
        quantity = request.form.get('quantity')

        ispublisher = cursor.execute(
            f"SELECT COUNT(*) FROM publishers WHERE publishers.name='{publisher}'").fetchone()
        if ispublisher[0] == 0:
            cursor.execute(
                f"INSERT INTO publishers (name) VALUES ('{publisher}')")
        publisher_id = cursor.execute(
            f"SELECT id FROM publishers WHERE publishers.name='{publisher}'").fetchone()

        address_id = cursor.execute(f"""SELECT id FROM addresses 
                                WHERE addresses.floor_number='{floor}'
                                AND addresses.corridor_letter='{corridor}'
                                AND addresses.shelf_number='{shelf}'
                                """).fetchone()

        cursor.execute(f"""INSERT INTO books (title,publisher_id,volume,publication_year,category_id,address_id,quantity)
                       VALUES ('{title}','{publisher_id[0]}','{volume}','{publicationyear}','{category_id}','{address_id[0]}','{quantity}')
                                """)
        cursor.connection.commit()

        for author in authors:
            isauthor = cursor.execute(
                f"SELECT COUNT(*) FROM authors WHERE authors.name='{author}'").fetchone()
            if isauthor[0] == 0:
                cursor.execute(
                    f"INSERT INTO authors (name) VALUES ('{author}')")
                cursor.connection.commit()
                author_id = cursor.execute(
                    f"SELECT id FROM authors WHERE authors.name='{author}'").fetchone()[0]
                book_id = cursor.execute(
                    f"SELECT id FROM books WHERE books.title='{title}'").fetchone()[0]
                cursor.execute(
                    f"INSERT INTO book_authors (book_id,author_id) VALUES ('{book_id}','{author_id}')")
                cursor.connection.commit()

        return redirect('/books')
    return render_template('add_book.html', categories=categories)
##########################################################################################


@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    cursor = create_cursor()
    quantity = cursor.execute(
        f"SELECT quantity FROM books WHERE books.id='{book_id}'").fetchone()[0]
    floor = cursor.execute(
        f"SELECT floor_number FROM addresses WHERE addresses.id=(SELECT address_id FROM books WHERE books.id='{book_id}')").fetchone()[0]
    corridor = cursor.execute(
        f"SELECT corridor_letter FROM addresses WHERE addresses.id=(SELECT address_id FROM books WHERE books.id='{book_id}')").fetchone()[0]
    shelf = cursor.execute(
        f"SELECT shelf_number FROM addresses WHERE addresses.id=(SELECT address_id FROM books WHERE books.id='{book_id}')").fetchone()[0]

    if request.method == 'POST':
        quantity = request.form.get('quantity')
        floor = request.form.get('floor')
        corridor = request.form.get('corridor')
        shelf = request.form.get('shelf')
        address_id = cursor.execute(f"""SELECT id FROM addresses 
                        WHERE addresses.floor_number='{floor}'
                        AND addresses.corridor_letter='{corridor}'
                        AND addresses.shelf_number='{shelf}'
                        """).fetchone()
        query_string = f"""UPDATE books
                        SET quantity='{quantity}',address_id='{address_id[0]}'
                        WHERE books.id={book_id} """
        cursor = create_cursor()
        cursor.execute(query_string)
        cursor.connection.commit()

        return redirect(f"/book/{book_id}")

    return render_template('edit_book.html', quantity=quantity, book_id=book_id, floor=floor, corridor=corridor, shelf=shelf)
##############################################################################################################################################
# LOANS
##############################################################################################################################################


@app.route('/loans', methods=['GET', 'POST'])
def loans():
    order = 'id'
    today = datetime.date.today()
    if request.method == 'POST':
        order = request.form.get('orderby')
    query_string = f"""SELECT 
                * 
            FROM 
                loans 
            ORDER BY 
                {order}"""
    cursor = create_cursor()
    cursor.execute(query_string)
    rows = cursor.fetchall()
    return render_template('loans.html', rows=rows, order=order, today=today)
##########################################################################################


@app.route('/new_loan', methods=['GET', 'POST'])
def new_loan():
    cursor = create_cursor()
    books = cursor.execute(
        f"SELECT title,id FROM books WHERE books.quantity>0").fetchall()
    members = cursor.execute(
        f"SELECT first_name,last_name,id FROM members").fetchall()

    if request.method == 'POST':
        member_id = request.form.get('member_name')
        book_id = request.form.get('book_name')
        due_date = request.form.get('due_date')
        cursor.execute(f"""INSERT INTO loans (book_id,member_id,loan_date,due_date)
               VALUES ('{book_id}','{member_id}',CONVERT(date, GETDATE()), CAST ('{due_date}' AS DATE))""")
        cursor.connection.commit()
        cursor.execute(
            f"UPDATE books SET quantity = quantity - 1 WHERE id = {book_id};")
        cursor.connection.commit()
        return redirect('/loans')

    return render_template('new_loan.html', books=books, members=members)

##########################################################################################


@app.route('/return_loan', methods=['POST'])
def return_loan():
    if request.method == 'POST':
        loan_id, book_id, member_id = map(
            int, request.form['loan_id'].split(','))
        cursor = create_cursor()
        cursor.execute(
            f"UPDATE loans SET return_date = CONVERT(date, GETDATE()) WHERE id={loan_id}")
        cursor.connection.commit()
        cursor.execute(
            f"UPDATE books SET quantity = quantity + 1 WHERE id = {book_id};")
        cursor.connection.commit()

    return redirect(f'/profile/{member_id}')

##########################################################################################


if __name__ == '__main__':
    app.run(debug=True)
