"""Negative-control regressions for the six V3 CORE/wrapper discrepancies."""
import json
import os
from pathlib import Path
import unittest


DEFAULT_ROOT = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('P1AY_REGRESSION_ROOT', DEFAULT_ROOT)).resolve()
RELEASE = ROOT / 'releases' / 'alpha-007'


class SpikeRegressionTests(unittest.TestCase):
    def test_state_save_defaults_unknown(self):
        state = json.loads((RELEASE / 'templates' / 'STATE_SAVE.json').read_text())
        self.assertEqual(state['safety_state'], 'UNKNOWN')

    def test_selective_save_uses_prepared_not_sent(self):
        save = json.loads((RELEASE / 'templates' / 'SELECTIVE_SAVE.json').read_text())
        self.assertEqual(save['status'], 'PREPARED_NOT_SENT')

    def test_selective_save_privacy_audit_fields_are_fail_closed(self):
        save = json.loads((RELEASE / 'templates' / 'SELECTIVE_SAVE.json').read_text())
        self.assertEqual(save['schema_version'], 'P1AY_SELECTIVE_SAVE_02')
        self.assertEqual(save['consent']['status'], 'NOT_GRANTED')
        self.assertEqual(save['owner_confirmation']['status'], 'NOT_CONFIRMED')
        self.assertEqual(save['scope'], [])
        self.assertEqual(save['provenance'], [])
        self.assertEqual(save['transfer_evidence'], [])
        self.assertEqual(save['revocation']['status'], 'NOT_REQUESTED')

    def test_core_status_vocabulary_includes_prepared_not_sent(self):
        for lang, marker in (('ru', 'Различай '), ('en', 'Distinguish ')):
            core = (RELEASE / 'locales' / lang / 'CORE.txt').read_text()
            line = next(line for line in core.splitlines() if line.startswith(marker))
            self.assertIn('PREPARED_NOT_SENT', line, lang)

    def test_core_declares_safety_state_vocabulary(self):
        for lang in ('ru', 'en'):
            core = (RELEASE / 'locales' / lang / 'CORE.txt').read_text()
            vocabulary_lines = [line for line in core.splitlines()
                if 'safety_state' in line and all(value in line for value in ('UNKNOWN', 'ANALYZE', 'PAUSED'))]
            self.assertTrue(vocabulary_lines, lang)
            self.assertTrue(any('ACTIVE' in line and ('не является' in line or 'not a safety_state' in line)
                for line in vocabulary_lines), lang)

    def test_ru_core_references_packaged_reference_name(self):
        core = (RELEASE / 'locales' / 'ru' / 'CORE.txt').read_text()
        self.assertNotIn('REFERENCE_FULL', core)
        self.assertIn('REFERENCE.md', core)

    def test_communication_vocabulary_includes_proposed(self):
        communication = (RELEASE / 'templates' / 'COMMUNICATION.txt').read_text()
        status_line = next(line for line in communication.splitlines() if line.startswith('Statuses:'))
        self.assertIn('PROPOSED', status_line)


if __name__ == '__main__':
    unittest.main()
