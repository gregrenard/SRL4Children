// Utility functions for SRL4C UI

export const getScoreColor = (score) => {
  if (score == null) return 'text-gray-400';
  if (score < 2.5) return 'text-red-600';
  if (score < 3.5) return 'text-amber-600';
  return 'text-green-600';
};

export const getScoreBgColor = (score) => {
  if (score == null) return 'bg-gray-500';
  if (score < 2.5) return 'bg-red-500';
  if (score < 3.5) return 'bg-amber-500';
  return 'bg-green-500';
};

export const getStatusIcon = (status) => {
  switch (status) {
    case 'completed': return '✓';
    case 'running': return '◐';
    case 'pending': return '○';
    case 'failed': return '✗';
    case 'online': return '●';
    case 'offline': return '○';
    case 'untested': return '◌';
    case 'abandoned': return '○';
    case 'stale': return '◌';
    default: return '○';
  }
};

export const getStatusColor = (status) => {
  switch (status) {
    case 'completed':
    case 'online': return 'text-green-600';
    case 'running': return 'text-everyone-blue';
    case 'pending':
    case 'untested': return 'text-gray-400';
    case 'failed':
    case 'offline': return 'text-red-600';
    case 'abandoned':
    case 'stale': return 'text-gray-400';
    default: return 'text-gray-400';
  }
};

export const shortId = (id) => id?.substring(0, 8) || '';

export const isJobRunning = (item) => item?.status === 'running' || item?.status === 'pending';

export const formatTime = (timestamp) => {
  if (!timestamp) return '';
  const date = new Date(timestamp);
  return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
};

export const formatDate = (timestamp) => {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp).toLocaleDateString();
};

export const formatDateTime = (timestamp) => {
  if (!timestamp) return 'Unknown';
  return new Date(timestamp).toLocaleString();
};

export const escapeHtml = (text) => {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
};
