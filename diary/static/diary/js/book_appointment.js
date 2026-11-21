function clearSelectedSlot(form) {
    form.querySelectorAll('.slot-btn').forEach(button => {
        button.classList.remove('slot-selected');
        if (!button.disabled) button.setAttribute('aria-pressed', 'false');
    });
    form.querySelector('#selected-date').value = '';
    form.querySelector('#selected-time').value = '';
    form.querySelector('#selected-info').style.display = 'none';
    form.querySelector('.booking-actions button[type="submit"]').disabled = true;
}

function selectSlot(date, time, btn) {
    const form = btn.closest('.patient-booking-form');
    if (!form || btn.disabled || btn.closest('[data-booking-panel]')?.hidden) return;
    // Перевіряємо, чи цей слот вже обраний
    const isAlreadySelected = btn.classList.contains('slot-selected');
    clearSelectedSlot(form);
    
    // Якщо слот вже був обраний — знімаємо вибір і виходимо
    if (isAlreadySelected) {
        return;
    }
    
    // Інакше — виділяємо обрану
    btn.classList.add('slot-selected');
    btn.setAttribute('aria-pressed', 'true');
    
    // Записуємо в приховані поля
    form.querySelector('#selected-date').value = date;
    form.querySelector('#selected-time').value = time;
    
    // Показуємо інформацію
    form.querySelector('#selected-text').textContent = date.split('-').reverse().join('.') + ' о ' + time;
    form.querySelector('#selected-info').style.display = 'block';
    form.querySelector('.booking-actions button[type="submit"]').disabled = false;
}

// Перемикаємо лише час обраного дня, зберігаючи введені скарги.
(() => {
    'use strict';
    const form = document.querySelector('.patient-booking-form');
    if (!form) return;
    const week = form.querySelector('.booking-week');
    const buttons = [...form.querySelectorAll('[data-booking-day]')];
    const panels = [...form.querySelectorAll('[data-booking-panel]')];
    if (!week || !panels.length) return;
    let activeDate;
    function showDay(date) {
        if (activeDate === date) return;
        activeDate = date;
        clearSelectedSlot(form);
        panels.forEach(panel => { panel.hidden = panel.dataset.bookingPanel !== date; });
        buttons.forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.bookingDay === date));
        });
    }
    buttons.forEach(button => button.addEventListener('click', () => showDay(button.dataset.bookingDay)));
    const firstAvailable = panels.find(panel => panel.querySelector('.slot-free:not(:disabled)')) || panels[0];
    showDay(firstAvailable.dataset.bookingPanel);
    week.hidden = false;
})();
