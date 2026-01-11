import { LoadingSpinner, ErrorState } from '../common';
import AddCard from './AddCard';

export const PipelineColumn = ({ children, addLabel, onAdd, description, loading, error }) => (
  <div className="flex flex-col h-full min-h-0 overflow-hidden">
    <div className="flex-1 overflow-y-auto custom-scroll space-y-2 pr-2">
      <AddCard label={addLabel} onClick={onAdd} description={description} />
      {loading ? <LoadingSpinner /> : error ? <ErrorState message={error} /> : children}
    </div>
  </div>
);

export default PipelineColumn;
