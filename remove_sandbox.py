import os
import re

files = [
    'frontend/src/pages/ApiKeys.tsx',
    'frontend/src/pages/Jobs.tsx',
    'frontend/src/pages/Onboarding.tsx',
    'frontend/src/pages/Rules.tsx',
    'frontend/src/pages/Sessions.tsx'
]

pattern = re.compile(r'\s*<div className="font-mono[^>]*>\s*SANDBOX\s*</div>', re.MULTILINE)

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    new_content = pattern.sub('', content)
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f'Removed from {filepath}')
    else:
        print(f'Not found in {filepath}')
