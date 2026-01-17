import { useState, useEffect } from 'react';
import api from '../../api/client';
import { formatTime } from '../../utils/helpers';

export const LogsPanel = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const data = await api.getLogs(100);
      setLogs(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to fetch logs:', err);
      setLogs([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 10000); // 10 seconds to reduce load
    return () => clearInterval(interval);
  }, []);

  const getLevelColor = (level) => {
    switch (level) {
      case 'error': return 'text-red-600 bg-red-50';
      case 'warning': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getLevelIcon = (level) => {
    switch (level) {
      case 'error': return '✗';
      case 'warning': return '⚠';
      default: return '•';
    }
  };

  return (
    <div className="h-[30vh] bg-white border-t border-gray-200 flex flex-col">
      <div className="h-10 px-4 flex items-center justify-between bg-gray-50 border-b border-gray-200 flex-shrink-0">
        <span className="text-sm font-medium text-gray-600 flex items-center gap-2">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Activity Log
          {logs.length > 0 && <span className="text-xs text-gray-400">({logs.length})</span>}
        </span>
      </div>

      <div className="flex-1 overflow-y-auto custom-scroll p-3">
        {loading ? (
          <div className="text-center text-gray-400 text-sm py-4">Loading logs...</div>
        ) : logs.length === 0 ? (
          <div className="text-center text-gray-400 text-sm py-4">No activity yet</div>
        ) : (
          <div className="space-y-1">
            {logs.map((log) => (
              <div key={log.id} className="flex items-start gap-2 text-xs py-1.5 px-2 rounded hover:bg-gray-50">
                <span className={`flex-shrink-0 w-5 h-5 rounded flex items-center justify-center text-[10px] ${getLevelColor(log.level)}`}>
                  {getLevelIcon(log.level)}
                </span>
                <span className="text-gray-400 flex-shrink-0 font-mono">{formatTime(log.timestamp)}</span>
                <span className="text-gray-500 flex-shrink-0 uppercase text-[10px] tracking-wider bg-gray-100 px-1.5 py-0.5 rounded">{log.source}</span>
                <span className="text-gray-700 flex-1">{log.message}</span>
                {log.entity_id && (
                  <span className="text-gray-400 font-mono text-[10px]">{log.entity_id}</span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsPanel;
