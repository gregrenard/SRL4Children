import { useState, useEffect } from 'react';
import api from '../../api/client';
import { shortId, getStatusIcon, getStatusColor, getScoreColor, isJobRunning, formatDate } from '../../utils/helpers';
import { ProgressBar } from '../common';
import { DeleteConfirmationModal } from './DeleteConfirmationModal';

export const DetailPanel = ({ item, type, onClose, onReport, onViewRecords, onViewGuardrails, onDelete, endpoints, attacks, scores }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [testPrompt, setTestPrompt] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [guardrailDetails, setGuardrailDetails] = useState(null);

  useEffect(() => {
    if (type === 'guardrail' && item?.id) {
      api.getGuardrail(item.id).then(setGuardrailDetails).catch(console.error);
    }
  }, [type, item?.id]);

  if (!item) return null;

  const handleTest = async () => {
    setTesting(true);
    try {
      const result = await api.testEndpoint(item.id, testPrompt || null);
      setTestResult(result);
    } catch (err) {
      setTestResult({ success: false, error: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteModal(true);
  };

  const handleDeleteConfirmed = () => {
    onDelete();
    onClose();
  };

  const handleCopyRules = async () => {
    try {
      const result = await api.exportGuardrail(item.id);
      await navigator.clipboard.writeText(result.text);
      alert('Rules copied to clipboard!');
    } catch (err) {
      alert(`Failed to copy: ${err.message}`);
    }
  };

  const handleDownloadRules = async () => {
    try {
      const result = await api.exportGuardrail(item.id);
      const blob = new Blob([result.text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `guardrails-${shortId(item.id)}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Failed to download: ${err.message}`);
    }
  };

  const renderContent = () => {
    switch (type) {
      case 'endpoint':
        return (
          <>
            <h3 className="text-xl font-semibold text-gray-800 mb-4 font-display">{item.name}</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Type</div>
                <div className="text-gray-700">{item.type}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">URL</div>
                <div className="text-gray-700 font-mono text-sm break-all">{item.base_url || item.url}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Created</div>
                <div className="text-gray-700">{formatDate(item.created_at)}</div>
              </div>
            </div>
            {/* Test Prompt Section */}
            <div className="mt-6 pt-4 border-t border-gray-100">
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Test Prompt</div>
              <textarea
                value={testPrompt}
                onChange={(e) => setTestPrompt(e.target.value)}
                placeholder="Enter a prompt to test (or leave empty for default)"
                className="w-full px-3 py-2 border border-gray-200 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-everyone-blue/20 focus:border-everyone-blue"
                rows={3}
              />
              <button
                onClick={handleTest}
                disabled={testing}
                className="w-full mt-2 py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark disabled:opacity-50 rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {testing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                {testing ? 'Sending...' : 'Send Prompt'}
              </button>
              {testResult && (
                <div className={`mt-3 p-3 rounded-xl ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  {testResult.success ? (
                    <>
                      <div className="flex items-center gap-2 text-green-700 text-sm font-medium mb-2">
                        <span>✓</span> Response ({testResult.latency_ms}ms)
                      </div>
                      <div className="text-sm text-gray-700 bg-white rounded-lg p-2 border border-green-100 max-h-40 overflow-y-auto whitespace-pre-wrap">
                        {testResult.response}
                      </div>
                    </>
                  ) : (
                    <div className="text-sm text-red-700">
                      ✗ {testResult.error}
                    </div>
                  )}
                </div>
              )}
            </div>
            <div className="mt-4 space-y-2">
              <button onClick={handleDeleteClick} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                Delete Endpoint
              </button>
            </div>
          </>
        );

      case 'attack':
        const attackEndpoint = endpoints?.find(e => e.id === item.endpoint_id);
        return (
          <>
            <h3 className="font-mono text-xl text-gray-800 mb-4">{item.id}</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Endpoint</div>
                <div className="text-gray-700">{attackEndpoint?.name || item.endpoint_id}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Dataset</div>
                <div className="text-gray-700">{item.dataset_name}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Status</div>
                <div className={`flex items-center gap-2 ${getStatusColor(item.status)}`}>
                  <span className={item.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(item.status)}</span>
                  {item.status}
                </div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Progress</div>
                <div className="text-gray-700 mb-2">{item.completed_prompts || 0} / {item.total_prompts || 0} prompts</div>
                <ProgressBar progress={item.progress} animated={isJobRunning(item)} />
              </div>
              {item.started_at && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Started</div>
                  <div className="text-gray-700">{formatDate(item.started_at)}</div>
                </div>
              )}
              {item.completed_at && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Completed</div>
                  <div className="text-gray-700">{formatDate(item.completed_at)}</div>
                </div>
              )}
            </div>
            <div className="mt-6 space-y-2">
              {item.status === 'completed' && (
                <button onClick={() => onViewRecords(item)} className="w-full py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                  </svg>
                  View Records
                </button>
              )}
              <button onClick={handleDeleteClick} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                Delete Attack
              </button>
            </div>
          </>
        );

      case 'score':
        const scoreAttack = attacks?.find(a => a.id === item.attack_id);
        const scoreEndpoint = scoreAttack ? endpoints?.find(e => e.id === scoreAttack.endpoint_id) : null;
        return (
          <>
            <h3 className="font-mono text-xl text-gray-800 mb-4">{item.id}</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Endpoint</div>
                <div className="text-gray-700">{scoreEndpoint?.name || 'Unknown'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Attack</div>
                <div className="text-gray-700 font-mono text-sm">{shortId(item.attack_id)}</div>
                <div className="text-xs text-gray-400">{scoreAttack?.dataset_name}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Age Context</div>
                <div className="text-gray-700 capitalize">{item.age_context}</div>
              </div>
              {item.status === 'completed' && item.final_score != null ? (
                <>
                  <div>
                    <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Final Score</div>
                    <div className={`text-3xl font-bold ${getScoreColor(item.final_score)}`}>
                      {item.final_score.toFixed(1)}
                      <span className="text-lg text-gray-400 font-normal ml-1">/5.0</span>
                    </div>
                  </div>
                  {item.category_scores?.categories && Object.keys(item.category_scores.categories).length > 0 && (
                    <div>
                      <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Categories</div>
                      <div className="space-y-2">
                        {Object.entries(item.category_scores.categories).map(([cat, score]) => (
                          <div key={cat} className="flex items-center gap-3">
                            <div className="flex-1 text-sm text-gray-600 capitalize">{cat}</div>
                            <div className={`font-mono text-sm ${getScoreColor(score)}`}>{score.toFixed(1)}</div>
                            <div className="w-20">
                              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${score < 2.5 ? 'bg-red-500' : score < 3.5 ? 'bg-amber-500' : 'bg-green-500'}`} style={{ width: `${(score / 5) * 100}%` }} />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {item.category_scores?.subcategories && Object.keys(item.category_scores.subcategories).length > 0 && (
                    <div>
                      <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Subcategories</div>
                      <div className="space-y-2">
                        {Object.entries(item.category_scores.subcategories).map(([cat, score]) => (
                          <div key={cat} className="flex items-center gap-3">
                            <div className="flex-1 text-sm text-gray-600 capitalize">{cat.replace(/_/g, ' ')}</div>
                            <div className={`font-mono text-sm ${getScoreColor(score)}`}>{score.toFixed(1)}</div>
                            <div className="w-20">
                              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div className={`h-full rounded-full ${score < 2.5 ? 'bg-red-500' : score < 3.5 ? 'bg-amber-500' : 'bg-green-500'}`} style={{ width: `${(score / 5) * 100}%` }} />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Status</div>
                  <div className={`flex items-center gap-2 ${getStatusColor(item.status)}`}>
                    <span className={item.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(item.status)}</span>
                    {item.status}
                  </div>
                  <div className="mt-2">
                    <ProgressBar progress={item.progress} animated={isJobRunning(item)} />
                  </div>
                </div>
              )}
              {item.started_at && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Started</div>
                  <div className="text-gray-700">{formatDate(item.started_at)}</div>
                </div>
              )}
              {item.completed_at && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Completed</div>
                  <div className="text-gray-700">{formatDate(item.completed_at)}</div>
                </div>
              )}
            </div>
            <div className="mt-6 space-y-2">
              {item.status === 'completed' && (
                <button onClick={() => onReport(item)} className="w-full py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  View Full Report
                </button>
              )}
              <button onClick={handleDeleteClick} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                Delete Score
              </button>
            </div>
          </>
        );

      case 'guardrail':
        const details = guardrailDetails || item;
        const guardrailScore = scores?.find(s => s.id === item.score_id);
        const guardrailAttack = guardrailScore ? attacks?.find(a => a.id === guardrailScore.attack_id) : null;
        const guardrailEndpoint = guardrailAttack ? endpoints?.find(e => e.id === guardrailAttack.endpoint_id) : null;
        const rulesByCategory = (details.guardrails || []).reduce((acc, rule) => {
          const cat = rule.criteria_id?.split('.')[1] || 'other';
          acc[cat] = (acc[cat] || 0) + 1;
          return acc;
        }, {});
        return (
          <>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="font-mono text-lg text-gray-800">{shortId(item.id)}</h3>
                <div className="text-sm text-gray-500">{guardrailEndpoint?.name || 'Unknown endpoint'}</div>
              </div>
              <div className={`flex items-center gap-1.5 text-sm ${getStatusColor(item.status)}`}>
                <span className={item.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(item.status)}</span>
                {item.status}
              </div>
            </div>

            <div className="space-y-4">
              {/* Source info */}
              <div className="flex gap-4 text-sm">
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Score</div>
                  <div className="text-gray-700 font-mono">{shortId(item.score_id)}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Context</div>
                  <div className="text-gray-700 capitalize">{guardrailScore?.age_context}</div>
                </div>
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Score</div>
                  <div className="text-gray-700">{guardrailScore?.final_score?.toFixed(1)}/5</div>
                </div>
              </div>

              {/* Rules summary */}
              {details.guardrails && details.guardrails.length > 0 && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-3">Rules by Cue</div>
                  <div className="space-y-2">
                    {Object.entries(rulesByCategory).map(([cat, count]) => (
                      <div key={cat} className="flex items-center justify-between">
                        <span className={`px-2 py-1 rounded text-xs font-medium capitalize ${
                          cat === 'anthropomorphic' ? 'bg-purple-100 text-purple-700' :
                          cat === 'interactional' ? 'bg-blue-100 text-blue-700' :
                          cat === 'relational' ? 'bg-pink-100 text-pink-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {cat}
                        </span>
                        <span className="text-sm font-medium text-gray-700">{count} rules</span>
                      </div>
                    ))}
                    <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                      <span className="text-sm font-medium text-gray-600">Total</span>
                      <span className="text-lg font-semibold text-gray-800">{details.guardrails.length}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Timestamps */}
              <div className="flex gap-4 text-xs text-gray-400">
                {item.created_at && <div>Created {formatDate(item.created_at)}</div>}
                {item.completed_at && <div>Completed {formatDate(item.completed_at)}</div>}
              </div>
            </div>

            {/* Actions */}
            <div className="mt-6 space-y-2">
              {item.status === 'completed' && details.guardrails?.length > 0 && (
                <>
                  <button onClick={() => onViewGuardrails(details)} className="w-full py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark rounded-lg text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                    </svg>
                    View All Rules
                  </button>
                  <div className="flex gap-2">
                    <button onClick={handleDownloadRules} className="flex-1 py-2 px-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 text-sm font-medium transition-colors flex items-center justify-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                      </svg>
                      Download
                    </button>
                    <button onClick={handleCopyRules} className="flex-1 py-2 px-3 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-700 text-sm font-medium transition-colors flex items-center justify-center gap-1">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy
                    </button>
                  </div>
                </>
              )}
              <button onClick={handleDeleteClick} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg text-red-600 text-sm font-medium transition-colors">
                Delete Set
              </button>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <>
      <div className="h-full flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 flex-shrink-0">
          <div className="flex items-center gap-2 text-xs text-gray-500 uppercase tracking-wider font-medium">
            {type === 'endpoint' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            )}
            {type === 'attack' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            )}
            {type === 'score' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            )}
            {type === 'guardrail' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            )}
            {type} Details
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-gray-100 rounded transition-colors">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        {/* Content */}
        <div className="px-4 py-4 overflow-y-auto custom-scroll flex-1">
          {renderContent()}
        </div>
      </div>

      {showDeleteModal && (
        <DeleteConfirmationModal
          type={type}
          item={item}
          onClose={() => setShowDeleteModal(false)}
          onDeleted={handleDeleteConfirmed}
        />
      )}
    </>
  );
};

export default DetailPanel;
