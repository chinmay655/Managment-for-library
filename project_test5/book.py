from datetime import datetime
from typing import Optional

class Book:
    """Represents a book in the library system."""
    
    def __init__(self, book_id: str, title: str, author: str, isbn: str, 
                 category: str = "General", copies: int = 1):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.isbn = isbn
        self.category = category
        self.total_copies = copies
        self.available_copies = copies
        self.borrowed_by = {}  # {member_id: borrow_date}
    
    def is_available(self) -> bool:
        """Check if the book is available for borrowing."""
        return self.available_copies > 0
    
    def borrow(self, member_id: str) -> bool:
        """Borrow the book to a member."""
        if self.is_available():
            self.available_copies -= 1
            self.borrowed_by[member_id] = datetime.now()
            return True
        return False
    
    def return_book(self, member_id: str) -> bool:
        """Return the book from a member."""
        if member_id in self.borrowed_by:
            self.available_copies += 1
            del self.borrowed_by[member_id]
            return True
        return False
    
    def get_borrower_info(self) -> dict:
        """Get information about who borrowed the book."""
        return self.borrowed_by.copy()
    
    def __str__(self) -> str:
        return f"Book(ID: {self.book_id}, Title: {self.title}, Author: {self.author}, Available: {self.available_copies}/{self.total_copies})"
    
    def __repr__(self) -> str:
        return self.__str__()
