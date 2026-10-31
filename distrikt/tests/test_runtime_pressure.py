import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from runtime_pressure import resource_pressure


class RuntimePressureTests(unittest.TestCase):
    def test_missing_and_invalid_metrics_remain_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            self.assertFalse(resource_pressure(root)['available'])
            for name,value in [('cpu','nan'),('memory','-1'),('io','101')]:
                (root/name).write_text(('some' if name=='cpu' else 'full')+' avg60='+value)
            result=resource_pressure(root)
            self.assertFalse(result['available']);self.assertFalse(result['high'])

    def test_sustained_pressure_uses_the_actual_rolling_average_not_an_instant_sample(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'cpu').write_text('some avg10=99.00 avg60=2.00 avg300=0.00 total=1\n')
            (root/'memory').write_text('some avg60=95.00\nfull avg60=0.00\n')
            self.assertFalse(resource_pressure(root)['high'])
            (root/'memory').write_text('some avg60=95.00\nfull avg60=15.00\n')
            result=resource_pressure(root)
            self.assertTrue(result['available']);self.assertTrue(result['high'])
            self.assertEqual(result['readings'],{'cpu':2.0,'memory':15.0})


if __name__=='__main__':unittest.main()
