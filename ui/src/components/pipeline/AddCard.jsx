export const AddCard = ({ label, onClick }) => (
  <button
    onClick={onClick}
    className="w-full p-3 bg-everyone-blue/5 hover:bg-everyone-blue/10 border-2 border-dashed border-everyone-blue/30 hover:border-everyone-blue/50 rounded-xl text-everyone-blue text-sm font-medium transition-all duration-200 flex items-center justify-center gap-2"
  >
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
    {label}
  </button>
);

export default AddCard;
