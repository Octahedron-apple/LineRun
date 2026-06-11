import os
import re
import sys
import subprocess
import shlex

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
        if not Name:
            raise ValueError("Path cannot be empty.")
        base = os.path.realpath(self.Path)
        target = os.path.realpath(os.path.join(base, Name))
        if not target.startswith(base + os.sep):
            raise ValueError("Path traversal is not allowed.")
        return target
    def Add_File(self, Name):
        file_path = self.get_safe_path(Name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w'):
            pass
    def All_files(self, regex=None):
        all_files = []
        try:
            pattern = re.compile(regex) if regex else None
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")
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
        if Name.startswith("-"):
            raise ValueError("Package name cannot start with a hyphen.")
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
        if Name.startswith("-"):
            raise ValueError("Package name cannot start with a hyphen.")
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
        import threading
        file_path = self.get_safe_path(Name)
        python_path = os.path.join(self.Venv_Path, "bin", "python")
        if self.is_nixos:
            shell_nix_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "shell.nix"))
            command = ["nix-shell", shell_nix_path, "--run", f"{shlex.quote(python_path)} {shlex.quote(file_path)}"]
        else:
            command = [python_path, file_path]  
        
        process = subprocess.Popen(
            command,
            cwd=self.Path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        limit_bytes = 1024 * 1024  # 1MB
        out_data = bytearray()
        err_data = bytearray()
        
        def read_stream(stream, buffer):
            while True:
                chunk = stream.read(4096)
                if not chunk:
                    break
                buffer.extend(chunk)
                if len(buffer) > limit_bytes:
                    try:
                        process.terminate()
                    except Exception:
                        pass
                    break
                    
        t_out = threading.Thread(target=read_stream, args=(process.stdout, out_data))
        t_err = threading.Thread(target=read_stream, args=(process.stderr, err_data))
        t_out.start()
        t_err.start()
        
        timeout_occurred = False
        try:
            process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            process.terminate()
            process.wait()
            timeout_occurred = True
            
        t_out.join()
        t_err.join()
        
        stdout_str = out_data.decode('utf-8', errors='replace')
        stderr_str = err_data.decode('utf-8', errors='replace')
        
        if len(out_data) > limit_bytes:
            stdout_str += "\n...[Output truncated due to excessive length]..."
        if len(err_data) > limit_bytes:
            stderr_str += "\n...[Output truncated due to excessive length]..."
            
        if timeout_occurred:
            stderr_str += "\nExecution timed out after 30 seconds."
            exit_code = 124
        else:
            exit_code = process.returncode
            
        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "exit_code": exit_code
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
    def Replace_In_File(self, Name, TargetContent, ReplacementContent, StartLine=1, EndLine=None, AllowMultiple=False):
        file_path = self.get_safe_path(Name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {Name} does not exist.")  
        with open(file_path, 'r') as f:
            lines = f.readlines() 
        StartLine = max(1, StartLine)
        if EndLine is None or EndLine > len(lines):
            EndLine = len(lines)  
        range_content = "".join(lines[StartLine-1:EndLine])
        if TargetContent not in range_content:
            raise ValueError(f"Target content not found between lines {StartLine} and {EndLine}.")
        occurrences = range_content.count(TargetContent)
        if occurrences > 1 and not AllowMultiple:
            raise ValueError(f"Found {occurrences} occurrences of TargetContent. Specify AllowMultiple=True to replace all, or narrow StartLine/EndLine.") 
        new_range_content = range_content.replace(TargetContent, ReplacementContent, -1 if AllowMultiple else 1)
        new_content = "".join(lines[:StartLine-1]) + new_range_content + "".join(lines[EndLine:])
        with open(file_path, 'w') as f:
            f.write(new_content)