from app.core.database import SessionLocal
from app.models.domain import RuleTestCase, RuleVersion

db = SessionLocal()
rv = db.query(RuleVersion).filter(RuleVersion.id == "44144c44-eed0-48ae-83ed-820cf8e3917a").first()
print("Rule:", rv.rule_id if rv else None)
tcs = db.query(RuleTestCase).filter(RuleTestCase.rule_version_id == "44144c44-eed0-48ae-83ed-820cf8e3917a").all()
for tc in tcs:
    print(repr(tc.raw_sample))
