import json
import subprocess
from pathlib import Path

from aegis_os.attestation import generate_signing_key, sign_distribution_bundle
from aegis_os.distribution import build_distribution_bundle
from aegis_os.transparency import append_transparency_event, build_trust_report, verify_transparency_ledger
from aegis_os.trust import initialize_trust_policy, revoke_trust_key


def _repo(tmp_path: Path) -> Path:
    root=tmp_path/'repo'; root.mkdir()
    subprocess.run(['git','init','-q'],cwd=root,check=True)
    subprocess.run(['git','config','user.email','x@y.z'],cwd=root,check=True)
    subprocess.run(['git','config','user.name','Test'],cwd=root,check=True)
    (root/'README.md').write_text('AEGIS\n')
    subprocess.run(['git','add','.'],cwd=root,check=True)
    subprocess.run(['git','commit','-qm','base'],cwd=root,check=True)
    return root


def _release(tmp_path: Path):
    priv=tmp_path/'private.pem'; pub=tmp_path/'public.pem'
    key_id=generate_signing_key(priv,pub)
    policy=tmp_path/'policy.json'; initialize_trust_policy(pub,policy)
    bundle=build_distribution_bundle(tmp_path/'dist',root=_repo(tmp_path))
    att,sig=sign_distribution_bundle(bundle,priv)
    return key_id,policy,bundle,att,sig


def test_append_only_hash_chain_and_verification(tmp_path: Path):
    ledger=tmp_path/'ledger.jsonl'
    first=append_transparency_event(ledger,'release-published','v1.2.0',{'commit':'abc'})
    second=append_transparency_event(ledger,'key-rotated','ed25519:new',{'predecessor':'old'})
    result=verify_transparency_ledger(ledger)
    assert result.status=='verified' and result.event_count==2
    assert second.previous_hash==first.event_hash


def test_tampered_ledger_is_rejected(tmp_path: Path):
    ledger=tmp_path/'ledger.jsonl'
    append_transparency_event(ledger,'release-published','v1.2.0',{'commit':'abc'})
    data=json.loads(ledger.read_text()); data['details']['commit']='tampered'
    ledger.write_text(json.dumps(data)+'\n')
    assert verify_transparency_ledger(ledger).status=='invalid'


def test_trusted_report_with_verified_ledger(tmp_path: Path):
    _,policy,bundle,att,sig=_release(tmp_path)
    ledger=tmp_path/'ledger.jsonl'; append_transparency_event(ledger,'release-published',bundle.name,{'sha256':'recorded'})
    report=build_trust_report(bundle,att,sig,policy,ledger)
    assert report.overall_verdict=='TRUSTED'
    assert report.transparency=='verified'


def test_revoked_signer_report_is_rejected(tmp_path: Path):
    key_id,policy,bundle,att,sig=_release(tmp_path)
    revoke_trust_key(policy,key_id,'compromise')
    report=build_trust_report(bundle,att,sig,policy)
    assert report.overall_verdict=='REJECTED'
    assert 'signing-key-revoked' in report.reasons


def test_report_is_exportable_json(tmp_path: Path):
    _,policy,bundle,att,sig=_release(tmp_path)
    report=build_trust_report(bundle,att,sig,policy)
    payload=json.loads(report.to_json())
    assert payload['overall_verdict']=='TRUSTED'
