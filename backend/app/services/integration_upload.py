import os
from typing import List

UPLOAD_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
os.makedirs(UPLOAD_ROOT, exist_ok=True)

def list_uploads() -> List[str]:
    return [f for f in os.listdir(UPLOAD_ROOT) if os.path.isfile(os.path.join(UPLOAD_ROOT, f))]
