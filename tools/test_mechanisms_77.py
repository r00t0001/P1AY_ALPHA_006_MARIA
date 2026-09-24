"""Source-bound negative regressions for the approved grouped product map."""
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from compile_core import compile_core
from mechanism_registry import validate_registry, registry_view, EXPECTED
from release_files import FILES, RELEASE
from verify_release import verify
ROOT=Path(__file__).resolve().parents[1]

class Mechanism77Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        for name in FILES:
            path=self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,path)
    def tearDown(self):
        self.tmp.cleanup()
    def master(self):
        return json.loads((self.root/'canon/CORE_MASTER.json').read_text())
    def mutate(self,fn):
        data=self.master();fn(data)
        (self.root/'canon/CORE_MASTER.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    def rejected(self):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            validate_registry(self.root,self.master())
    def test_changed_english_definition_requires_contract_update(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][20].update(definition_en='Automatic permanent memory.'))
        self.rejected()
    def test_original_section_name_preserved(self):
        self.mutate(lambda d:d['mechanism_registry']['groups'][0].update(ru='Invented group'))
        self.rejected()
    def test_record_source_line_is_exact(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][0]['source'].update(line=500))
        self.rejected()
    def test_all_original_ids_once(self):
        result=validate_registry(self.root,self.master())
        self.assertEqual(result['count'],77)
        self.assertEqual(result['source_definition_parity'],'PASS')
    def test_eight_original_sections(self):
        d=self.master()['mechanism_registry']
        self.assertEqual(len(d['groups']),8)
        self.assertEqual([sum(x['group_id']==g['id'] for x in d['mechanisms']) for g in d['groups']], [11,11,14,14,4,6,12,5])
    def test_corrected_save_preserves_prior_definition(self):
        m=self.master()['mechanism_registry']['mechanisms'][17]
        self.assertEqual(m['definition_ru'],'переносимое и проверяемое состояние системы.')
        self.assertEqual(m['definition_en'],'portable and verifiable system state.')
        self.assertEqual(m['correction']['previous_definition_ru'],'переносимое и проверяемое состояние человека.')
    def test_duplicate_id_cannot_satisfy_77(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'].__setitem__(76,copy.deepcopy(d['mechanism_registry']['mechanisms'][0])))
        self.rejected()
    def test_empty_definition_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][34].update(definition_ru=''))
        self.rejected()
    def test_unrelated_name_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][6].update(name='Invented mechanism'))
        self.rejected()
    def test_wrong_group_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][6].update(group_id='G02'))
        self.rejected()
    def test_original_wording_cannot_be_replaced_by_summary(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][4].update(definition_ru='Проверять что-нибудь.'))
        self.rejected()
    def test_source_deletion_rejected(self):
        (self.root/'canon/sources/MECHANISMS_77_ORIGINAL_RU.md').unlink()
        with self.assertRaises((ValueError,OSError)):
            validate_registry(self.root,self.master())
    def test_source_tampering_rejected(self):
        p=self.root/'canon/sources/MECHANISMS_77_ORIGINAL_RU.md';p.write_text(p.read_text()+'changed')
        self.rejected()
    def test_approval_tampering_rejected(self):
        p=self.root/'canon/sources/MECHANISMS_77_APPROVAL_RU.md';p.write_text('invented approval')
        self.rejected()
    def test_wrong_source_identity_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['source'].update(original_file_sha256='0'*64))
        self.rejected()
    def test_old_save_definition_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][17].update(definition_ru='переносимое и проверяемое состояние человека.'))
        self.rejected()
    def test_wrong_english_save_definition_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][17].update(definition_en='portable person state.'))
        self.rejected()
    def test_empty_english_definition_rejected(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][0].update(definition_en=' '))
        self.rejected()
    def test_translation_not_falsely_original(self):
        self.mutate(lambda d:d['mechanism_registry']['english_translation'].update(status='ORIGINAL_EN_RECOVERED'))
        self.rejected()
    def test_77_not_runtime_certification(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'][0].update(external_runtime_validation='PASS'))
        self.rejected()
    def test_218_atomic_recount_not_accepted(self):
        self.mutate(lambda d:d['mechanism_registry'].update(count=218))
        self.rejected()
    def test_source_view_has_77_in_both_cores(self):
        d=self.master()['mechanism_registry']
        for lang in ('ru','en'):
            text=(self.root/RELEASE/f'locales/{lang}/CORE.txt').read_text()
            self.assertIn(registry_view(d,lang).strip(),text)
    def test_legacy_53_remains_separate(self):
        for lang in ('ru','en'):
            self.assertTrue((self.root/RELEASE/f'locales/{lang}/SYSTEMS_53_LEGACY.md').is_file())
    def test_optimized_python_rejects_missing_mechanism(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'].pop(50))
        compile_core(self.root)
        run=subprocess.run([sys.executable,'-O',str(self.root/'tools/verify_release.py')],capture_output=True,text=True,cwd=self.root)
        self.assertNotEqual(run.returncode,0)
    def test_generated_registry_json_cannot_drift(self):
        p=self.root/RELEASE/'MECHANISMS_77.json';p.write_text('{}')
        with self.assertRaises(ValueError):verify(self.root,require_manifest=False)
    def test_generated_systems_cannot_drop_entry(self):
        p=self.root/RELEASE/'locales/ru/SYSTEMS.md';p.write_text(p.read_text().replace('77. **Brand Presentation System**','76. **Brand Presentation System**'))
        with self.assertRaises(ValueError):verify(self.root,require_manifest=False)
    def test_compiler_check_does_not_rewrite_systems(self):
        p=self.root/RELEASE/'locales/en/SYSTEMS.md';p.write_text(p.read_text()+'bad')
        before=p.read_bytes()
        with self.assertRaises(ValueError):compile_core(self.root,check=True)
        self.assertEqual(before,p.read_bytes())
    def test_existing_friendship_and_way_retained(self):
        d=self.master()
        self.assertIn('BOUNDARIES.FRIENDSHIP.001',[r['id'] for r in d['required_rules']])
        self.assertIn('WAY_6BG_3MAIN_001',d['preserved_core_bodies']['ru'])
    def test_later_system_operational_additions_retained(self):
        self.assertIn('LINK-BASED SAVE SYNC',self.master()['system_operational_additions']['en'])
    def test_variant_build_revision_is_explicit(self):
        d=self.master();self.assertEqual(d['artifact_revision'],3)
        self.assertEqual(d['supersedes_artifact_sha256'],'e8fd3065b301904bfb89267193f06a3bd1bf442d150982a14263b2f4230a7cf4')

# Test each of the 77 source requirements separately. The tests do not imply
# independent human review or live behavior of the corresponding mechanism.
def deletion_test(number):
    def test(self):
        self.mutate(lambda d:d['mechanism_registry']['mechanisms'].pop(number-1))
        self.rejected()
    return test
for n in range(1,78):
    setattr(Mechanism77Tests,f'test_missing_source_mechanism_{n:03}_rejected',deletion_test(n))

if __name__=='__main__':
    unittest.main()
