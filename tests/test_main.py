import os
import re
import pytest
from unittest.mock import patch
from linerun.main import Code_Runner

@pytest.fixture
def runner(tmp_path):
    sandbox_dir = tmp_path / "sandbox"
    venv_dir = tmp_path / "venv"
    os.makedirs(sandbox_dir, exist_ok=True)
    r = Code_Runner(Path=str(sandbox_dir), Venv_Path=str(venv_dir))
    yield r

def test_get_safe_path(runner, tmp_path):
    safe = runner.get_safe_path("test.py")
    assert safe == os.path.realpath(os.path.join(runner.Path, "test.py"))
    with pytest.raises(ValueError):
        runner.get_safe_path("/absolute/path")
    with pytest.raises(ValueError):
        runner.get_safe_path("../outside.py")
        
    # Symlink Test
    outside_dir = tmp_path / "outside"
    os.makedirs(outside_dir, exist_ok=True)
    outside_file = outside_dir / "secret.txt"
    with open(outside_file, 'w') as f:
        f.write("secret")
    
    symlink_path = os.path.join(runner.Path, "symlink")
    os.symlink(str(outside_dir), symlink_path)
    
    with pytest.raises(ValueError):
        runner.get_safe_path("symlink/secret.txt")

def test_add_delete_file(runner):
    runner.Add_File("script.py")
    assert os.path.exists(os.path.join(runner.Path, "script.py"))
    runner.Delete_File("script.py")
    assert not os.path.exists(os.path.join(runner.Path, "script.py"))

def test_all_files(runner):
    runner.Add_File("a.txt")
    runner.Add_File("b.py")
    runner.Add_File("dir/c.txt")
    files = runner.All_files()
    assert len(files) == 3
    txt_files = runner.All_files(r"\.txt$")
    assert len(txt_files) == 2
    
    with pytest.raises(ValueError, match="Invalid regex"):
        runner.All_files(r"[A-Z")

def test_read_write_replace(runner):
    runner.Write_File("test.txt", "hello world\nhello world\nhello world")
    assert "hello world" in runner.Read_File("test.txt")
    runner.Replace_In_File("test.txt", "world", "universe", EndLine=1)
    assert runner.Read_File("test.txt") == "hello universe\nhello world\nhello world"
    runner.Replace_In_File("test.txt", "world", "galaxy", StartLine=3, EndLine=3)
    assert runner.Read_File("test.txt") == "hello universe\nhello world\nhello galaxy"
    runner.Write_File("test2.txt", "a b c\na b c")
    runner.Replace_In_File("test2.txt", "b", "z", AllowMultiple=True)
    assert runner.Read_File("test2.txt") == "a z c\na z c"
    runner.Write_File("test3.txt", "duplicate duplicate")
    with pytest.raises(ValueError, match="Found 2 occurrences"):
        runner.Replace_In_File("test3.txt", "duplicate", "single")
        
    # Negative StartLine test
    runner.Write_File("test4.txt", "line1\nline2\nline3\nline4")
    runner.Replace_In_File("test4.txt", "line1", "new1", StartLine=-5, EndLine=2)
    assert runner.Read_File("test4.txt") == "new1\nline2\nline3\nline4"

def test_run_code(runner, tmp_path):
    runner.Write_File("run_test.py", "print('success')")
    out = runner.Run_Code("run_test.py")
    assert "success" in out["stdout"]
    assert out["exit_code"] == 0
    
    # Environment Isolation Test: relative paths should resolve to sandbox
    runner.Write_File("iso_test.py", "open('data.json', 'w').write('isolated')")
    runner.Run_Code("iso_test.py")
    assert os.path.exists(os.path.join(runner.Path, "data.json"))
    
    # Shell Injection Test
    runner.Write_File("echo.py", "print('hacked')")
    runner.Write_File("script.py; python echo.py", "print('safe')")
    out = runner.Run_Code("script.py; python echo.py")
    assert "hacked" not in out["stdout"]

@patch('linerun.main.subprocess.run')
def test_modules(mock_run, runner):
    mock_run.return_value.stdout = "six"
    mock_run.return_value.returncode = 0
    
    runner.Add_Module("six")
    # Verify pip install was called
    args, kwargs = mock_run.call_args
    assert "install" in args[0]
    assert "six" in args[0]
    
    modules = runner.List_Modules()
    assert modules == "six"
    
    runner.Remove_Module("six")
    args, kwargs = mock_run.call_args
    assert "uninstall" in args[0]
    assert "six" in args[0]
