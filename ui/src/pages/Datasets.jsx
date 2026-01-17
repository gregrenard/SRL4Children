import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { Topbar } from '../components/layout';
import { JudgesModal, GeneratorsModal } from '../components/modals';

const generateId = () => Math.random().toString(36).substring(2, 10);

export const Datasets = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  // Data
  const [datasets, setDatasets] = useState([]);
  const [allCriteria, setAllCriteria] = useState([]);
  const [endpoints, setEndpoints] = useState([]);

  // Current dataset state
  const [currentDataset, setCurrentDataset] = useState(null);
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(false);

  // View state
  const [view, setView] = useState('prompts'); // 'prompts' or 'coverage'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState({ type: null, value: null });

  // Editor state
  const [isNewDataset, setIsNewDataset] = useState(false);

  // Test state
  const [selectedEndpoint, setSelectedEndpoint] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [showTestPanel, setShowTestPanel] = useState(true);

  // Modal state
  const [showJudgesModal, setShowJudgesModal] = useState(false);
  const [showGeneratorsModal, setShowGeneratorsModal] = useState(false);
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [saveDescription, setSaveDescription] = useState('');
  const [saving, setSaving] = useState(false);

  // Load initial data
  useEffect(() => {
    loadDatasets();
    loadCriteria();
    api.getEndpoints().then(setEndpoints).catch(console.error);
  }, []);

  const loadDatasets = () => {
    api.getDatasets()
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setDatasets(list);
        // Load initial dataset from URL or first one
        const urlDataset = searchParams.get('dataset');
        if (urlDataset) {
          const ds = list.find(d => d.name === urlDataset);
          if (ds) loadDataset(ds);
        } else if (list.length > 0 && !currentDataset && !isNewDataset) {
          loadDataset(list[0]);
        }
      })
      .catch(console.error);
  };

  const loadCriteria = () => {
    api.getCriteria()
      .then(data => setAllCriteria(Array.isArray(data) ? data : []))
      .catch(console.error);
  };

  const loadDataset = async (dataset) => {
    setLoading(true);
    setIsNewDataset(false);
    setCurrentDataset(dataset);
    setSearchParams({ dataset: dataset.name });
    setTestResults({});
    setSelectedFilter({ type: null, value: null });
    setSearchQuery('');

    try {
      const data = await api.getDatasetPrompts(dataset.name, 1, 10000);
      const loadedPrompts = (data.prompts || []).map(p => ({
        id: generateId(),
        criteria_id: p.criteria_id || p.category || '',
        prompt: p.prompt || '',
        selected: false
      }));
      setPrompts(loadedPrompts);
    } catch (err) {
      console.error('Failed to load dataset:', err);
      setPrompts([]);
    } finally {
      setLoading(false);
    }
  };

  const startNewDataset = () => {
    setCurrentDataset(null);
    setIsNewDataset(true);
    setPrompts([{ id: generateId(), criteria_id: '', prompt: '', selected: false }]);
    setTestResults({});
    setSearchParams({});
  };

  // Prompt editing
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
    const validPrompts = getFilteredPrompts();
    const allSelected = validPrompts.length > 0 && validPrompts.every(p => p.selected);
    const validIds = new Set(validPrompts.map(p => p.id));
    setPrompts(prompts.map(p => validIds.has(p.id) ? { ...p, selected: !allSelected } : p));
  };

  // Filtering
  const getFilteredPrompts = () => {
    let filtered = prompts;

    if (selectedFilter.type) {
      filtered = filtered.filter(p => {
        const parts = (p.criteria_id || '').split('.');
        if (selectedFilter.type === 'category') return parts[0] === selectedFilter.value;
        if (selectedFilter.type === 'subcategory') return parts[1] === selectedFilter.value;
        if (selectedFilter.type === 'criteria') return p.criteria_id === selectedFilter.value;
        return true;
      });
    }

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      filtered = filtered.filter(p =>
        p.prompt.toLowerCase().includes(q) ||
        (p.criteria_id || '').toLowerCase().includes(q)
      );
    }

    return filtered;
  };

  const handleFilterClick = (type, value) => {
    if (selectedFilter.type === type && selectedFilter.value === value) {
      setSelectedFilter({ type: null, value: null });
    } else {
      setSelectedFilter({ type, value });
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedFilter({ type: null, value: null });
  };

  // Testing
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

  // Saving
  const handleSave = async () => {
    if (!saveName.trim()) return;

    setSaving(true);
    try {
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

      setShowSaveModal(false);
      setSaveName('');
      setSaveDescription('');
      loadDatasets();
    } catch (err) {
      alert('Failed to save: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!currentDataset) return;
    try {
      await api.deleteDataset(currentDataset.id);
      setShowDeleteModal(false);
      const remaining = datasets.filter(d => d.id !== currentDataset.id);
      if (remaining.length > 0) {
        loadDataset(remaining[0]);
      } else {
        startNewDataset();
      }
      loadDatasets();
    } catch (err) {
      alert('Failed to delete: ' + err.message);
    }
  };

  // Criteria grouping for coverage view
  const criteriaCounts = prompts.reduce((acc, p) => {
    const id = p.criteria_id || '';
    acc[id] = (acc[id] || 0) + 1;
    return acc;
  }, {});

  const criteriaByCategory = allCriteria.reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = {};
    if (!acc[c.category][c.subcategory]) acc[c.category][c.subcategory] = [];
    acc[c.category][c.subcategory].push({
      ...c,
      promptCount: criteriaCounts[c.id] || 0
    });
    return acc;
  }, {});

  const criteriaBySubcategory = allCriteria.reduce((acc, c) => {
    const sub = c.subcategory || 'other';
    if (!acc[sub]) acc[sub] = [];
    acc[sub].push(c);
    return acc;
  }, {});

  const totalPresent = allCriteria.filter(c => criteriaCounts[c.id] > 0).length;
  const totalMissing = allCriteria.length - totalPresent;

  const filteredPrompts = getFilteredPrompts();
  const validPromptsCount = prompts.filter(p => p.prompt.trim()).length;
  const isEditable = isNewDataset || (currentDataset && !currentDataset.is_builtin);

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Topbar
        onJudgesClick={() => setShowJudgesModal(true)}
        onGeneratorsClick={() => setShowGeneratorsModal(true)}
      />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}
      {showGeneratorsModal && <GeneratorsModal onClose={() => setShowGeneratorsModal(false)} />}

      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Dataset List */}
        <div className="w-56 bg-white border-r border-gray-200 flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-gray-100">
            <button
              onClick={startNewDataset}
              className="w-full py-2 px-3 bg-everyone-blue text-white rounded-lg text-sm font-medium hover:bg-everyone-blue/90 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Dataset
            </button>
          </div>

          <div className="p-3 flex-1 overflow-y-auto">
            <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Datasets</div>
            <div className="space-y-1">
              {datasets.map(d => (
                <button
                  key={d.id}
                  onClick={() => loadDataset(d)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                    currentDataset?.id === d.id && !isNewDataset
                      ? 'bg-everyone-blue text-white'
                      : 'hover:bg-gray-100 text-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className="truncate flex-1">{d.name}</span>
                    {d.is_builtin && (
                      <span className={`text-xs px-1.5 rounded ${
                        currentDataset?.id === d.id && !isNewDataset ? 'bg-white/20' : 'bg-blue-100 text-blue-600'
                      }`}>
                        built-in
                      </span>
                    )}
                  </div>
                  <div className={`text-xs ${currentDataset?.id === d.id && !isNewDataset ? 'text-blue-100' : 'text-gray-400'}`}>
                    {d.prompt_count || 0} prompts
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 border-t border-gray-100">
            <button
              onClick={() => setShowUploadModal(true)}
              className="w-full py-2 px-3 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
            >
              Upload CSV
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Toolbar */}
          <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-4">
              <h1 className="text-lg font-semibold text-gray-800">
                {isNewDataset ? 'New Dataset' : currentDataset?.name || 'Select a dataset'}
              </h1>
              {currentDataset && !isNewDataset && (
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  currentDataset.is_builtin ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
                }`}>
                  {currentDataset.is_builtin ? 'Built-in' : 'Custom'}
                </span>
              )}
              <span className="text-sm text-gray-500">{validPromptsCount} prompts</span>
              {allCriteria.length > 0 && (
                <span className="text-sm text-gray-400">
                  <span className="text-green-600">{totalPresent}</span>/<span>{allCriteria.length}</span> behaviors
                </span>
              )}
            </div>

            <div className="flex items-center gap-3">
              {/* View Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-0.5">
                <button
                  onClick={() => setView('prompts')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    view === 'prompts' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
                  }`}
                >
                  Prompts
                </button>
                <button
                  onClick={() => setView('coverage')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    view === 'coverage' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500'
                  }`}
                >
                  Coverage
                </button>
              </div>

              {isEditable && (
                <button
                  onClick={() => setShowSaveModal(true)}
                  disabled={validPromptsCount === 0}
                  className="px-4 py-2 bg-everyone-blue hover:bg-everyone-blue/90 disabled:opacity-50 rounded-lg text-sm font-medium text-white transition-colors"
                >
                  {isNewDataset ? 'Save Dataset' : 'Save Copy'}
                </button>
              )}

              {currentDataset && !currentDataset.is_builtin && !isNewDataset && (
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  title="Delete dataset"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              )}
            </div>
          </div>

          {/* Filter Bar */}
          {view === 'prompts' && (
            <div className="bg-white border-b border-gray-200 px-4 py-2 flex items-center gap-3 flex-shrink-0">
              {selectedFilter.type && (
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    selectedFilter.type === 'category' ? 'bg-blue-100 text-blue-700' :
                    selectedFilter.type === 'subcategory' ? 'bg-purple-100 text-purple-700' :
                    'bg-green-100 text-green-700'
                  }`}>
                    {selectedFilter.value.split('.').pop()}
                  </span>
                  <button
                    onClick={() => setSelectedFilter({ type: null, value: null })}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                </div>
              )}
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search prompts..."
                className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-everyone-blue"
              />
              {(searchQuery || selectedFilter.type) && (
                <button
                  onClick={clearFilters}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Clear
                </button>
              )}
              <span className="text-xs text-gray-400">{filteredPrompts.length} shown</span>
            </div>
          )}

          {/* Content Area */}
          <div className="flex-1 overflow-auto p-4">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-2 border-everyone-blue border-t-transparent rounded-full animate-spin"></div>
              </div>
            ) : view === 'coverage' ? (
              /* Coverage View */
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {Object.keys(criteriaByCategory).length === 0 ? (
                  <div className="p-8 text-center text-gray-400">No criteria data available</div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {Object.entries(criteriaByCategory).sort().map(([category, subcategories]) => {
                      const categoryCount = Object.values(subcategories).flat().reduce((sum, c) => sum + c.promptCount, 0);
                      const isSelectedCategory = selectedFilter.type === 'category' && selectedFilter.value === category;

                      return (
                        <div key={category}>
                          <div
                            className={`px-4 py-2 border-b border-gray-200 cursor-pointer transition-colors ${
                              isSelectedCategory ? 'bg-blue-100' : 'bg-blue-50 hover:bg-blue-100'
                            }`}
                            onClick={() => { handleFilterClick('category', category); setView('prompts'); }}
                          >
                            <span className="text-sm font-semibold text-blue-700 capitalize">{category}</span>
                            <span className={`text-xs ml-2 ${categoryCount > 0 ? 'text-green-600 font-medium' : 'text-gray-400'}`}>
                              ({categoryCount} prompts)
                            </span>
                          </div>

                          {Object.entries(subcategories).sort().map(([subcategory, items]) => {
                            const subcategoryCount = items.reduce((sum, c) => sum + c.promptCount, 0);

                            return (
                              <div key={subcategory}>
                                <div
                                  className="px-4 py-1.5 border-b border-gray-100 cursor-pointer bg-purple-50 hover:bg-purple-100"
                                  onClick={() => { handleFilterClick('subcategory', subcategory); setView('prompts'); }}
                                >
                                  <span className="text-xs font-medium text-purple-700 capitalize">{subcategory}</span>
                                  <span className={`text-xs ml-1 ${subcategoryCount > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                                    ({subcategoryCount})
                                  </span>
                                </div>

                                <table className="w-full text-sm">
                                  <tbody className="divide-y divide-gray-50">
                                    {items.sort((a, b) => a.name.localeCompare(b.name)).map(c => (
                                      <tr
                                        key={c.id}
                                        className="hover:bg-gray-50 cursor-pointer"
                                        onClick={() => { handleFilterClick('criteria', c.id); setView('prompts'); }}
                                      >
                                        <td className="px-4 py-2">
                                          <div className="font-medium text-gray-700">{c.name}</div>
                                          {c.description && (
                                            <div className="text-xs text-gray-400 truncate max-w-md">{c.description}</div>
                                          )}
                                        </td>
                                        <td className="px-4 py-2 text-center w-24">
                                          {c.promptCount > 0 ? (
                                            <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                                              {c.promptCount}
                                            </span>
                                          ) : (
                                            <span className="text-gray-300">—</span>
                                          )}
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                            );
                          })}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            ) : (
              /* Prompts View */
              <div className="space-y-4">
                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-gray-50 border-b border-gray-200">
                      <tr>
                        <th className="w-10 px-3 py-3">
                          <input
                            type="checkbox"
                            checked={filteredPrompts.length > 0 && filteredPrompts.every(p => p.selected)}
                            onChange={toggleSelectAll}
                            className="rounded border-gray-300"
                          />
                        </th>
                        <th className="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-64">Behavior</th>
                        <th className="text-left px-3 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Prompt</th>
                        {isEditable && <th className="w-10"></th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {filteredPrompts.length === 0 ? (
                        <tr>
                          <td colSpan={isEditable ? 4 : 3} className="px-4 py-8 text-center text-gray-400">
                            {prompts.length === 0 ? 'No prompts yet. Add one below.' : 'No prompts match your filter.'}
                          </td>
                        </tr>
                      ) : (
                        filteredPrompts.map((p) => {
                          const result = testResults[p.id];
                          return (
                            <tr key={p.id} className={`${p.selected ? 'bg-blue-50' : 'hover:bg-gray-50'} ${result ? 'border-b-0' : ''}`}>
                              <td className="px-3 py-2">
                                <input
                                  type="checkbox"
                                  checked={p.selected}
                                  onChange={() => toggleSelect(p.id)}
                                  className="rounded border-gray-300"
                                />
                              </td>
                              <td className="px-3 py-2">
                                {isEditable ? (
                                  <select
                                    value={p.criteria_id}
                                    onChange={(e) => updatePrompt(p.id, 'criteria_id', e.target.value)}
                                    className="w-full bg-gray-50 border border-gray-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-everyone-blue"
                                  >
                                    <option value="">Select behavior...</option>
                                    {Object.entries(criteriaBySubcategory).map(([sub, items]) => (
                                      <optgroup key={sub} label={sub}>
                                        {items.map(c => (
                                          <option key={c.id} value={c.id}>{c.name.replace(/_/g, ' ')}</option>
                                        ))}
                                      </optgroup>
                                    ))}
                                  </select>
                                ) : (
                                  <CriteriaBadge criteriaId={p.criteria_id} />
                                )}
                              </td>
                              <td className="px-3 py-2">
                                {isEditable ? (
                                  <input
                                    type="text"
                                    value={p.prompt}
                                    onChange={(e) => updatePrompt(p.id, 'prompt', e.target.value)}
                                    placeholder="Enter prompt text..."
                                    className="w-full bg-transparent border-0 focus:outline-none focus:ring-0 text-sm text-gray-700"
                                  />
                                ) : (
                                  <span className="text-sm text-gray-700">{p.prompt}</span>
                                )}
                              </td>
                              {isEditable && (
                                <td className="px-3 py-2">
                                  <button
                                    onClick={() => removePrompt(p.id)}
                                    className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                                  >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                  </button>
                                </td>
                              )}
                            </tr>
                          );
                        })
                      )}
                    </tbody>
                  </table>

                  {isEditable && (
                    <div className="px-3 py-2 border-t border-gray-100">
                      <button
                        onClick={addPrompt}
                        className="text-sm text-everyone-blue hover:text-everyone-blue/80 font-medium flex items-center gap-1"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                        </svg>
                        Add Prompt
                      </button>
                    </div>
                  )}
                </div>

                {/* Test Results */}
                {Object.keys(testResults).length > 0 && (
                  <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                    <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Test Results</span>
                      <button onClick={() => setTestResults({})} className="text-xs text-gray-500 hover:text-gray-700">
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
            )}
          </div>
        </div>

        {/* Right Sidebar - Test Controls */}
        {showTestPanel && (
          <div className="w-56 bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
            <div className="p-4 border-b border-gray-100">
              <div className="text-xs text-gray-400 uppercase tracking-wider font-medium mb-2">Test Endpoint</div>
              <select
                value={selectedEndpoint}
                onChange={(e) => setSelectedEndpoint(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
              >
                <option value="">Select...</option>
                {endpoints.map(e => (
                  <option key={e.id} value={e.id}>{e.name}</option>
                ))}
              </select>
            </div>

            <div className="p-4 flex-1">
              <button
                onClick={testSelected}
                disabled={!selectedEndpoint || !hasSelection || testing}
                className="w-full py-2.5 px-4 bg-everyone-blue hover:bg-everyone-blue/90 disabled:opacity-50 disabled:cursor-not-allowed rounded-lg text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {testing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                {testing ? 'Testing...' : `Test (${selectedPrompts.length})`}
              </button>

              <div className="mt-3 text-xs text-gray-500 text-center">
                {!selectedEndpoint && 'Select an endpoint'}
                {selectedEndpoint && !hasSelection && 'Select prompts to test'}
              </div>
            </div>

            <div className="p-4 border-t border-gray-100 bg-gray-50">
              <div className="text-xs text-gray-500">
                <strong>{selectedPrompts.length}</strong> of {prompts.length} selected
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Save Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">
              {isNewDataset ? 'Save Dataset' : 'Save as New Dataset'}
            </h3>
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
              <div className="text-sm text-gray-500">{validPromptsCount} prompts will be saved</div>
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
                className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue/90 disabled:opacity-50 transition-colors"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Modal */}
      {showDeleteModal && currentDataset && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Delete Dataset</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <strong>{currentDataset.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {showUploadModal && (
        <UploadDatasetModal
          onClose={() => setShowUploadModal(false)}
          onSuccess={() => {
            setShowUploadModal(false);
            loadDatasets();
          }}
        />
      )}
    </div>
  );
};

// Helper component for criteria badge display
const CriteriaBadge = ({ criteriaId }) => {
  const parts = (criteriaId || '').split('.');
  const criteria = parts[2] || parts[0] || '';
  return (
    <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
      {criteria || 'unassigned'}
    </span>
  );
};

// Upload Dataset Modal
const UploadDatasetModal = ({ onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [csvContent, setCsvContent] = useState('');
  const [fileName, setFileName] = useState('');
  const [error, setError] = useState('');
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileName(file.name);
    if (!name) setName(file.name.replace(/\.csv$/i, ''));

    const reader = new FileReader();
    reader.onload = (event) => setCsvContent(event.target.result);
    reader.onerror = () => setError('Failed to read file');
    reader.readAsText(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) { setError('Name is required'); return; }
    if (!csvContent.trim()) { setError('Please select a CSV file'); return; }

    setUploading(true);
    try {
      await api.createDataset({
        name: name.trim(),
        description: description.trim() || null,
        csv_content: csvContent,
      });
      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to upload dataset');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Upload Dataset</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my_custom_dataset"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Custom prompts for testing..."
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CSV File</label>
            <div className="flex gap-2">
              <input ref={fileInputRef} type="file" accept=".csv" onChange={handleFileChange} className="hidden" />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200 transition-colors"
              >
                Choose File
              </button>
              <span className="flex-1 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-500 truncate">
                {fileName || 'No file selected'}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">CSV must have columns: PromptID, Category, Prompt</p>
          </div>
          {error && <div className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">{error}</div>}
          <div className="flex gap-3 justify-end pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              Cancel
            </button>
            <button type="submit" disabled={uploading} className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue/90 disabled:opacity-50 transition-colors">
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Datasets;
