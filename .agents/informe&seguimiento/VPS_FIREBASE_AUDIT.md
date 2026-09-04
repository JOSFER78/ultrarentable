# VPS / FIREBASE LEARNING AUDIT — BLOCKING CHECKLIST

Status: BLOCKED_REMOTE

## Objective
Recover and verify the historical learning system before designing or migrating any new learning authority.

## Required inspection on the VPS
1. Workspace: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
2. Search environment files, systemd units, scripts and old services for Firebase/Firestore configuration.
3. Identify Firebase project ID / Firestore database ID and exact client implementation used historically.
4. Enumerate collections/subcollections related to learning, failures, experiments, mutations, debates, strategies, versions, feedback and research.
5. Export a read-only recovery snapshot before writes or migrations.
6. Record document counts and date ranges for each relevant collection.
7. Identify whether the historical source is Firestore, Realtime Database or another Firebase-backed store.
8. Compare historical entities with `contracts/learning_contracts.py`.
9. Compare historical strategy/version records with `contracts/lineage_contracts.py` and `CanonicalStrategy`.
10. Determine whether SQLite `services/semantic_ai/learning_store.py` already contains a synchronized subset, a newer copy or an independent dataset.

## Prohibitions
- Do not delete Firebase data.
- Do not overwrite Firebase data.
- Do not fabricate missing records.
- Do not mark a migration complete without counts/hashes/reconciliation evidence.

## Exit criteria
PASS only when:
- source of historical learning is identified;
- recovery snapshot exists;
- relevant collections are inventoried;
- mapping to current contracts is documented;
- discrepancies are explicitly recorded;
- proposed synchronization authority is approved by the project source-of-truth documents.

Until then: PHASE 0 = BLOCKED_REMOTE.
