import os
import re

class Code_Runner:
    def __init__(self, Path):
        self.Path = Path
        if os.path.exists(Path) and os.listdir(Path):
            raise ValueError(f"Directory '{Path}' is not empty.")

    def _get_safe_path(self, Name):
        if os.path.isabs(Name):
            raise ValueError("Input must be a relative path.")
        base = os.path.abspath(self.Path)
        target = os.path.abspath(os.path.join(base, Name))
        if not (target == base or target.startswith(base + os.sep)):
            raise ValueError("Path traversal is not allowed.")
        return target

    def Add_File(self, Name):
        file_path = self._get_safe_path(Name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w'):
            pass

    def All_files(self, regex=None):
        all_files = []
        pattern = re.compile(regex) if regex else None
        if not os.path.exists(self.Path):
            return []
        for root, _, files in os.walk(self.Path):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.Path)
                if pattern is None or pattern.search(rel_path):
                    all_files.append(rel_path)
        return all_files

    def Delete_File(self, Name):
        file_path = self._get_safe_path(Name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)