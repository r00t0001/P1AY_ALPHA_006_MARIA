import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from p1ay_sync.engine import Engine,sign
from p1ay_sync.contracts import sha,migrate,identity_errors,read_json

IDENTITY={'user_id':'fixture-001','subject':'FIXTURE','exact_aliases':['Example']}
def save():return {'schema_version':'P1AY_SAVE_04','core_version':'ALPHA_007','owner':{'user_id':'fixture-001','subject':'FIXTURE','confirmed':True},'updated_at':'2026-09-23','safety_state':'PAUSED','sources':['fixture:source'],'quests':[],'facts':[],'permissions':[],'handshake':{'status':'PRESERVED'},'conflicts':[]}

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.e=Engine(self.root/'live.sqlite');self.e.initialize(IDENTITY)
        self.file=self.root/'source.json';self.file.write_text(json.dumps(save()))
        self.e.register_source('fixture-001','fixture:source',self.file)
        self.version=self.e.bootstrap('fixture-001',save(),'fixture:source')
    def tearDown(self):self.e.close();self.tmp.cleanup()
    def event(self,body=None):return self.e.make_event('fixture-001',body or save())
    def staged(self,body=None):
        wire=self.event(body);self.assertEqual(self.e.receive(wire),'STAGED')
        self.e.approve(wire['message']['event_id'],'fixture:source');return wire
    def test_round_trip_signed_peer_receipt(self):
        peer=Engine(self.root/'phone.sqlite','PHONE')
        try:
            peer.initialize(IDENTITY);peer.register_source('fixture-001','fixture:source',self.file)
            peer.bootstrap('fixture-001',save(),'fixture:source')
            peer.enroll_peer('fixture-001','COMPUTER',self.e.key('fixture-001','COMPUTER'))
            self.e.enroll_peer('fixture-001','PHONE',peer.key('fixture-001','PHONE'))
            body=save();body['facts'].append({'id':'fact-1','value':'synthetic'})
            wire=self.staged(body);eid=wire['message']['event_id']
            version=self.e.apply(eid)
            self.assertFalse(self.e.health('fixture-001')['peer_applied'])
            self.assertEqual(peer.receive(wire),'STAGED');peer.approve(eid,'fixture:source')
            self.assertEqual(peer.apply(eid),version)
            ack=json.loads(peer.db.execute("SELECT body FROM outbox WHERE kind='RECEIPT'").fetchone()[0])
            self.e.accept_receipt(ack);self.e.accept_receipt(ack)
            self.assertTrue(self.e.health('fixture-001')['peer_applied'])
        finally:peer.close()
    def test_retry_does_not_duplicate(self):
        wire=self.staged();eid=wire['message']['event_id']
        self.e.receive(wire);self.e.apply(eid);self.e.apply(eid)
        self.assertEqual(self.e.health('fixture-001')['events'],1)
        self.assertEqual(self.e.db.execute('SELECT count(*) FROM receipts').fetchone()[0],1)
    def test_id_collision(self):
        wire=self.staged();wire['message']['save']['facts']=['changed'];wire['message']['payload_hash']=sha(wire['message']['save'])
        wire['signature']=sign(wire['message'],self.e.key('fixture-001','COMPUTER'))
        with self.assertRaises(ValueError):self.e.receive(wire)
    def test_spoof_owner_and_unknown_source_rejected(self):
        body=save();body['owner']['user_id']='other'
        self.assertEqual(self.e.receive(self.event(body)),'REJECTED')
        body=save();body['sources']=['arbitrary claim']
        self.assertEqual(self.e.receive(self.event(body)),'REJECTED')
    def test_missing_structure_rejected(self):
        body=save();del body['quests']
        self.assertEqual(self.e.receive(self.event(body)),'REJECTED')
    def test_unapproved_apply_blocked(self):
        wire=self.event();self.e.receive(wire)
        with self.assertRaises(ValueError):self.e.apply(wire['message']['event_id'])
    def test_paused_and_handshake_preserved(self):
        for mode in ('resume','delete'):
            body=save()
            if mode=='resume':body['safety_state']='ANALYZE'
            else:del body['handshake']
            wire=self.staged(body)
            self.assertEqual(self.e.apply(wire['message']['event_id']),'CONFLICT')
            self.assertEqual(self.e.head('fixture-001'),self.version)
    def test_stale_base_at_receive_and_apply(self):
        a=save();a['facts']=[{'id':'a'}];b=save();b['facts']=[{'id':'b'}]
        first=self.staged(a);second=self.staged(b);third=self.event(b)
        self.e.apply(first['message']['event_id'])
        self.assertEqual(self.e.apply(second['message']['event_id']),'CONFLICT')
        self.assertEqual(self.e.receive(third),'CONFLICT')
    def test_rollback_on_failure(self):
        body=save();body['facts']=[{'id':'test'}];wire=self.staged(body)
        def crash():raise RuntimeError('simulated crash after version insert')
        with self.assertRaises(RuntimeError):self.e.apply(wire['message']['event_id'],crash)
        self.assertEqual(self.e.head('fixture-001'),self.version)
        self.assertEqual(self.e.db.execute('SELECT count(*) FROM versions').fetchone()[0],1)
        self.e.apply(wire['message']['event_id'])
    def test_process_death_atomic_recovery(self):
        body=save();body['facts']=[{'id':'crash'}];wire=self.staged(body);eid=wire['message']['event_id']
        code='from p1ay_sync.engine import Engine;import os,sys;e=Engine(sys.argv[1]);e.apply(sys.argv[2],lambda:os._exit(71))'
        result=subprocess.run([sys.executable,'-c',code,str(self.e.path),eid],capture_output=True)
        self.assertEqual(result.returncode,71)
        self.assertEqual(self.e.head('fixture-001'),self.version)
        self.assertEqual(self.e.db.execute('SELECT count(*) FROM versions').fetchone()[0],1)
        self.e.apply(eid)
    def test_backup_restore_and_tamper(self):
        dest=self.root/'backup.sqlite';receipt=self.e.backup(dest)
        Engine.restore(dest,self.root/'restored.sqlite',receipt['sha256'])
        restored=Engine(self.root/'restored.sqlite')
        try:self.assertEqual(restored.head('fixture-001'),self.version)
        finally:restored.close()
        with self.assertRaises(ValueError):Engine.restore(dest,self.root/'bad.sqlite','0'*64)
        with self.assertRaises(ValueError):Engine.restore(dest,self.e.path,receipt['sha256'])
    def test_earlier_panel_edits_detected_and_deduplicated(self):
        self.assertEqual(self.e.observe_panel('Conflicts',[['CF-1','OPEN'],['CF-2','OPEN']]),2)
        self.assertEqual(self.e.observe_panel('Conflicts',[['CF-1','RESOLVED'],['CF-2','OPEN']]),1)
        self.assertEqual(self.e.observe_panel('Conflicts',[['CF-1','RESOLVED'],['CF-2','OPEN']]),0)
    def test_panel_contains_no_private_payload_or_keys(self):
        text=json.dumps(self.e.health('fixture-001'))
        for token in ('handshake','fixture:source',self.e.key('fixture-001','COMPUTER')):self.assertNotIn(token,text)
    def test_lossless_legacy_migration(self):
        for schema in ('P1AY_SAVE_02','P1AY_SAVE_03','P1AY_SAVE_04'):
            body=save();body['schema_version']=schema;body['unknown_extension']={'keep':True}
            wrapped=migrate(body,IDENTITY)
            self.assertEqual(wrapped['payload'],body);self.assertEqual(wrapped['source_hash'],sha(body))
        body=save();body['schema_version']='FUTURE'
        with self.assertRaises(ValueError):migrate(body,IDENTITY)
    def test_bad_signature_and_unregistered_peer(self):
        wire=self.event();wire['signature']='0'*64
        with self.assertRaises(ValueError):self.e.receive(wire)
        wire=self.event();wire['message']['sender_device']='UNREGISTERED'
        with self.assertRaises(ValueError):self.e.receive(wire)
    def test_source_cannot_be_silently_replaced(self):
        self.file.write_text('{}')
        with self.assertRaises(ValueError):self.e.register_source('fixture-001','fixture:source',self.file)
    def test_bootstrap_requires_matching_source_content(self):
        other=Engine(self.root/'other.sqlite')
        try:
            other.initialize(IDENTITY);other.register_source('fixture-001','fixture:source',self.file)
            body=save();body['facts']=['invented']
            with self.assertRaises(ValueError):other.bootstrap('fixture-001',body,'fixture:source')
        finally:other.close()
    def test_duplicate_json_keys_rejected(self):
        self.file.write_text('{"owner":1,"owner":2}')
        with self.assertRaises(ValueError):read_json(self.file)
    def test_contradictory_alias(self):
        body=save();body['owner']['alias']='NOT_THE_OWNER'
        self.assertTrue(identity_errors(body,IDENTITY))

if __name__=='__main__':unittest.main()
