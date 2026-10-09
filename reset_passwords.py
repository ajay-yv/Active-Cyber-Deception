import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(project_root, 'backend')

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.app.repositories.user_repository import UserRepository
from backend.app.core.users import hash_password

def reset_all():
    repo = UserRepository()
    for username, pwd in [('admin', 'Admin@8431'), ('doctor', 'Doctor@1432'), ('reception', 'reception123'), ('hacker', 'hacker123')]:
        repo.update_password(username, hash_password(pwd))
        repo.set_block(username, False)
    print("ALL DEFAULT PASSWORDS SUCCESSFULLY RESTORED & UNBLOCKED!")
    print(" - admin / Admin@8431")
    print(" - doctor / Doctor@1432")
    print(" - reception / reception123")
    print(" - hacker / hacker123")

if __name__ == '__main__':
    reset_all()

