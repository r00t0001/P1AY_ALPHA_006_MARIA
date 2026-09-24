import copy
import json
from pathlib import Path
import unittest
from verify_release import verify
from validate_way_direction import validate_way_direction

class ReleaseIntegrityTests(unittest.TestCase):
    def test_public_contract(self):
        self.assertEqual(verify(require_manifest=False)['status'],'PASS')
    def test_completed_and_waiting_main_slots_rejected(self):
        save={'way_direction':{'phase':'ACTIVE','offered_directions':[{'id':'a','title':'A'},{'id':'b','title':'B'}],
            'selected_direction_ids':['a','b'],'background_tasks':[], 'main_task_ids':['a0','b0','b1'],'open_main_slots':0}}
        for direction in ('a','b'):
            for n in range(3):save['way_direction']['background_tasks'].append(dict(id=direction+str(n),title='Synthetic task',linked_direction_ids=[direction],why_helpful='Fixture',next_action='Fixture',done_criteria='Fixture',status='PROPOSED'))
        self.assertEqual(validate_way_direction(save),[])
        for status in ('DONE','WAITING','IN_REVIEW','CANCELLED'):
            changed=copy.deepcopy(save);changed['way_direction']['background_tasks'][0]['status']=status
            self.assertTrue(validate_way_direction(changed),status)

    def test_save_templates_follow_core_vocabulary(self):
        root=Path(__file__).resolve().parents[1]
        release=root/'releases'/'alpha-007'
        state=json.loads((release/'templates'/'STATE_SAVE.json').read_text())
        selective=json.loads((release/'templates'/'SELECTIVE_SAVE.json').read_text())
        self.assertEqual(state['safety_state'],'UNKNOWN')
        self.assertEqual(selective['status'],'PREPARED_NOT_SENT')
        for lang in ('en','ru'):
            core=(release/'locales'/lang/'CORE.txt').read_text()
            for value in ('UNKNOWN','ANALYZE','PAUSED','PREPARED_NOT_SENT'):
                self.assertIn(value,core)
