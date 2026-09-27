import sys
import os

backend_dir = r'c:\Users\ajayy\OneDrive\Desktop\EHR\backend'
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.repositories.user_repository import UserRepository
from app.core.users import hash_password

def reset_all():
    repo = UserRepository()
    for username, pwd in [('admin', 'admin123'), ('doctor', 'doctor123'), ('reception', 'reception123'), ('hacker', 'hacker123')]:
        repo.update_password(username, hash_password(pwd))
        repo.set_block(username, False)
    print("ALL DEFAULT PASSWORDS SUCCESSFULLY RESTORED & UNBLOCKED!")
    print(" - admin / admin123")
    print(" - doctor / doctor123")
    print(" - reception / reception123")
    print(" - hacker / hacker123")

if __name__ == '__main__':
    reset_all()

