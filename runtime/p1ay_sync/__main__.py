"""Run with python -m p1ay_sync. Commands do not transmit to external services."""
import argparse
import json
from pathlib import Path
from .contracts import read_json, migrate
from .engine import Engine


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',required=True,type=Path)
    parser.add_argument('--device',default='COMPUTER')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('init');p.add_argument('identity',type=Path)
    p=sub.add_parser('source');p.add_argument('owner');p.add_argument('ref');p.add_argument('file',type=Path)
    p=sub.add_parser('bootstrap');p.add_argument('owner');p.add_argument('ref');p.add_argument('file',type=Path)
    p=sub.add_parser('propose');p.add_argument('owner');p.add_argument('file',type=Path);p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('receive');p.add_argument('file',type=Path)
    p=sub.add_parser('approve');p.add_argument('event_id');p.add_argument('--evidence',required=True)
    p=sub.add_parser('apply');p.add_argument('event_id')
    p=sub.add_parser('ack');p.add_argument('file',type=Path)
    p=sub.add_parser('enroll');p.add_argument('owner');p.add_argument('peer');p.add_argument('key_file',type=Path)
    p=sub.add_parser('resolve');p.add_argument('conflict_id');p.add_argument('--evidence',required=True)
    p=sub.add_parser('observe-panel');p.add_argument('panel');p.add_argument('file',type=Path)
    p=sub.add_parser('status');p.add_argument('owner')
    p=sub.add_parser('export-outbox');p.add_argument('owner');p.add_argument('directory',type=Path)
    p=sub.add_parser('backup');p.add_argument('destination',type=Path)
    p=sub.add_parser('restore');p.add_argument('source',type=Path);p.add_argument('--sha256',required=True)
    p=sub.add_parser('migrate');p.add_argument('owner');p.add_argument('file',type=Path);p.add_argument('destination',type=Path)
    args=parser.parse_args()
    def create(path,data):
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        import os
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,'w') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
    if args.command=='restore':
        Engine.restore(args.source,args.db,args.sha256);print('{"status":"RESTORED"}');return
    engine=Engine(args.db,args.device)
    result=None
    try:
        if args.command=='init':result=engine.initialize(read_json(args.identity))
        elif args.command=='source':result=engine.register_source(args.owner,args.ref,args.file)
        elif args.command=='bootstrap':result=engine.bootstrap(args.owner,read_json(args.file),args.ref)
        elif args.command=='propose':
            wire=engine.make_event(args.owner,read_json(args.file));result=engine.receive(wire);create(args.output,wire)
        elif args.command=='receive':result=engine.receive(read_json(args.file))
        elif args.command=='approve':result=engine.approve(args.event_id,args.evidence)
        elif args.command=='apply':result=engine.apply(args.event_id)
        elif args.command=='ack':result=engine.accept_receipt(read_json(args.file))
        elif args.command=='enroll':result=engine.enroll_peer(args.owner,args.peer,args.key_file.read_text().strip())
        elif args.command=='resolve':result=engine.resolve_conflict(args.conflict_id,args.evidence)
        elif args.command=='observe-panel':result=engine.observe_panel(args.panel,read_json(args.file))
        elif args.command=='status':result=engine.health(args.owner)
        elif args.command=='backup':result=engine.backup(args.destination)
        elif args.command=='migrate':
            result=migrate(read_json(args.file),engine.identity(args.owner));create(args.destination,result)
            result={'status':'STAGED_NOT_APPLIED','output':str(args.destination)}
        elif args.command=='export-outbox':
            # IDs never become filesystem paths. Repeated export verifies bytes before reuse.
            import hashlib
            result=[]
            for row in engine.db.execute("SELECT message_id,body FROM outbox WHERE owner_id=? AND status='PENDING'",(args.owner,)):
                path=args.directory/(hashlib.sha256(row[0].encode()).hexdigest()+'.json')
                if path.exists():
                    if read_json(path)!=json.loads(row[1]):raise ValueError('existing outbox file differs')
                else:create(path,json.loads(row[1]))
                result.append(str(path))
        print(json.dumps({'result':result},ensure_ascii=False,indent=2))
    finally:engine.close()

if __name__=='__main__':main()
