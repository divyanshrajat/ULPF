import { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Database, FolderTree, Network, Shield, ChevronRight, ChevronDown } from 'lucide-react';

const OCSF_SCHEMA_DATA = {
  categories: [
    {
      id: 'system',
      name: 'System Activity',
      icon: Database,
      classes: [
        {
          id: 1001,
          name: 'File Activity',
          description: 'Events relating to file system operations.',
          fields: [
            { name: 'activity_id', type: 'Integer', required: true, desc: 'The normalized identifier of the activity.' },
            { name: 'file.name', type: 'String', required: true, desc: 'The name of the file.' },
            { name: 'file.path', type: 'String', required: true, desc: 'The absolute path to the file.' },
            { name: 'actor.user.name', type: 'String', required: false, desc: 'The user who performed the action.' }
          ]
        },
        {
          id: 1007,
          name: 'Process Activity',
          description: 'Events relating to process creation, termination, etc.',
          fields: [
            { name: 'activity_id', type: 'Integer', required: true, desc: 'The normalized identifier of the activity.' },
            { name: 'process.name', type: 'String', required: true, desc: 'The name of the process executable.' },
            { name: 'process.pid', type: 'Integer', required: true, desc: 'The process ID.' },
            { name: 'process.cmd_line', type: 'String', required: false, desc: 'The command line arguments.' }
          ]
        }
      ]
    },
    {
      id: 'network',
      name: 'Network Activity',
      icon: Network,
      classes: [
        {
          id: 4001,
          name: 'Network Traffic',
          description: 'Events related to network traffic and connections.',
          fields: [
            { name: 'activity_id', type: 'Integer', required: true, desc: 'The normalized identifier of the activity.' },
            { name: 'source.ip', type: 'IP Address', required: true, desc: 'Source IP address.' },
            { name: 'destination.ip', type: 'IP Address', required: true, desc: 'Destination IP address.' },
            { name: 'destination.port', type: 'Integer', required: true, desc: 'Destination port number.' },
            { name: 'connection_info.protocol_name', type: 'String', required: false, desc: 'The protocol name (e.g., TCP, UDP).' }
          ]
        },
        {
          id: 4002,
          name: 'HTTP Activity',
          description: 'Events related to HTTP requests and responses.',
          fields: [
            { name: 'activity_id', type: 'Integer', required: true, desc: 'The normalized identifier of the activity.' },
            { name: 'http_request.http_method', type: 'String', required: true, desc: 'The HTTP method (e.g., GET, POST).' },
            { name: 'http_request.url.path', type: 'String', required: true, desc: 'The URL path.' },
            { name: 'http_response.code', type: 'Integer', required: true, desc: 'The HTTP status code.' },
            { name: 'source.ip', type: 'IP Address', required: false, desc: 'Source IP address.' }
          ]
        }
      ]
    },
    {
      id: 'iam',
      name: 'Identity & Access',
      icon: Shield,
      classes: [
        {
          id: 3002,
          name: 'Authentication',
          description: 'Events relating to authentication attempts.',
          fields: [
            { name: 'activity_id', type: 'Integer', required: true, desc: 'The normalized identifier of the activity (e.g. Logon, Logoff).' },
            { name: 'user.name', type: 'String', required: true, desc: 'The username attempting authentication.' },
            { name: 'user.domain', type: 'String', required: false, desc: 'The domain of the user.' },
            { name: 'auth_protocol', type: 'String', required: false, desc: 'The protocol used (e.g., Kerberos, NTLM).' },
            { name: 'status', type: 'String', required: true, desc: 'Success, Failure, etc.' }
          ]
        }
      ]
    }
  ]
};

export function Schemas() {
  const [activeCategoryId, setActiveCategoryId] = useState<string>('network');
  const [activeClassId, setActiveClassId] = useState<number>(4001);

  const activeCategory = OCSF_SCHEMA_DATA.categories.find(c => c.id === activeCategoryId);
  const activeClass = activeCategory?.classes.find(c => c.id === activeClassId);

  const handleCategoryClick = (categoryId: string) => {
    setActiveCategoryId(categoryId);
    // Auto-select the first class in the new category
    const cat = OCSF_SCHEMA_DATA.categories.find(c => c.id === categoryId);
    if (cat && cat.classes.length > 0) {
      setActiveClassId(cat.classes[0].id);
    }
  };

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Schema Browser</h1>
          <p className="text-slate-400 mt-1">Explore the standard OCSF taxonomy and data models.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        <div className="lg:col-span-1 space-y-4 overflow-y-auto pr-2 custom-scrollbar">
          <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider sticky top-0 bg-slate-950 py-2 z-10">Categories</h3>
          <div className="space-y-2">
            {OCSF_SCHEMA_DATA.categories.map((cat) => {
              const isActive = cat.id === activeCategoryId;
              return (
                <div key={cat.id} className="space-y-1">
                  <div 
                    onClick={() => handleCategoryClick(cat.id)}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors flex items-center justify-between ${
                      isActive ? 'bg-slate-800 border-brand-cyan text-brand-cyan' : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <cat.icon className="w-5 h-5" />
                      <span className="font-medium">{cat.name}</span>
                    </div>
                    {isActive ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4 opacity-50" />}
                  </div>
                  
                  {/* Expanded Classes list */}
                  {isActive && (
                    <div className="pl-6 pr-2 py-2 space-y-1">
                      {cat.classes.map(cls => (
                        <div 
                          key={cls.id}
                          onClick={() => setActiveClassId(cls.id)}
                          className={`px-3 py-2 rounded-md text-sm cursor-pointer transition-colors ${
                            activeClassId === cls.id ? 'bg-brand-cyan/10 text-brand-cyan font-medium' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                          }`}
                        >
                          {cls.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        <div className="lg:col-span-3 min-h-0">
          <Card className="h-full flex flex-col border-slate-800">
            {activeCategory && activeClass ? (
              <>
                <div className="flex items-center gap-3 p-6 border-b border-slate-800 shrink-0">
                  <div className="p-3 bg-brand-cyan/10 rounded-lg text-brand-cyan">
                    <activeCategory.icon className="w-8 h-8" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-100">{activeCategory.name}</h2>
                    <p className="text-sm text-slate-400">Category ID: {activeCategory.id}</p>
                  </div>
                </div>

                <div className="p-6 flex-1 overflow-y-auto custom-scrollbar space-y-6">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-slate-200 flex items-center gap-2">
                        <FolderTree className="w-5 h-5 text-brand-purple" />
                        {activeClass.name} 
                      </h3>
                      <span className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-xs font-mono">Class ID: {activeClass.id}</span>
                    </div>
                    <p className="text-slate-400 mb-6">{activeClass.description}</p>
                    
                    <div className="bg-slate-900/50 rounded-lg border border-slate-800 overflow-hidden">
                      <table className="w-full text-left text-sm text-slate-300">
                        <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                          <tr>
                            <th className="px-4 py-3 font-medium">Field Name</th>
                            <th className="px-4 py-3 font-medium">Type</th>
                            <th className="px-4 py-3 font-medium">Requirement</th>
                            <th className="px-4 py-3 font-medium">Description</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {activeClass.fields.map((field, idx) => (
                            <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                              <td className="px-4 py-4 font-mono text-xs text-brand-cyan">{field.name}</td>
                              <td className="px-4 py-4 text-brand-purple text-xs">{field.type}</td>
                              <td className="px-4 py-4">
                                {field.required ? (
                                  <span className="px-2 py-0.5 bg-brand-amber/10 text-brand-amber rounded text-xs">Required</span>
                                ) : (
                                  <span className="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs">Optional</span>
                                )}
                              </td>
                              <td className="px-4 py-4 text-slate-400">{field.desc}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-500">
                Select a schema category to view details
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
