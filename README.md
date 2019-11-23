<<<<<<< HEAD
# Project 1

Web Programming with Python and JavaScript

Intro-

    This project allows for users to create an account, log in, search for books and  read reviews,
    check ratings and submit reviews andratings of their own.

    Users are promted to login at the "/login" route with <login.html> if not already logged in; and are given the option to register at the "/register" route with <register.html> if not already registered. There is a javascript function in place to prevent the form from submitting if the username is already registered. Once registered or logged in, the user is redirected to the "/search" route that renders <search.html>. User details("userid, username, hashed password) live on a tablenamed users in the database.

    Books can be searched via ISBN / Athor's name / Book title from the "/search" route page
    after being logged in. Partial entries yeild results if similar matches are found in the databse.

    The search is conducted against a books table in the database that has a preloaded selection of books. <books.csv> contains the list of books and are loaded in to the database by running <import.py>

    The results of the query are then  returned to the search page and formatted as a table. The columns in the table represent the books that returned from the search and are clickable. Clicking a given column renders <book.html> through the "/book" route.

    The <book.html> page diplays details about the book from the database and adds to it, ratings data colleced from an API call at GOODREADS.com. This page also searches the database for local reviews and ratings and displays them. The user is presented with the optionto rate and review the selected book from the page which is then inseerted in the reviews table in the database. Users are prevented from rating or reviewing a given book more than once but this function is only implemented on the server side and th user is redirected to the <error.html> page via the error function. A front end check has not yet been implemented. 

    All html pages extend the <templates.html> page and are styled by <styles.css> and bootstrap.
=======
# matthewmridha
>>>>>>> 947d1a0d795766e052d1b6783535fcd93564fa33
