import { getStatusIcon, getStatusColor } from '../../utils/helpers';

export const EndpointCard = ({ endpoint, selected, onClick, onNewAttack }) => (
  <div
    onClick={onClick}
    onContextMenu={(e) => { e.preventDefault(); onNewAttack?.(endpoint); }}
    className={`card p-3 cursor-pointer transition-all duration-200 ${selected ? 'selected' : ''}`}
  >
    <div className="font-medium text-gray-800 truncate">{endpoint.name}</div>
    <div className="text-xs text-gray-400 truncate mt-0.5">
      {endpoint.type} · {(endpoint.base_url || endpoint.url || '').replace(/https?:\/\//, '').substring(0, 20)}
    </div>
    <div className={`text-xs mt-1.5 flex items-center gap-1.5 ${getStatusColor(endpoint.status || 'untested')}`}>
      <span className="text-[10px]">{getStatusIcon(endpoint.status || 'untested')}</span>
      {endpoint.status || 'untested'}
    </div>
  </div>
);

export default EndpointCard;
