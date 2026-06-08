import os
import shutil
from dotrun.main import Code_Runner
def test_add_and_delete_file():
    test_base = "./test"
    sandbox_dir = os.path.join(test_base, "sandbox")
    venv_dir = os.path.join(test_base, "venv")
    if os.path.exists(test_base):
        shutil.rmtree(test_base)
    os.makedirs(sandbox_dir, exist_ok=True)
    try:
        runner = Code_Runner(Path=sandbox_dir, Venv_Path=venv_dir)
        test_filename = "script.py"
        runner.Add_File(test_filename)
        expected_file_path = os.path.join(sandbox_dir, test_filename)
        assert os.path.exists(expected_file_path), "Add_File failed to create the file."
        assert os.path.isfile(expected_file_path), "Created path is not a file."
        runner.Delete_File(test_filename)  
        assert not os.path.exists(expected_file_path), "Delete_File failed to remove the file."
    finally:
        if os.path.exists(test_base):
            shutil.rmtree(test_base)
