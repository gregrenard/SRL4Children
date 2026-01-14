import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { Topbar } from '../components/layout';
import { JudgesModal, GeneratorsModal } from '../components/modals';

const PAGE_SIZE = 50;

export const Datasets = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [datasets, setDatasets] = useState([]);
  const [datasetName, setDatasetName] = useState(searchParams.get('dataset') || '');
  const [currentDataset, setCurrentDataset] = useState(null);
  const [allCriteria, setAllCriteria] = useState([]);
  const [allPromptsCache, setAllPromptsCache] = useState(null);
  const [filteredPrompts, setFilteredPrompts] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPrompts, setTotalPrompts] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState({ type: null, value: null }); // { type: 'category'|'subcategory'|'criteria', value: string }
  const [loading, setLoading] = useState(false);
  const [showJudgesModal, setShowJudgesModal] = useState(false);
  const [showGeneratorsModal, setShowGeneratorsModal] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const totalPages = Math.ceil(totalPrompts / PAGE_SIZE) || 1;

  // Load datasets
  const loadDatasets = () => {
    api.getDatasets()
      .then(data => {
        const list = Array.isArray(data) ? data : [];
        setDatasets(list);
        if (!datasetName && list.length > 0) {
          setDatasetName(list[0].name);
        }
      })
      .catch(console.error);
  };

  // Load all criteria for coverage comparison
  const loadCriteria = () => {
    api.getCriteria()
      .then(data => setAllCriteria(Array.isArray(data) ? data : []))
      .catch(console.error);
  };

  useEffect(() => {
    loadDatasets();
    loadCriteria();
  }, []);

  // Update currentDataset when datasetName or datasets change
  useEffect(() => {
    const ds = datasets.find(d => d.name === datasetName);
    setCurrentDataset(ds || null);
  }, [datasetName, datasets]);

  // Load prompts when dataset changes
  useEffect(() => {
    if (datasetName) {
      loadAllPrompts();
    }
  }, [datasetName]);

  const loadAllPrompts = async () => {
    setLoading(true);
    try {
      const data = await api.getDatasetPrompts(datasetName, 1, 10000);
      const prompts = data.prompts || [];
      setAllPromptsCache(prompts);
      applyFiltersToPrompts(prompts, selectedFilter, searchQuery);
    } catch (err) {
      console.error('Failed to load prompts:', err);
      setAllPromptsCache([]);
      setFilteredPrompts([]);
      setTotalPrompts(0);
    } finally {
      setLoading(false);
    }
  };

  const switchDataset = (name) => {
    setDatasetName(name);
    setSearchQuery('');
    setSelectedFilter({ type: null, value: null });
    setAllPromptsCache(null);
    setFilteredPrompts(null);
    setSearchParams({ dataset: name });
  };

  // Sort prompts by category > subcategory > criteria
  const sortPrompts = (prompts) => {
    return [...prompts].sort((a, b) => {
      const partsA = (a.criteria_id || a.category || '').toLowerCase().split('.');
      const partsB = (b.criteria_id || b.category || '').toLowerCase().split('.');

      const catCompare = (partsA[0] || '').localeCompare(partsB[0] || '');
      if (catCompare !== 0) return catCompare;

      const subCompare = (partsA[1] || '').localeCompare(partsB[1] || '');
      if (subCompare !== 0) return subCompare;

      const critCompare = (partsA[2] || '').localeCompare(partsB[2] || '');
      return critCompare;
    });
  };

  const applyFiltersToPrompts = (prompts, filter, search) => {
    if (!prompts) return;

    let filtered = prompts.filter(p => {
      const criteriaId = p.criteria_id || p.category || '';
      const parts = criteriaId.split('.');

      // Apply hierarchical filter
      if (filter.type === 'category' && parts[0] !== filter.value) return false;
      if (filter.type === 'subcategory' && parts[1] !== filter.value) return false;
      if (filter.type === 'criteria' && criteriaId !== filter.value) return false;

      // Apply search
      if (search) {
        const matchesSearch = p.prompt.toLowerCase().includes(search.toLowerCase()) ||
          criteriaId.toLowerCase().includes(search.toLowerCase());
        if (!matchesSearch) return false;
      }

      return true;
    });

    filtered = sortPrompts(filtered);
    setFilteredPrompts(filtered);
    setTotalPrompts(filtered.length);
    setCurrentPage(1);
  };

  const handleFilterClick = (type, value) => {
    // Toggle off if clicking same filter
    if (selectedFilter.type === type && selectedFilter.value === value) {
      setSelectedFilter({ type: null, value: null });
      applyFiltersToPrompts(allPromptsCache, { type: null, value: null }, searchQuery);
    } else {
      setSelectedFilter({ type, value });
      applyFiltersToPrompts(allPromptsCache, { type, value }, searchQuery);
    }
  };

  const handleSearch = () => {
    applyFiltersToPrompts(allPromptsCache, selectedFilter, searchQuery);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setSelectedFilter({ type: null, value: null });
    applyFiltersToPrompts(allPromptsCache, { type: null, value: null }, '');
  };

  // Build criteria counts from prompts
  const criteriaCounts = (allPromptsCache || []).reduce((acc, p) => {
    const criteriaId = p.criteria_id || p.category;
    acc[criteriaId] = (acc[criteriaId] || 0) + 1;
    return acc;
  }, {});

  // Group all criteria by category > subcategory, with counts from dataset
  const criteriaByCategory = allCriteria.reduce((acc, c) => {
    if (!acc[c.category]) acc[c.category] = {};
    if (!acc[c.category][c.subcategory]) acc[c.category][c.subcategory] = [];
    acc[c.category][c.subcategory].push({
      ...c,
      promptCount: criteriaCounts[c.id] || 0
    });
    return acc;
  }, {});

  // Calculate totals
  const totalPresent = allCriteria.filter(c => criteriaCounts[c.id] > 0).length;
  const totalMissing = allCriteria.length - totalPresent;

  // Pagination
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const currentPrompts = filteredPrompts?.slice(startIndex, startIndex + PAGE_SIZE) || [];

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
      window.scrollTo(0, 0);
    }
  };

  const nextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
      window.scrollTo(0, 0);
    }
  };

  const handleDelete = async () => {
    if (!currentDataset) return;
    try {
      await api.deleteDataset(currentDataset.id);
      setShowDeleteModal(false);
      const remaining = datasets.filter(d => d.id !== currentDataset.id);
      if (remaining.length > 0) {
        switchDataset(remaining[0].name);
      } else {
        setDatasetName('');
        setAllPromptsCache(null);
        setFilteredPrompts(null);
      }
      loadDatasets();
    } catch (err) {
      console.error('Failed to delete dataset:', err);
      alert('Failed to delete dataset: ' + err.message);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Topbar
        onJudgesClick={() => setShowJudgesModal(true)}
        onGeneratorsClick={() => setShowGeneratorsModal(true)}
      />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}
      {showGeneratorsModal && <GeneratorsModal onClose={() => setShowGeneratorsModal(false)} />}

      <div className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        {/* Dataset Selector */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <span className="text-gray-500">Dataset:</span>
            <select
              value={datasetName}
              onChange={(e) => switchDataset(e.target.value)}
              className="bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-medium text-everyone-blue focus:outline-none focus:border-everyone-blue"
            >
              <option value="">Select dataset...</option>
              {datasets.map(d => (
                <option key={d.id} value={d.name}>
                  {d.name} ({d.prompt_count || d.rows || 0} prompts)
                </option>
              ))}
            </select>
            {currentDataset && (
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                currentDataset.is_builtin
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-green-100 text-green-700'
              }`}>
                {currentDataset.is_builtin ? 'Built-in' : 'Custom'}
              </span>
            )}
            <button
              onClick={() => setShowUploadModal(true)}
              className="px-3 py-1.5 bg-everyone-blue text-white rounded-lg text-sm hover:bg-everyone-blue-dark transition-colors"
            >
              Upload Dataset
            </button>
            {currentDataset && !currentDataset.is_builtin && (
              <button
                onClick={() => setShowDeleteModal(true)}
                className="px-3 py-1.5 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            )}
          </div>
          <div className="text-sm text-gray-500">
            <span className="text-green-600 font-medium">{totalPresent}</span> covered /
            <span className="text-gray-400 ml-1">{totalMissing}</span> missing
          </div>
        </div>

        {/* Criteria Coverage Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden mb-4">
          {loading ? (
            <div className="p-8 text-center text-gray-400">Loading...</div>
          ) : Object.keys(criteriaByCategory).length === 0 ? (
            <div className="p-8 text-center text-gray-400">No criteria data available</div>
          ) : (
            <div className="divide-y divide-gray-200">
              {Object.entries(criteriaByCategory).sort().map(([category, subcategories]) => {
                const categoryCount = Object.values(subcategories).flat().reduce((sum, c) => sum + c.promptCount, 0);
                const isSelectedCategory = selectedFilter.type === 'category' && selectedFilter.value === category;

                return (
                  <div key={category}>
                    {/* Category Header */}
                    <div
                      className={`px-4 py-2 border-b border-gray-200 cursor-pointer transition-colors ${
                        isSelectedCategory ? 'bg-blue-100' : 'bg-blue-50 hover:bg-blue-100'
                      }`}
                      onClick={() => handleFilterClick('category', category)}
                    >
                      <span className="text-sm font-semibold text-blue-700 capitalize">{category}</span>
                      <span className={`text-xs ml-2 ${categoryCount > 0 ? 'text-green-600 font-medium' : 'text-gray-400'}`}>
                        ({categoryCount} prompts)
                      </span>
                    </div>

                    {Object.entries(subcategories).sort().map(([subcategory, items]) => {
                      const subcategoryCount = items.reduce((sum, c) => sum + c.promptCount, 0);
                      const isSelectedSubcategory = selectedFilter.type === 'subcategory' && selectedFilter.value === subcategory;

                      return (
                        <div key={subcategory}>
                          {/* Subcategory Header */}
                          <div
                            className={`px-4 py-1.5 border-b border-gray-100 cursor-pointer transition-colors ${
                              isSelectedSubcategory ? 'bg-purple-100' : 'bg-purple-50 hover:bg-purple-100'
                            }`}
                            onClick={() => handleFilterClick('subcategory', subcategory)}
                          >
                            <span className="text-xs font-medium text-purple-700 capitalize">{subcategory}</span>
                            <span className={`text-xs ml-1 ${subcategoryCount > 0 ? 'text-green-600' : 'text-gray-400'}`}>
                              ({subcategoryCount} prompts)
                            </span>
                          </div>

                          {/* Criteria Table */}
                          <table className="w-full text-sm">
                            <thead className="bg-gray-50 text-xs text-gray-500">
                              <tr>
                                <th className="text-left px-4 py-2 font-medium">Criteria</th>
                                <th className="text-center px-4 py-2 font-medium w-32">Prompts</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-50">
                              {items.sort((a, b) => a.name.localeCompare(b.name)).map(c => {
                                const isSelected = selectedFilter.type === 'criteria' && selectedFilter.value === c.id;
                                return (
                                  <tr
                                    key={c.id}
                                    className={`cursor-pointer transition-colors ${
                                      isSelected ? 'bg-green-100' : 'hover:bg-gray-50'
                                    }`}
                                    onClick={() => handleFilterClick('criteria', c.id)}
                                  >
                                    <td className="px-4 py-2">
                                      <div className="font-medium text-gray-700">{c.name}</div>
                                      {c.description && (
                                        <div className="text-xs text-gray-400 truncate max-w-md" title={c.description}>
                                          {c.description}
                                        </div>
                                      )}
                                    </td>
                                    <td className="px-4 py-2 text-center">
                                      {c.promptCount > 0 ? (
                                        <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 rounded font-medium">
                                          {c.promptCount}
                                        </span>
                                      ) : (
                                        <span className="text-gray-300">—</span>
                                      )}
                                    </td>
                                  </tr>
                                );
                              })}
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

        {/* Active Filter & Search */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
          <div className="flex gap-4 items-center">
            {selectedFilter.type && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Filtering by:</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  selectedFilter.type === 'category' ? 'bg-blue-100 text-blue-700' :
                  selectedFilter.type === 'subcategory' ? 'bg-purple-100 text-purple-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  {selectedFilter.value.split('.').pop()}
                </span>
                <button
                  onClick={() => handleFilterClick(selectedFilter.type, selectedFilter.value)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
            )}
            <div className="flex-1">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search prompts..."
                className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
              />
            </div>
            <button
              onClick={handleSearch}
              className="px-4 py-2 bg-everyone-blue text-white rounded-lg text-sm hover:bg-everyone-blue-dark transition-colors"
            >
              Search
            </button>
            <button
              onClick={clearFilters}
              className="px-3 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm hover:bg-gray-200 transition-colors"
            >
              Clear
            </button>
          </div>
        </div>

        {/* Prompts Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">
              Prompts {selectedFilter.type && `(filtered)`}
            </span>
            <span className="text-xs text-gray-500">{totalPrompts} prompts</span>
          </div>
          <div className="overflow-x-auto custom-scroll">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-12">#</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-28">Category</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-36">Subcategory</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-36">Criteria</th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Prompt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : currentPrompts.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-gray-400">No prompts found</td>
                  </tr>
                ) : (
                  currentPrompts.map((p, i) => {
                    const parts = (p.criteria_id || p.category || '').split('.');
                    const category = parts[0] || '';
                    const subcategory = parts[1] || '';
                    const criteria = parts[2] || parts[0] || '';
                    return (
                      <tr key={p.id || i} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-gray-400 font-mono text-xs">{startIndex + i + 1}</td>
                        <td className="px-4 py-3">
                          <span className="inline-block px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">
                            {category}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-block px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs">
                            {subcategory}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <span className="inline-block px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-medium">
                            {criteria}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-gray-700">{p.prompt}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4 text-sm">
          <button
            onClick={prevPage}
            disabled={currentPage <= 1}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-gray-500">Page {currentPage} of {totalPages}</span>
          <button
            onClick={nextPage}
            disabled={currentPage >= totalPages}
            className="px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>

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

      {/* Delete Confirmation Modal */}
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
    </div>
  );
};

// Upload Dataset Modal Component
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
    if (!name) {
      setName(file.name.replace(/\.csv$/i, ''));
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      setCsvContent(event.target.result);
    };
    reader.onerror = () => {
      setError('Failed to read file');
    };
    reader.readAsText(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!name.trim()) {
      setError('Name is required');
      return;
    }
    if (!csvContent.trim()) {
      setError('Please select a CSV file');
      return;
    }

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
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                className="hidden"
              />
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
            <p className="text-xs text-gray-400 mt-1">
              CSV must have columns: PromptID, Category, Prompt
            </p>
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
              disabled={uploading}
              className="px-4 py-2 bg-everyone-blue text-white rounded-lg hover:bg-everyone-blue-dark transition-colors disabled:opacity-50"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Datasets;
