import requests

from secrets import API_SECRET_KEY


API_BASE_URL = 'https://api.nytimes.com/svc/books/v3/'

key = API_SECRET_KEY


def get_all_categories():
    """Return all categories from API"""

    res = requests.get(f"{API_BASE_URL}lists/names.json?api-key={key}")

    data = res.json()
    results = data["results"]
    
    categories = [result['list_name_encoded'] for result in results]
    categories = list(dict.fromkeys(categories))
    return categories


def get_book_by_author(author):
    """Return all titles by author from API"""

    res = requests.get(f"{API_BASE_URL}reviews.json?api-key={key}",
                params={'author': author})

    data = res.json()
    results = data["results"]

    return results


def get_books_by_category(category):
    """Return all bestselling titles for specific category from API"""

    res = requests.get(f"{API_BASE_URL}lists/current/{category}.json?api-key={key}")

    data = res.json()
    results = data["results"]
    books = results["books"]

    book_results = []
    for book in books:
        book = {
            "book_title": book['title'],
            "book_author": book['author'],
            "book_image" : book['book_image']
        }
        book_results.append(book)
    return book_results


def get_book_by_title_author(title, author):
    """Return book with specific title and author from API"""

    res = requests.get(f"{API_BASE_URL}lists/best-sellers/history.json?api-key={key}",
                params={'title': title, 'author': author})

    data = res.json()
    results = data["results"]

    return results




