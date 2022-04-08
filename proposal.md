### Capstone 1 - Project Proposal - Booklovers App
  

#### 1. What goal will your website be designed to achieve?
The goal will be to offer booklovers a website where they can search best selling books, read reviews, rate books and create their own personalized list of books to read and track.

#### 2. What kind of users will visit your site? In other words, what is the demographic of your users?  
Anyone who likes to read or is connected to the world of books, including authors, publishers and reviewers, will find this site useful.

#### 3. What data do you plan on using? You may have not picked your actual API yet, which is fine, just outline what kind of data you would like it to contain.
The app will use the The New York Times Books API to access data.
Data to be used will be:
* Lists of bestsellers - hardcover-fiction, hardcover-nonfiction, paperback-fiction/nonfiction etc.
* Date of publication of lists
* Books on the bestsellers list for the specified date and list name
* Details of specific book - Author, ISBN, title
Reviews of book - upto 5


#### 4. In brief, outline your approach to creating your project (knowing that you may not know everything in advance and that these details might change later). Answer questions like the ones below, but feel free to add more information:

  a. What does your database schema look like?
  
The database will have:
* Users - username, password and email address. 
* Books - Author, title, ISBN, reviews
* List of users' favorite books, books to read/books checked off


b. What kinds of issues might you run into with your API?   
* There may be issues with the API going offline or validation errors.

c. Is there any sensitive information you need to secure?  
* Password will need to be secure so the app will use Flask-BCrypt to store it as a hashed password.

d. What functionality will your app include?   
User will be able to:
* search bestselling lists by type/latest or specific date, 
read reviews filtered by author, ISBN or title
* register for an account and login/logout to be able to:
  * rate books 
  * mark books as favorite
  * create own list of books to read and check off
  * delete items on list


e. What will the user flow look like?
* When a user goes to the website URL, the home page will be displayed.
* The home page will have links to the signup page and login page. 
* The home page will also have a form for any user (registered or not) to search for the bestsellers lists by type/date, specific book or author and will display the results on a show page. 
* If the user is registered and logged in, the show page will allow the user to rate and/or favorite a book and add it to their list. 
* If user is logged in, the home page will also show links to their profile page where they can create lists and/or edit their lists
* When the user signs up/logs in, they will be taken to the user profile page where they can view their own list of books/ratings with a link to book details


f. What features make your site more than CRUD? Do you have any stretch goals?
* The site will use an API to fetch data and then use it as per the functionalities mentioned above to make the site go beyond CRUD implementation. 
* My stretch goals will be able to implement a system to recommend books based on books by the same author and let users search other users in the database who like the same books.