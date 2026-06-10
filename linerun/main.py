import os
import re
import sys
import subprocess

def Is_Nixos():
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release", "r") as f:
            if "nixos" in f.read().lower():
                return True
    if os.path.exists("/etc/nixos"):
        return True
    return False

class Code_Runner:
    def __init__(self, Path, Venv_Path):
        self.Path = Path
        self.Venv_Path = Venv_Path   
        self.is_nixos = Is_Nixos()
        if os.path.exists(Path) and os.listdir(Path):
            raise ValueError(f"Directory '{Path}' is not empty.")       
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", self.Venv_Path],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create virtual environment: {e.stderr.decode('utf-8')}")
    def get_safe_path(self, Name):
        if os.path.isabs(Name):
            raise ValueError("Input must be a relative path.")
        base = os.path.abspath(self.Path)
        target = os.path.abspath(os.path.join(base, Name))
        if not (target == base or target.startswith(base + os.sep)):
            raise ValueError("Path traversal is not allowed.")
        return target
    def Add_File(self, Name):
        file_path = self.get_safe_path(Name)
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
        file_path = self.get_safe_path(Name)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            os.remove(file_path)
    def Add_Module(self, Name):
        PATH = os.path.join(self.Venv_Path, "bin", "pip")
        try:
            subprocess.run(
                [PATH, "install", Name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to install module {Name}: {e.stderr.decode('utf-8')}")
    def List_Modules(self):
        PATH = os.path.join(self.Venv_Path, "bin", "pip")
        try:
            result = subprocess.run(
                [PATH, "list"],
                check=True,
                capture_output=True,
                text=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to list modules: {e.stderr}")
    def Remove_Module(self, Name):
        PATH = os.path.join(self.Venv_Path, "bin", "pip")
        try:
            subprocess.run(
                [PATH, "uninstall", "-y", Name],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to remove module {Name}: {e.stderr.decode('utf-8')}")
    def Run_Code(self, Name):
        file_path = self.get_safe_path(Name)
        python_path = os.path.join(self.Venv_Path, "bin", "python")
        if self.is_nixos:
            command = ["nix-shell", "--run", f"{python_path} {file_path}"]
        else:
            command = [python_path, file_path]  
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode
        }
    def Read_File(self, Name):
        file_path = self.get_safe_path(Name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {Name} does not exist.")
        with open(file_path, 'r') as f:
            return f.read()
    def Write_File(self, Name, Content):
        file_path = self.get_safe_path(Name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(Content)
    def Replace_In_File(self, Name, TargetContent, ReplacementContent):
        file_path = self.get_safe_path(Name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {Name} does not exist.")  
        with open(file_path, 'r') as f:
            content = f.read()      
        if TargetContent not in content:
            raise ValueError(f"Target content not found in {Name}. The AI must provide an exact match.")     
        new_content = content.replace(TargetContent, ReplacementContent, 1) 
        with open(file_path, 'w') as f:
            f.write(new_content)