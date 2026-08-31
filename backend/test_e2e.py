import urllib.request
import json
import uuid

BASE = 'http://127.0.0.1:8000/api/v1'

def post_json(path, data):
    req = urllib.request.Request(
        f'{BASE}{path}',
        data=json.dumps(data).encode(),
        headers={
            'Content-Type': 'application/json',
            'X-ULPF-User': 'admin',
            'X-ULPF-Role': 'admin',
            'User-Agent': 'ULPF-Test'
        }
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())

def get_json(path):
    req = urllib.request.Request(
        f'{BASE}{path}',
        headers={
            'X-ULPF-User': 'admin',
            'X-ULPF-Role': 'admin',
            'User-Agent': 'ULPF-Test'
        }
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())

print("=== 1. Creating Source ===")
src = post_json('/sources', {
    'name': 'Cisco-Firewall-Tokyo',
    'vendor': 'Cisco',
    'product': 'ASA',
    'transport': 'syslog'
})
src_id = src['source_id']
print('Created source:', src_id, src['name'])

print("\n=== 2. Creating Onboarding Session ===")
session = post_json('/onboarding', {'source_id': src_id})
session_id = session['id']
print('Created onboarding session:', session_id, 'stage:', session['current_stage'])

print("\n=== 3. Uploading Sample Log to Vault & Discovery ===")
sample_log = b"""<14>1 2026-08-31T10:15:22.123Z fw-tokyo-01 CEF:0|Cisco|ASA|9.0|100|ACCEPT|1|src=192.168.1.100 dst=10.0.0.5 spt=51234 dpt=443 proto=TCP act=permit
<14>1 2026-08-31T10:15:23.123Z fw-tokyo-01 CEF:0|Cisco|ASA|9.0|100|ACCEPT|1|src=192.168.1.101 dst=10.0.0.6 spt=51235 dpt=443 proto=TCP act=permit
<14>1 2026-08-31T10:15:24.123Z fw-tokyo-01 CEF:0|Cisco|ASA|9.0|100|ACCEPT|1|src=192.168.1.102 dst=10.0.0.7 spt=51236 dpt=80 proto=TCP act=permit
"""

boundary = '----WebKitFormBoundaryULPFTest123'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="cisco_asa.log"\r\n'
    f'Content-Type: text/plain\r\n\r\n'
).encode() + sample_log + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    f'{BASE}/onboarding/{session_id}/upload',
    data=body,
    headers={
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'User-Agent': 'ULPF-Test'
    }
)
with urllib.request.urlopen(req) as res:
    discovery_res = json.loads(res.read())

print('Discovery format:', discovery_res.get('format'))
print('Discovered pattern:', discovery_res.get('pattern'))
print('Proposals count:', len(discovery_res.get('proposals', [])))
for p in discovery_res.get('proposals', [])[:4]:
    print(f"  - {p['source_field']} -> {p['proposed_target']} (confidence: {p['confidence']})")

print("\n=== 4. Approving Review & Creating Mapping ===")
reviews = get_json('/reviews')
matching_review = next((r for r in reviews.get('items', []) if r['source_id'] == src_id), None)
if matching_review:
    rev_id = matching_review['review_id']
    bindings = {p['source_field']: p['proposed_target'] for p in matching_review['proposals']}
    approved = post_json(f'/reviews/{rev_id}/approve', {'field_bindings': bindings})
    print('Approved review:', rev_id, 'Mapping ID:', approved.get('mapping_id'))

print("\n=== 5. Processing Ingestion for Session ===")
proc = post_json(f'/onboarding/{session_id}/process', {})
print('Processed events:', proc)

print("\n=== 6. Verifying Traces, Normalized Events & Stats ===")
traces = get_json('/traces')
print('Total traces:', traces.get('total'))
events = get_json('/events')
print('Total normalized events:', events.get('total'))
stats = get_json('/stats/overview')
print('Pipeline stats:', stats)
print('\n>>> E2E BACKEND INTEGRATION TEST COMPLETED SUCCESSFULLY! <<<')
