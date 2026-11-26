"""KTM totals use current card rows, not the general geographic address pool."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'app'))
from profile_features import current_territory_totals,summaries


def card(ident,rows=None,**changes):
    return dict(id=ident,number=ident,addresses=rows or [],**changes)


class KtmReportTotalsTests(unittest.TestCase):
    def test_current_card_points_include_manual_rows_not_unassigned_addresses(self):
        raw={'cards':[card('c1',[{'count':3},{'count':2}]),
                      card('manual',[{'count':6}]),
                      card('unknown',[{'count':0,'count_unknown':True}]),
                      card('empty',[])],
             'archived_cards':[card('archived',[{'count':99}])],
             'geo':[{'entity':'address','count':12345}],
             'ib':[{'id':'ib-a','address_id':None},{'id':'ib-b','address_id':'geo-a'}]}
        self.assertEqual(current_territory_totals(raw),
                         {'visit_points':11,'unknown_visit_cards':2,'complete_visit_points':11,
                          'temporary_cards':0,'ib_total':2,'ib_on_current_cards':0,'cards_with_ib':0})

    def test_mixed_known_unknown_never_invents_missing_count(self):
        raw={'cards':[card('mixed',[{'count':5},{'count':0,'count_unknown':True}]),
                      card('invalid',[{'count':'123'}])],
             'ib':[]}
        self.assertEqual(current_territory_totals(raw),
                         {'visit_points':5,'unknown_visit_cards':2,'complete_visit_points':0,
                          'temporary_cards':0,'ib_total':0,'ib_on_current_cards':0,'cards_with_ib':0})

    def test_period_summary_is_aggregate_only_and_preserves_coverage(self):
        raw={
            'today':'2026-11-21','revision':'fictional-r1',
            'cards':[card('c1',[{'count':5}]),card('c2',[{'count':4}]),card('c3',[])],
            'archived_cards':[card('old',[{'count':12}])],
            'completions':[{'card_id':'c1','date':'2026-01-10'},
                           {'card_id':'c1','date':'2026-11-01'},
                           {'card_id':'old','date':'2026-11-10'}],
            'loans':[],'ib':[{'id':'one','card_id':'c1'}]}
        result=summaries(raw)
        self.assertEqual(result['territory_totals'],
                         {'visit_points':9,'unknown_visit_cards':1,'complete_visit_points':9,
                          'temporary_cards':0,'ib_total':1,'ib_on_current_cards':1,'cards_with_ib':1})
        self.assertEqual(result['periods']['calendar']['missing'],2)
        self.assertEqual(result['periods']['service']['missing'],2)
        self.assertEqual(result['periods']['rolling']['missing'],2)
        self.assertNotIn('cards',result)
        self.assertNotIn('c1',str(result))
        self.assertNotIn('card_id',str(result))


if __name__=='__main__':
    unittest.main()
