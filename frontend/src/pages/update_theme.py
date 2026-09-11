import re

def update_file(file_path, replacements):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    for pattern, repl in replacements:
        content = re.sub(pattern, repl, content)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

dashboard_replacements = [
    (r'<div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl p-6 overflow-x-auto">', r'<Card className="flex items-center justify-between overflow-x-auto p-6">'),
    (r'          <PipelineStage name="TRACE"     count=\{stats\.events_normalized\}  status="success" icon=\{GitCommit\} />\n        </div>', r'          <PipelineStage name="TRACE"     count={stats.events_normalized}  status="success" icon={GitCommit} />\n        </Card>'),
    (r'<div key=\{name\} className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3">', r'<Card key={name} className="flex items-center gap-3 p-3">'),
    (r'                  \)}>{String\(status\)}</div>\n                </div>\n              </div>', r'                  )}>{String(status)}</div>\n                </div>\n              </Card>'),
    (r'bg-slate-900 border-slate-800 ', ''),
    (r'bg-slate-900 border border-slate-800 ', ''),
    (r'bg-slate-850', 'bg-slate-800/50')
]

update_file('c:/Users/Lenovo/Desktop/SIH2026/ULPF/frontend/src/pages/Dashboard.tsx', dashboard_replacements)

source_details_replacements = [
    (r'<div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl">', r'<Card className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-6 shadow-xl">'),
    (r'              </span>\n            </div>\n          </div>\n        </div>\n      </div>', r'              </span>\n            </div>\n          </div>\n        </div>\n      </Card>'),
    (r'<div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-slate-900 p-3 rounded-xl border border-slate-800">', r'<Card className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between p-3">'),
    (r'            \)}\n          </div>\n        </div>', r'            )}\n          </div>\n        </Card>'),
    (r'className="([^"]*)bg-slate-900 border-slate-800([^"]*)"', r'className="\1\2"'),
    (r'className="([^"]*)bg-slate-900 border border-slate-800([^"]*)"', r'className="\1\2"'),
    (r'className="\s+', 'className="'),
    (r'\s+"', '"')
]

update_file('c:/Users/Lenovo/Desktop/SIH2026/ULPF/frontend/src/pages/SourceDetails.tsx', source_details_replacements)
print('Done')
