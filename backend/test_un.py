from app.core.database import SessionLocal
from app.models.domain import UnresolvedEvent

db = SessionLocal()
evs = db.query(UnresolvedEvent).filter(UnresolvedEvent.source_id == "paloalto").all()
for ev in evs[:5]:
    print(repr(ev.raw_payload))
