import os
import re

directory = 'c:/Users/Lenovo/Desktop/SIH2026/ULPF/frontend/src'

replacements = [
    # Dark mode backgrounds -> Light mode backgrounds
    (r'bg-slate-950', r'bg-slate-50'),
    (r'bg-slate-900', r'bg-white'),
    (r'bg-slate-800', r'bg-slate-100'),
    (r'bg-\[\#09090b\]', r'bg-slate-50'),
    (r'bg-\[\#18181b\]', r'bg-white'),
    
    # Borders
    (r'border-slate-800', r'border-slate-200'),
    (r'border-\[\#27272a\]', r'border-slate-200'),
    
    # Text colors
    (r'text-slate-100', r'text-slate-900'),
    (r'text-slate-200', r'text-slate-800'),
    (r'text-slate-300', r'text-slate-700'),
    (r'text-slate-400', r'text-slate-600'),
    (r'text-slate-500', r'text-slate-500'),
    (r'text-white', r'text-slate-900'),
    (r'text-gray-300', r'text-slate-700'),
    (r'text-gray-400', r'text-slate-600'),
    (r'text-gray-500', r'text-slate-500'),
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
                
            # Add serif font to main headings (h1, h2)
            content = re.sub(r'<h1 className="([^"]*)"', r'<h1 className="\1 font-serif"', content)
            content = re.sub(r'<h2 className="([^"]*)"', r'<h2 className="\1 font-serif"', content)
            
            if content != original_content:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content)

print("Theme application complete.")
