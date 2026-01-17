import { useState, useEffect } from 'react';
import { marked } from 'marked';
import api from '../../api/client';
import { shortId, getScoreColor, formatDateTime } from '../../utils/helpers';
import { LoadingSpinner } from '../common';
import { RadarChart } from '../charts/RadarChart';

export const ReportModal = ({ score, attacks, endpoints, onClose }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  const attack = attacks?.find(a => a.id === score.attack_id);
  const endpoint = attack ? endpoints?.find(e => e.id === attack.endpoint_id) : null;

  useEffect(() => {
    api.getScoreReport(score.id)
      .then(data => setReport(data.report))
      .catch(err => setReport(`Error loading report: ${err.message}`))
      .finally(() => setLoading(false));
  }, [score.id]);

  const handleExport = (type) => {
    if (type === 'download') {
      const blob = new Blob([report || ''], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `srl4c-report-${shortId(score.id)}.md`;
      a.click();
    } else {
      navigator.clipboard.writeText(report || '');
      alert('Report copied to clipboard!');
    }
    setExporting(false);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <button onClick={onClose} className="flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back
          </button>
          <div className="relative">
            <button onClick={() => setExporting(!exporting)} className="flex items-center gap-2 px-4 py-2 bg-everyone-blue hover:bg-everyone-blue-dark rounded-xl text-white text-sm font-medium transition-colors">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Export
            </button>
            {exporting && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-xl border border-gray-200 shadow-xl overflow-hidden z-10">
                <button onClick={() => handleExport('download')} className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors">Download as .md</button>
                <button onClick={() => handleExport('copy')} className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors">Copy to clipboard</button>
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scroll p-6 bg-gray-50">
          <div className="bg-white rounded-xl p-4 mb-6 border border-gray-200">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-3">Report Context</div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-400">Endpoint:</span><span className="text-gray-800 ml-2">{endpoint?.name || 'Unknown'}</span></div>
              <div><span className="text-gray-400">Attack:</span><span className="text-gray-800 font-mono ml-2">{shortId(attack?.id)}</span><span className="text-gray-400 ml-2">· {attack?.dataset_name}</span></div>
              <div><span className="text-gray-400">Score:</span><span className="text-gray-800 font-mono ml-2">{shortId(score.id)}</span><span className="text-gray-400 ml-2">· {score.age_context} ·</span><span className={`ml-1 font-semibold ${getScoreColor(score.final_score)}`}>{score.final_score?.toFixed(1)}/5.0</span></div>
              <div><span className="text-gray-400">Generated:</span><span className="text-gray-800 ml-2">{formatDateTime(score.started_at)}</span></div>
            </div>
          </div>

          {/* Cue-level radar (global overview) */}
          {score.category_scores?.categories && Object.keys(score.category_scores.categories).length > 0 && (
            <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-4 text-center">Cue Overview</div>
              <RadarChart categoryScores={score.category_scores.categories} />
              <div className="flex justify-center gap-6 mt-4 text-xs">
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-red-100 border border-red-400"></div><span className="text-gray-500">Poor (0-2.5)</span></div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-amber-100 border border-amber-400"></div><span className="text-gray-500">Fair (2.5-3.5)</span></div>
                <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-green-100 border border-green-400"></div><span className="text-gray-500">Good (3.5-5)</span></div>
              </div>
            </div>
          )}

          {/* Behavior-level radar (detailed breakdown) */}
          {score.category_scores?.subcategories && Object.keys(score.category_scores.subcategories).length > 0 && (
            <div className="bg-white rounded-xl p-6 mb-6 border border-gray-200">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-4 text-center">Behavior Breakdown</div>
              <RadarChart categoryScores={score.category_scores.subcategories} />
            </div>
          )}

          <div className="bg-white rounded-xl p-6 border border-gray-200">
            <div className="text-xs text-gray-400 uppercase tracking-wider mb-4">Full Report</div>
            {loading ? (
              <LoadingSpinner />
            ) : (
              <div
                className="markdown-body"
                dangerouslySetInnerHTML={{ __html: marked.parse(report || '') }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportModal;
