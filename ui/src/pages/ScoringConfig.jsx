import { useState, useEffect } from 'react';
import api from '../api/client';
import { Topbar } from '../components/layout';
import { JudgesModal, GeneratorsModal, MatricesModal } from '../components/modals';

const AGE_GROUPS = [
  { value: 'child', label: 'Child (6-12)' },
  { value: 'teenager', label: 'Teenager (13-17)' },
  { value: 'young_adult', label: 'Young Adult (18-25)' },
];

const PRESENCE_LEVELS = [1, 2, 3, 4, 5];

export const ScoringConfig = () => {
  const [matrices, setMatrices] = useState([]);
  const [criteria, setCriteria] = useState([]);
  const [selectedMatrix, setSelectedMatrix] = useState('educational');
  const [selectedAge, setSelectedAge] = useState('child');
  const [matrixDetail, setMatrixDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editedEntries, setEditedEntries] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  // Modals
  const [showJudgesModal, setShowJudgesModal] = useState(false);
  const [showGeneratorsModal, setShowGeneratorsModal] = useState(false);
  const [showMatricesModal, setShowMatricesModal] = useState(false);
  const [showCloneModal, setShowCloneModal] = useState(false);

  // Load data
  useEffect(() => {
    loadMatrices();
    loadCriteria();
  }, []);

  useEffect(() => {
    if (selectedMatrix) {
      loadMatrixDetail(selectedMatrix);
    }
  }, [selectedMatrix]);

  const loadMatrices = async () => {
    try {
      const data = await api.getMatrices();
      setMatrices(data);
      // Select educational by default, or first non-flat matrix
      if (data.length > 0) {
        const defaultMatrix = data.find(m => m.name === 'educational') ||
                             data.find(m => m.name !== 'flat') ||
                             data[0];
        setSelectedMatrix(defaultMatrix.name);
      }
    } catch (err) {
      console.error('Failed to load matrices:', err);
    }
  };

  const loadCriteria = async () => {
    try {
      const data = await api.getCriteria();
      setCriteria(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load criteria:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMatrixDetail = async (name) => {
    try {
      const data = await api.getMatrix(name);
      setMatrixDetail(data);
      setEditedEntries({});
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to load matrix detail:', err);
      setMatrixDetail(null);
    }
  };

  // Get score for a behavior at a presence level
  const getScore = (behaviorId, presenceLevel) => {
    const key = `${behaviorId}-${selectedAge}-${presenceLevel}`;

    // Check edited entries first
    if (editedEntries[key] !== undefined) {
      return editedEntries[key];
    }

    // Find in matrix entries
    if (matrixDetail?.entries) {
      const entry = matrixDetail.entries.find(
        e => e.behavior_id === behaviorId &&
             e.age_group === selectedAge &&
             e.presence_level === presenceLevel
      );
      if (entry) return entry.score;
    }

    // Default: identity mapping (for flat matrix)
    return presenceLevel;
  };

  // Handle score change
  const handleScoreChange = (behaviorId, presenceLevel, value) => {
    const numValue = parseFloat(value);
    if (isNaN(numValue) || numValue < 0 || numValue > 5) return;

    const key = `${behaviorId}-${selectedAge}-${presenceLevel}`;
    setEditedEntries(prev => ({
      ...prev,
      [key]: Math.round(numValue * 10) / 10
    }));
    setHasChanges(true);
  };

  // Save changes
  const handleSave = async () => {
    if (!matrixDetail || matrixDetail.is_builtin) return;

    setSaving(true);
    try {
      // Build full entries list from current + edited
      const allEntries = [];

      for (const c of criteria) {
        for (const age of AGE_GROUPS) {
          for (const presence of PRESENCE_LEVELS) {
            const key = `${c.id}-${age.value}-${presence}`;
            const score = editedEntries[key] !== undefined
              ? editedEntries[key]
              : getScore(c.id, presence);

            allEntries.push({
              behavior_id: c.id,
              age_group: age.value,
              presence_level: presence,
              score: score
            });
          }
        }
      }

      await api.updateMatrixEntries(matrixDetail.id, allEntries);
      await loadMatrixDetail(selectedMatrix);
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to save:', err);
      alert('Failed to save changes: ' + err.message);
    } finally {
      setSaving(false);
    }
  };

  // Reset changes
  const handleReset = () => {
    setEditedEntries({});
    setHasChanges(false);
  };

  // Clone matrix
  const handleClone = async (newName, description) => {
    try {
      await api.cloneMatrix(selectedMatrix, { new_name: newName, description });
      await loadMatrices();
      setSelectedMatrix(newName);
      setShowCloneModal(false);
    } catch (err) {
      console.error('Failed to clone matrix:', err);
      alert('Failed to clone: ' + err.message);
    }
  };

  // Group criteria by category > subcategory
  const criteriaByCategory = criteria.reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = {};
    if (!acc[c.category][c.subcategory]) acc[c.category][c.subcategory] = [];
    acc[c.category][c.subcategory].push(c);
    return acc;
  }, {});

  const currentMatrix = matrices.find(m => m.name === selectedMatrix);
  const isReadOnly = currentMatrix?.is_builtin !== false;

  // Subcategory labels
  const subcategoryLabels = {
    anthropomorphic: 'Anthropomorphic Cues',
    interactional: 'Interactional Cues',
    relational: 'Relational Cues',
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Topbar
        onJudgesClick={() => setShowJudgesModal(true)}
        onGeneratorsClick={() => setShowGeneratorsModal(true)}
        onMatricesClick={() => setShowMatricesModal(true)}
      />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}
      {showGeneratorsModal && <GeneratorsModal onClose={() => setShowGeneratorsModal(false)} />}
      {showMatricesModal && <MatricesModal onClose={() => setShowMatricesModal(false)} />}

      <div className="flex-1 max-w-6xl mx-auto px-4 py-6 w-full">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-800 font-display">Scoring Configuration</h1>
          <p className="text-sm text-gray-500 mt-1">
            Configure how presence levels map to safety scores for each context and age group
          </p>
        </div>

        {/* Context & Age Selectors */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap items-center gap-6">
            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Context:</label>
              <select
                value={selectedMatrix}
                onChange={(e) => setSelectedMatrix(e.target.value)}
                className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm font-medium text-everyone-blue focus:outline-none focus:border-everyone-blue min-w-[180px]"
              >
                {matrices.filter(m => m.name !== 'flat').map(m => (
                  <option key={m.id} value={m.name}>
                    {m.name.charAt(0).toUpperCase() + m.name.slice(1)}
                    {m.is_builtin ? ' (built-in)' : ' (custom)'}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3">
              <label className="text-sm font-medium text-gray-700">Age Group:</label>
              <select
                value={selectedAge}
                onChange={(e) => setSelectedAge(e.target.value)}
                className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm font-medium text-everyone-blue focus:outline-none focus:border-everyone-blue min-w-[160px]"
              >
                {AGE_GROUPS.map(age => (
                  <option key={age.value} value={age.value}>{age.label}</option>
                ))}
              </select>
            </div>

            <div className="flex-1" />

            <button
              onClick={() => setShowCloneModal(true)}
              className="px-4 py-2 bg-everyone-blue text-white rounded-lg text-sm font-medium hover:bg-everyone-blue/90 transition-colors"
            >
              + Clone to Custom
            </button>
          </div>

          {matrixDetail?.description && (
            <div className="mt-3 text-sm text-gray-600 bg-blue-50 rounded-lg px-3 py-2">
              {matrixDetail.description}
            </div>
          )}
        </div>

        {/* Matrix Editor */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : Object.keys(criteriaByCategory).length === 0 ? (
            <div className="p-8 text-center text-gray-400">No criteria found</div>
          ) : (
            <div>
              {/* Table Header */}
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-3 flex items-center">
                <div className="flex-1 text-sm font-semibold text-gray-700">Behavior</div>
                <div className="w-20 text-center text-xs font-medium text-gray-500 uppercase">Weight</div>
                <div className="w-80 text-center text-xs font-medium text-gray-500 uppercase">
                  Presence Level → Score
                </div>
              </div>

              {/* Presence level headers */}
              <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 flex items-center">
                <div className="flex-1" />
                <div className="w-20" />
                <div className="w-80 flex">
                  {PRESENCE_LEVELS.map(p => (
                    <div key={p} className="flex-1 text-center text-xs font-medium text-gray-400">
                      P={p}
                    </div>
                  ))}
                </div>
              </div>

              {/* Criteria grouped by subcategory */}
              {Object.entries(criteriaByCategory).sort().map(([category, subcategories]) => (
                <div key={category}>
                  {Object.entries(subcategories).sort().map(([subcategory, items]) => (
                    <div key={subcategory}>
                      {/* Subcategory Header */}
                      <div className="bg-purple-50 px-4 py-2 border-b border-gray-100">
                        <span className="text-sm font-semibold text-purple-700">
                          {subcategoryLabels[subcategory] || subcategory}
                        </span>
                        <span className="text-xs text-purple-400 ml-2">({items.length} behaviors)</span>
                      </div>

                      {/* Behaviors */}
                      {items.sort((a, b) => a.name.localeCompare(b.name)).map(c => (
                        <div
                          key={c.id}
                          className="px-4 py-3 border-b border-gray-50 flex items-center hover:bg-gray-50"
                        >
                          <div className="flex-1">
                            <div className="font-medium text-gray-700 text-sm">{c.name}</div>
                            {c.description && (
                              <div className="text-xs text-gray-400 truncate max-w-md" title={c.description}>
                                {c.description}
                              </div>
                            )}
                          </div>

                          {/* Weight */}
                          <div className="w-20 text-center">
                            <span className="font-mono text-sm text-gray-400">1.0</span>
                          </div>

                          {/* Presence → Score mapping */}
                          <div className="w-80 flex gap-1">
                            {PRESENCE_LEVELS.map(presence => {
                              const score = getScore(c.id, presence);
                              const isEdited = editedEntries[`${c.id}-${selectedAge}-${presence}`] !== undefined;

                              return (
                                <div key={presence} className="flex-1">
                                  <input
                                    type="number"
                                    step="0.1"
                                    min="0"
                                    max="5"
                                    value={score}
                                    onChange={(e) => handleScoreChange(c.id, presence, e.target.value)}
                                    disabled={isReadOnly}
                                    className={`w-full text-center text-sm py-1.5 rounded border transition-colors
                                      ${isReadOnly
                                        ? 'bg-gray-50 border-gray-200 text-gray-500 cursor-not-allowed'
                                        : isEdited
                                          ? 'bg-yellow-50 border-yellow-300 text-yellow-700 font-medium'
                                          : 'bg-white border-gray-200 text-gray-700 hover:border-everyone-blue focus:border-everyone-blue focus:outline-none'
                                      }`}
                                  />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {isReadOnly ? (
              <span className="flex items-center gap-2">
                <svg className="w-4 h-4 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Built-in matrices are read-only. Clone to create an editable custom matrix.
              </span>
            ) : hasChanges ? (
              <span className="text-yellow-600 font-medium">You have unsaved changes</span>
            ) : (
              <span>Custom matrix - editable</span>
            )}
          </div>

          {!isReadOnly && (
            <div className="flex gap-3">
              <button
                onClick={handleReset}
                disabled={!hasChanges}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={!hasChanges || saving}
                className="px-6 py-2 bg-everyone-blue text-white rounded-lg text-sm font-medium hover:bg-everyone-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {saving && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Clone Modal */}
      {showCloneModal && (
        <CloneMatrixModal
          sourceName={selectedMatrix}
          onClose={() => setShowCloneModal(false)}
          onClone={handleClone}
        />
      )}
    </div>
  );
};

// Clone Matrix Modal
const CloneMatrixModal = ({ sourceName, onClose, onClone }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      await onClone(name.trim(), description.trim() || null);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Clone Matrix</h3>
        <p className="text-sm text-gray-600 mb-4">
          Create a custom copy of <strong>{sourceName}</strong> that you can edit.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="my-custom-educational"
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
              autoFocus
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Custom scoring for therapy bots..."
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            />
          </div>

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
              disabled={!name.trim() || creating}
              className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue/90 transition-colors disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Clone'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScoringConfig;
