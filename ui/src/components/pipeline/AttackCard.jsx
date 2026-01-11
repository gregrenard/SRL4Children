import { shortId, getStatusIcon, getStatusColor, isJobRunning, formatDate } from '../../utils/helpers';
import { ProgressBar } from '../common';

export const AttackCard = ({ attack, selected, onClick, onNewScore }) => (
  <div
    onClick={onClick}
    onContextMenu={(e) => { e.preventDefault(); onNewScore?.(attack); }}
    className={`card p-3 cursor-pointer transition-all duration-200 ${selected ? 'selected' : ''}`}
  >
    <div className="font-mono text-sm text-gray-800">{shortId(attack.id)}</div>
    <div className="text-xs text-gray-400 truncate mt-0.5">{attack.dataset_name}</div>
    <div className={`text-xs mt-1.5 flex items-center gap-1.5 ${getStatusColor(attack.status)}`}>
      <span className={attack.status === 'running' ? 'animate-spin-slow' : ''}>{getStatusIcon(attack.status)}</span>
      {attack.completed_prompts || 0}/{attack.total_prompts || 0} prompts
    </div>
    {isJobRunning(attack) && (
      <div className="mt-2">
        <ProgressBar progress={attack.progress} animated />
      </div>
    )}
    {attack.started_at && (
      <div className="text-xs text-gray-400 mt-2">Started {formatDate(attack.started_at)}</div>
    )}
  </div>
);

export default AttackCard;
