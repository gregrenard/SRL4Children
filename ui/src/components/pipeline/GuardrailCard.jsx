import { shortId, getStatusIcon, getStatusColor, isJobRunning } from '../../utils/helpers';
import { ProgressBar } from '../common';

export const GuardrailCard = ({ guardrail, selected, onClick }) => (
  <div
    onClick={onClick}
    className={`card p-3 cursor-pointer transition-all duration-200 ${selected ? 'ring-2 ring-everyone-blue bg-everyone-blue/5' : ''}`}
  >
    <div className="font-mono text-sm text-gray-800">{shortId(guardrail.id)}</div>
    <div className="text-xs text-gray-400 mt-0.5">from {shortId(guardrail.score_id)}</div>
    <div className={`text-xs mt-1.5 flex items-center gap-1.5 ${getStatusColor(guardrail.status)}`}>
      <span className={guardrail.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(guardrail.status)}</span>
      {guardrail.status === 'completed' ? `${guardrail.rules_count || 0} rules` : guardrail.status}
    </div>
    {isJobRunning(guardrail) && (
      <div className="mt-2">
        <ProgressBar progress={guardrail.progress} animated />
      </div>
    )}
  </div>
);

export default GuardrailCard;
