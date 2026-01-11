export const ErrorState = ({ message, onRetry }) => (
  <div className="text-center py-8">
    <div className="text-red-600 text-sm mb-2">{message}</div>
    {onRetry && (
      <button onClick={onRetry} className="text-xs text-everyone-blue hover:text-everyone-blue-dark">
        Retry
      </button>
    )}
  </div>
);

export default ErrorState;
