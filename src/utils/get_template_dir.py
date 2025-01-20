import os

def get_template_dir() -> str:
    return os.path.join(os.path.abspath(''), 'src')