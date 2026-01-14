import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import api from '../../api/client';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { href: '/datasets', label: 'Datasets', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { href: '/judges', label: 'Judges', icon: 'M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3' },
];

export const Topbar = ({ onJudgesClick, onGeneratorsClick }) => {
  const [activeJudge, setActiveJudge] = useState(null);
  const [activeGenerator, setActiveGenerator] = useState(null);

  // Fetch active configs on mount and periodically
  useEffect(() => {
    const fetchConfigs = () => {
      api.getActiveJudges().then(data => setActiveJudge(data.active?.replace('.judges', ''))).catch(() => {});
      api.getActiveGenerators().then(data => setActiveGenerator(data.active?.replace('.generators', ''))).catch(() => {});
    };
    fetchConfigs();
    const interval = setInterval(fetchConfigs, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/srl4c-logo.png" alt="SRL4C" className="w-9 h-9 rounded-lg" />
          <div>
            <span className="text-lg font-bold font-display">
              <span className="text-everyone-blue">everyone</span><span className="text-everyone-purple">.AI</span>
            </span>
            <span className="text-gray-400 font-normal text-sm ml-2">/ SRL4C</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-xs">
            {activeJudge && (
              <button
                onClick={onJudgesClick}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors cursor-pointer"
                title="Click to change judge config"
              >
                <svg className="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" />
                </svg>
                <span className="text-gray-600 font-medium">{activeJudge}</span>
              </button>
            )}
            {activeGenerator && (
              <button
                onClick={onGeneratorsClick}
                className="flex items-center gap-1.5 px-2.5 py-1 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors cursor-pointer"
                title="Click to change generator config"
              >
                <svg className="w-3.5 h-3.5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-gray-600 font-medium">{activeGenerator}</span>
              </button>
            )}
          </div>
          <nav className="flex items-center gap-1">
            {NAV_ITEMS.map(item => (
              <NavLink
                key={item.href}
                to={item.href}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isActive
                      ? 'text-white bg-everyone-blue'
                      : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                  }`
                }
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={item.icon} />
                </svg>
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </div>
    </div>
  );
};

export default Topbar;
