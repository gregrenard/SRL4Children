import { useState } from 'react';
import { shortId } from '../../utils/helpers';

export const GuardrailsModal = ({ guardrail, onClose }) => {
  const [expandedId, setExpandedId] = useState(null);
  const [filter, setFilter] = useState('');

  const rules = guardrail.guardrails || [];

  // Group rules by criteria category (first part of criteria_id)
  const groupedRules = rules.reduce((acc, rule) => {
    const category = rule.criteria_id?.split('.')[1] || 'other';
    if (!acc[category]) acc[category] = [];
    acc[category].push(rule);
    return acc;
  }, {});

  const filteredRules = filter
    ? rules.filter(r =>
        r.rule_text?.toLowerCase().includes(filter.toLowerCase()) ||
        r.criteria_id?.toLowerCase().includes(filter.toLowerCase())
      )
    : null;

  const handleExportTxt = async () => {
    const text = rules.map(r => `[${r.criteria_id}]\n${r.rule_text}`).join('\n\n---\n\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guardrails-${shortId(guardrail.id)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleCopyAll = async () => {
    const text = rules.map(r => r.rule_text).join('\n\n');
    await navigator.clipboard.writeText(text);
  };

  const getCategoryColor = (category) => {
    const colors = {
      anthropomorphic: 'bg-purple-100 text-purple-700 border-purple-200',
      interactional: 'bg-blue-100 text-blue-700 border-blue-200',
      relational: 'bg-pink-100 text-pink-700 border-pink-200',
    };
    return colors[category] || 'bg-gray-100 text-gray-700 border-gray-200';
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-3">
            <button onClick={onClose} className="flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Guardrail Rules</h2>
              <div className="text-sm text-gray-500">
                <span className="font-mono">{shortId(guardrail.id)}</span>
                <span className="mx-2">·</span>
                <span>{rules.length} rules</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleCopyAll} className="flex items-center gap-2 px-3 py-1.5 text-gray-600 hover:bg-gray-100 rounded-lg text-sm font-medium transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy All
            </button>
            <button onClick={handleExportTxt} className="flex items-center gap-2 px-4 py-1.5 bg-everyone-blue hover:bg-everyone-blue-dark rounded-lg text-white text-sm font-medium transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter rules..."
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-everyone-blue/20 focus:border-everyone-blue"
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scroll p-4">
          {filteredRules ? (
            /* Filtered view - flat list */
            <div className="space-y-3">
              {filteredRules.length === 0 ? (
                <div className="text-center text-gray-500 py-8">No rules match your filter</div>
              ) : (
                filteredRules.map((rule) => (
                  <div
                    key={rule.id}
                    onClick={() => setExpandedId(expandedId === rule.id ? null : rule.id)}
                    className="bg-gray-50 rounded-lg p-4 border border-gray-200 cursor-pointer hover:border-gray-300 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${getCategoryColor(rule.criteria_id?.split('.')[1])}`}>
                        {rule.criteria_id?.split('.')[1] || 'other'}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm text-gray-700 ${expandedId === rule.id ? '' : 'line-clamp-2'}`}>
                          {rule.rule_text}
                        </div>
                        <div className="text-xs text-gray-400 mt-1 font-mono">
                          {rule.criteria_id}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : (
            /* Grouped view */
            <div className="space-y-6">
              {Object.entries(groupedRules).map(([category, categoryRules]) => (
                <div key={category}>
                  <div className="flex items-center gap-2 mb-3">
                    <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${getCategoryColor(category)}`}>
                      {category}
                    </span>
                    <span className="text-xs text-gray-400">{categoryRules.length} rules</span>
                  </div>
                  <div className="space-y-2">
                    {categoryRules.map((rule) => (
                      <div
                        key={rule.id}
                        onClick={() => setExpandedId(expandedId === rule.id ? null : rule.id)}
                        className="bg-white rounded-lg p-3 border border-gray-200 cursor-pointer hover:border-gray-300 transition-colors"
                      >
                        <div className={`text-sm text-gray-700 ${expandedId === rule.id ? '' : 'line-clamp-2'}`}>
                          {rule.rule_text}
                        </div>
                        <div className="text-xs text-gray-400 mt-1 font-mono">
                          {rule.criteria_id?.split('.').slice(2).join('.')}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default GuardrailsModal;
