"""Build an immutable, deterministic, allowlisted JULIA 0.7.2 bundle."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,zipfile
from pathlib import Path,PurePosixPath
from release_files import FILES,MANIFEST,RELEASE,NAME,VERSION,ARTIFACT_REVISION
from verify_release import verify,VerificationError
ROOT=Path(__file__).resolve().parents[1]

def validate_zip_members(z):
    names=z.namelist()
    if len(names)!=len(set(names)) or len(names)!=len({n.casefold() for n in names}):
        raise VerificationError('Duplicate or case-colliding ZIP members')
    if set(names)!=set(FILES)|{MANIFEST}:
        raise VerificationError('ZIP_ALLOWLIST_MISMATCH')
    for i in z.infolist():
        p=PurePosixPath(i.filename)
        if p.is_absolute() or '..' in p.parts or '\\' in i.filename:
            raise VerificationError('Unsafe ZIP path')
        mode=(i.external_attr>>16)&0o170000
        if mode not in (0,0o100000):raise VerificationError('Non-regular ZIP member')
        if i.file_size>5_000_000:raise VerificationError('Oversized ZIP member')
    if z.testzip() is not None:raise VerificationError('ZIP CRC failure')

def tests(root):
    env=os.environ.copy();env.pop('P1AY_REGRESSION_ROOT',None);env['PYTHONPATH']=str(root/'tools')
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tools','-p','test_*.py'],cwd=root,env=env,capture_output=True,text=True)
    if p.returncode:raise VerificationError(p.stdout+p.stderr)
    return p.stdout+p.stderr

def runtime_tests(root):
    env=os.environ.copy();env['PYTHONPATH']=str(root/'runtime')
    p=subprocess.run([sys.executable,'-m','unittest','discover','-s','runtime/tests','-p','test_*.py'],cwd=root,env=env,capture_output=True,text=True)
    if p.returncode:raise VerificationError(p.stdout+p.stderr)
    return p.stdout+p.stderr

def build(output):
    result=verify(ROOT,require_manifest=False)
    source_log=tests(ROOT)
    runtime_source_log=runtime_tests(ROOT)
    if output.exists():raise VerificationError('Choose a new output directory; builds are immutable')
    output.mkdir(parents=True);stage=output/'repository';stage.mkdir()
    entries=[]
    for name in FILES:
        src=ROOT/name;dest=stage/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dest);data=dest.read_bytes()
        entries.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    manifest={'schema_version':'P1AY_RELEASE_MANIFEST_02','release':'ALPHA_007','version':VERSION,'artifact_revision':ARTIFACT_REVISION,'files':entries,'self_reference':{'path':MANIFEST,'hashed_in_files':False},'verification_scope':'FILE_AND_DECLARED_RULE_CONTRACT_NOT_LIVE_MODEL_PROOF'}
    (stage/MANIFEST).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    verify(stage,require_manifest=True)
    archive=output/(NAME+'.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(FILES+[MANIFEST]):
            info=zipfile.ZipInfo(name,date_time=(2026,9,24,0,0,0));info.external_attr=0o100644<<16
            z.writestr(info,(stage/name).read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with tempfile.TemporaryDirectory() as d,zipfile.ZipFile(archive) as z:
        validate_zip_members(z);z.extractall(d);verify(Path(d),require_manifest=True)
        extracted_log=tests(Path(d))
        runtime_extracted_log=runtime_tests(Path(d))
        opt=subprocess.run([sys.executable,'-O',str(Path(d)/'tools/verify_release.py')],cwd=d,capture_output=True,text=True)
        if opt.returncode:raise VerificationError(opt.stdout+opt.stderr)
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    (output/(archive.name+'.sha256')).write_text(digest+'  '+archive.name+'\n')
    (output/'SOURCE_TESTS.txt').write_text(source_log)
    (output/'EXTRACTED_TESTS.txt').write_text(extracted_log)
    (output/'RUNTIME_SOURCE_TESTS.txt').write_text(runtime_source_log)
    (output/'RUNTIME_EXTRACTED_TESTS.txt').write_text(runtime_extracted_log)
    result.update(version=VERSION,archive=archive.name,sha256=digest,zip_members=len(FILES)+1,zip_crc='PASS',extracted_verification='PASS',optimized_verification='PASS',external_review='PENDING',computer_writeback='NOT_PERFORMED')
    (output/'BUILD_RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    build(ap.parse_args().output.resolve())
