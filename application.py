import os
import requests

from flask import Flask, session, render_template, request, url_for, redirect, jsonify, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug import generate_password_hash, check_password_hash

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def error(message):
    return render_template("error.html", message=message)

# INDEX
@app.route("/")
def index():
    if session.get("user_id") == None:
        return redirect(url_for("login"))
    return redirect(url_for("search"))

# API REQUEST


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():

    # clear existing session if any
    session.clear()

    if request.method == "POST":
        # check inputs 
        if not str(request.form.get("username")):
            return error("Username required")
        if not str(request.form.get("password")):
            return error("password required")

        # if inputs fields are filled, check database
        username = str(request.form.get("username"))
        user = db.execute("SELECT * FROM users WHERE username = :username",
                            {"username" : username}).fetchone()

        # if username and passwords match, login
        if  not user == None and check_password_hash(user["hash"], request.form.get("password")):
            session["user_id"] = user.userid
            return redirect(url_for("search"))
        else:
            return error("incorrect username or password")
    return render_template("login.html")

#LOGOUT
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# REGISTER
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check inputs, make sure input fields are filled and passwords match
        if not str(request.form.get("set_username")):
            return error("username is required")
        if not str(request.form.get("set_password")):
            return error("pasword is required")
        if not str(request.form.get("confirm_password")):
            return error("confirm password field is mandatory")
        if not (request.form.get("set_password")) == (request.form.get("confirm_password")):
            return error("passwords do not match")

        # if inputs are okay, move on with registration
        username = str(request.form.get("set_username"))

        # if username in database, reject
        if db.execute("SELECT * FROM users WHERE username = :username ",
                      {"username" : username}).rowcount > 0:
            return error("Username in use")

        # if username available :     
        # hash new password
        hash = generate_password_hash(str(request.form.get("set_password")))
        
        # insert into database
        new_user = db.execute("INSERT INTO users(username, hash) values(:username, :hash)",
                    {"username" : username,
                    "hash" : hash})
        db.commit()

        # if fails to enter in to database
        if not new_user:
            error("unsuccessfull: something went wrong during registration")

        # if registration is successfull, log user in
        currentUser = db.execute("SELECT userid FROM users WHERE username = :username",
                                {"username" : username}).fetchone()
        session["user_id"] = currentUser
        flash("Registration successfull")
        return redirect(url_for("search"))
    return render_template("register.html")

# BOOK
# gets data regarding selected book from googreads and renders book page
@app.route("/book", methods=["GET", "POST"])
def book():

    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))

    # isbn from the clicked book row
    if request.method == "POST":
        isbn = str(request.form.get("selectedBook"))
        if isbn == None:
            return error("Error passing data")

        # get book info from database
        books = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                    {"isbn" : isbn}).fetchone()

        if books == None:
            return error("Book not in database")

        # get book reviews and ratings from database
        if db.execute("SELECT review FROM reviews WHERE isbn = :isbn", {"isbn" : isbn}).rowcount == 0:
            reviews = ""
        else:
            reviews = db.execute("SELECT review FROM reviews WHERE isbn = :isbn", 
                                {"isbn" : isbn}).fetchall()
        if db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {"isbn" : isbn}).rowcount == 0:
            rating = "Not Rated"
        else:
            rating = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", 
                                {"isbn" : isbn}).fetchone()
            rating = "{:.1f}".format(rating[0])
        
        #assign book details to variables
        author = books.author or "unknown"
        title = books.title or "unknown"
        year = books.year or "unknown"

        # get data from goodreads
        KEY = "DBTorgTVjzeRbhOLGNtzQ"
        URL = "https://www.goodreads.com/book/review_counts.json"

        # send request
        try:
            res = requests.get(URL, params={"key": KEY, "isbns": isbn})
        except:
            return error("API error")
        data = (res.json())

        #assign imported data to variables
        average_rating =  data["books"][0]["average_rating"] or "No rating data"
        ratings_count = data["books"][0]["work_ratings_count"] or "No rating data"

        return render_template("book.html", average_rating=average_rating, ratings_count=ratings_count, author=author, title=title, year=year, isbn=isbn, reviews=reviews, rating=rating)
    return redirect(url_for("search"))

# CHECK
# checks if username is available for front-end authentication
@app.route("/check", methods=["GET", "POST"])
def check():
    username = request.args.get("username", "")
    
    # go through usernames in database and check against input username
    # return true if username does not exist in database
    names = db.execute("SELECT username FROM users").fetchall()
    for name in names:
        if name["username"] == username:
            return jsonify(False)
    return jsonify(True)


# SEARCH
@app.route("/search")
def search():

    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))
    return render_template("search.html")

# search book by isbn from database 
@app.route("/search_isbn", methods=["GET", "POST"])
def search_isbn():

    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form.get("isbn"):
            isbn = str(request.form.get("isbn"))
            books = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn",
                                {"isbn" : "%" + isbn + "%"}).fetchall()
            if books == None:
                return error("Book not in database")
            return render_template("/search.html", books=books, show_results=1)

# search book by author from database
@app.route("/search_author", methods=["GET", "POST"])
def search_author():

    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form.get("author"):
            author = str(request.form.get("author"))
            books = db.execute("SELECT * FROM books WHERE author LIKE :author",
                               {"author" : "%" + author + "%"}).fetchall()
            if books == None:
                return error("Book not in database")
            return render_template("/search.html", books=books, show_results=1)

#search book by title from database
@app.route("/search_title", methods=["GET", "POST"])
def search_title():

    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))
    if request.method == "POST":
        if request.form.get("title"):
            title = str(request.form.get("title"))
            books = db.execute("SELECT * FROM books WHERE title LIKE :title",
                               {"title" : "%" + title + "%"}).fetchall()
            if books == None:
                return error("Book not in database")
            return render_template("/search.html", books=books, show_results=1)

# RATE
# user ratings and reviews
@app.route("/rate", methods=["GET", "POST"])
def rate():
    
    # login required
    if session.get("user_id") == None:
        return redirect(url_for("login"))

    # get ratings, review, user and put into variables
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        review = str(request.form.get("review")) or None
        userid = int(session.get("user_id")[0])
        isbn = str(request.form.get("isbn"))
        
        
    #check if user has rated book before
    
        if db.execute("SELECT * FROM reviews WHERE isbn = :isbn AND userid = :userid", {"isbn" : isbn, "userid" : userid}).rowcount == 0:
        #insert into database
            if not review == None:
                newRating = db.execute("INSERT INTO reviews (rating, review, userid, isbn) VALUES (:rating, :review, :userid, :isbn)",
                                        {"rating" : rating, "review" : review, "userid" : userid, "isbn" : isbn})
                db.commit()
            else:
                newRating = db.execute("INSERT INTO reviews (rating, userid, isbn) VALUES (:rating, :userid, :isbn)",
                                        {"rating" : rating, "userid" : userid, "isbn" : isbn})
                db.commit()
        
                if not newRating:
                    return error("database error")
    
                flash("Thank you for your opinion")
                return redirect(url_for("book"))
    
        # prevent  double
        else:    
            return error("you have already rated this book")

@app.route("/api/<string:isbn>")
def isbn_api(isbn):
    isbn = str(isbn)
    print(isbn)
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
            {"isbn" : isbn}).fetchone()
    if book is None:
        return jsonify({
            "ERROR" : "BOOK NOT IN DATABASE"
        })
    title = book.title
    author = book.author
    year = book.year
    isbn = isbn
    
    if db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {"isbn" : isbn}).rowcount == 0:
            rating = "Not Rated"
    else:
        rating = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", 
                            {"isbn" : isbn}).fetchone()
        rating = "{:.1f}".format(rating[0])

    reviewCount = db.execute("SELECT * FROM reviews WHERE isbn = :isbn",
                    {"isbn" : isbn}).rowcount
                    
    return jsonify({"isbn" : isbn,
                    "title" : title,
                    "author" : author,
                    "year" : year,
                    "isbn" : isbn,
                    "review_count" : reviewCount,
                    "rating" : rating
                    })

    
        
    
    
    


    






