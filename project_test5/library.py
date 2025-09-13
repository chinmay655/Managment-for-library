from datetime import datetime, timedelta, date
from typing import List, Optional, Dict
from book import Book
from member import Member
from notifications import NotificationService
from attendance import AttendanceTracker, VisitorType

class Library:
    """Main library management system."""
    
    def __init__(self, name: str = "Community Library"):
        self.name = name
        self.books: Dict[str, Book] = {}  # book_id -> Book
        self.members: Dict[str, Member] = {}  # member_id -> Member
        self.transactions = []  # Transaction history
        
        # Initialize notification service (to be configured later)
        self.notification_service: Optional[NotificationService] = None
        
        # Initialize attendance tracker
        self.attendance_tracker = AttendanceTracker()
    
    # Book Management
    def add_book(self, book_id: str, title: str, author: str, isbn: str, 
                 category: str = "General", copies: int = 1) -> bool:
        """Add a new book to the library."""
        if book_id in self.books:
            return False
        
        book = Book(book_id, title, author, isbn, category, copies)
        self.books[book_id] = book
        self._log_transaction("ADD_BOOK", f"Added book: {title}")
        return True
    
    def remove_book(self, book_id: str) -> bool:
        """Remove a book from the library."""
        if book_id not in self.books:
            return False
        
        book = self.books[book_id]
        if book.available_copies < book.total_copies:
            return False  # Can't remove borrowed books
        
        del self.books[book_id]
        self._log_transaction("REMOVE_BOOK", f"Removed book: {book.title}")
        return True
    
    def search_books(self, query: str, search_type: str = "title") -> List[Book]:
        """Search for books by title, author, or category."""
        results = []
        query = query.lower()
        
        for book in self.books.values():
            if search_type == "title" and query in book.title.lower():
                results.append(book)
            elif search_type == "author" and query in book.author.lower():
                results.append(book)
            elif search_type == "category" and query in book.category.lower():
                results.append(book)
            elif search_type == "isbn" and query in book.isbn:
                results.append(book)
        
        return results
    
    def get_book(self, book_id: str) -> Optional[Book]:
        """Get a book by ID."""
        return self.books.get(book_id)
    
    def list_all_books(self) -> List[Book]:
        """Get all books in the library."""
        return list(self.books.values())
    
    def list_available_books(self) -> List[Book]:
        """Get all available books."""
        return [book for book in self.books.values() if book.is_available()]
    
    # Member Management
    def add_member(self, member_id: str, name: str, email: str, phone: str, 
                   membership_type: str = "Regular") -> bool:
        """Add a new member to the library."""
        if member_id in self.members:
            return False
        
        member = Member(member_id, name, email, phone, membership_type)
        self.members[member_id] = member
        self._log_transaction("ADD_MEMBER", f"Added member: {name}")
        return True
    
    def remove_member(self, member_id: str) -> bool:
        """Remove a member from the library."""
        if member_id not in self.members:
            return False
        
        member = self.members[member_id]
        if member.borrowed_books:
            return False  # Can't remove member with borrowed books
        
        del self.members[member_id]
        self._log_transaction("REMOVE_MEMBER", f"Removed member: {member.name}")
        return True
    
    def get_member(self, member_id: str) -> Optional[Member]:
        """Get a member by ID."""
        return self.members.get(member_id)
    
    def list_all_members(self) -> List[Member]:
        """Get all members."""
        return list(self.members.values())
    
    # Borrowing and Returning
    def borrow_book(self, member_id: str, book_id: str) -> bool:
        """Borrow a book to a member."""
        member = self.get_member(member_id)
        book = self.get_book(book_id)
        
        if not member or not book:
            return False
        
        if not member.can_borrow():
            return False
        
        if not book.is_available():
            return False
        
        # Process the borrowing
        if book.borrow(member_id) and member.borrow_book(book_id):
            self._log_transaction("BORROW", f"Member {member.name} borrowed {book.title}")
            return True
        
        return False
    
    def return_book(self, member_id: str, book_id: str) -> bool:
        """Return a book from a member."""
        member = self.get_member(member_id)
        book = self.get_book(book_id)
        
        if not member or not book:
            return False
        
        if book_id not in member.borrowed_books:
            return False
        
        # Process the return
        if book.return_book(member_id) and member.return_book(book_id):
            self._log_transaction("RETURN", f"Member {member.name} returned {book.title}")
            return True
        
        return False
    
    # Reporting and Statistics
    def get_overdue_books(self, days: int = 14) -> List[Dict]:
        """Get list of overdue books."""
        overdue = []
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for book in self.books.values():
            for member_id, borrow_date in book.borrowed_by.items():
                if borrow_date < cutoff_date:
                    member = self.get_member(member_id)
                    overdue.append({
                        'book': book,
                        'member': member,
                        'borrow_date': borrow_date,
                        'days_overdue': (datetime.now() - borrow_date).days
                    })
        
        return overdue
    
    def get_library_stats(self) -> Dict:
        """Get library statistics."""
        total_books = len(self.books)
        total_copies = sum(book.total_copies for book in self.books.values())
        available_copies = sum(book.available_copies for book in self.books.values())
        borrowed_copies = total_copies - available_copies
        total_members = len(self.members)
        active_members = len([m for m in self.members.values() if m.borrowed_books])
        
        return {
            'total_books': total_books,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'borrowed_copies': borrowed_copies,
            'total_members': total_members,
            'active_members': active_members
        }
    
    def _log_transaction(self, action: str, description: str):
        """Log a transaction."""
        self.transactions.append({
            'timestamp': datetime.now(),
            'action': action,
            'description': description
        })
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict]:
        """Get recent transaction history."""
        return self.transactions[-limit:] if limit else self.transactions
    
    # Notification Management
    def setup_notifications(self, smtp_server: str, smtp_port: int, 
                          smtp_user: str, smtp_password: str, sender_email: str):
        """Setup email notification service."""
        self.notification_service = NotificationService(
            smtp_server, smtp_port, smtp_user, smtp_password, sender_email
        )
    
    def send_overdue_reminders(self) -> int:
        """Send overdue book reminders to members."""
        if not self.notification_service:
            return 0
        
        overdue_books = self.get_overdue_books()
        return self.notification_service.send_overdue_reminders(overdue_books)
    
    def send_notification(self, member_id: str, subject: str, message: str) -> bool:
        """Send a notification to a specific member."""
        if not self.notification_service:
            return False
        
        member = self.get_member(member_id)
        if not member:
            return False
        
        return self.notification_service.send_email(member.email, subject, message)
    
    def send_bulk_notification(self, subject: str, message: str) -> int:
        """Send notification to all members."""
        if not self.notification_service:
            return 0
        
        member_emails = [member.email for member in self.members.values()]
        return self.notification_service.send_bulk_emails(member_emails, subject, message)
    
    # Attendance and Visitor Management
    def check_in_member(self, member_id: str) -> bool:
        """Check in a library member."""
        member = self.get_member(member_id)
        if not member:
            return False
        
        return self.attendance_tracker.check_in(
            member_id, member.name, VisitorType.MEMBER
        )
    
    def check_in_visitor(self, visitor_id: str, name: str, purpose: str = "") -> bool:
        """Check in a non-member visitor."""
        return self.attendance_tracker.check_in(
            visitor_id, name, VisitorType.VISITOR, purpose
        )
    
    def check_in_staff(self, staff_id: str, name: str) -> bool:
        """Check in a staff member."""
        return self.attendance_tracker.check_in(
            staff_id, name, VisitorType.STAFF
        )
    
    def check_out(self, visitor_id: str) -> bool:
        """Check out any visitor (member, visitor, or staff)."""
        return self.attendance_tracker.check_out(visitor_id)
    
    def get_current_visitors(self):
        """Get list of currently present visitors."""
        return self.attendance_tracker.get_current_visitors()
    
    def get_daily_attendance_stats(self, target_date: date = None) -> Dict:
        """Get attendance statistics for a specific date."""
        return self.attendance_tracker.get_daily_stats(target_date)
    
    def get_visitor_history(self, visitor_id: str):
        """Get attendance history for a specific visitor."""
        return self.attendance_tracker.get_visitor_history(visitor_id)
    
    def get_peak_hours(self, target_date: date = None) -> Dict:
        """Get peak hours analysis."""
        return self.attendance_tracker.get_peak_hours(target_date)
    
    def export_attendance_report(self, start_date: date, end_date: date):
        """Export attendance report for a date range."""
        return self.attendance_tracker.export_attendance_report(start_date, end_date)
    
    def __str__(self) -> str:
        stats = self.get_library_stats()
        current_visitors = len(self.get_current_visitors())
        return f"Library: {self.name} | Books: {stats['total_books']} | Members: {stats['total_members']} | Borrowed: {stats['borrowed_copies']} | Current Visitors: {current_visitors}"
