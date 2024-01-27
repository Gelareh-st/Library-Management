from flask import Flask, render_template
from database import create_cursor
from flask import Flask, request, render_template , redirect ,flash
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

@app.route('/')
def index():
    return render_template('index.html')
##############################################################################################################################################
###################################################################################################################################### MEMBERS
##############################################################################################################################################
@app.route('/members', methods=['GET', 'POST'])
def members():
    order='id';
    search="";
    if request.method == 'POST':
        order = request.form.get('orderby') 
        search = request.form.get('search')
    query_string=f"""SELECT 
                   * 
                FROM 
                   members WHERE first_name LIKE '{search}%'
                OR 
                   last_name LIKE '{search}%'
                OR 
                   id LIKE '{search}'
                ORDER BY 
                   {order} """;
    
    cursor=create_cursor();
    cursor.execute(query_string)
    rows = cursor.fetchall()
    # headers = [column[0] for column in cursor.headers]
    
    return render_template('members.html', rows=rows , order=order, search=search)
##########################################################################################
@app.route('/profile/<int:user_id>')
def profile(user_id):
    cursor=create_cursor()
    cursor.execute("SELECT * FROM members WHERE id=?", (user_id,))
    user = cursor.fetchone()
    cursor.execute("SELECT phone_number FROM phone_numbers WHERE member_id=?", (user_id,))
    numbers = cursor.fetchall()
    cursor.execute("""SELECT 
                    loans.id ,books.id, books.title, loans.loan_date, loans.due_date , loans.return_date
                FROM 
                    loans
                JOIN 
                    books ON loans.book_id = books.id
                WHERE 
                    loans.member_id=?;""", (user_id,) )
    loans = cursor.fetchall()
    return render_template('profile.html', user=user, numbers=numbers, loans=loans)
##########################################################################################
@app.route('/delete_profile', methods=['POST'])
def delete_profile():
    user_id = int(request.form['id'])
    cursor = create_cursor()
    cursor.execute(f"DELETE FROM members WHERE members.id={user_id}")
    cursor.commit()
    return redirect('/members')
##############################################################################################################################################
######################################################################################################################################## BOOKS
##############################################################################################################################################
@app.route('/books', methods=['GET', 'POST'])
def books():
    order='id';
    search="";
    if request.method == 'POST':
        order = request.form.get('orderby') 
        search = request.form.get('search')
    query_string=f"""SELECT 
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
                """;
    cursor=create_cursor();
    cursor.execute(query_string)
    rows = cursor.fetchall()
    return render_template('books.html', rows=rows , order=order, search=search)
##########################################################################################
@app.route('/book/<int:book_id>', methods=['GET', 'POST'])
def book(book_id):
    result=""
    if request.method == 'POST':
        result = request.form.get('delete')    
    cursor=create_cursor()
    query_string=f"""SELECT 
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
            """;
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
                    loans.book_id=?;""", (book_id,) )
    loans = cursor.fetchall()
    return render_template('book.html', book=book , loans=loans )
##########################################################################################
@app.route('/delete_book', methods=['POST'])
def delete_book():
    book_id = int(request.form['id'])
    cursor = create_cursor()
    cursor.execute(f"DELETE FROM books WHERE books.id={book_id}")
    cursor.commit()
    return redirect('/books')
##########################################################################################
@app.route('/add_book',methods=['GET', 'POST'] )
def add_book():
    cursor = create_cursor()
    categories=cursor.execute(f"SELECT * FROM categories").fetchall()

    if request.method == 'POST':
        title=request.form.get('title')
        publisher=request.form.get('publisher')
        authors= request.form.getlist('textInputs[]')
        volume=int(request.form.get('volume'))
        publicationyear=int(request.form.get('year'))
        category_id=int(request.form.get('category'))
        floor=request.form.get('floor')
        corridor=request.form.get('corridor')
        shelf=request.form.get('shelf')
        quantity=request.form.get('quantity')
        print("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",authors)

        ispublisher=cursor.execute(f"SELECT COUNT(*) FROM publishers WHERE publishers.name='{publisher}'").fetchone()
        if ispublisher[0]==0:
            cursor.execute(f"INSERT INTO publishers (name) VALUES ('{publisher}')")
        publisher_id= cursor.execute(f"SELECT id FROM publishers WHERE publishers.name='{publisher}'").fetchone()

        address_id=cursor.execute(f"""SELECT id FROM addresses 
                                WHERE addresses.floor_number='{floor}'
                                AND addresses.corridor_letter='{corridor}'
                                AND addresses.shelf_number='{shelf}'
                                """).fetchone()
        
        cursor.execute(f"""INSERT INTO books (title,publisher_id,volume,publication_year,category_id,address_id,quantity)
                       VALUES ('{title}','{publisher_id[0]}','{volume}','{publicationyear}','{category_id}','{address_id[0]}','{quantity}')
                                """);
        cursor.connection.commit()
                
        for author in authors:
            print(author)
            isauthor = cursor.execute(f"SELECT COUNT(*) FROM authors WHERE authors.name='{author}'").fetchone()
            if isauthor[0] == 0:
                print("nabudddddddddddddddddddd")
                cursor.execute(f"INSERT INTO authors (name) VALUES ('{author}')")
                cursor.connection.commit()
                author_id = cursor.execute(f"SELECT id FROM authors WHERE authors.name='{author}'").fetchone()[0]
                book_id = cursor.execute(f"SELECT id FROM books WHERE books.title='{title}'").fetchone()[0]
                cursor.execute(f"INSERT INTO book_authors (book_id,author_id) VALUES ('{book_id}','{author_id}')")
                cursor.connection.commit()

        return redirect('/books') 
    return render_template('add_book.html' , categories=categories)
##############################################################################################################################################
######################################################################################################################################## LOANS
##############################################################################################################################################
@app.route('/loans', methods=['GET', 'POST'])
def loans():
    order='id';
    if request.method == 'POST':
        order = request.form.get('orderby') 
    query_string=f"""SELECT 
                * 
            FROM 
                loans 
            ORDER BY 
                {order}""";
    cursor=create_cursor();
    cursor.execute(query_string)
    rows = cursor.fetchall()
    return render_template('loans.html', rows=rows , order=order)
##########################################################################################
@app.route('/add_member',methods=['GET', 'POST'] )
def add_member():
    query_string=""
    if request.method == 'POST':
        fname = request.form.get('fname') 
        lname = request.form.get('lname') 
        ncode = int(request.form.get('ncode'))
        number = int(request.form.get('number'))
        number2 = request.form.get('number2')
        query_string=f"""INSERT INTO members (first_name, last_name, national_code, registration_date) 
        VALUES ('{fname}', '{lname}', '{ncode}', CONVERT(date, GETDATE()))""";
        cursor=create_cursor()
        cursor.execute(query_string)
        cursor.connection.commit()
        # flash('Book deleted successfully')
        query_string=f"""
                    INSERT INTO phone_numbers (member_id, phone_number)
                    VALUES ((SELECT id FROM members WHERE national_code='{ncode}'), '{number}');
                """
        cursor=create_cursor()
        cursor.execute(query_string)
        cursor.connection.commit()
        if number2:
            query_string=f"""
                    INSERT INTO phone_numbers (member_id, phone_number)
                    VALUES ((SELECT id FROM members WHERE national_code='{ncode}'), '{number2}');
                """
            cursor=create_cursor()
            cursor.execute(query_string)
            cursor.connection.commit()

        
        return redirect('/members') 
        
    return render_template('add_member.html')
##########################################################################################
@app.route('/new_loan',methods=['GET', 'POST'])
def new_loan():
    cursor=create_cursor()
    books=cursor.execute(f"SELECT title,id FROM books").fetchall()
    members=cursor.execute(f"SELECT first_name,last_name,id FROM members").fetchall()

    if request.method == 'POST':
        member_id=request.form.get('member_name') 
        book_id=request.form.get('book_name')
        due_date= request.form.get('due_date')
        cursor.execute(f"""INSERT INTO loans (book_id,member_id,loan_date,due_date)
               VALUES ('{book_id}','{member_id}',CONVERT(date, GETDATE()), CAST ('{due_date}' AS DATE))""")

        cursor.connection.commit()
        return redirect('/loans') 

    return render_template('new_loan.html' , books=books , members=members)

##########################################################################################
##########################################################################################
##########################################################################################
##########################################################################################




if __name__ == '__main__':
    app.run(debug=True)
