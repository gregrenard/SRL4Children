// Shared UI components for SRL4C

const TOPBAR_HTML = `
<div class="bg-white border-b border-gray-200 px-6 py-3 flex-shrink-0">
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-everyone-blue to-everyone-purple flex items-center justify-center">
        <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      </div>
      <div>
        <span class="text-lg font-bold" style="font-family: 'Poppins', sans-serif;">
          <span class="text-everyone-blue">everyone</span><span class="text-everyone-purple">.AI</span>
        </span>
        <span class="text-gray-400 font-normal text-sm ml-2">/ SRL4C</span>
      </div>
    </div>

    <div class="flex items-center gap-4">
      <div id="topbar-status" class="flex items-center gap-3">
        <!-- Status indicators injected here -->
      </div>
      <nav class="flex items-center gap-1" id="topbar-nav">
        <!-- Active state set by JS based on current page -->
      </nav>
    </div>
  </div>
</div>
`;

const NAV_ITEMS = [
  { href: 'index.html', label: 'Dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { href: 'prompts.html', label: 'Datasets', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
];

function initTopbar(containerId = 'topbar') {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = TOPBAR_HTML;

  // Determine current page
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';

  // Render nav items
  const nav = document.getElementById('topbar-nav');
  if (nav) {
    nav.innerHTML = NAV_ITEMS.map(item => {
      const isActive = currentPage === item.href || (currentPage === '' && item.href === 'index.html');
      const activeClass = isActive
        ? 'text-white bg-everyone-blue'
        : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100';
      return `
        <a href="${item.href}" class="flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeClass}">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${item.icon}" />
          </svg>
          ${item.label}
        </a>
      `;
    }).join('');
  }
}

// Export for use
window.SRL4C = window.SRL4C || {};
window.SRL4C.initTopbar = initTopbar;
