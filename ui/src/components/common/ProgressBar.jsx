export const ProgressBar = ({ progress, animated = false }) => (
  <div className="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
    <div
      className={`h-full bg-gradient-to-r from-everyone-blue to-everyone-purple rounded-full transition-all duration-500 ${animated ? 'progress-animated' : ''}`}
      style={{ width: `${(progress || 0) * 100}%` }}
    />
  </div>
);

export default ProgressBar;
