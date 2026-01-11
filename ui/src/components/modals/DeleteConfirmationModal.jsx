import { useState, useEffect } from 'react';
import api from '../../api/client';

const entityConfig = {
  endpoint: {
    label: 'Endpoint',
    previewFn: api.previewDeleteEndpoint,
    deleteFn: (id, force) => api.deleteEndpoint(id, force),
    childrenDescription: (preview) => {
      const parts = [];
      if (preview.will_delete.attacks > 0) parts.push(`${preview.will_delete.attacks} attack(s)`);
      if (preview.will_delete.records > 0) parts.push(`${preview.will_delete.records} record(s)`);
      if (preview.will_delete.scores > 0) parts.push(`${preview.will_delete.scores} score(s)`);
      if (preview.will_delete.evaluations > 0) parts.push(`${preview.will_delete.evaluations} evaluation(s)`);
      if (preview.will_delete.guardrail_sets > 0) parts.push(`${preview.will_delete.guardrail_sets} guardrail set(s)`);
      if (preview.will_delete.guardrails > 0) parts.push(`${preview.will_delete.guardrails} guardrail rule(s)`);
      return parts.join(', ');
    },
  },
  attack: {
    label: 'Attack',
    previewFn: api.previewDeleteAttack,
    deleteFn: (id) => api.deleteAttack(id),
    childrenDescription: (preview) => {
      const parts = [];
      if (preview.will_delete.records > 0) parts.push(`${preview.will_delete.records} record(s)`);
      if (preview.will_delete.scores > 0) parts.push(`${preview.will_delete.scores} score(s)`);
      if (preview.will_delete.evaluations > 0) parts.push(`${preview.will_delete.evaluations} evaluation(s)`);
      if (preview.will_delete.guardrail_sets > 0) parts.push(`${preview.will_delete.guardrail_sets} guardrail set(s)`);
      if (preview.will_delete.guardrails > 0) parts.push(`${preview.will_delete.guardrails} guardrail rule(s)`);
      return parts.join(', ');
    },
  },
  score: {
    label: 'Score',
    previewFn: api.previewDeleteScore,
    deleteFn: (id) => api.deleteScore(id),
    childrenDescription: (preview) => {
      const parts = [];
      if (preview.will_delete.evaluations > 0) parts.push(`${preview.will_delete.evaluations} evaluation(s)`);
      if (preview.will_delete.guardrail_sets > 0) parts.push(`${preview.will_delete.guardrail_sets} guardrail set(s)`);
      if (preview.will_delete.guardrails > 0) parts.push(`${preview.will_delete.guardrails} guardrail rule(s)`);
      return parts.join(', ');
    },
  },
  guardrail: {
    label: 'Guardrail Set',
    previewFn: api.previewDeleteGuardrail,
    deleteFn: (id) => api.deleteGuardrail(id),
    childrenDescription: (preview) => {
      if (preview.will_delete.guardrails > 0) {
        return `${preview.will_delete.guardrails} guardrail rule(s)`;
      }
      return '';
    },
  },
};

export const DeleteConfirmationModal = ({ type, item, onClose, onDeleted }) => {
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  const config = entityConfig[type];

  useEffect(() => {
    if (!item?.id || !config) return;

    setLoading(true);
    setError(null);
    config.previewFn(item.id)
      .then(setPreview)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [item?.id, type]);

  const handleDelete = async () => {
    setDeleting(true);
    setError(null);
    try {
      // For endpoints with children, force=true is required
      const needsForce = type === 'endpoint' && preview?.has_children;
      await config.deleteFn(item.id, needsForce);
      onDeleted();
      onClose();
    } catch (err) {
      setError(err.message);
      setDeleting(false);
    }
  };

  if (!item || !config) return null;

  const hasChildren = preview?.has_children;
  const childrenDesc = preview ? config.childrenDescription(preview) : '';

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-md shadow-2xl">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 font-display">Delete {config.label}</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-everyone-blue border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4">
              <div className="text-red-700 text-sm">{error}</div>
            </div>
          ) : (
            <div className="space-y-4">
              {hasChildren ? (
                <>
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                    <div className="flex items-start gap-3">
                      <svg className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <div>
                        <div className="text-amber-800 font-medium">Cascade Delete Warning</div>
                        <div className="text-amber-700 text-sm mt-1">
                          This {config.label.toLowerCase()} has related data that will also be deleted:
                        </div>
                        <div className="text-amber-800 text-sm font-medium mt-2">
                          {childrenDesc}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="text-gray-600 text-sm">
                    Are you sure you want to delete this {config.label.toLowerCase()} and all its related data? This action cannot be undone.
                  </div>
                </>
              ) : (
                <div className="text-gray-600">
                  Are you sure you want to delete this {config.label.toLowerCase()}? This action cannot be undone.
                </div>
              )}

              {preview && (
                <div className="bg-gray-50 rounded-xl p-3 border border-gray-200">
                  <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                    {type === 'endpoint' ? 'Name' : 'ID'}
                  </div>
                  <div className="font-mono text-sm text-gray-700 truncate">
                    {type === 'endpoint' ? (preview.endpoint?.name || item.name) : item.id}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 p-4 border-t border-gray-100">
          <button
            onClick={onClose}
            disabled={deleting}
            className="flex-1 py-2.5 px-4 bg-gray-100 hover:bg-gray-200 disabled:opacity-50 rounded-xl text-gray-700 text-sm font-medium transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={loading || deleting}
            className="flex-1 py-2.5 px-4 bg-red-500 hover:bg-red-600 disabled:opacity-50 rounded-xl text-white text-sm font-medium transition-colors flex items-center justify-center gap-2"
          >
            {deleting && <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>}
            {deleting ? 'Deleting...' : hasChildren ? 'Delete All' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;
