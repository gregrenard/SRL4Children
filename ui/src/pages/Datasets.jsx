import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { Topbar } from '../components/layout';
import { JudgesModal } from '../components/modals';

const PAGE_SIZE = 50;

const escapeHtml = (text) => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};

export const Datasets = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const [datasets, setDatasets] = useState([]);
  const [datasetName, setDatasetName] = useState(searchParams.get('dataset') || '');
  const [allPromptsCache, setAllPromptsCache] = useState(null);
  const [filteredPrompts, setFilteredPrompts] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPrompts, setTotalPrompts] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [principleFilter, setPrincipleFilter] = useState('');
  const [sortOrder, setSortOrder] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showJudgesModal, setShowJudgesModal] = useState(false);

  const totalPages = Math.ceil(totalPrompts / PAGE_SIZE) || 1;

  // Load datasets
  useEffect(() => {
    api.getDatasets()
      .then(data => {
        setDatasets(Array.isArray(data) ? data : []);
        if (!datasetName && data.length > 0) {
          setDatasetName(data[0].name);
        }
      })
      .catch(console.error);
  }, []);

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
      setFilteredPrompts(prompts);
      setTotalPrompts(prompts.length);
      setCurrentPage(1);
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
    setPrincipleFilter('');
    setSortOrder(null);
    setAllPromptsCache(null);
    setFilteredPrompts(null);
    setSearchParams({ dataset: name });
  };

  const applyFilters = () => {
    if (!allPromptsCache) return;

    let filtered = allPromptsCache.filter(p => {
      const matchesSearch = !searchQuery ||
        p.prompt.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.category.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesPrinciple = !principleFilter || p.category === principleFilter;
      return matchesSearch && matchesPrinciple;
    });

    if (sortOrder) {
      filtered = [...filtered].sort((a, b) => {
        const catA = a.category.toLowerCase();
        const catB = b.category.toLowerCase();
        return sortOrder === 'asc' ? catA.localeCompare(catB) : catB.localeCompare(catA);
      });
    }

    setFilteredPrompts(filtered);
    setTotalPrompts(filtered.length);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setSearchQuery('');
    setPrincipleFilter('');
    setSortOrder(null);
    if (allPromptsCache) {
      setFilteredPrompts(allPromptsCache);
      setTotalPrompts(allPromptsCache.length);
      setCurrentPage(1);
    }
  };

  const toggleSort = () => {
    if (sortOrder === null) setSortOrder('asc');
    else if (sortOrder === 'asc') setSortOrder('desc');
    else setSortOrder(null);
  };

  useEffect(() => {
    applyFilters();
  }, [sortOrder, principleFilter]);

  const filterByPrinciple = (principle) => {
    setPrincipleFilter(principle === principleFilter ? '' : principle);
  };

  // Get principle counts
  const principleCounts = allPromptsCache?.reduce((acc, p) => {
    acc[p.category] = (acc[p.category] || 0) + 1;
    return acc;
  }, {}) || {};

  const sortedPrinciples = Object.entries(principleCounts).sort((a, b) => b[1] - a[1]);

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

  return (
    <div className="min-h-screen flex flex-col">
      <Topbar onSettingsClick={() => setShowJudgesModal(true)} />
      {showJudgesModal && <JudgesModal onClose={() => setShowJudgesModal(false)} />}

      <div className="flex-1 max-w-7xl mx-auto px-4 py-6 w-full">
        {/* Dataset Selector */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Dataset:</span>
            <select
              value={datasetName}
              onChange={(e) => switchDataset(e.target.value)}
              className="bg-white border border-gray-200 rounded-lg px-3 py-1.5 text-sm font-medium text-everyone-blue focus:outline-none focus:border-everyone-blue"
            >
              <option value="">Select dataset...</option>
              {datasets.map(d => (
                <option key={d.name} value={d.name}>{d.name} ({d.rows})</option>
              ))}
            </select>
          </div>
          <span className="text-sm text-gray-500">
            {principleFilter
              ? `${totalPrompts} prompts (${principleFilter.split('.').pop()})`
              : `${totalPrompts} prompts total`
            }
          </span>
        </div>

        {/* Principles Summary */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-3">Principles in this dataset</div>
          <div className="flex flex-wrap gap-2">
            {loading ? (
              <span className="text-gray-400 text-sm">Loading...</span>
            ) : sortedPrinciples.length === 0 ? (
              <span className="text-gray-400 text-sm">No principles found</span>
            ) : (
              sortedPrinciples.map(([principle, count]) => {
                const shortName = principle.split('.').pop();
                const isActive = principleFilter === principle;
                return (
                  <button
                    key={principle}
                    onClick={() => filterByPrinciple(principle)}
                    className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'bg-purple-600 text-white'
                        : 'bg-purple-100 hover:bg-purple-200 text-purple-700'
                    }`}
                  >
                    {shortName} <span className={isActive ? 'text-purple-200' : 'text-purple-400'}>{count}</span>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Search */}
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-4 flex gap-4 items-center">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && applyFilters()}
              placeholder="Search prompts (press Enter)..."
              className="w-full bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-everyone-blue"
            />
          </div>
          <button
            onClick={applyFilters}
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

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto custom-scroll">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-16">#</th>
                  <th
                    className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider w-48 cursor-pointer hover:text-everyone-blue select-none"
                    onClick={toggleSort}
                  >
                    <span className="flex items-center gap-1">
                      Principle
                      <span className="text-everyone-blue">
                        {sortOrder === 'asc' ? '↑' : sortOrder === 'desc' ? '↓' : '↕'}
                      </span>
                    </span>
                  </th>
                  <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Prompt</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {loading ? (
                  <tr>
                    <td colSpan="3" className="px-4 py-8 text-center text-gray-400">Loading...</td>
                  </tr>
                ) : currentPrompts.length === 0 ? (
                  <tr>
                    <td colSpan="3" className="px-4 py-8 text-center text-gray-400">No prompts found</td>
                  </tr>
                ) : (
                  currentPrompts.map((p, i) => (
                    <tr key={p.id || i} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-gray-400 font-mono text-xs">{startIndex + i + 1}</td>
                      <td className="px-4 py-3">
                        <span className="inline-block px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                          {p.category.split('.').pop()}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{p.prompt}</td>
                    </tr>
                  ))
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
    </div>
  );
};

export default Datasets;
