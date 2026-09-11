import asyncio
import os
import signal
import subprocess
import time
import uuid

os.chdir(r"c:\Users\Lenovo\Desktop\SIH2026\ULPF\backend")

# Patch queue idle time for faster test
with open('app/core/queue.py', 'r') as f:
    content = f.read()
content = content.replace('CLAIM_IDLE_MS = 30_000', 'CLAIM_IDLE_MS = 2_000')
with open('app/core/queue.py', 'w') as f:
    f.write(content)

try:
    from app.core.database import SessionLocal
    from app.models.domain import NormalizedEvent, DeadLetter, Trace, UnresolvedEvent
    from app.core.queue import EventRecord, event_queue

    async def main():
        db = SessionLocal()
        traces = db.query(Trace).count()
        ne = db.query(NormalizedEvent).count()
        dl = db.query(DeadLetter).count()
        ue = db.query(UnresolvedEvent).count()
        print(f'Before: Traces={traces}, NE={ne}, DL={dl}, UE={ue}')

        print('Publishing 10 events...')
        source_id = "test-source-queue"
        for i in range(10):
            trace_id = str(uuid.uuid4())
            t = Trace(trace_id=trace_id, source_id=source_id)
            db.add(t)
            record = EventRecord(
                trace_id=trace_id,
                source_id=source_id,
                payload=f'{{"test": {i}}}'.encode(),
                byte_length=100
            )
            await event_queue.publish(record)
        db.commit()

        print('Starting worker process...')
        worker = subprocess.Popen(['python', '-c', '''
import asyncio
from app.workers.processor import worker_loop
asyncio.run(worker_loop())
'''])
        
        # let it process a bit
        time.sleep(1.0)
        
        print('Killing worker process mid-processing...')
        worker.terminate()
        worker.wait()
        
        print('Waiting for CLAIM_IDLE_MS (2s) to pass...')
        time.sleep(3)
        
        print('Restarting worker process...')
        worker2 = subprocess.Popen(['python', '-c', '''
import asyncio
from app.workers.processor import worker_loop

async def run_briefly():
    task = asyncio.create_task(worker_loop())
    await asyncio.sleep(5)
    task.cancel()

try:
    asyncio.run(run_briefly())
except asyncio.CancelledError:
    pass
'''])
        worker2.wait()
        
        traces2 = db.query(Trace).count()
        ne2 = db.query(NormalizedEvent).count()
        dl2 = db.query(DeadLetter).count()
        ue2 = db.query(UnresolvedEvent).count()
        print(f'After: Traces={traces2}, NE={ne2}, DL={dl2}, UE={ue2}')
        print(f'Delta NE={ne2-ne}, DL={dl2-dl}, UE={ue2-ue}. Total handled: {(ne2-ne) + (dl2-dl) + (ue2-ue)} (Expected: 10)')
        if (ne2-ne) + (dl2-dl) + (ue2-ue) >= 10:
            print("TEST PASSED: Events were not dropped.")
        else:
            print("TEST FAILED: Some events were dropped.")
            
    asyncio.run(main())
finally:
    # restore queue
    with open('app/core/queue.py', 'r') as f:
        content = f.read()
    content = content.replace('CLAIM_IDLE_MS = 2_000', 'CLAIM_IDLE_MS = 30_000')
    with open('app/core/queue.py', 'w') as f:
        f.write(content)
