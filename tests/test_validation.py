import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from independent_validation import replay_safe

class ValidationTests(unittest.TestCase):
    def test_independent_replay_and_negative_control(self):
        flows=[dict(date='2026-01-02',amount='-300',evidence_id='rent'),
               dict(date='2026-01-05',amount='600',evidence_id='salary')]
        self.assertTrue(replay_safe('1000','200',flows,[('2026-01-01','500')])['safe'])
        self.assertFalse(replay_safe('1000','200',flows,[('2026-01-01','501')])['safe'])
        self.assertFalse(replay_safe('1000','200',flows+[dict(date='2026-02-01',amount='-2000',evidence_id='liability')],[])['safe'])
if __name__=='__main__':unittest.main()
