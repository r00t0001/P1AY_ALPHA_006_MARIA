"""Negative controls for 0.7.2; synthetic data only, no network or provider calls."""
import copy,io,json,os,shutil,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from compile_core import compile_core,outputs
from verify_release import verify,VerificationError
from release_files import FILES,MANIFEST,RELEASE,REQUIRED_RULE_IDS
from build_release import validate_zip_members
from validate_way_direction import validate_way_direction
from classify_reward import classify
ROOT=Path(__file__).resolve().parents[1]

class Canon072Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        for n in FILES:
            dst=self.root/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/n,dst)
    def tearDown(self):self.tmp.cleanup()
    def mutate(self,path,fn):
        p=self.root/path;data=json.loads(p.read_text());fn(data);p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    def fail(self):
        with self.assertRaises((VerificationError,ValueError,KeyError,TypeError)):
            verify(self.root,require_manifest=False)
    def make_manifest(self):
        import hashlib
        entries=[{'path':n,'bytes':(self.root/n).stat().st_size,'sha256':hashlib.sha256((self.root/n).read_bytes()).hexdigest()} for n in FILES]
        (self.root/MANIFEST).write_text(json.dumps({'version':'0.7.2','files':entries}))
    def test_duplicate_manifest_entry_rejected(self):
        self.make_manifest()
        self.mutate(MANIFEST,lambda d:d['files'].append(copy.deepcopy(d['files'][0])))
        with self.assertRaises(VerificationError):verify(self.root,require_manifest=True)
    def test_manifest_hash_tampering_rejected(self):
        self.make_manifest();self.mutate(MANIFEST,lambda d:d['files'][0].update(sha256='0'*64))
        with self.assertRaises(VerificationError):verify(self.root,require_manifest=True)
    def test_manifest_version_drift_rejected(self):
        self.make_manifest();self.mutate(MANIFEST,lambda d:d.update(version='V5'))
        with self.assertRaises(VerificationError):verify(self.root,require_manifest=True)
    def test_unexpected_source_member_rejected(self):
        (self.root/'unexpected_personal.txt').write_text('synthetic private data');self.fail()
    def test_source_authority_drift_rejected(self):
        self.mutate('canon/CORE_MASTER.json',lambda d:d.update(authoring_authority='other.md'));compile_core(self.root);self.fail()
    def test_generated_root_is_exact_ru_view(self):
        self.assertEqual((self.root/'CORE.md').read_bytes(),(self.root/RELEASE/'locales/ru/CORE.txt').read_bytes())
    def test_compile_check_never_writes(self):
        p=self.root/'CORE.md';p.write_text(p.read_text()+'tamper');before=p.read_bytes()
        with self.assertRaises(ValueError):compile_core(self.root,check=True)
        self.assertEqual(before,p.read_bytes())
    def test_arbitrary_core_drift_rejected(self):
        p=self.root/RELEASE/'locales/ru/CORE.txt';p.write_text(p.read_text()+'tamper');self.fail()
    def test_source_change_requires_regeneration(self):
        self.mutate('canon/CORE_MASTER.json',lambda d:d['required_rules'][1].update(ru=d['required_rules'][1]['ru']+' changed'))
        self.fail()
    def test_version_source_drift_rejected(self):
        self.mutate('canon/CORE_MASTER.json',lambda d:d.update(version='0.7.1'));self.fail()
    def test_release_version_drift_rejected(self):
        self.mutate(RELEASE/'release.json',lambda d:d.update(version='007.1'));self.fail()
    def test_fake_live_pass_rejected(self):
        self.mutate(RELEASE/'VALIDATION.json',lambda d:d.update(chatgpt_live='PASS'));self.fail()
    def test_fake_independent_pass_rejected(self):
        self.mutate(RELEASE/'VALIDATION.json',lambda d:d.update(independent_technical_review='PASS'));self.fail()
    def test_fake_77_map_verification_rejected(self):
        self.mutate(RELEASE/'PRODUCT_MAP_STATUS.json',lambda d:d.update(complete_named_map=['invented']*77));self.fail()
    def test_false_runtime_inclusion_rejected(self):
        self.mutate(RELEASE/'release.json',lambda d:d.update(runtime_scope='INCLUDED'));self.fail()
    def test_false_computer_merge_rejected(self):
        self.mutate(RELEASE/'SOURCE_PROVENANCE.json',lambda d:d.update(full_computer_merge='COMPLETE'));self.fail()
    def test_shared_template_consent_cannot_default_true(self):
        self.mutate(RELEASE/'templates/SELECTIVE_SAVE.json',lambda d:d['consent'].update(status='GRANTED'));self.fail()
    def test_empty_template_safety_not_active(self):
        self.mutate(RELEASE/'templates/STATE_SAVE.json',lambda d:d.update(safety_state='ACTIVE'));self.fail()
    def test_missing_file_rejected(self):
        (self.root/'LICENSE').unlink();self.fail()
    def test_symlink_rejected(self):
        p=self.root/'LICENSE';p.unlink();p.symlink_to(ROOT/'LICENSE');self.fail()
    def test_private_path_marker_rejected(self):
        p=self.root/'README.md';p.write_text(p.read_text()+'\n'+'/'+'Users/'+'fixture');self.fail()
    def test_unpackaged_markdown_link_rejected(self):
        p=self.root/'README.md';p.write_text(p.read_text()+'\n[missing](absent.md)');self.fail()
    def test_optimized_python_rejects_broken_version(self):
        self.mutate(RELEASE/'release.json',lambda d:d.update(version='broken'))
        run=subprocess.run([sys.executable,'-O',str(self.root/'tools/verify_release.py')],capture_output=True,text=True,cwd=self.root)
        self.assertNotEqual(run.returncode,0);self.assertIn('FAIL',run.stderr)
    def test_canon_formula_exact(self):
        for target in ('CORE.md',str(RELEASE/'locales/ru/CORE.txt')):
            self.assertIn('НЕ ЛЕЙ ВОДУ. НЕ ПИЗДИ. НЕ ПИЛИ.',(self.root/target).read_text())
    def test_no_forged_friendship_peer_ack(self):
        d=json.loads((self.root/'canon/RECONCILIATION.json').read_text())
        self.assertEqual(next(x for x in d['items'] if x['id']=='PHONE_FRIENDSHIP_TRANSPORT')['disposition'],'UNVERIFIED')
    def test_paused_and_way_rules_survive(self):
        text=(self.root/RELEASE/'locales/ru/CORE.txt').read_text()
        for exact in ('Импорт PAUSED сохраняет паузу','WAY_6BG_3MAIN_001','Режим A','Режим B','Режим C','Два YES не дают бессрочных разрешений'):
            self.assertIn(exact,text)
    def test_third_party_access_not_implied_by_owner_id(self):
        text=(self.root/RELEASE/'locales/ru/CORE.txt').read_text()
        self.assertIn('Совпадение owner_id не является технической аутентификацией',text)
    def test_no_fixed_warning_count_in_public_friendship_rule(self):
        d=json.loads((self.root/'canon/CORE_MASTER.json').read_text())
        r=next(x for x in d['required_rules'] if x['id']=='BOUNDARIES.FRIENDSHIP.001')
        self.assertNotIn('три',r['ru']);self.assertIn('Не блокируй людей',r['ru'])

# One independent unit-test result per removed required rule group.
def removal_test(rule_id):
    def test(self):
        self.mutate('canon/CORE_MASTER.json',lambda d:d.update(required_rules=[r for r in d['required_rules'] if r['id']!=rule_id]))
        compile_core(self.root);self.fail()
    return test
for identifier in REQUIRED_RULE_IDS:
    setattr(Canon072Tests,'test_missing_rule_'+identifier.replace('.','_').lower(),removal_test(identifier))

class JsonBoundaryTests(unittest.TestCase):
    def test_nonobject_save_rejected(self):
        for payload in (None,[],0,'text',False):self.assertTrue(validate_way_direction(payload))
    def test_unhashable_phase_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':[]}}))
    def test_unhashable_selected_id_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':'SELECTED','selected_direction_ids':[{}]}}))
    def test_unhashable_main_id_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':'ACTIVE','main_task_ids':[[]]}}))
    def test_boolean_slot_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':'ACTIVE','open_main_slots':True}}))
    def test_unhashable_task_id_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':'ACTIVE','background_tasks':[{'id':[]} ]}}))
    def test_unhashable_task_link_rejected(self):
        self.assertTrue(validate_way_direction({'way_direction':{'phase':'ACTIVE','background_tasks':[{'id':'a','status':'PROPOSED','linked_direction_ids':[{}]}]}}))
    def test_nonobject_reward_is_explicit_error(self):
        for payload in (None,[],False,1,'text'):
            with self.assertRaises(ValueError):classify(payload)

class ZipBoundaryTests(unittest.TestCase):
    def zcheck(self,names):
        data=io.BytesIO()
        with zipfile.ZipFile(data,'w') as z:
            for name in names:z.writestr(name,'fixture')
        data.seek(0)
        with zipfile.ZipFile(data) as z:
            with self.assertRaises(VerificationError):validate_zip_members(z)
    def test_path_traversal_rejected(self):self.zcheck(['../outside.txt'])
    def test_absolute_path_rejected(self):self.zcheck(['/outside.txt'])
    def test_unexpected_private_member_rejected(self):self.zcheck(['private/PLAYER.md'])
    def test_case_collision_rejected(self):self.zcheck(['CORE.md','core.md'])
    def test_incomplete_zip_rejected(self):self.zcheck(['README.md'])


    def test_ppd_contract_present(self):
        master=json.loads((ROOT/'canon/CORE_MASTER.json').read_text())
        r=next(x for x in master['required_rules'] if x['id']=='PPD.PRODUCT_PROOF.001')
        self.assertIn('Activated',r['ru']);self.assertIn('CVA',r['ru']);self.assertIn('D3',r['ru']);self.assertIn('D7',r['ru']);self.assertIn('pay',r['ru'])

if __name__=='__main__':unittest.main()
