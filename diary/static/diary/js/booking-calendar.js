// Спільний український календар пацієнта й лікаря, незалежний від мови браузера.
(() => {
    'use strict';
    const months = ['Січень', 'Лютий', 'Березень', 'Квітень', 'Травень', 'Червень',
        'Липень', 'Серпень', 'Вересень', 'Жовтень', 'Листопад', 'Грудень'];
    const fullDate = new Intl.DateTimeFormat('uk-UA', { dateStyle: 'full' });
    function makeDate(year, month, day) {
        const result = new Date(0);
        result.setHours(0, 0, 0, 0);
        result.setFullYear(year, month, day);
        return result;
    }
    function parseDate(value, iso = false) {
        const match = value.match(iso ? /^(\d{4})-(\d{2})-(\d{2})$/ : /^(\d{2})\.(\d{2})\.(\d{4})$/);
        if (!match) return null;
        const year = Number(match[iso ? 1 : 3]);
        const month = Number(match[2]) - 1;
        const day = Number(match[iso ? 3 : 1]);
        const result = makeDate(year, month, day);
        return result.getFullYear() === year && result.getMonth() === month && result.getDate() === day ? result : null;
    }
    function isoDate(value) {
        return `${String(value.getFullYear()).padStart(4, '0')}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
    }

    document.querySelectorAll('[data-uk-calendar]').forEach((control, index) => {
        const text = control.querySelector('input[type="text"]');
        const native = control.querySelector('input[type="date"]');
        const trigger = control.querySelector('button');
        if (!text || !native || !trigger) return;
        const canChooseYear = control.hasAttribute('data-calendar-year');
        const today = makeDate(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());
        const minimum = parseDate(native.min, true) || makeDate(1900, 0, 1);
        const maximum = parseDate(native.max, true) || (canChooseYear ? today : makeDate(9998, 11, 31));
        const clamp = value => value < minimum ? minimum : value > maximum ? maximum : value;
        let focusedDate = clamp(today);
        let month = makeDate(focusedDate.getFullYear(), focusedDate.getMonth(), 1);

        const popup = document.createElement('div');
        popup.className = 'booking-calendar';
        popup.id = `booking-calendar-${index}`;
        popup.lang = 'uk';
        popup.hidden = true;
        popup.setAttribute('role', 'dialog');
        popup.setAttribute('aria-label', 'Виберіть дату');
        popup.innerHTML = `
            <div class="booking-calendar-heading">
                <button type="button" data-month="-1" aria-label="Попередній місяць">‹</button>
                <span class="booking-calendar-month" aria-live="polite"></span>
                ${canChooseYear ? '<input type="number" class="booking-calendar-year" aria-label="Рік" inputmode="numeric" step="1">' : ''}
                <button type="button" data-month="1" aria-label="Наступний місяць">›</button>
            </div>
            <div class="booking-calendar-weekdays" aria-hidden="true">
                <span>Пн</span><span>Вт</span><span>Ср</span><span>Чт</span><span>Пт</span><span>Сб</span><span>Нд</span>
            </div>
            <div class="booking-calendar-days" role="group" aria-label="Дні місяця"></div>
            <div class="booking-calendar-footer">
                <button type="button" data-clear>Очистити</button>
                <button type="button" data-today>Сьогодні</button>
            </div>`;
        const popupArea = control.closest('[data-calendar-group]')?.querySelector('[data-calendar-popup-area]');
        (popupArea || control).append(popup);
        const days = popup.querySelector('.booking-calendar-days');
        const previous = popup.querySelector('[data-month="-1"]');
        const next = popup.querySelector('[data-month="1"]');
        const yearInput = popup.querySelector('.booking-calendar-year');
        trigger.hidden = false;
        trigger.setAttribute('aria-haspopup', 'dialog');
        trigger.setAttribute('aria-controls', popup.id);
        trigger.setAttribute('aria-expanded', 'false');

        function close(restoreFocus = false) {
            popup.hidden = true;
            trigger.setAttribute('aria-expanded', 'false');
            if (restoreFocus) trigger.focus();
        }
        function focusDay() {
            days.querySelector(`[data-date="${isoDate(focusedDate)}"]`)?.focus();
        }
        function render() {
            const year = month.getFullYear();
            popup.querySelector('.booking-calendar-month').textContent = canChooseYear
                ? months[month.getMonth()]
                : `${months[month.getMonth()]} ${year} р.`;
            if (yearInput) yearInput.value = year;
            previous.disabled = makeDate(month.getFullYear(), month.getMonth(), 0) < minimum;
            next.disabled = makeDate(month.getFullYear(), month.getMonth() + 1, 1) > maximum;
            const selected = parseDate(text.value);
            const start = 1 - (month.getDay() + 6) % 7;
            days.replaceChildren();
            for (let offset = 0; offset < 42; offset++) {
                const date = makeDate(month.getFullYear(), month.getMonth(), start + offset);
                const button = document.createElement('button');
                button.type = 'button';
                button.textContent = date.getDate();
                button.dataset.date = isoDate(date);
                button.disabled = date < minimum || date > maximum;
                button.tabIndex = +date === +focusedDate ? 0 : -1;
                button.classList.toggle('is-other-month', date.getMonth() !== month.getMonth());
                button.setAttribute('aria-label', fullDate.format(date));
                button.setAttribute('aria-pressed', String(selected !== null && +date === +selected));
                if (+date === +today) button.setAttribute('aria-current', 'date');
                days.append(button);
            }
        }
        function choose(value) {
            native.value = value ? isoDate(value) : '';
            text.value = value ? isoDate(value).split('-').reverse().join('.') : '';
            text.dispatchEvent(new Event('input', { bubbles: true }));
            text.dispatchEvent(new Event('change', { bubbles: true }));
            close();
            text.focus();
        }
        function moveMonth(delta) {
            const lastDay = makeDate(month.getFullYear(), month.getMonth() + delta + 1, 0).getDate();
            focusedDate = clamp(makeDate(month.getFullYear(), month.getMonth() + delta, Math.min(focusedDate.getDate(), lastDay)));
            month = makeDate(focusedDate.getFullYear(), focusedDate.getMonth(), 1);
            render();
        }
        trigger.addEventListener('click', () => {
            if (!popup.hidden) { close(); return; }
            focusedDate = clamp(parseDate(text.value) || today);
            month = makeDate(focusedDate.getFullYear(), focusedDate.getMonth(), 1);
            popup.hidden = false;
            trigger.setAttribute('aria-expanded', 'true');
            render();
            focusDay();
        });
        previous.addEventListener('click', () => moveMonth(-1));
        next.addEventListener('click', () => moveMonth(1));
        if (yearInput) {
            yearInput.min = minimum.getFullYear();
            yearInput.max = maximum.getFullYear();
            yearInput.addEventListener('change', () => {
                const year = yearInput.valueAsNumber;
                if (Number.isInteger(year) && yearInput.validity.valid) {
                    moveMonth((year - month.getFullYear()) * 12);
                } else {
                    yearInput.value = month.getFullYear();
                }
            });
            yearInput.addEventListener('keydown', event => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    yearInput.blur();
                    focusDay();
                }
            });
        }
        days.addEventListener('click', event => {
            const button = event.target.closest('[data-date]');
            if (button && !button.disabled) choose(parseDate(button.dataset.date, true));
        });
        popup.querySelector('[data-clear]').addEventListener('click', () => choose(null));
        const todayButton = popup.querySelector('[data-today]');
        todayButton.disabled = today < minimum || today > maximum;
        todayButton.addEventListener('click', () => choose(today));
        popup.addEventListener('keydown', event => {
            if (event.key === 'Escape') { event.preventDefault(); close(true); return; }
            const button = event.target.closest('[data-date]');
            if (!button) return;
            focusedDate = parseDate(button.dataset.date, true);
            const deltas = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
            if (event.key in deltas) {
                focusedDate = clamp(makeDate(focusedDate.getFullYear(), focusedDate.getMonth(), focusedDate.getDate() + deltas[event.key]));
                month = makeDate(focusedDate.getFullYear(), focusedDate.getMonth(), 1);
                render();
            } else if (event.key === 'PageUp' || event.key === 'PageDown') {
                moveMonth(event.key === 'PageUp' ? -1 : 1);
            } else return;
            event.preventDefault();
            focusDay();
        });
        function closeOutside(event) {
            if (!control.contains(event.target) && !popup.contains(event.target)) close();
        }
        document.addEventListener('pointerdown', closeOutside);
        document.addEventListener('focusin', closeOutside);
    });
})();
