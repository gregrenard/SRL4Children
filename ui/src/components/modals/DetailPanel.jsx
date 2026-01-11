import { useState, useEffect } from 'react';
import api from '../../api/client';
import { shortId, getStatusIcon, getStatusColor, getScoreColor, isJobRunning, formatDate } from '../../utils/helpers';
import { ProgressBar } from '../common';

export const DetailPanel = ({ item, type, onClose, onReport, onDelete, endpoints, attacks, scores }) => {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [deleting, setDeleting] = useState(false);
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
      const result = await api.testEndpoint(item.id);
      setTestResult(result);
    } catch (err) {
      setTestResult({ success: false, message: err.message });
    } finally {
      setTesting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete this ${type}?`)) return;
    setDeleting(true);
    try {
      const deleteFn = { endpoint: api.deleteEndpoint, attack: api.deleteAttack, score: api.deleteScore, guardrail: api.deleteGuardrail }[type];
      await deleteFn(item.id);
      onDelete();
      onClose();
    } catch (err) {
      alert(`Delete failed: ${err.message}`);
    } finally {
      setDeleting(false);
    }
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
              {testResult && (
                <div className={`p-3 rounded-xl ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                  <div className={`text-sm ${testResult.success ? 'text-green-700' : 'text-red-700'}`}>
                    {testResult.success ? '✓ Connection successful' : `✗ ${testResult.error || testResult.message}`}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-6 space-y-2">
              <button onClick={handleTest} disabled={testing} className="w-full py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark disabled:opacity-50 rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                {testing && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
                Test Connection
              </button>
              <button onClick={handleDelete} disabled={deleting} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                {deleting ? 'Deleting...' : 'Delete Endpoint'}
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
            </div>
            <div className="mt-6">
              <button onClick={handleDelete} disabled={deleting} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                {deleting ? 'Deleting...' : 'Delete Attack'}
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
                  {item.category_scores && (
                    <div>
                      <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Category Breakdown</div>
                      <div className="space-y-2">
                        {Object.entries(item.category_scores).map(([cat, score]) => (
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
              <button onClick={handleDelete} disabled={deleting} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                {deleting ? 'Deleting...' : 'Delete Score'}
              </button>
            </div>
          </>
        );

      case 'guardrail':
        const details = guardrailDetails || item;
        const guardrailScore = scores?.find(s => s.id === item.score_id);
        const guardrailAttack = guardrailScore ? attacks?.find(a => a.id === guardrailScore.attack_id) : null;
        const guardrailEndpoint = guardrailAttack ? endpoints?.find(e => e.id === guardrailAttack.endpoint_id) : null;
        return (
          <>
            <h3 className="font-mono text-xl text-gray-800 mb-4">{item.id}</h3>
            <div className="space-y-3">
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Endpoint</div>
                <div className="text-gray-700">{guardrailEndpoint?.name || 'Unknown'}</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Source Score</div>
                <div className="text-gray-700 font-mono text-sm">{shortId(item.score_id)}</div>
                <div className="text-xs text-gray-400">{guardrailScore?.age_context} · {guardrailScore?.final_score?.toFixed(1)}/5.0</div>
              </div>
              <div>
                <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Status</div>
                <div className={`flex items-center gap-2 ${getStatusColor(item.status)}`}>
                  <span className={item.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(item.status)}</span>
                  {item.status}
                </div>
              </div>
              {details.guardrails && details.guardrails.length > 0 && (
                <div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-2">Rules ({details.guardrails.length})</div>
                  <div className="space-y-2 max-h-64 overflow-y-auto custom-scroll pr-2">
                    {details.guardrails.map((rule) => (
                      <div key={rule.id} className="bg-gray-50 rounded-xl p-3 border border-gray-200">
                        <div className="text-sm text-gray-700">{rule.rule_text}</div>
                        <div className="text-xs text-gray-400 mt-1 truncate">{rule.principle_id}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="mt-6 space-y-2">
              {item.status === 'completed' && (
                <button onClick={handleCopyRules} className="w-full py-2 px-4 bg-everyone-blue hover:bg-everyone-blue-dark rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  Copy Rules
                </button>
              )}
              <button onClick={handleDelete} disabled={deleting} className="w-full py-2 px-4 bg-red-50 hover:bg-red-100 border border-red-200 rounded-xl text-red-600 text-sm font-medium transition-colors">
                {deleting ? 'Deleting...' : 'Delete Set'}
              </button>
            </div>
          </>
        );

      default:
        return null;
    }
  };

  return (
    <div className="h-full bg-white border border-gray-200 rounded-2xl shadow-lg animate-fade-in flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-gray-100">
        <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">{type} Details</div>
        <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
          <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div className="p-4 overflow-y-auto custom-scroll flex-1">
        {renderContent()}
      </div>
    </div>
  );
};

export default DetailPanel;
