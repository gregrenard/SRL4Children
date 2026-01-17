import { useState, useEffect } from 'react';
import api from '../../api/client';

export const MatricesModal = ({ onClose }) => {
  const [matrices, setMatrices] = useState([]);
  const [selectedMatrix, setSelectedMatrix] = useState(null);
  const [matrixDetail, setMatrixDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMatrices();
  }, []);

  const loadMatrices = async () => {
    setLoading(true);
    try {
      const data = await api.getMatrices();
      setMatrices(data);
      if (data.length > 0) {
        // Select first matrix by default
        const first = data[0];
        setSelectedMatrix(first.id);
        loadMatrixDetail(first.id);
      }
    } catch (err) {
      console.error('Failed to load matrices:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadMatrixDetail = async (id) => {
    try {
      const data = await api.getMatrix(id);
      setMatrixDetail(data);
    } catch (err) {
      console.error('Failed to load matrix detail:', err);
      setMatrixDetail(null);
    }
  };

  const handleSelect = (matrix) => {
    setSelectedMatrix(matrix.id);
    loadMatrixDetail(matrix.id);
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 animate-fade-in flex items-center justify-center p-8">
      <div className="bg-white rounded-2xl border border-gray-200 w-full max-w-2xl shadow-2xl max-h-[80vh] flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-gray-800 font-display">Scoring Matrices</h3>
          <button onClick={onClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 flex-1 overflow-hidden flex flex-col gap-4">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-everyone-blue border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : (
            <>
              {/* Matrix selector */}
              <div>
                <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Available Matrices</label>
                <div className="flex flex-wrap gap-2">
                  {matrices.map(m => (
                    <button
                      key={m.id}
                      onClick={() => handleSelect(m)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 ${
                        selectedMatrix === m.id
                          ? 'bg-everyone-blue text-white'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {m.name}
                      {m.is_builtin && (
                        <span className={`text-xs ${selectedMatrix === m.id ? 'text-white/70' : 'text-gray-400'}`}>
                          (built-in)
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Matrix detail */}
              {matrixDetail && (
                <div className="flex-1 overflow-hidden flex flex-col">
                  <label className="block text-xs text-gray-500 uppercase tracking-wider mb-2">Matrix Details</label>
                  <div className="bg-gray-50 rounded-xl p-4 border border-gray-200 space-y-3">
                    <div>
                      <span className="text-xs text-gray-500">Name:</span>
                      <span className="ml-2 text-sm font-medium text-gray-700">{matrixDetail.name}</span>
                    </div>
                    {matrixDetail.description && (
                      <div>
                        <span className="text-xs text-gray-500">Description:</span>
                        <span className="ml-2 text-sm text-gray-700">{matrixDetail.description}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-xs text-gray-500">Entries:</span>
                      <span className="ml-2 text-sm text-gray-700">
                        {matrixDetail.entries?.length || 0} custom mappings
                      </span>
                    </div>
                    {matrixDetail.entries?.length === 0 && (
                      <p className="text-xs text-gray-400 italic">
                        No custom entries. Uses identity mapping (presence level = score).
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Help text */}
              <div className="bg-blue-50 rounded-xl p-3 border border-blue-100">
                <p className="text-xs text-blue-700">
                  <strong>How scoring matrices work:</strong> After the LLM judge detects a behavior&apos;s presence level (1-5),
                  the matrix maps it to a final score based on age group and context.
                  The &quot;flat&quot; matrix uses identity mapping (presence = score).
                </p>
              </div>
            </>
          )}
        </div>

        <div className="flex items-center gap-3 p-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="flex-1 py-2.5 px-4 bg-everyone-blue hover:bg-everyone-blue/90 rounded-xl text-white text-sm font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default MatricesModal;
