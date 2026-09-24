import copy
import unittest
from classify_reward import classify

class ClassifierTests(unittest.TestCase):
    def setUp(self):
        self.event = dict(status='DONE', result='Synthetic fixture', evidence=['fixture'], verifier='reviewer',
            date='2026-09-16', event_id='SYNTHETIC_1', dedup_group='SYNTHETIC_GROUP',
            verifier_is_sole_self_report=False, scores=dict(scope=0,verification=1,durability=0,impact=0))
    def test_all_gate_fields_required(self):
        for field in ('result','evidence','verifier','date','event_id','dedup_group'):
            e=copy.deepcopy(self.event); e.pop(field)
            self.assertEqual(classify(e)['points'],0)
    def test_self_report_and_unknown_verification_fail_closed(self):
        for value in (True,None):
            self.event['verifier_is_sole_self_report']=value
            self.assertEqual(classify(self.event)['points'],0)
    def test_boundaries(self):
        for axes,expected in [((0,1,0,0),1),((1,1,1,0),1),((1,1,1,1),2),((2,1,1,1),2),((2,1,2,1),3),((2,2,2,2),3)]:
            self.event['scores']=dict(zip(('scope','verification','durability','impact'),axes))
            self.assertEqual(classify(self.event)['points'],expected)
    def test_verification_override(self):
        self.event['scores']=dict(scope=2,verification=0,durability=2,impact=2)
        self.assertEqual(classify(self.event)['points'],0)
    def test_invalid_scores_rejected(self):
        for bad in (-1,3,True,'2'):
            self.event['scores']['scope']=bad
            with self.assertRaises(ValueError):classify(self.event)
    def test_not_done_gets_no_points(self):
        self.event['status']='IN_REVIEW'
        self.assertEqual(classify(self.event)['points'],0)
