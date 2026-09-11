import os
import re

directory = 'c:/Users/Lenovo/Desktop/SIH2026/ULPF/frontend/src'

replacements = [
    # Fix dark panels to light panels
    (r'bg-\[\#101D24\]', r'bg-white'),
    (r'border-\[\#1E3038\]', r'border-slate-200'),
    (r'bg-\[\#0D1920\]', r'bg-slate-50'),
    (r'text-\[\#DCE7EA\]', r'text-slate-900'),
    (r'text-\[\#12201B\]', r'text-slate-900'),
    (r'bg-\[\#062024\]', r'bg-white'),
    (r'text-\[\#32b2ac\]', r'text-slate-900'),
    # Also fix brand colors if they were used for text on dark backgrounds
    (r'text-brand-cyan', r'text-slate-900'),
    (r'text-brand-amber', r'text-amber-600'),
]

for root, _, files in os.walk(directory):
    for file in files:
        if file.endswith('.tsx'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            original_content = content
            for p, r in replacements:
                content = re.sub(p, r, content)
                
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

print("Panel theme fix complete.")
