import { useState, useEffect } from 'react';
import api from '../../api/client';

export const GeneratorsModal = ({ onClose }) => {
  const [generators, setGenerators] = useState([]);
  const [selectedGenerator, setSelectedGenerator] = useState(null);
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [switching, setSwitching] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    loadGenerators();
  }, []);

  const loadGenerators = async () => {
    setLoading(true);
    try {
      const data = await api.getGenerators();
      setGenerators(data);
      const active = data.find(g => g.is_active);
      if (active) {
        setSelectedGenerator(active.name);
        loadContent(active.name);
      }
    } catch (err) {
      console.error('Failed to load generators:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadContent = async (name) => {
    try {
      const data = await api.getGeneratorContent(name);
      setContent(data.content);
    } catch (err) {
      setContent('Failed to load content');
    }
  };

  const handleSelect = async (name) => {
    setSelectedGenerator(name);
    loadContent(name);
  };

  const handleApply = async () => {
    if (!selectedGenerator) return;
    setSwitching(true);
    try {
      await api.setActiveGenerators(selectedGenerator);
      await loadGenerators();
    } catch (err) {
      console.error('Failed to switch generators:', err);
    } finally {
      setSwitching(false);
    }
  };

  const handleTest = async () => {
    if (!selectedGenerator) return;
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.testGenerator(selectedGenerator);
      setTestResult(result);
    } catch (err) {
      console.error('Failed to test generator:', err);
      setTestResult({ name: 'Error', model: '', success: false, error: err.message });
    } finally {
      setTesting(false);
    }
  };

  const activeGenerator = generators.find(g => g.is_active);
  const isChanged = selectedGenerator && activeGenerator && selectedGenerator !== activeGenerator.name;

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 font-display">Generator Configuration</h3>
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
              {/* Generator selector */}
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Select Configuration</label>
                <div className="flex flex-wrap gap-2">
                  {generators.map(g => (
                    <button
                      key={g.name}
                      onClick={() => handleSelect(g.name)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 ${
                        selectedGenerator === g.name
                          ? 'bg-everyone-blue text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {g.name.replace('.generators', '')}
                      <span className={`text-xs ${selectedGenerator === g.name ? 'text-white/70' : 'text-gray-400'}`}>
                        ({g.model})
                      </span>
                      {g.is_active && (
                        <span className={`text-xs ${selectedGenerator === g.name ? 'text-white/70' : 'text-green-600'}`}>
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

              {/* Test result */}
              {testResult && (
                <div className="bg-gray-50 rounded-xl p-3 border border-gray-200">
                  <div className="text-xs text-gray-500 uppercase tracking-wider mb-2">Test Result</div>
                  <div className="flex items-center gap-2 text-sm">
                    {testResult.success ? (
                      <span className="text-green-600">✓</span>
                    ) : (
                      <span className="text-red-500">✗</span>
                    )}
                    <span className="font-medium">{testResult.name}</span>
                    <span className="text-gray-400">{testResult.model}</span>
                    {testResult.success ? (
                      <span className="text-gray-400 text-xs">{testResult.response_time_ms}ms</span>
                    ) : (
                      <span className="text-red-500 text-xs">{testResult.error}</span>
                    )}
                  </div>
                </div>
              )}

              {/* Help text */}
              <p className="text-xs text-gray-400">
                Generator configs are stored in ~/.srl4c/*.generators. Used for guardrail generation.
              </p>
            </>
          )}
        </div>

        <div className="flex items-center gap-3 p-4 border-t border-gray-100">
          <button
            onClick={handleTest}
            disabled={testing || !selectedGenerator}
            className="py-2.5 px-4 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded-xl text-gray-700 text-sm font-medium transition-colors flex items-center gap-2"
            title={selectedGenerator ? `Test ${selectedGenerator}` : 'Select a config first'}
          >
            {testing && <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin"></div>}
            {testing ? 'Testing...' : `Test ${selectedGenerator?.replace('.generators', '') || ''}`}
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

export default GeneratorsModal;
