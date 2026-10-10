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
    credentials = [
        ('admin', 'Admin@8431'),
        ('doctor', 'Priya@10'),
        ('doctor_priya', 'Priya@10'),
        ('doctor_ramesh', 'Ramesh@29'),
        ('doctor_sarah', 'Sarah@38'),
        ('doctor_rajesh', 'Rajesh@47'),
        ('doctor_anita', 'Anita@56'),
        ('patient', 'Patient@1432'),
        ('reception', 'reception123'),
        ('hacker', 'hacker123'),
    ]
    for username, pwd in credentials:
        repo.update_password(username, hash_password(pwd))
        repo.set_block(username, False)
    print("ALL DEFAULT PASSWORDS SUCCESSFULLY RESTORED & UNBLOCKED!")
    print(" - admin / Admin@8431")
    print(" - doctor (Dr. Priya Nair) / Priya@10")
    print(" - doctor_priya (Dr. Priya Nair) / Priya@10")
    print(" - doctor_ramesh (Dr. Ramesh Kumar) / Ramesh@29")
    print(" - doctor_sarah (Dr. Sarah Jenkins) / Sarah@38")
    print(" - doctor_rajesh (Dr. Rajesh Patel) / Rajesh@47")
    print(" - doctor_anita (Dr. Anita Sharma) / Anita@56")
    print(" - patient / Patient@1432")
    print(" - reception / reception123")
    print(" - hacker / hacker123")

if __name__ == '__main__':
    reset_all()

