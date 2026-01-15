import { useState, useEffect } from 'react';
import api from '../../api/client';
import { shortId } from '../../utils/helpers';
import { LoadingSpinner } from '../common';

export const AttackRecordsModal = ({ attack, onClose }) => {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [expandedId, setExpandedId] = useState(null);
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    api.getAttackRecords(attack.id, page, pageSize)
      .then(data => {
        setRecords(data.records);
        setTotal(data.total);
      })
      .catch(err => console.error('Failed to load records:', err))
      .finally(() => setLoading(false));
  }, [attack.id, page]);

  const totalPages = Math.ceil(total / pageSize);

  const truncate = (text, maxLen = 100) => {
    if (!text) return '-';
    return text.length > maxLen ? text.slice(0, maxLen) + '...' : text;
  };

  const getCriteriaShortName = (criteriaId) => {
    if (!criteriaId) return '-';
    const parts = criteriaId.split('.');
    return parts[parts.length - 1].replace(/_/g, ' ');
  };

  const getCategoryBadge = (criteriaId) => {
    if (!criteriaId) return null;
    const parts = criteriaId.split('.');
    if (parts.length < 2) return null;
    const subcat = parts[1];
    const colors = {
      anthropomorphic: 'bg-purple-100 text-purple-700',
      interactional: 'bg-blue-100 text-blue-700',
      relational: 'bg-pink-100 text-pink-700',
    };
    return (
      <span className={`px-2 py-0.5 rounded-full text-xs ${colors[subcat] || 'bg-gray-100 text-gray-700'}`}>
        {subcat}
      </span>
    );
  };

  const handleExportCsv = async () => {
    // Fetch all records for export
    const allData = await api.getAttackRecords(attack.id, 1, 10000);
    const rows = [
      ['ID', 'Criteria', 'Prompt', 'Response', 'Error'],
      ...allData.records.map(r => [
        r.id,
        r.criteria_id,
        `"${(r.prompt || '').replace(/"/g, '""')}"`,
        `"${(r.response || '').replace(/"/g, '""')}"`,
        `"${(r.error || '').replace(/"/g, '""')}"`,
      ])
    ];
    const csv = rows.map(row => row.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attack-${shortId(attack.id)}-records.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-7xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <button onClick={onClose} className="flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <div>
              <h2 className="text-lg font-semibold text-gray-800">Attack Records</h2>
              <div className="text-sm text-gray-500">
                <span className="font-mono">{shortId(attack.id)}</span>
                <span className="mx-2">·</span>
                <span>{attack.dataset_name}</span>
                <span className="mx-2">·</span>
                <span>{total} records</span>
              </div>
            </div>
          </div>
          <button onClick={handleExportCsv} className="flex items-center gap-2 px-4 py-2 bg-everyone-blue hover:bg-everyone-blue-dark rounded-xl text-white text-sm font-medium transition-colors">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export CSV
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto custom-scroll">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <LoadingSpinner />
            </div>
          ) : records.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No records found</div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50 sticky top-0">
                <tr className="text-left text-xs text-gray-500 uppercase tracking-wider">
                  <th className="px-4 py-3 w-12">#</th>
                  <th className="px-4 py-3 w-40">Criteria</th>
                  <th className="px-4 py-3">Prompt</th>
                  <th className="px-4 py-3">Response</th>
                  <th className="px-4 py-3 w-20">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {records.map((record, idx) => {
                  const isExpanded = expandedId === record.id;
                  const rowNum = (page - 1) * pageSize + idx + 1;
                  return (
                    <tr
                      key={record.id}
                      onClick={() => setExpandedId(isExpanded ? null : record.id)}
                      className={`cursor-pointer transition-colors ${isExpanded ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
                    >
                      <td className="px-4 py-3 text-sm text-gray-400 font-mono">{rowNum}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-col gap-1">
                          {getCategoryBadge(record.criteria_id)}
                          <span className="text-xs text-gray-600">{getCriteriaShortName(record.criteria_id)}</span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {isExpanded ? (
                          <div className="whitespace-pre-wrap bg-gray-100 rounded-lg p-3 text-xs font-mono max-h-48 overflow-y-auto">
                            {record.prompt}
                          </div>
                        ) : (
                          truncate(record.prompt, 80)
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-700">
                        {isExpanded ? (
                          <div className="whitespace-pre-wrap bg-gray-100 rounded-lg p-3 text-xs font-mono max-h-48 overflow-y-auto">
                            {record.response || record.error || '-'}
                          </div>
                        ) : (
                          truncate(record.response || record.error, 80)
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {record.error ? (
                          <span className="text-red-500 text-xs">Error</span>
                        ) : record.response ? (
                          <span className="text-green-500 text-xs">OK</span>
                        ) : (
                          <span className="text-gray-400 text-xs">-</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 bg-gray-50">
            <div className="text-sm text-gray-500">
              Showing {(page - 1) * pageSize + 1}-{Math.min(page * pageSize, total)} of {total}
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 rounded-lg text-sm font-medium bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 rounded-lg text-sm font-medium bg-white border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AttackRecordsModal;
