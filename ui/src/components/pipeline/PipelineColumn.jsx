import { LoadingSpinner, ErrorState } from '../common';
import AddCard from './AddCard';
import InfoCard from './InfoCard';

export const PipelineColumn = ({ children, addLabel, onAdd, subtitle, description, loading, error }) => (
  <div className="flex flex-col h-full min-h-0 overflow-hidden">
    {subtitle && (
      <p className="text-xs text-everyone-blue mb-2 truncate flex-shrink-0">for {subtitle}</p>
    )}
    <div className="flex-1 overflow-y-auto custom-scroll space-y-2 pr-2">
      <AddCard label={addLabel} onClick={onAdd} />
      {description && <InfoCard>{description}</InfoCard>}
      {loading ? <LoadingSpinner /> : error ? <ErrorState message={error} /> : children}
    </div>
  </div>
);

export default PipelineColumn;
