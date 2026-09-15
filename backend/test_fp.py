from app.core.database import SessionLocal
from app.models.domain import Rule, RuleVersion, RuleFingerprint
db = SessionLocal()
rules = db.query(Rule).all()
for r in rules:
    print(f"Rule: {r.rule_id} Status: {r.status}")
    fps = db.query(RuleFingerprint).filter(RuleFingerprint.rule_id == r.rule_id).all()
    print("  Fingerprints:", [fp.fingerprint for fp in fps])
    vs = db.query(RuleVersion).filter(RuleVersion.rule_id == r.rule_id).all()
    for v in vs:
        print(f"  Version: {v.id} Status: {v.status}")
