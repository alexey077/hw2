from __future__ import annotations
from typing import List, Optional


class Book:
    def __init__(self, title: str, author: str, year: int, is_available: bool = True) -> None:
        self.title = title
        self.author = author
        self.year = year
        self.is_available = is_available  # книга свободна или уже на руках

    def get_info(self) -> str:
        status = "доступна" if self.is_available else "на руках"
        return f"«{self.title}» — {self.author}, {self.year} год ({status})"

    def borrow(self) -> bool:
        """Пытаемся взять книгу. Вернёт True, если получилось."""
        if not self.is_available:
            return False
        self.is_available = False
        return True

    def return_book(self) -> None:
        """Вернуть книгу обратно в библиотеку."""
        self.is_available = True

    def __repr__(self) -> str:
        return f"Book({self.title!r}, {self.author!r}, {self.year}, available={self.is_available})"


class TextBook(Book):
    def __init__(self, title: str, author: str, year: int, subject: str, is_available: bool = True) -> None:
        super().__init__(title, author, year, is_available)
        self.subject = subject  # предмет, по которому учебник

    def get_info(self) -> str:
        status = "доступен" if self.is_available else "на руках"
        return f"«{self.title}» — {self.author}, {self.year} год, предмет: {self.subject} ({status})"

    def __repr__(self) -> str:
        return (
            f"TextBook({self.title!r}, {self.author!r}, {self.year}, "
            f"subject={self.subject!r}, available={self.is_available})"
        )


class Library:
    def __init__(self) -> None:
        self.books: List[Book] = []  # тут лежат все книги

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def find_books_by_author(self, author: str) -> List[Book]:
        return [book for book in self.books if book.author == author]

    def get_available_books(self) -> List[Book]:
        return [book for book in self.books if book.is_available]

    def borrow_book(self, title: str) -> Optional[Book]:
        """Пытаемся выдать книгу по названию."""
        for book in self.books:
            if book.title == title and book.is_available:
                book.borrow()
                return book
        return None


if __name__ == "__main__":
    book1 = Book("Преступление и наказание", "Ф.М. Достоевский", 1866)
    book2 = TextBook("Алгебра", "И.И. Иванов", 2020, "Математика")

    library = Library()
    library.add_book(book1)
    library.add_book(book2)

    print("Книги в библиотеке:")
    for b in library.books:
        print("-", b.get_info())

    print("\nСвободные книги:")
    for b in library.get_available_books():
        print("-", b.get_info())

    print("\nПробуем взять 'Алгебру'...")
    taken = library.borrow_book("Алгебра")
    if taken:
        print("Взяли:", taken.get_info())
    else:
        print("Не получилось взять 'Алгебру'")

    print("\nСвободные книги после этого:")
    for b in library.get_available_books():
        print("-", b.get_info())

    print("\nАлгебра сейчас доступна?", book2.is_available)


#Сделал Book -  книгу, у которой есть название, автор, год и признак: свободна или на руках
#TextBook - это тот же Book только учебник и описание чуть другое
#Library — список, где можно добавить, найти по автору, посмотреть, какая сейчас свободна, можно взять книгу по названию. 
#В примере внизу я кладу туда две книги, беру Алгебру и она становится недоступной.