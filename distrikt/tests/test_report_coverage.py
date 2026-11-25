"""Fictional aggregate-only coverage regression for LTM #33."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from profile_features import summaries


class ReportCoverageTests(unittest.TestCase):
    def test_recorded_days_and_current_assignment_counts(self):
        raw={
            'today':'2026-10-16','revision':'fictional-33',
            'cards':[
                {'id':'fictional-a','last_completed':'2026-10-12'},
                {'id':'fictional-b','last_completed':'2026-08-31'},
                {'id':'fictional-c','last_completed':'2026-02-30'},
                {'id':'fictional-d'},
                {'id':'fictional-e'},
            ],
            'loans':[
                {'card_id':'fictional-c','assigned':None,'returned':None},
                {'card_id':'fictional-d','assigned':'2026-08-01','returned':'2026-09-01'},
            ],
            'completions':[
                {'card_id':'fictional-a','date':'2026-09-01','created':'2026-10-16'},
                {'card_id':'fictional-b','date':'2026-08-31','previous_completed':'2025-10-16'},
                {'card_id':'fictional-c','date':'2026-02-30'},
                {'card_id':'fictional-c','date':None},
                {'card_id':'fictional-d','date':'2026-10-17'},
                {'card_id':'fictional-e','date':'2026-10-16'},
                {'card_id':'fictional-archived','date':'2026-09-01'},
            ],
            'ib':[],
        }
        original=copy.deepcopy(raw)
        summary=summaries(raw)
        service=summary['periods']['service']
        self.assertEqual((service['start'],service['end']),('2026-09-01','2026-10-16'))
        self.assertEqual((service['completions'],service['completed_territories'],service['missing']),(3,2,3))
        self.assertEqual((service['missing_assigned'],service['missing_home']),(1,2))
        self.assertEqual(summary['periods']['calendar']['completed_territories'],3)
        self.assertEqual(summary['periods']['rolling']['completed_territories'],3)
        self.assertEqual(raw,original)
        self.assertNotIn('fictional-a',str(summary))
        self.assertNotIn('fictional-c',str(summary))

    def test_retained_dates_are_coverage_not_additional_events(self):
        raw={
            'today':'2026-10-16','revision':'fictional-33',
            'cards':[{'id':'fictional-retained','last_completed':None}],
            'loans':[],
            # A later-known date may survive on a manually backdated event.
            'completions':[{'card_id':'fictional-retained','date':'2025-10-15','previous_completed':'2025-10-16'}],
        }
        rolling=summaries(raw)['periods']['rolling']
        self.assertEqual(rolling['completions'],0)
        self.assertEqual(rolling['completed_territories'],1)
        self.assertEqual(rolling['missing'],0)


if __name__=='__main__':
    unittest.main()
