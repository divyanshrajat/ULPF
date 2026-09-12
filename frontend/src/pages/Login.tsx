import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function Login() {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('ulpf-admin');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      let res;
      if (isLoginMode) {
        const body = new URLSearchParams();
        body.append('username', username);
        body.append('password', password);
        
        res = await fetch('/api/v1/auth/login', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body
        });
      } else {
        res = await fetch('/api/v1/auth/signup', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username, password })
        });
      }
      
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error("Invalid username or password");
        } else if (res.status === 400) {
          const errData = await res.json().catch(() => null);
          throw new Error(errData?.detail || "Registration failed");
        }
        throw new Error(isLoginMode ? "Login failed" : "Registration failed");
      }
      
      const data = await res.json();
      sessionStorage.setItem('ulpf_token', data.access_token);
      
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full h-[100vh] min-h-[100vh] relative overflow-hidden flex flex-col lg:flex-row bg-[#F6F9FD] font-sans text-[#082744] box-border">
      
      {/* =========================================================================
          BACKGROUND LAYER (Z: 0 to 2)
      ========================================================================= */}
      
      {/* Base Light Background */}
      <div className="absolute inset-0 bg-[#F6F9FD] z-[0] pointer-events-none" />

      {/* Sweeping Architectural Blue/Navy Transition */}
      <svg className="absolute inset-0 w-full h-full object-cover z-[1] pointer-events-none hidden lg:block" preserveAspectRatio="none" viewBox="0 0 1920 1080">
        <defs>
          <linearGradient id="navyBase" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06294A" />
            <stop offset="100%" stopColor="#062D50" />
          </linearGradient>
          <linearGradient id="glowTranslucent" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EAF3FF" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#1769D5" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* 1. Deep Navy Base (Right side ~46%) */}
        {/* Originates top upper-middle, sweeps toward bottom center */}
        <path d="M1020,0 L1920,0 L1920,1080 L900,1080 C1020,700 1120,400 1020,0 Z" fill="url(#navyBase)" />

        {/* 2. Very dark navy curved layer (Depth) */}
        <path d="M1070,0 L1920,0 L1920,1080 L980,1080 C1070,800 1170,300 1070,0 Z" fill="#041E38" opacity="0.3" />

        {/* 3. Muted blue curved layer */}
        <path d="M970,0 L1170,0 L920,1080 L820,1080 C920,700 1070,400 970,0 Z" fill="#1769D5" opacity="0.15" />

        {/* 4. Light blue translucent band near the split */}
        <path d="M900,0 L980,0 L870,1080 L790,1080 C870,700 1020,400 900,0 Z" fill="url(#glowTranslucent)" />
      </svg>

      {/* Far-Right Digital Globe / Network Graphic */}
      <div 
        className="absolute z-[2] pointer-events-none hidden lg:block opacity-30" 
        style={{ right: '-8%', top: '20%', width: '40vw', height: '40vw' }}
      >
        <svg viewBox="0 0 500 500" className="w-full h-full text-white">
          <circle cx="250" cy="250" r="240" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="4 8" />
          <circle cx="250" cy="250" r="180" fill="none" stroke="currentColor" strokeWidth="0.25" />
          <circle cx="250" cy="250" r="120" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="2 4" />
          
          <path d="M250,10 A240,240 0 0,0 250,490" fill="none" stroke="currentColor" strokeWidth="0.25" />
          <path d="M250,10 A160,240 0 0,0 250,490" fill="none" stroke="currentColor" strokeWidth="0.25" />
          <path d="M250,10 A80,240 0 0,0 250,490" fill="none" stroke="currentColor" strokeWidth="0.25" />
          
          <path d="M10,250 A240,80 0 0,0 490,250" fill="none" stroke="currentColor" strokeWidth="0.25" />
          <path d="M10,250 A240,160 0 0,0 490,250" fill="none" stroke="currentColor" strokeWidth="0.25" />
          
          <circle cx="250" cy="10" r="2" fill="currentColor" />
          <circle cx="250" cy="490" r="2" fill="currentColor" />
          <circle cx="10" cy="250" r="2" fill="currentColor" />
          <circle cx="490" cy="250" r="2" fill="currentColor" />
          <circle cx="370" cy="120" r="3" fill="#C89B3C" />
          <circle cx="160" cy="380" r="3" fill="#1769D5" />
          <path d="M250,250 L370,120 M250,250 L160,380" fill="none" stroke="currentColor" strokeWidth="0.25" />
        </svg>
      </div>

      {/* Far-Right Vertical Process Labels */}
      <div 
        className="absolute z-[3] pointer-events-none hidden xl:flex flex-col items-end"
        style={{ right: '3%', top: '35%' }}
      >
        <div className="flex flex-col gap-5 text-[11px] font-bold text-white/50 tracking-[4px] uppercase text-right">
          <span>Ingest</span>
          <span>Normalize</span>
          <span>Mask</span>
          <span>Unify</span>
          <span>Analyze</span>
          <div className="w-12 h-[1px] bg-white/20 my-2 ml-auto"></div>
          <div className="flex flex-col gap-3 text-[9px] text-white/30 tracking-[3px]">
            <span>Cleaner Logs</span>
            <span>Safer Systems</span>
            <span>Stronger Operations</span>
          </div>
        </div>
      </div>

      {/* Demo Prototype Badge */}
      <div 
        className="absolute z-[10] flex flex-col items-end"
        style={{ top: '25px', right: '35px' }}
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/10 bg-black/20 backdrop-blur-sm">
          <div className="w-2 h-2 rounded-full bg-[#10b981] shadow-[0_0_6px_rgba(16,185,129,0.8)]"></div>
          <span className="text-[10px] font-bold text-white tracking-widest uppercase">Demo Prototype</span>
        </div>
        <span className="text-[9px] font-medium text-white/50 tracking-wider mt-1">Not a live production environment</span>
      </div>


      {/* =========================================================================
          CONTENT LAYER (Z: 20)
      ========================================================================= */}
      
      {/* --- LEFT PANEL --- */}
      <div className="w-full lg:w-[54%] h-full flex flex-col justify-center px-[5vw] lg:pl-[4vw] lg:pr-[3vw] relative z-[20] overflow-y-auto lg:overflow-visible">
        
        {/* Branding */}
        <div className="flex items-center gap-4 mb-[clamp(2vh,4vh,50px)] mt-[2vh] lg:mt-0 shrink-0">
          <img src="/assets/ulpf_logo.png" alt="ULPF Logo" className="h-[clamp(64px,6vw,90px)] w-auto object-contain drop-shadow-md" />
          <div className="flex flex-col justify-center">
            <span className="text-[clamp(36px,4vw,56px)] font-extrabold text-[#062744] tracking-tight leading-none mb-1">ULPF</span>
            <span className="text-[clamp(14px,1.5vw,18px)] font-bold text-[#062744] tracking-wide mb-1">Universal Log Pre-processing Framework</span>
            <div className="flex items-center">
              <div className="h-[2.5px] w-8 bg-[#C89B3C] mr-2"></div>
              <span className="text-[clamp(12px,1.2vw,15px)] text-[#1769D5] italic font-medium">Different Logs. <span className="text-[#C89B3C] font-bold">One Framework.</span></span>
            </div>
          </div>
        </div>

        {/* Eyebrow */}
        <p className="text-[clamp(9px,0.9vw,11px)] font-bold tracking-[0.25em] text-[#61738A] uppercase mb-[clamp(1vh,2vh,20px)] shrink-0">
          Logs power operations. We make them intelligent.
        </p>

        {/* Headline */}
        <h1 className="text-[clamp(44px,4.5vw,64px)] font-extrabold tracking-[-0.02em] leading-[1.02] mb-[clamp(2vh,3vh,30px)] shrink-0">
          <span className="text-[#061F3A] block">Different Logs.</span>
          <span className="text-[#1769D5] block">One Framework.</span>
        </h1>

        {/* Description */}
        <p className="text-[clamp(13px,1.1vw,16px)] text-[#61738A] font-medium leading-[1.5] max-w-[85%] mb-[clamp(3vh,4vh,40px)] shrink-0">
          Universal Log Pre-processing Framework for encrypted log ingestion, schema normalization, parsing, masking, and unified log intelligence.
        </p>

        {/* Feature Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 xl:gap-3 w-full max-w-[700px] mb-[clamp(3vh,4vh,40px)] shrink-0">
          {[
            { title: "Multi-Source\nIngestion", color: "text-[#1769D5]", icon: "M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" },
            { title: "Schema\nNormalization", color: "text-[#8B5CF6]", icon: "M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" },
            { title: "Sensitive Data\nMasking", color: "text-[#F59E0B]", icon: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" },
            { title: "Unified\nLog Format", color: "text-[#10B981]", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" }
          ].map((feature, idx) => (
            <div key={idx} className="bg-white rounded-[10px] shadow-sm border border-[#DCE5EF] p-2 flex flex-col items-center justify-center text-center gap-1.5 h-[clamp(80px,10vh,110px)] hover:shadow-md transition-shadow">
              <svg className={`w-[clamp(20px,2vw,24px)] h-[clamp(20px,2vw,24px)] ${feature.color}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d={feature.icon}/></svg>
              <span className="text-[clamp(10px,0.9vw,12px)] font-bold text-[#061F3A] leading-tight whitespace-pre-line">{feature.title}</span>
            </div>
          ))}
        </div>

        {/* Pipeline Graphic */}
        <div className="flex items-center justify-center relative w-full max-w-[700px] bg-white border border-[#DCE5EF] p-[clamp(12px,1.5vh,20px)] rounded-[16px] shadow-sm shrink-0">
          <div className="flex w-full justify-between items-center relative z-10">
            {/* Left Sources */}
            <div className="flex flex-col gap-[clamp(4px,0.6vh,8px)] w-[20%]">
              {[
                { name: 'APP', color: 'text-[#1769D5]', bg: 'bg-[#EAF3FF]', icon: <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" /></svg> },
                { name: 'SYSLOG', color: 'text-[#8B5CF6]', bg: 'bg-[#F3E8FF]', icon: <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg> },
                { name: 'CLOUD', color: 'text-[#F43F5E]', bg: 'bg-[#FFE4E6]', icon: <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" /></svg> },
                { name: 'NETWORK', color: 'text-[#F59E0B]', bg: 'bg-[#FEF3C7]', icon: <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" /></svg> },
                { name: 'SECURITY', color: 'text-[#10B981]', bg: 'bg-[#D1FAE5]', icon: <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg> }
              ].map((src) => (
                <div key={src.name} className="bg-white rounded px-1.5 py-1 text-[clamp(8px,0.7vw,10px)] font-extrabold text-[#062744] shadow-sm border border-[#DCE5EF] flex items-center gap-1.5 w-full">
                  <div className={`w-5 h-5 rounded flex items-center justify-center shrink-0 ${src.bg} ${src.color}`}>
                    {src.icon}
                  </div>
                  {src.name}
                </div>
              ))}
            </div>

            {/* Center ULPF Node */}
            <div className="w-[22%] aspect-square max-h-[100px] bg-white rounded-[10px] shadow-md border border-[#DCE5EF] flex flex-col items-center justify-center p-2 z-10 relative">
               <img src="/assets/ulpf_logo.png" alt="ULPF Logo" className="w-[60%] object-contain mb-1" />
               <span className="text-[clamp(10px,0.9vw,12px)] font-extrabold text-[#062744]">ULPF</span>
            </div>

            {/* Right Output */}
            <div className="w-[32%] bg-white rounded-[10px] shadow-md border border-[#DCE5EF] p-[clamp(8px,1vh,16px)] flex flex-col z-10">
              <div className="flex items-center gap-2 border-b border-[#F5F8FC] pb-1.5 mb-1.5">
                <div className="w-5 h-5 bg-[#EAF3FF] text-[#1769D5] rounded flex items-center justify-center shrink-0">
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </div>
                <span className="text-[clamp(9px,0.8vw,11px)] font-bold text-[#061F3A] leading-tight">Unified Log Stream</span>
              </div>
              <div className="flex flex-col gap-1 text-[clamp(8px,0.7vw,10px)] font-semibold text-[#61738A]">
                <div className="flex items-center gap-1"><span className="text-[#10b981] font-bold">✓</span> Standardized Format</div>
                <div className="flex items-center gap-1"><span className="text-[#10b981] font-bold">✓</span> Masked Sensitive</div>
                <div className="flex items-center gap-1"><span className="text-[#10b981] font-bold">✓</span> Analysis Ready</div>
                <div className="flex items-center gap-1"><span className="text-[#10b981] font-bold">✓</span> Stronger Security</div>
              </div>
            </div>
          </div>

          {/* Connecting Lines */}
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-[1]">
            <svg className="w-full h-full" preserveAspectRatio="none" viewBox="0 0 700 200">
              <path d="M 150 30 C 240 30, 240 100, 330 100" fill="none" stroke="#1769D5" strokeWidth="1.5" strokeOpacity="0.25" />
              <path d="M 150 65 C 240 65, 240 100, 330 100" fill="none" stroke="#8B5CF6" strokeWidth="1.5" strokeOpacity="0.25" />
              <path d="M 150 100 C 240 100, 240 100, 330 100" fill="none" stroke="#F43F5E" strokeWidth="2" strokeOpacity="0.3" />
              <path d="M 150 135 C 240 135, 240 100, 330 100" fill="none" stroke="#F59E0B" strokeWidth="1.5" strokeOpacity="0.25" />
              <path d="M 150 170 C 240 170, 240 100, 330 100" fill="none" stroke="#10B981" strokeWidth="1.5" strokeOpacity="0.25" />
              
              <path d="M 370 100 L 460 100" fill="none" stroke="#C89B3C" strokeWidth="1.5" strokeDasharray="4 4" />
              <circle cx="370" cy="100" r="2.5" fill="#C89B3C" />
              <circle cx="460" cy="100" r="2.5" fill="#C89B3C" />
            </svg>
          </div>
          
          <div className="absolute bottom-[clamp(4px,0.5vh,8px)] left-1/2 -translate-x-1/2 text-[clamp(7px,0.6vw,9px)] font-bold tracking-[0.2em] text-[#61738A] uppercase z-10">
            PRE-PROCESS &gt; NORMALIZE &gt; UNIFY
          </div>
        </div>

      </div>


      {/* --- RIGHT PANEL --- */}
      <div className="w-full lg:w-[46%] h-full flex items-center justify-center lg:justify-start lg:pl-[2vw] relative z-[20] p-6 lg:p-0">
        
        {/* LOGIN CARD */}
        <div className="w-full max-w-[540px] lg:w-[34vw] min-w-[320px] bg-white rounded-[20px] border border-[#DCE5EF] shadow-2xl p-[clamp(24px,4vh,42px)] relative z-[30]">
          
          {/* Header */}
          <div className="flex items-center gap-3 mb-[clamp(20px,3vh,30px)]">
            <div className="w-[clamp(40px,4vh,48px)] h-[clamp(40px,4vh,48px)] bg-[#EAF3FF] rounded-full flex items-center justify-center text-[#1769D5] shrink-0 border border-blue-100">
              {isLoginMode ? (
                <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>
              ) : (
                <svg className="w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
              )}
            </div>
            <div>
              <h3 className="text-[clamp(18px,1.8vw,24px)] font-bold text-[#061F3A] leading-tight">
                {isLoginMode ? 'Secure sign-in' : 'Create your account'}
              </h3>
              <p className="text-[clamp(12px,1vw,13px)] font-medium text-[#61738A] mt-0.5">
                {isLoginMode ? 'Access your ULPF workspace' : 'Set up your secure workspace access'}
              </p>
            </div>
          </div>
          
          {/* Form */}
          <form className="space-y-[clamp(12px,2vh,20px)]" onSubmit={handleAuth}>
            <div>
              <label htmlFor="username" className="block text-[13px] font-bold text-[#061F3A] mb-1.5">
                Username or Email
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-[18px] w-[18px] text-[#61738A]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/></svg>
                </div>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="block w-full pl-9 rounded-[8px] border border-[#DCE5EF] h-[clamp(44px,5vh,48px)] text-[#062744] font-medium placeholder-[#61738A]/50 focus:border-[#1769D5] focus:outline-none focus:ring-1 focus:ring-[#1769D5] text-[14px] bg-white transition-colors"
                  placeholder="Enter your username or email"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-[13px] font-bold text-[#061F3A] mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-[18px] w-[18px] text-[#61738A]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete={isLoginMode ? "current-password" : "new-password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-9 pr-9 rounded-[8px] border border-[#DCE5EF] h-[clamp(44px,5vh,48px)] text-[#062744] font-medium placeholder-[#61738A]/50 focus:border-[#1769D5] focus:outline-none focus:ring-1 focus:ring-[#1769D5] text-[14px] bg-white transition-colors"
                  placeholder="Enter your password"
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer hover:text-[#061F3A] transition-colors">
                  <svg className="h-[18px] w-[18px] text-[#61738A]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                </div>
              </div>
            </div>

            {isLoginMode && (
              <div className="flex items-center justify-between pt-0.5">
                <div className="flex items-center">
                  <input id="remember-me" name="remember-me" type="checkbox" className="h-4 w-4 rounded border-[#DCE5EF] text-[#1769D5] focus:ring-[#1769D5] cursor-pointer" />
                  <label htmlFor="remember-me" className="ml-2 block text-[13px] text-[#61738A] font-medium cursor-pointer">Remember me</label>
                </div>
                <div className="text-[13px]">
                  <a href="#" className="font-bold text-[#1769D5] hover:text-[#082C4F] transition-colors">Forgot password?</a>
                </div>
              </div>
            )}

            {error && (
              <div className="text-[#dc2626] bg-[#fef2f2] p-2.5 rounded text-[12px] font-bold border border-[#fecaca] flex items-start gap-2">
                 <svg className="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="flex w-full justify-center items-center gap-2 rounded-[8px] bg-[#082F5B] h-[clamp(46px,5.5vh,50px)] px-4 text-[15px] font-bold text-white hover:bg-[#061F3A] focus:outline-none focus:ring-2 focus:ring-[#082F5B] focus:ring-offset-2 disabled:opacity-70 transition-colors mt-[clamp(16px,2.5vh,24px)]"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>
                  {isLoginMode ? 'Signing in...' : 'Creating account...'}
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  {isLoginMode ? 'Continue' : 'Create Account'}
                  <svg className="w-4 h-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="m12 5 7 7-7 7"/></svg>
                </span>
              )}
            </button>
          </form>
          
          <div className="mt-[clamp(12px,2vh,20px)] text-center">
            <button
              type="button"
              onClick={() => { setIsLoginMode(!isLoginMode); setError(''); }}
              className="text-[13px] font-bold text-[#1769D5] hover:text-[#082C4F] focus:outline-none transition-colors"
            >
              {isLoginMode ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
          
          {isLoginMode && (
            <>
              <div className="relative mt-[clamp(16px,2.5vh,24px)] mb-[clamp(12px,2vh,16px)]">
                <div className="absolute inset-0 flex items-center" aria-hidden="true">
                  <div className="w-full border-t border-[#DCE5EF]" />
                </div>
                <div className="relative flex justify-center text-[10px] font-bold leading-none">
                  <span className="bg-white px-2 text-[#61738A] uppercase tracking-[0.2em]">OR</span>
                </div>
              </div>
              
              <div className="w-full flex flex-col">
                <div className="flex items-center gap-2 mb-[clamp(8px,1vh,12px)] text-[#061F3A] font-bold text-[13px]">
                  <svg className="w-[14px] h-[14px] text-[#1769D5]" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                  Demo Accounts
                </div>
                <div className="border border-[#DCE5EF] rounded-[8px] bg-white overflow-hidden divide-y divide-[#DCE5EF]">
                  <div className="flex items-center justify-between px-3 h-[clamp(36px,4.5vh,42px)] hover:bg-[#F6F9FD] cursor-pointer transition-colors" onClick={() => { setUsername('admin'); setPassword('ulpf-admin'); }}>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-[#061F3A] text-[12px] w-12">admin</span>
                      <span className="text-[#61738A] text-[11px] font-medium">— Full Access</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between px-3 h-[clamp(36px,4.5vh,42px)] hover:bg-[#F6F9FD] cursor-pointer transition-colors" onClick={() => { setUsername('analyst'); setPassword('ulpf-admin'); }}>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-[#061F3A] text-[12px] w-12">analyst</span>
                      <span className="text-[#61738A] text-[11px] font-medium">— Read Only</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between px-3 h-[clamp(36px,4.5vh,42px)] hover:bg-[#F6F9FD] cursor-pointer transition-colors" onClick={() => { setUsername('auditor'); setPassword('ulpf-admin'); }}>
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-[#061F3A] text-[12px] w-12">auditor</span>
                      <span className="text-[#61738A] text-[11px] font-medium">— Logs Only</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          
        </div>
      </div>
    </div>
  );
}
