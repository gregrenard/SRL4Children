import { useState, useEffect } from 'react';
import api from '../api/client';
import { Topbar } from '../components/layout';

const generateId = () => Math.random().toString(36).substring(2, 10);

export const Editor = () => {
  // Data
  const [endpoints, setEndpoints] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [datasets, setDatasets] = useState([]);

  // Editor state
  const [prompts, setPrompts] = useState([
    { id: generateId(), criteria_id: '', prompt: '', selected: false }
  ]);
  const [selectedEndpoint, setSelectedEndpoint] = useState('');
  const [currentDataset, setCurrentDataset] = useState(null); // null = ad-hoc mode

  // Test results
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState({}); // {promptId: {response, error, latency_ms}}

  // Save modal
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [saving, setSaving] = useState(false);

  // Load initial data
  useEffect(() => {
    api.getEndpoints().then(setEndpoints).catch(console.error);
    api.getCriteria().then(data => setCriteria(Array.isArray(data) ? data : [])).catch(console.error);
    api.getDatasets().then(data => setDatasets(Array.isArray(data) ? data : [])).catch(console.error);
  }, []);

  // Group criteria by subcategory for dropdown
  const criteriaBySubcategory = criteria.reduce((acc, c) => {
    const sub = c.subcategory || 'other';
    if (!acc[sub]) acc[sub] = [];
    acc[sub].push(c);
    return acc;
  }, {});

  const addPrompt = () => {
    setPrompts([...prompts, { id: generateId(), criteria_id: '', prompt: '', selected: false }]);
  };

  const removePrompt = (id) => {
    if (prompts.length > 1) {
      setPrompts(prompts.filter(p => p.id !== id));
      const newResults = { ...testResults };
      delete newResults[id];
      setTestResults(newResults);
    }
  };

  const updatePrompt = (id, field, value) => {
    setPrompts(prompts.map(p => p.id === id ? { ...p, [field]: value } : p));
  };

  const toggleSelect = (id) => {
    setPrompts(prompts.map(p => p.id === id ? { ...p, selected: !p.selected } : p));
  };

  const toggleSelectAll = () => {
    const allSelected = prompts.every(p => p.selected);
    setPrompts(prompts.map(p => ({ ...p, selected: !allSelected })));
  };

  const selectedPrompts = prompts.filter(p => p.selected && p.prompt.trim());
  const hasSelection = selectedPrompts.length > 0;

  const testSelected = async () => {
    if (!selectedEndpoint || !hasSelection) return;

    setTesting(true);
    const results = { ...testResults };

    for (const p of selectedPrompts) {
      results[p.id] = { loading: true };
      setTestResults({ ...results });

      try {
        const result = await api.testEndpoint(selectedEndpoint, p.prompt);
        results[p.id] = result;
      } catch (err) {
        results[p.id] = { success: false, error: err.message };
      }
      setTestResults({ ...results });
    }

    setTesting(false);
  };

  const clearResults = () => {
    setTestResults({});
  };

  const loadDataset = async (dataset) => {
    try {
      const data = await api.getDatasetPrompts(dataset.name, 1, 10000);
      const loadedPrompts = (data.prompts || []).map(p => ({
        id: generateId(),
        criteria_id: p.criteria_id || '',
        prompt: p.prompt || '',
        selected: false
      }));
      setPrompts(loadedPrompts.length > 0 ? loadedPrompts : [{ id: generateId(), criteria_id: '', prompt: '', selected: false }]);
      setCurrentDataset(dataset);
      setTestResults({});
    } catch (err) {
      console.error('Failed to load dataset:', err);
    }
  };

  const newAdHoc = () => {
    setPrompts([{ id: generateId(), criteria_id: '', prompt: '', selected: false }]);
    setCurrentDataset(null);
    setTestResults({});
  };

  const handleSave = async () => {
    if (!saveName.trim()) return;

    setSaving(true);
    try {
      // Build CSV content
      const validPrompts = prompts.filter(p => p.prompt.trim());
      const csvLines = ['PromptID,Category,Prompt'];
      validPrompts.forEach((p, i) => {
        const promptId = `prompt-${i + 1}`;
        const category = p.criteria_id || 'emotional_reliance.interactional.validation';
        const escapedPrompt = `"${p.prompt.replace(/"/g, '""')}"`;
        csvLines.push(`${promptId},${category},${escapedPrompt}`);
      });

      await api.createDataset({
        name: saveName.trim(),
        description: saveDescription.trim() || null,
        csv_content: csvLines.join('\n')
      });

      // Refresh datasets
      const data = await api.getDatasets();
      setDatasets(Array.isArray(data) ? data : []);

      setShowSaveModal(false);
      setSaveName('');
      setSaveDescription('');
    } catch (err) {
      alert('Failed to save: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const validPromptsCount = prompts.filter(p => p.prompt.trim()).length;

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Topbar />

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Datasets */}
        <div className="w-56 bg-white border-r border-gray-200 flex flex-col">
          <div className="p-3 border-b border-gray-100">
            <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Mode</div>
            <button
              onClick={newAdHoc}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                !currentDataset ? 'bg-everyone-blue text-white' : 'hover:bg-gray-100 text-gray-700'
              }`}
            >
              Ad-hoc
            </button>
          </div>

          <div className="p-3 flex-1 overflow-y-auto">
            <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Load Dataset</div>
            <div className="space-y-1">
              {datasets.map(d => (
                <button
                  key={d.id}
                  onClick={() => loadDataset(d)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentDataset?.id === d.id ? 'bg-everyone-blue text-white' : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <div className="truncate">{d.name}</div>
                  <div className={`text-xs ${currentDataset?.id === d.id ? 'text-blue-100' : 'text-gray-400'}`}>
                    {d.prompt_count || 0} prompts
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-semibold text-gray-800">
                {currentDataset ? currentDataset.name : 'Ad-hoc Editor'}
              </h1>
              <span className="text-sm text-gray-500">{validPromptsCount} prompts</span>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSaveModal(true)}
                disabled={validPromptsCount === 0}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded-lg text-sm font-medium text-gray-700 transition-colors"
              >
                Save as Dataset
              </button>
            </div>
          </div>

          {/* Prompt Table */}
          <div className="flex-1 overflow-auto p-4">
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="w-10 px-3 py-3">
                      <input
                        type="checkbox"
                        checked={prompts.length > 0 && prompts.every(p => p.selected)}
                        onChange={toggleSelectAll}
                        className="rounded border-gray-300"
                      />
                    </th>
                    <th className="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-64">Behavior</th>
                    <th className="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Prompt</th>
                    <th className="w-10"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {prompts.map((p) => (
                    <tr key={p.id} className={p.selected ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                      <td className="px-3 py-2">
                        <input
                          type="checkbox"
                          checked={p.selected}
                          onChange={() => toggleSelect(p.id)}
                          className="rounded border-gray-300"
                        />
                      </td>
                      <td className="px-3 py-2">
                        <select
                          value={p.criteria_id}
                          onChange={(e) => updatePrompt(p.id, 'criteria_id', e.target.value)}
                          className="w-full bg-gray-50 border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-everyone-blue"
                        >
                          <option value="">Select behavior...</option>
                          {Object.entries(criteriaBySubcategory).map(([sub, items]) => (
                            <optgroup key={sub} label={sub}>
                              {items.map(c => (
                                <option key={c.id} value={c.id}>
                                  {c.name.replace(/_/g, ' ')}
                                </option>
                              ))}
                            </optgroup>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={p.prompt}
                          onChange={(e) => updatePrompt(p.id, 'prompt', e.target.value)}
                          placeholder="Enter prompt text..."
                          className="w-full bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-gray-700"
                        />
                      </td>
                      <td className="px-3 py-2">
                        <button
                          onClick={() => removePrompt(p.id)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                          title="Remove"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="px-3 py-2 border-t border-gray-100">
                <button
                  onClick={addPrompt}
                  className="text-sm text-everyone-blue hover:text-everyone-blue-dark font-medium flex items-center gap-1"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Prompt
                </button>
              </div>
            </div>

            {/* Test Results */}
            {Object.keys(testResults).length > 0 && (
              <div className="mt-4 bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Test Results</span>
                  <button onClick={clearResults} className="text-xs text-gray-500 hover:text-gray-700">
                    Clear
                  </button>
                </div>
                <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
                  {prompts.filter(p => testResults[p.id]).map(p => {
                    const result = testResults[p.id];
                    return (
                      <div key={p.id} className="p-4">
                        <div className="text-sm font-medium text-gray-800 mb-2 line-clamp-1">{p.prompt}</div>
                        {result.loading ? (
                          <div className="text-sm text-gray-400 flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-gray-300 border-t-everyone-blue rounded-full animate-spin"></div>
                            Testing...
                          </div>
                        ) : result.success ? (
                          <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                            <div className="text-xs text-green-600 mb-1">{result.latency_ms}ms</div>
                            <div className="text-sm text-gray-700 whitespace-pre-wrap">{result.response}</div>
                          </div>
                        ) : (
                          <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <div className="text-sm text-red-700">{result.error}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Sidebar - Test Controls */}
        <div className="w-64 bg-white border-l border-gray-200 flex flex-col">
          <div className="p-4 border-b border-gray-100">
            <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Endpoint</div>
            <select
              value={selectedEndpoint}
              onChange={(e) => setSelectedEndpoint(e.target.value)}
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            >
              <option value="">Select endpoint...</option>
              {endpoints.map(e => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
          </div>

          <div className="p-4 flex-1">
            <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-3">Actions</div>

            <div className="space-y-3">
              <button
                onClick={testSelected}
                disabled={!selectedEndpoint || !hasSelection || testing}
                className="w-full py-2.5 px-4 bg-everyone-blue hover:bg-everyone-blue-dark disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {testing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                {testing ? 'Testing...' : `Test Selected (${selectedPrompts.length})`}
              </button>

              <div className="text-xs text-gray-500 text-center">
                {!selectedEndpoint && 'Select an endpoint'}
                {selectedEndpoint && !hasSelection && 'Select prompts to test'}
              </div>
            </div>
          </div>

          <div className="p-4 border-t border-gray-100 bg-gray-50">
            <div className="text-xs text-gray-500">
              <strong>{selectedPrompts.length}</strong> of {prompts.length} selected
            </div>
          </div>
        </div>
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Save as Dataset</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="my_custom_dataset"
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
                <input
                  type="text"
                  value={saveDescription}
                  onChange={(e) => setSaveDescription(e.target.value)}
                  placeholder="Custom prompts for testing..."
                  className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
                />
              </div>

              <div className="text-sm text-gray-500">
                {validPromptsCount} prompts will be saved
              </div>
            </div>

            <div className="flex gap-3 justify-end mt-6">
              <button
                onClick={() => setShowSaveModal(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={!saveName.trim() || saving}
                className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue-dark disabled:opacity-50 transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Editor;
