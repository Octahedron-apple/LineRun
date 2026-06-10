import os
import shutil
import pytest
from linerun.main import Code_Runner
@pytest.fixture
def runner():
    test_base = "./test"
    sandbox_dir = os.path.join(test_base, "sandbox")
    venv_dir = os.path.join(test_base, "venv")
    if os.path.exists(test_base):
        shutil.rmtree(test_base)
    os.makedirs(sandbox_dir, exist_ok=True)
    r = Code_Runner(Path=sandbox_dir, Venv_Path=venv_dir)
    yield r
    if os.path.exists(test_base):
        shutil.rmtree(test_base)
def test_get_safe_path(runner):
    safe = runner.get_safe_path("test.py")
    assert safe == os.path.abspath(os.path.join(runner.Path, "test.py"))
    with pytest.raises(ValueError):
        runner.get_safe_path("/absolute/path")
    with pytest.raises(ValueError):
        runner.get_safe_path("../outside.py")
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
def test_run_code(runner):
    runner.Write_File("run_test.py", "print('success')")
    out = runner.Run_Code("run_test.py")
    assert "success" in out["stdout"]
    assert out["exit_code"] == 0
def test_modules(runner):
    runner.Add_Module("six")
    runner.Write_File("test_six.py", "import six\nprint('six loaded')")
    out = runner.Run_Code("test_six.py")
    assert "six loaded" in out["stdout"]
    modules = runner.List_Modules()
    assert modules is not None
    assert "six" in modules
    
    runner.Remove_Module("six")
