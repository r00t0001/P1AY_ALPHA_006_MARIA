"""SQLite inbox/outbox and immutable versions. No automatic external side effects."""
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import uuid
from .contracts import canonical, sha, identity_errors, save_errors, continuity_errors


def now():return datetime.now(timezone.utc).isoformat()

def sign(message,key):
    return hmac.new(bytes.fromhex(key), canonical(message).encode(), hashlib.sha256).hexdigest()

DDL = '''
CREATE TABLE IF NOT EXISTS identities(owner_id TEXT PRIMARY KEY, identity TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS peers(owner_id TEXT, device TEXT, secret TEXT NOT NULL, PRIMARY KEY(owner_id,device));
CREATE TABLE IF NOT EXISTS sources(owner_id TEXT, ref TEXT, hash TEXT NOT NULL, payload_hash TEXT, verified_at TEXT NOT NULL, PRIMARY KEY(owner_id,ref));
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT UNIQUE NOT NULL,owner_id TEXT NOT NULL,device TEXT NOT NULL,base_version TEXT,hash TEXT NOT NULL,envelope TEXT NOT NULL,status TEXT NOT NULL,detail TEXT NOT NULL,received_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS versions(version TEXT PRIMARY KEY,owner_id TEXT NOT NULL,parent TEXT,payload TEXT NOT NULL,created_at TEXT NOT NULL,event_id TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS heads(owner_id TEXT PRIMARY KEY,version TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals(event_id TEXT PRIMARY KEY,event_hash TEXT NOT NULL,evidence_ref TEXT NOT NULL,approved_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS conflicts(conflict_id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,event_id TEXT NOT NULL,reason TEXT NOT NULL,base_version TEXT,local_version TEXT,status TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS conflict_revisions(seq INTEGER PRIMARY KEY AUTOINCREMENT,conflict_id TEXT NOT NULL,status TEXT NOT NULL,evidence_ref TEXT,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS receipts(receipt_id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,device TEXT NOT NULL,version TEXT NOT NULL,event_id TEXT NOT NULL,body TEXT NOT NULL,received_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS outbox(message_id TEXT PRIMARY KEY,owner_id TEXT NOT NULL,kind TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY,started_at TEXT NOT NULL,completed_at TEXT,result TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS panel_rows(panel TEXT,row_id TEXT,row_hash TEXT NOT NULL,body TEXT NOT NULL,seen_at TEXT NOT NULL,PRIMARY KEY(panel,row_id));
CREATE TABLE IF NOT EXISTS panel_changes(seq INTEGER PRIMARY KEY AUTOINCREMENT,panel TEXT,row_id TEXT,row_hash TEXT,body TEXT NOT NULL,seen_at TEXT NOT NULL);
'''

class Engine:
    def __init__(self,path,device='COMPUTER'):
        self.path=Path(path);self.device=device
        if self.path.is_symlink():raise ValueError('database symlink forbidden')
        self.path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        # Restrict creation of SQLite sidecars too. Existing parent directories are not chmodded.
        oldmask=os.umask(0o077)
        try:
            self.db=sqlite3.connect(self.path,timeout=30,isolation_level=None)
            os.chmod(self.path,0o600)
            self.db.row_factory=sqlite3.Row
            self.db.execute('PRAGMA journal_mode=WAL')
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('PRAGMA foreign_keys=ON')
            version=self.db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0,1):raise ValueError('unsupported database version')
            if version==0 and self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table'").fetchone():raise ValueError('unrecognized existing database')
            self.db.executescript(DDL)
            self.db.execute('PRAGMA user_version=1')
        finally:os.umask(oldmask)

    def close(self):self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK');raise

    def initialize(self,identity):
        owner=identity['user_id'];encoded=canonical(identity)
        with self.transaction():
            row=self.db.execute('SELECT identity FROM identities WHERE owner_id=?',(owner,)).fetchone()
            if row and row[0]!=encoded:raise ValueError('identity changed; explicit reconciliation required')
            self.db.execute('INSERT OR IGNORE INTO identities VALUES (?,?)',(owner,encoded))
            self.db.execute('INSERT OR IGNORE INTO peers VALUES (?,?,?)',(owner,self.device,secrets.token_hex(32)))

    def enroll_peer(self,owner,device,key):
        if device==self.device or len(bytes.fromhex(key))!=32:raise ValueError('invalid peer enrollment')
        self.identity(owner)
        with self.transaction():
            row=self.db.execute('SELECT secret FROM peers WHERE owner_id=? AND device=?',(owner,device)).fetchone()
            if row and row[0]!=key:raise ValueError('key rotation requires explicit migration')
            self.db.execute('INSERT OR IGNORE INTO peers VALUES (?,?,?)',(owner,device,key))

    def identity(self,owner):
        row=self.db.execute('SELECT identity FROM identities WHERE owner_id=?',(owner,)).fetchone()
        if not row:raise ValueError('unregistered owner')
        return json.loads(row[0])

    def key(self,owner,device):
        row=self.db.execute('SELECT secret FROM peers WHERE owner_id=? AND device=?',(owner,device)).fetchone()
        if not row:raise ValueError('unregistered device; no authenticated transport')
        return row[0]

    def register_source(self,owner,ref,path):
        self.identity(owner)
        source=Path(path)
        if source.is_symlink() or not source.is_file():raise ValueError('source must be a regular local evidence file')
        raw=source.read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        try:payload_hash=sha(json.loads(raw))
        except (ValueError,UnicodeDecodeError):payload_hash=None
        with self.transaction():
            prior=self.db.execute('SELECT hash FROM sources WHERE owner_id=? AND ref=?',(owner,ref)).fetchone()
            if prior and prior[0]!=digest:raise ValueError('source revision changed; register a new reference')
            self.db.execute('INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?)',(owner,ref,digest,payload_hash,now()))
        return digest

    def source_known(self,owner,ref):
        return bool(self.db.execute('SELECT 1 FROM sources WHERE owner_id=? AND ref=?',(owner,ref)).fetchone())

    def head(self,owner):
        row=self.db.execute('SELECT version FROM heads WHERE owner_id=?',(owner,)).fetchone()
        return row[0] if row else None

    def payload(self,version):
        row=self.db.execute('SELECT payload FROM versions WHERE version=?',(version,)).fetchone()
        if not row:raise ValueError('unknown version')
        return json.loads(row[0])

    def bootstrap(self,owner,payload,source_ref):
        """Preserve an already-authoritative local snapshot, including old schema defects."""
        self.identity(owner)
        if not isinstance(payload.get('owner'),dict) or payload['owner'].get('user_id')!=owner:raise ValueError('bootstrap owner mismatch')
        if not self.source_known(owner,source_ref):raise ValueError('bootstrap evidence not registered')
        source=self.db.execute('SELECT hash,payload_hash FROM sources WHERE owner_id=? AND ref=?',(owner,source_ref)).fetchone()
        source_hash=source[0]
        if source[1]!=sha(payload):raise ValueError('bootstrap payload does not match registered evidence')
        # Caller additionally verifies raw file bytes; normalized content version is independent.
        version=sha({'owner_id':owner,'payload':payload})
        with self.transaction():
            existing=self.head(owner)
            if existing and existing!=version:raise ValueError('already bootstrapped; use reviewed event')
            self.db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?,?,?,?)',(version,owner,None,canonical(payload),now(),'bootstrap:'+source_hash))
            self.db.execute('INSERT OR IGNORE INTO heads VALUES (?,?)',(owner,version))
        return version

    def make_event(self,owner,payload,event_id=None):
        msg={'schema_version':'P1AY_SYNC_EVENT_01','event_id':event_id or str(uuid.uuid4()),'owner_id':owner,
             'sender_device':self.device,'base_version':self.head(owner),'payload_hash':sha(payload),'save':payload,'created_at':now()}
        return {'message':msg,'signature':sign(msg,self.key(owner,self.device))}

    def receive(self,wire):
        if len(canonical(wire).encode())>8_000_000:raise ValueError('event size limit')
        msg=wire['message']
        required={'schema_version','event_id','owner_id','sender_device','base_version','payload_hash','save','created_at'}
        if set(msg)!=required or msg['schema_version']!='P1AY_SYNC_EVENT_01':raise ValueError('invalid event envelope')
        if any(not isinstance(msg[k],str) or not msg[k] for k in ('event_id','owner_id','sender_device','payload_hash','created_at')):raise ValueError('invalid event field')
        if msg['base_version'] is not None and not isinstance(msg['base_version'],str):raise ValueError('invalid base')
        owner=msg['owner_id'];identity=self.identity(owner)
        if not hmac.compare_digest(wire.get('signature',''),sign(msg,self.key(owner,msg['sender_device']))):raise ValueError('invalid device signature')
        payload=msg['save']
        if sha(payload)!=msg['payload_hash']:raise ValueError('payload hash mismatch')
        digest=sha(msg)
        with self.transaction():
            old=self.db.execute('SELECT hash,status FROM events WHERE event_id=?',(msg['event_id'],)).fetchone()
            if old:
                if old['hash']!=digest:raise ValueError('event ID reused with different bytes')
                return old['status']
            errors=save_errors(payload)
            errors+=identity_errors(payload,identity) if isinstance(payload,dict) else ['invalid SAVE']
            if isinstance(payload,dict) and isinstance(payload.get('sources'),list):
                errors += ['unverified source reference' for ref in payload['sources'] if not isinstance(ref,str) or not self.source_known(owner,ref)]
            status='REJECTED' if errors else 'STAGED'
            current=self.head(owner)
            if not errors and current!=msg['base_version']:status='CONFLICT';errors=['base version differs from local head']
            self.db.execute('INSERT INTO events(event_id,owner_id,device,base_version,hash,envelope,status,detail,received_at) VALUES (?,?,?,?,?,?,?,?,?)',
                (msg['event_id'],owner,msg['sender_device'],msg['base_version'],digest,canonical(wire),status,canonical(errors),now()))
            if status=='CONFLICT':self._conflict(msg,current,'STALE_BASE')
            if msg['sender_device']==self.device and status=='STAGED':
                self.db.execute('INSERT INTO outbox VALUES (?,?,?,?,?,?)',(msg['event_id'],owner,'EVENT',canonical(wire),'PENDING',now()))
        return status

    def _conflict(self,msg,current,reason):
        cid='conflict:'+msg['event_id']+':'+reason
        if self.db.execute('SELECT 1 FROM conflicts WHERE conflict_id=?',(cid,)).fetchone():return
        self.db.execute('INSERT INTO conflicts VALUES (?,?,?,?,?,?,?,?)',(cid,msg['owner_id'],msg['event_id'],reason,msg['base_version'],current,'OPEN',now()))
        self.db.execute('INSERT INTO conflict_revisions(conflict_id,status,evidence_ref,created_at) VALUES (?,?,?,?)',(cid,'OPEN',None,now()))

    def approve(self,event_id,evidence_ref):
        with self.transaction():
            event=self.db.execute('SELECT * FROM events WHERE event_id=?',(event_id,)).fetchone()
            if not event or event['status']!='STAGED':raise ValueError('only validated staged events may be approved')
            if not self.source_known(event['owner_id'],evidence_ref):raise ValueError('approval evidence not registered')
            self.db.execute('INSERT OR IGNORE INTO approvals VALUES (?,?,?,?)',(event_id,event['hash'],evidence_ref,now()))

    def apply(self,event_id,failpoint=None):
        with self.transaction():
            event=self.db.execute('SELECT * FROM events WHERE event_id=?',(event_id,)).fetchone()
            if not event:raise ValueError('event not found')
            if event['status']=='APPLIED':return sha({'owner_id':event['owner_id'],'payload':json.loads(event['envelope'])['message']['save']})
            if event['status']!='STAGED':raise ValueError('event is not validated/staged')
            approval=self.db.execute('SELECT * FROM approvals WHERE event_id=?',(event_id,)).fetchone()
            if not approval or approval['event_hash']!=event['hash']:raise ValueError('explicit evidence-bound approval required')
            msg=json.loads(event['envelope'])['message'];owner=event['owner_id'];current=self.head(owner)
            if current!=event['base_version']:
                self._conflict(msg,current,'STALE_BASE_AT_APPLY')
                self.db.execute("UPDATE events SET status='CONFLICT' WHERE event_id=?",(event_id,))
                return 'CONFLICT'
            errors=continuity_errors(self.payload(current),msg['save']) if current else []
            if errors:
                self._conflict(msg,current,'CONTINUITY')
                self.db.execute("UPDATE events SET status='CONFLICT',detail=? WHERE event_id=?",(canonical(errors),event_id))
                return 'CONFLICT'
            version=sha({'owner_id':owner,'payload':msg['save']})
            self.db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?,?,?,?)',(version,owner,current,canonical(msg['save']),now(),event_id))
            if failpoint:failpoint()
            self.db.execute('INSERT INTO heads VALUES (?,?) ON CONFLICT(owner_id) DO UPDATE SET version=excluded.version',(owner,version))
            self.db.execute("UPDATE events SET status='APPLIED' WHERE event_id=?",(event_id,))
            body={'schema_version':'P1AY_SYNC_RECEIPT_01','receipt_id':'ack:'+event_id+':'+self.device,'owner_id':owner,'device':self.device,'event_id':event_id,'version':version,'status':'APPLIED','created_at':now()}
            wire={'message':body,'signature':sign(body,self.key(owner,self.device))}
            self.db.execute('INSERT INTO receipts VALUES (?,?,?,?,?,?,?)',(body['receipt_id'],owner,self.device,version,event_id,canonical(wire),now()))
            self.db.execute('INSERT INTO outbox VALUES (?,?,?,?,?,?)',(body['receipt_id'],owner,'RECEIPT',canonical(wire),'PENDING',now()))
            return version

    def accept_receipt(self,wire):
        msg=wire['message']
        if set(msg)!={'schema_version','receipt_id','owner_id','device','event_id','version','status','created_at'} or msg['schema_version']!='P1AY_SYNC_RECEIPT_01' or msg['status']!='APPLIED':raise ValueError('invalid receipt')
        if msg['device']==self.device:raise ValueError('peer receipt required')
        if not hmac.compare_digest(wire.get('signature',''),sign(msg,self.key(msg['owner_id'],msg['device']))):raise ValueError('receipt signature invalid')
        with self.transaction():
            event=self.db.execute('SELECT * FROM events WHERE event_id=?',(msg['event_id'],)).fetchone()
            if not event or event['owner_id']!=msg['owner_id'] or event['status']!='APPLIED':raise ValueError('receipt has no applied local event')
            expected=sha({'owner_id':event['owner_id'],'payload':json.loads(event['envelope'])['message']['save']})
            if msg['version']!=expected:raise ValueError('receipt version mismatch')
            old=self.db.execute('SELECT body FROM receipts WHERE receipt_id=?',(msg['receipt_id'],)).fetchone()
            if old and old[0]!=canonical(wire):raise ValueError('receipt ID collision')
            self.db.execute('INSERT OR IGNORE INTO receipts VALUES (?,?,?,?,?,?,?)',(msg['receipt_id'],msg['owner_id'],msg['device'],msg['version'],msg['event_id'],canonical(wire),now()))
            self.db.execute("UPDATE outbox SET status='PEER_APPLIED' WHERE message_id=?",(msg['event_id'],))
            return 'PEER_APPLIED'

    def resolve_conflict(self,cid,evidence_ref):
        with self.transaction():
            row=self.db.execute('SELECT * FROM conflicts WHERE conflict_id=?',(cid,)).fetchone()
            if not row or not self.source_known(row['owner_id'],evidence_ref):raise ValueError('resolution evidence required')
            if row['status']=='RESOLVED':return
            self.db.execute("UPDATE conflicts SET status='RESOLVED' WHERE conflict_id=?",(cid,))
            self.db.execute('INSERT INTO conflict_revisions(conflict_id,status,evidence_ref,created_at) VALUES (?,?,?,?)',(cid,'RESOLVED',evidence_ref,now()))
            # Resolution never applies the rejected/stale payload; create a new rebased event.

    def observe_panel(self,panel,rows):
        """Snapshot all ID-bearing rows, including old conflicts; no canonical merge."""
        changed=0
        with self.transaction():
            ids=[r[0] for r in rows if r and r[0]]
            if len(ids)!=len(set(ids)):raise ValueError('duplicate panel row IDs')
            for row in rows:
                if not row or not row[0]:continue
                key=row[0];digest=sha(row)
                old=self.db.execute('SELECT row_hash FROM panel_rows WHERE panel=? AND row_id=?',(panel,key)).fetchone()
                if old and old[0]==digest:continue
                changed+=1
                self.db.execute('INSERT INTO panel_changes(panel,row_id,row_hash,body,seen_at) VALUES (?,?,?,?,?)',(panel,key,digest,canonical(row),now()))
                self.db.execute('INSERT INTO panel_rows VALUES (?,?,?,?,?) ON CONFLICT(panel,row_id) DO UPDATE SET row_hash=excluded.row_hash,body=excluded.body,seen_at=excluded.seen_at',(panel,key,digest,canonical(row),now()))
            # Removed rows are tombstones in the observation history, not deletions of evidence.
            for old in self.db.execute('SELECT row_id FROM panel_rows WHERE panel=?',(panel,)).fetchall():
                if old[0] not in ids:
                    self.db.execute('INSERT INTO panel_changes(panel,row_id,row_hash,body,seen_at) VALUES (?,?,?,?,?)',(panel,old[0],None,'null',now()))
                    self.db.execute('DELETE FROM panel_rows WHERE panel=? AND row_id=?',(panel,old[0]));changed+=1
        return changed

    def health(self,owner):
        self.identity(owner);head=self.head(owner)
        count=lambda table,where='',args=():self.db.execute('SELECT count(*) FROM '+table+' WHERE owner_id=? '+where,(owner,*args)).fetchone()[0]
        return {'schema_version':'P1AY_SYNC_HEALTH_01','owner_id':owner,'content_version':head,
                'events':count('events'),'staged':count('events',"AND status='STAGED'"),'rejected':count('events',"AND status='REJECTED'"),
                'open_conflicts':count('conflicts',"AND status='OPEN'"),'pending_outbox':count('outbox',"AND status='PENDING'"),
                'peer_applied':bool(self.db.execute('SELECT 1 FROM receipts WHERE owner_id=? AND version=? AND device!=?',(owner,head,self.device)).fetchone()),
                'status':'PEER_CONFIRMED' if self.db.execute('SELECT 1 FROM receipts WHERE owner_id=? AND version=? AND device!=?',(owner,head,self.device)).fetchone() else 'LOCAL_ONLY_OR_PEER_PENDING'}

    def backup(self,destination):
        destination=Path(destination)
        if destination.exists():raise ValueError('backup destination must be new')
        destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd=os.open(destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
        target=sqlite3.connect(destination)
        try:
            self.db.backup(target)
            if target.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('backup integrity failure')
        finally:target.close()
        return {'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'bytes':destination.stat().st_size}

    @staticmethod
    def restore(source,destination,expected_hash):
        source=Path(source);destination=Path(destination)
        if hashlib.sha256(source.read_bytes()).hexdigest()!=expected_hash:raise ValueError('restore hash mismatch')
        if destination.exists():raise ValueError('restore never overwrites existing state')
        original=sqlite3.connect('file:'+str(source.resolve())+'?mode=ro',uri=True)
        try:
            if original.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('bad source DB')
            if original.execute('PRAGMA user_version').fetchone()[0]!=1:raise ValueError('unsupported DB version')
            destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            fd=os.open(destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
            restored=sqlite3.connect(destination)
            try:original.backup(restored)
            finally:restored.close()
        finally:original.close()
