// Формат відображення дати не залежить від мови браузера.
(() => {
    'use strict';
    document.querySelectorAll('.profile-date-control, .records-date-control').forEach(control => {

        const text = control.querySelector('input[type="text"]');
        const calendar = control.querySelector('input[type="date"]');
        const button = control.querySelector('button');
        if (!text || !calendar || !button || typeof calendar.showPicker !== 'function') return;

        calendar.hidden = false;
        button.hidden = false;

        button.addEventListener('click', () => {
            const match = text.value.match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
            calendar.value = match ? `${match[3]}-${match[2]}-${match[1]}` : '';
            try {
                calendar.showPicker();
            } catch {
                // Ручне введення залишається доступним, якщо браузер блокує календар.
                text.focus();
            }
        });

        calendar.addEventListener('change', () => {
            if (!calendar.value) return;
            const [year, month, day] = calendar.value.split('-');
            text.value = `${day}.${month}.${year}`;
            text.dispatchEvent(new Event('input', { bubbles: true }));
            text.dispatchEvent(new Event('change', { bubbles: true }));
            text.focus();
        });
    });
})();
