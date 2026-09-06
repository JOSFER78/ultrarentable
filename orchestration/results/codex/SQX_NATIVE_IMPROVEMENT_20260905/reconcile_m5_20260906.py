"""One reviewed recovery of completed native work; never starts a native retest."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

BASE = Path('/opt/SQX-headless/import')
sys.path.insert(0, str(BASE))
import sqx_native_improvement as engine
import sqx_improvement_stage as stage

candidate_id = 'faff40442f5b192e7ce6b324fbf8e09dd2d5d1bea67c0b234daac2830d6940e2'
review_id = '377bdbbde22bc088ad8a6c3eeae23517b429c952e8ac3bc1551c51a6caf92d20'
root = BASE / ('auto_improvement_' + candidate_id[:20])
manifest_path = root / 'manifest.json'
registry = BASE / 'automatic_improvement_jobs'
reviews = BASE / 'reviewed_improvement_jobs'

def read(path):
    return json.loads(path.read_text())

with (registry / 'stage.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    service = subprocess.run(['systemctl', 'show', 'sqx-improvement.service',
                              '--property=ActiveState', '--value'], check=True,
                             capture_output=True, text=True).stdout.strip()
    if service not in ('failed', 'inactive'):
        raise RuntimeError('Improvement service must be inactive')
    active = reviews / 'active.json'
    record = registry / (candidate_id + '.json')
    review_path = reviews / (review_id + '.json')
    claim, job, review = read(active), read(record), read(review_path)
    manifest = read(manifest_path)
    if (claim['identity'] != review_id or claim['manifest'] != str(manifest_path)
            or review['identity'] != review_id or review['manifest'] != str(manifest_path)
            or engine.reviewed_identity(manifest_path) != review_id
            or job['candidate']['identity'] != candidate_id or job['experiment'] != str(root)
            or job['state'] != 'NEEDS_RECONCILIATION'
            or review['state'] != 'NEEDS_RECONCILIATION'
            or manifest['source_sha256'] != job['candidate']['source_sha256']):
        raise ValueError('Recovery identity or state mismatch')
    if job['error'] != 'ValueError: Unsupported sample or non-executed native order':
        raise ValueError('This recovery only handles the reviewed canceled-order failure')
    source = Path(job['candidate']['source'])
    if engine.sha(source.read_bytes()) != manifest['source_sha256']:
        raise ValueError('Original selected source changed')
    before = engine.native_evidence(manifest_path)
    # Full completion and fresh exports are proven by the saved native artifacts.
    status = stage.native_call('-project action=status name=' + manifest['project'])
    if ('Estado del proyecto ' + manifest['project']) not in status:
        raise ValueError('Owned completed project not found')
    backup = root / 'reconciliation_before.json'
    with backup.open('x') as stream:
        json.dump({'job': job, 'review': review, 'claim': claim,
                   'assessment': read(root / 'assessment.json'), 'native_evidence': before,
                   'project_status': status}, stream, indent=2)
    assessment = engine.assess(manifest_path, root / 'retest.csv')
    if engine.native_evidence(manifest_path) != before:
        raise ValueError('Native artifacts changed during recovery')
    stage.archive_and_release(manifest_path, assessment)
    if read(active) != claim:
        raise ValueError('Active claim changed during recovery')
    completed = datetime.now(timezone.utc).isoformat()
    digest = engine.sha((root / 'assessment.json').read_bytes())
    common = dict(state='COMPLETED_NOT_FUNDING_CERTIFIED', completed_utc=completed,
                  assessment=str(root / 'assessment.json'), assessment_sha256=digest,
                  recovered_without_native_rerun=True)
    review.pop('error', None)
    review.update(common)
    engine.atomic_report(review_path, review)
    job.pop('error', None)
    job.update(common, decisions=assessment['decisions'],
               next_stage_candidates=assessment['next_stage_candidates'])
    engine.atomic_report(record, job)
    os.replace(active, reviews / (review_id + '_closed_claim.json'))
    engine.atomic_report(registry / 'latest.json', job)
    result = {'state': job['state'], 'recovered_without_native_rerun': True,
              'assessment_sha256': digest, 'decisions': assessment['decisions'],
              'next_stage_candidates': assessment['next_stage_candidates'],
              'archived_files': len(read(root / 'archive_verified.json')['files']),
              'active_claim_exists': active.exists()}
    engine.atomic_report(root / 'reconciliation_result.json', result)
    print(json.dumps(result, indent=2))
