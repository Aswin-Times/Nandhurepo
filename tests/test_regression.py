import sys
import unittest
import tempfile
import hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from offline_regression import check_hash

class RegressionTests(unittest.TestCase):
    def test_hash_negative_control(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'output.csv';path.write_bytes(b'original')
            expected=hashlib.sha256(path.read_bytes()).hexdigest()
            check_hash(path,expected)
            path.write_bytes(b'corrupted')
            with self.assertRaises(ValueError):check_hash(path,expected)
if __name__=='__main__':unittest.main()
