import sys
import unittest
import tempfile
import json
import hashlib
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from release_submission import package_submission
from release_submission import validate_manifest_freshness

class ReleaseTests(unittest.TestCase):
    def test_unknown_hosted_provider_and_incomplete_usage_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'output.csv';out.write_text('fixture')
            digest=hashlib.sha256(out.read_bytes()).hexdigest()
            report=root/'usage.md';report.write_text('abc '+digest)
            base=dict(provider='openrouter',request_count=250,usage={'model_calls':1},fingerprint='abc',output_sha256=digest)
            for manifest in (dict(base,provider='obsolete'),dict(base,usage={'model_calls':1,'usage_missing_calls':1})):
                with self.assertRaises(ValueError):package_submission(root,out,report,manifest,root/'code.zip')
    def test_code_changed_after_run_is_detected(self):
        from main import fingerprint
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'dataset').mkdir();(root/'code').mkdir()
            source=root/'code'/'main.py';source.write_text('version=1')
            config={'provider':'offline'}
            manifest=dict(config=config,fingerprint=fingerprint(root/'dataset',config,root/'code'))
            validate_manifest_freshness(root,manifest)
            source.write_text('version=2')
            with self.assertRaises(ValueError):validate_manifest_freshness(root,manifest)
    def test_stale_or_offline_artifact_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);out=root/'output.csv';out.write_text('fixture')
            report=root/'usage.md';report.write_text('no final run')
            manifest=dict(provider='offline',request_count=250,usage={'model_calls':0},output_sha256='wrong')
            with self.assertRaises(ValueError):package_submission(root,out,report,manifest,root/'code.zip')

    def test_package_excludes_local_secrets_logs_and_caches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'code').mkdir();(root/'code'/'main.py').write_text('print("hello")')
            (root/'SOLUTION_README.md').write_text('setup');(root/'requirements.txt').write_text('')
            (root/'.env').write_text('SECRET=never-package');(root/'log.txt').write_text('private')
            out=root/'output.csv';out.write_text('fixture');digest=hashlib.sha256(out.read_bytes()).hexdigest()
            report=root/'usage.md';report.write_text('abc '+digest)
            manifest=dict(provider='openrouter',request_count=250,usage={'model_calls':1},fingerprint='abc',output_sha256=digest)
            destination=root/'code.zip'
            package_submission(root,out,report,manifest,destination)
            with zipfile.ZipFile(destination) as z:
                self.assertIn('evaluation/usage_report.md',z.namelist())
                self.assertIn('code/main.py',z.namelist())
                self.assertNotIn('.env',z.namelist());self.assertNotIn('log.txt',z.namelist())
if __name__=='__main__':unittest.main()
