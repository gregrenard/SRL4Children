import { useState, useEffect } from 'react';
import api from '../api/client';
import { Topbar } from '../components/layout';
import { JudgesModal, GeneratorsModal } from '../components/modals';

export const Judges = () => {
  const [judges, setJudges] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [selectedJudgeName, setSelectedJudgeName] = useState('');
  const [currentJudge, setCurrentJudge] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showJudgesModal, setShowJudgesModal] = useState(false);
  const [showGeneratorsModal, setShowGeneratorsModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  // Load judges list
  const loadJudges = () => {
    api.getEvalJudges()
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setJudges(list);
        if (!selectedJudgeName && list.length > 0) {
          setSelectedJudgeName(list.find(j => j.name === 'default')?.name || list[0].name);
        }
      })
      .catch(console.error);
  };

  // Load criteria definitions
  const loadCriteria = () => {
    api.getCriteria()
      .then(data => setCriteria(Array.isArray(data) ? data : []))
      .catch(console.error);
  };

  // Load selected judge details
  const loadJudgeDetails = async () => {
    if (!selectedJudgeName) return;
    setLoading(true);
    try {
      const data = await api.getEvalJudge(selectedJudgeName);
      setCurrentJudge(data);
    } catch (err) {
      console.error('Failed to load judge:', err);
      setCurrentJudge(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJudges();
    loadCriteria();
  }, []);

  useEffect(() => {
    if (selectedJudgeName) {
      loadJudgeDetails();
    }
  }, [selectedJudgeName]);

  const switchJudge = (name) => {
    setSelectedJudgeName(name);
  };

  const handleDelete = async () => {
    if (!currentJudge) return;
    try {
      await api.deleteEvalJudge(currentJudge.id);
      setShowDeleteModal(false);
      const remaining = judges.filter(j => j.id !== currentJudge.id);
      if (remaining.length > 0) {
        switchJudge(remaining[0].name);
      } else {
        setSelectedJudgeName('');
        setCurrentJudge(null);
      }
      loadJudges();
    } catch (err) {
      console.error('Failed to delete judge:', err);
      alert('Failed to delete judge: ' + err.message);
    }
  };

  // Build implementation map for quick lookup
  const implementationMap = (currentJudge?.implementations || []).reduce((acc, impl) => {
    acc[impl.criteria_id] = impl;
    return acc;
  }, {});

  // Get weight for a criteria
  const getWeight = (criteriaId) => {
    if (!currentJudge?.weights) return 1.0;
    const parts = criteriaId.split('.');
    const [category, subcategory, criteriaName] = parts;

    if (currentJudge.weights.criteria?.[criteriaId]) return currentJudge.weights.criteria[criteriaId];
    if (currentJudge.weights.criteria?.[criteriaName]) return currentJudge.weights.criteria[criteriaName];
    if (currentJudge.weights.subcategories?.[subcategory]) return currentJudge.weights.subcategories[subcategory];
    if (currentJudge.weights.categories?.[category]) return currentJudge.weights.categories[category];

    return 1.0;
  };

  // Group criteria by category > subcategory
  const criteriaByCategory = criteria.reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = {};
    if (!acc[c.category][c.subcategory]) acc[c.category][c.subcategory] = [];
    acc[c.category][c.subcategory].push(c);
    return acc;
  }, {});

  return (
    <div className="min-h-screen flex flex-col">
      <Topbar
        onJudgesClick={() => setShowJudgesModal(true)}
        onGeneratorsClick={() => setShowGeneratorsModal(true)}
      />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}
      {showGeneratorsModal && <GeneratorsModal onClose={() => setShowGeneratorsModal(false)} />}

      <div className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        {/* Judge Selector */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-gray-500">Judge:</span>
            <select
              value={selectedJudgeName}
              onChange={(e) => switchJudge(e.target.value)}
              className="bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-medium text-everyone-blue focus:outline-none focus:border-everyone-blue"
            >
              <option value="">Select judge...</option>
              {judges.map(j => (
                <option key={j.id} value={j.name}>
                  {j.name} ({j.implementation_count} criteria)
                </option>
              ))}
            </select>
            {currentJudge && (
              <>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  currentJudge.is_builtin
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-green-100 text-green-700'
                }`}>
                  {currentJudge.is_builtin ? 'Built-in' : 'Custom'}
                </span>
                {currentJudge.inherits_from_name && (
                  <span className="text-xs text-gray-400">
                    inherits from <span className="text-gray-600">{currentJudge.inherits_from_name}</span>
                  </span>
                )}
              </>
            )}
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3 py-1.5 bg-everyone-blue text-white rounded-lg text-sm hover:bg-everyone-blue-dark transition-colors"
            >
              Create Judge
            </button>
            {currentJudge && !currentJudge.is_builtin && (
              <button
                onClick={() => setShowDeleteModal(true)}
                className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            )}
          </div>
          <span className="text-sm text-gray-500">
            {criteria.length} criteria total
          </span>
        </div>

        {/* Judge Description */}
        {currentJudge?.description && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-700">
            {currentJudge.description}
          </div>
        )}

        {/* Criteria Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : Object.keys(criteriaByCategory).length === 0 ? (
            <div className="p-8 text-center text-gray-400">No criteria found</div>
          ) : (
            <div className="divide-y divide-gray-200">
              {Object.entries(criteriaByCategory).sort().map(([category, subcategories]) => (
                <div key={category}>
                  {/* Category Header */}
                  <div className="bg-blue-50 px-4 py-2 border-b border-gray-200">
                    <span className="text-sm font-semibold text-blue-700 capitalize">{category}</span>
                    <span className="text-xs text-blue-500 ml-2">
                      ({Object.values(subcategories).flat().length} criteria)
                    </span>
                  </div>

                  {Object.entries(subcategories).sort().map(([subcategory, items]) => (
                    <div key={subcategory}>
                      {/* Subcategory Header */}
                      <div className="bg-purple-50 px-4 py-1.5 border-b border-gray-100">
                        <span className="text-xs font-medium text-purple-700 capitalize">{subcategory}</span>
                        <span className="text-xs text-purple-400 ml-1">({items.length})</span>
                      </div>

                      {/* Criteria Table */}
                      <table className="w-full text-sm">
                        <thead className="bg-gray-50 text-xs text-gray-500">
                          <tr>
                            <th className="text-left px-4 py-2 font-medium">Criteria</th>
                            <th className="text-center px-2 py-2 font-medium w-20">Weight</th>
                            <th className="text-center px-2 py-2 font-medium w-20">Version</th>
                            <th className="text-left px-2 py-2 font-medium w-36">Author</th>
                            <th className="text-left px-2 py-2 font-medium w-28">Created</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {items.sort((a, b) => a.name.localeCompare(b.name)).map(c => {
                            const impl = implementationMap[c.id];
                            const weight = getWeight(c.id);
                            return (
                              <tr key={c.id} className="hover:bg-gray-50">
                                <td className="px-4 py-2">
                                  <div className="font-medium text-gray-700">{c.name}</div>
                                  {c.description && (
                                    <div className="text-xs text-gray-400 truncate max-w-md" title={c.description}>
                                      {c.description}
                                    </div>
                                  )}
                                </td>
                                <td className="px-2 py-2 text-center">
                                  <span className={`font-mono ${weight !== 1.0 ? 'text-orange-600 font-semibold' : 'text-gray-400'}`}>
                                    {weight.toFixed(1)}
                                  </span>
                                </td>
                                <td className="px-2 py-2 text-center text-gray-500">
                                  {impl?.version || '—'}
                                </td>
                                <td className="px-2 py-2 text-gray-500 truncate" title={impl?.author}>
                                  {impl?.author || '—'}
                                </td>
                                <td className="px-2 py-2 text-gray-400">
                                  {impl?.created_at?.split('T')[0] || '—'}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Create Judge Modal */}
      {showCreateModal && (
        <CreateJudgeModal
          judges={judges}
          criteriaByCategory={criteriaByCategory}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadJudges();
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && currentJudge && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Delete Judge</h3>
            <p className="text-gray-600 mb-6">
              Are you sure you want to delete <strong>{currentJudge.name}</strong>? This action cannot be undone.
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
    </div>
  );
};

// Create Judge Modal
const CreateJudgeModal = ({ judges, criteriaByCategory, onClose, onSuccess }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [inheritsFrom, setInheritsFrom] = useState('');
  const [weights, setWeights] = useState({});
  const [error, setError] = useState('');
  const [creating, setCreating] = useState(false);

  const handleWeightChange = (subcategory, value) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue) && value !== '') return;

    setWeights(prev => {
      const newSubcategories = { ...(prev.subcategories || {}) };
      if (value === '' || isNaN(numValue)) {
        delete newSubcategories[subcategory];
      } else {
        newSubcategories[subcategory] = Math.max(0, Math.min(5, numValue));
      }
      return { ...prev, subcategories: newSubcategories };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (!inheritsFrom) {
      setError('Please select a parent judge to inherit from');
      return;
    }

    const hasWeights = weights.subcategories && Object.keys(weights.subcategories).length > 0;

    setCreating(true);
    try {
      await api.createEvalJudge({
        name: name.trim(),
        description: description.trim() || null,
        inherits_from: inheritsFrom,
        weights: hasWeights ? weights : null,
      });
      onSuccess();
    } catch (err) {
      setError(err.message || 'Failed to create judge');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-xl p-6 max-w-2xl w-full mx-4 my-8">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Create Evaluation Judge</h3>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="my_custom_judge"
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Inherit From</label>
              <select
                value={inheritsFrom}
                onChange={(e) => setInheritsFrom(e.target.value)}
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
              >
                <option value="">Select parent judge...</option>
                {judges.map(j => (
                  <option key={j.id} value={j.id}>{j.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Custom weights for specific use case..."
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            />
          </div>

          {/* Weight Overrides */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Weight Overrides (optional)
            </label>
            <p className="text-xs text-gray-400 mb-3">
              Leave blank to use parent weights. Values: 0.0 - 5.0 (higher = more important)
            </p>
            <div className="max-h-64 overflow-y-auto border border-gray-200 rounded-lg p-3 space-y-3">
              {Object.entries(criteriaByCategory).map(([category, subcategories]) => (
                <div key={category}>
                  <div className="text-xs font-medium text-gray-600 uppercase mb-2">{category}</div>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.keys(subcategories).sort().map(subcategory => (
                      <div key={subcategory} className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 flex-1 truncate" title={subcategory}>
                          {subcategory}
                        </span>
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="5"
                          value={weights.subcategories?.[subcategory] ?? ''}
                          onChange={(e) => handleWeightChange(subcategory, e.target.value)}
                          placeholder="—"
                          className="w-16 bg-gray-50 border border-gray-200 rounded px-2 py-1 text-xs text-center focus:outline-none focus:border-everyone-blue"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {error && (
            <div className="text-red-500 text-sm bg-red-50 p-3 rounded-lg">
              {error}
            </div>
          )}

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating}
              className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue-dark transition-colors disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Judges;
