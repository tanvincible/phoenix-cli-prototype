import requests
import pyfiglet


def fetch_harry_potter_data():
    """
    Fetches Harry Potter book data and prints a celebratory message
    if the first book's title is "Harry Potter and the Sorcerer's Stone".
    Otherwise, prints the first book's title and author.
    """
    try:
        response = requests.get("https://www.anapioficeandfire.com/api/books")
        response.raise_for_status()  # Raise HTTPError for bad responses
        books = response.json()

        if books:
            first_book = books[0]
            title = first_book.get("name", "Unknown Title")
            authors = first_book.get("authors", ["Unknown Author"])
            author = ", ".join(authors)

            if title == "Harry Potter and the Sorcerer's Stone":
                ascii_art = pyfiglet.figlet_format("Hooray Harry Potter!")
                print(ascii_art)
            else:
                print(f"Title: {title}")
                print(f"Author: {author}")
        else:
            print("No books found in the API response.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    fetch_harry_potter_data()
