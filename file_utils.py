import os


def get_unique_filename(base_filename):
    directory = os.path.dirname(base_filename)
    filename = os.path.basename(base_filename)
    name, ext = os.path.splitext(filename)

    counter = 1
    while os.path.exists(base_filename):
        base_filename = os.path.join(directory, f"{name}_{counter}{ext}")
        counter += 1

    return base_filename

def ensure_directory_exists(filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
