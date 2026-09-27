(function () {
    const input = document.getElementById('icd10_search_input');
    const resultsBox = document.getElementById('icd10_results');
    const hiddenSelect = document.getElementById('id_icd10');
    let debounceTimer = null;
    let activeIndex = -1;
    let currentItems = [];

    function closeResults() {
        resultsBox.classList.remove('is-open');
        resultsBox.innerHTML = '';
        activeIndex = -1;
    }

    function selectItem(item) {
        // Додаємо/оновлюємо option у прихованому select і вибираємо його
        let option = hiddenSelect.querySelector(`option[value="${item.id}"]`);
        if (!option) {
            option = document.createElement('option');
            option.value = item.id;
            hiddenSelect.appendChild(option);
        }
        option.textContent = item.text;
        hiddenSelect.value = item.id;

        input.value = item.text;
        closeResults();
    }

    function renderResults(items) {
        currentItems = items;
        activeIndex = -1;

        if (!items.length) {
            resultsBox.innerHTML = '<div class="icd10-result-empty">Нічого не знайдено</div>';
            resultsBox.classList.add('is-open');
            return;
        }

        resultsBox.innerHTML = items.map((item, i) => {
            const [code, ...rest] = item.text.split(' — ');
            const name = rest.join(' — ');
            return `<div class="icd10-result-item" data-index="${i}">
                        <span class="code">${code}</span>${name}
                    </div>`;
        }).join('');

        resultsBox.classList.add('is-open');

        resultsBox.querySelectorAll('.icd10-result-item').forEach((el) => {
            el.addEventListener('mousedown', (e) => {
                e.preventDefault();
                const idx = parseInt(el.dataset.index, 10);
                selectItem(currentItems[idx]);
            });
        });
    }

    function fetchResults(query) {
        resultsBox.innerHTML = '<div class="icd10-result-loading">Пошук...</div>';
        resultsBox.classList.add('is-open');

        fetch(`/doctor/icd10-autocomplete/?q=${encodeURIComponent(query)}`, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then((res) => res.json())
            .then((data) => renderResults(data.results || []))
            .catch(() => {
                resultsBox.innerHTML = '<div class="icd10-result-empty">Помилка пошуку</div>';
            });
    }

    input.addEventListener('input', function () {
        const query = input.value.trim();

        // Якщо поле очищене — скидаємо вибір у прихованому select
        if (!query) {
            hiddenSelect.value = '';
            closeResults();
            return;
        }

        if (query.length < 2) {
            closeResults();
            return;
        }

        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => fetchResults(query), 250);
    });

    input.addEventListener('keydown', function (e) {
        const items = resultsBox.querySelectorAll('.icd10-result-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            activeIndex = Math.min(activeIndex + 1, items.length - 1);
            items.forEach((el, i) => el.classList.toggle('is-active', i === activeIndex));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            activeIndex = Math.max(activeIndex - 1, 0);
            items.forEach((el, i) => el.classList.toggle('is-active', i === activeIndex));
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0) selectItem(currentItems[activeIndex]);
        } else if (e.key === 'Escape') {
            closeResults();
        }
    });

    document.addEventListener('click', function (e) {
        if (!e.target.closest('.icd10-autocomplete')) {
            closeResults();
        }
    });
})();
