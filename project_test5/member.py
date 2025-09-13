from datetime import datetime
from typing import List, Optional

class Member:
    """Represents a library member."""
    
    def __init__(self, member_id: str, name: str, email: str, phone: str, 
                 membership_type: str = "Regular"):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.phone = phone
        self.membership_type = membership_type
        self.join_date = datetime.now()
        self.borrowed_books = []  # List of book_ids
        self.borrowing_history = []  # List of (book_id, borrow_date, return_date)
        self.max_books = 5 if membership_type == "Premium" else 3
    
    def can_borrow(self) -> bool:
        """Check if member can borrow more books."""
        return len(self.borrowed_books) < self.max_books
    
    def borrow_book(self, book_id: str) -> bool:
        """Add a book to member's borrowed list."""
        if self.can_borrow():
            self.borrowed_books.append(book_id)
            return True
        return False
    
    def return_book(self, book_id: str) -> bool:
        """Remove a book from member's borrowed list."""
        if book_id in self.borrowed_books:
            self.borrowed_books.remove(book_id)
            # Add to history
            self.borrowing_history.append((book_id, datetime.now(), datetime.now()))
            return True
        return False
    
    def get_borrowed_books(self) -> List[str]:
        """Get list of currently borrowed book IDs."""
        return self.borrowed_books.copy()
    
    def get_borrowing_history(self) -> List[tuple]:
        """Get borrowing history."""
        return self.borrowing_history.copy()
    
    def __str__(self) -> str:
        return f"Member(ID: {self.member_id}, Name: {self.name}, Type: {self.membership_type}, Books: {len(self.borrowed_books)}/{self.max_books})"
    
    def __repr__(self) -> str:
        return self.__str__()
