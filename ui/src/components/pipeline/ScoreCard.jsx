import { shortId, getStatusIcon, getStatusColor, getScoreColor, isJobRunning, formatDate } from '../../utils/helpers';
import { ProgressBar } from '../common';

export const ScoreCard = ({ score, selected, onClick, onReport, onNewGuardrail }) => (
  <div
    onClick={onClick}
    onContextMenu={(e) => { e.preventDefault(); onNewGuardrail?.(score); }}
    className={`card p-3 cursor-pointer transition-all duration-200 ${selected ? 'selected' : ''}`}
  >
    <div className="flex items-center justify-between">
      <div className="font-mono text-sm text-gray-800">{shortId(score.id)}</div>
      {score.status === 'completed' && (
        <button
          onClick={(e) => { e.stopPropagation(); onReport(score); }}
          className="text-gray-400 hover:text-everyone-blue transition-colors p-1 -mr-1"
          title="View Report"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </button>
      )}
    </div>
    <div className="text-xs text-gray-400 mt-0.5">
      {score.age_context}{score.context ? ` · ${score.context}` : ''} · {shortId(score.attack_id)}
    </div>
    {score.status === 'completed' && score.final_score != null ? (
      <div className={`text-lg font-semibold mt-1.5 ${getScoreColor(score.final_score)}`}>
        {score.final_score.toFixed(1)}
        <span className="text-xs text-gray-400 font-normal ml-1">/5.0</span>
      </div>
    ) : (
      <div className="mt-2">
        <div className={`text-xs mb-1 flex justify-between ${getStatusColor(score.status)}`}>
          <span>
            <span className={score.status === 'running' ? 'animate-spin-slow inline-block' : ''}>{getStatusIcon(score.status)}</span>
            <span className="ml-1">{score.status}</span>
          </span>
          {score.progress_total > 0 && (
            <span className="text-gray-400">{score.progress_current}/{score.progress_total}</span>
          )}
        </div>
        <ProgressBar progress={score.progress} animated={isJobRunning(score)} />
      </div>
    )}
    {score.started_at && (
      <div className="text-xs text-gray-400 mt-2">Started {formatDate(score.started_at)}</div>
    )}
  </div>
);

export default ScoreCard;
