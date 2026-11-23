// Відкриваємо системне вікно друку; оформлення задає @media print.
(() => {
    'use strict';

    const button = document.querySelector('[data-print-conclusion]');
    if (!button || typeof window.print !== 'function') return;

    button.hidden = false;
    button.addEventListener('click', () => window.print());
})();
