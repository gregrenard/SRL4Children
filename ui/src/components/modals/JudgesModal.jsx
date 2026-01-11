import { useState, useEffect } from 'react';
import api from '../../api/client';

export const JudgesModal = ({ onClose }) => {
  const [judges, setJudges] = useState([]);
  const [selectedJudge, setSelectedJudge] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState(null);

  useEffect(() => {
    loadJudges();
  }, []);

  const loadJudges = async () => {
    setLoading(true);
    try {
      const data = await api.getJudges();
      setJudges(data);
      const active = data.find(j => j.is_active);
      if (active) {
        setSelectedJudge(active.name);
        loadContent(active.name);
      }
    } catch (err) {
      console.error('Failed to load judges:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadContent = async (name) => {
    try {
      const data = await api.getJudgeContent(name);
      setContent(data.content);
    } catch (err) {
      setContent('Failed to load content');
    }
  };

  const handleSelect = async (name) => {
    setSelectedJudge(name);
    loadContent(name);
  };

  const handleApply = async () => {
    if (!selectedJudge) return;
    setSwitching(true);
    try {
      await api.setActiveJudges(selectedJudge);
      await loadJudges();
    } catch (err) {
      console.error('Failed to switch judges:', err);
    } finally {
      setSwitching(false);
    }
  };

  const handleTest = async () => {
    if (!selectedJudge) return;
    setTesting(true);
    setTestResults(null);
    try {
      const results = await api.testJudges(selectedJudge);
      setTestResults(results);
    } catch (err) {
      console.error('Failed to test judges:', err);
      setTestResults([{ name: 'Error', model: '', success: false, error: err.message }]);
    } finally {
      setTesting(false);
    }
  };

  const activeJudge = judges.find(j => j.is_active);
  const isChanged = selectedJudge && activeJudge && selectedJudge !== activeJudge.name;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 font-display">Judge Configuration</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 flex-1 overflow-hidden flex flex-col gap-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-everyone-blue border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <>
              {/* Judge selector */}
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Select Configuration</label>
                <div className="flex flex-wrap gap-2">
                  {judges.map(j => (
                    <button
                      key={j.name}
                      onClick={() => handleSelect(j.name)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 ${
                        selectedJudge === j.name
                          ? 'bg-everyone-blue text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {j.name.replace('.judges', '')}
                      <span className={`text-xs ${selectedJudge === j.name ? 'text-white/70' : 'text-gray-400'}`}>
                        ({j.judges_count} judges, {j.n_passes} passes)
                      </span>
                      {j.is_active && (
                        <span className={`text-xs ${selectedJudge === j.name ? 'text-white/70' : 'text-green-600'}`}>
                          (active)
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Config preview */}
              <div className="flex-1 overflow-hidden flex flex-col">
                <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Configuration Preview</label>
                <pre className="flex-1 overflow-auto bg-gray-50 rounded-xl p-4 text-xs font-mono text-gray-700 border border-gray-200">
                  {content || 'Select a configuration to preview'}
                </pre>
              </div>

              {/* Test results */}
              {testResults && (
                <div className="bg-gray-50 rounded-xl p-3 border border-gray-200">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Test Results</div>
                  <div className="space-y-1">
                    {testResults.map((r, i) => (
                      <div key={i} className="flex items-center gap-2 text-sm">
                        {r.success ? (
                          <span className="text-green-600">✓</span>
                        ) : (
                          <span className="text-red-500">✗</span>
                        )}
                        <span className="font-medium">{r.name}</span>
                        <span className="text-gray-400">{r.model}</span>
                        {r.success ? (
                          <span className="text-gray-400 text-xs">{r.response_time_ms}ms</span>
                        ) : (
                          <span className="text-red-500 text-xs">{r.error}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Help text */}
              <p className="text-xs text-gray-400">
                Judge configs are stored in ~/.srl4c/*.judges. Add your own by creating a new .judges file.
              </p>
            </>
          )}
        </div>

        <div className="flex items-center gap-3 p-4 border-t border-gray-100">
          <button
            onClick={handleTest}
            disabled={testing || !selectedJudge}
            className="py-2.5 px-4 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded-xl text-gray-700 text-sm font-medium transition-colors flex items-center gap-2"
            title={selectedJudge ? `Test ${selectedJudge}` : 'Select a config first'}
          >
            {testing && <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin"></div>}
            {testing ? 'Testing...' : `Test ${selectedJudge?.replace('.judges', '') || ''}`}
          </button>
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleApply}
            disabled={!isChanged || switching}
            className="flex-1 py-2.5 px-4 bg-everyone-blue hover:bg-everyone-blue/90 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
          >
            {switching && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            {switching ? 'Applying...' : isChanged ? 'Apply' : 'No Changes'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default JudgesModal;
