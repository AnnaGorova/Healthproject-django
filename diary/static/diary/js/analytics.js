(() => {
    'use strict';
    const element = document.getElementById('chart-data');
    if (!element || !window.HealthCharts) return;
    let data = JSON.parse(element.textContent);
    const { average, formatNumber, hasValues, createDataset, createOptions } = window.HealthCharts;
    const metrics = {
        pressure: { title: 'Артеріальний тиск', unit: 'мм рт. ст.', fields: [['pressure_systolic', 'Систолічний', '#218b70'], ['pressure_diastolic', 'Діастолічний', '#35c9a0']] },
        temperature: { title: 'Температура', unit: '°C', fields: [['temperature', 'Температура', '#48b99b']] },
        heart_rate: { title: 'Пульс', unit: 'уд/хв', fields: [['heart_rate', 'Пульс', '#c97979']] },
        spo2: { title: 'SpO₂', unit: '%', fields: [['spo2', 'SpO₂', '#6f98be']] },
        blood_sugar: { title: 'Глюкоза', unit: 'ммоль/л', fields: [['blood_sugar', 'Глюкоза', '#ac76bf']] },
        weight: { title: 'Вага', unit: 'кг', fields: [['weight', 'Вага', '#218b70']] },
        sleep_hours: { title: 'Сон', unit: 'год', fields: [['sleep_hours', 'Сон', '#6f98be']] },
        steps: { title: 'Кроки', unit: 'кроків', fields: [['steps', 'Кроки', '#218b70']] },
        water_intake: { title: 'Вода', unit: 'мл', fields: [['water_intake', 'Вода', '#6f98be']] },
        calories: { title: 'Калорії', unit: 'ккал', fields: [['calories', 'Калорії', '#c97979']] },
    };
    const riskLabels = { green: 'Норма', yellow: 'Помірний ризик', red: 'Високий ризик' };
    const valuesText = values => values.map(value => value === null ? '—' : formatNumber(value)).join('/');
    const riskValues = key => data[key === 'pressure' ? 'pressure_risk' : `${key}_risk`] || [];
    function indices(key) {
        return data.labels.map((_, index) => index).filter(index =>
            metrics[key].fields.every(([field]) => Number.isFinite(data[field]?.[index])));
    }
    function assessment(container, badge, key) {
        const last = indices(key).at(-1);
        const risk = riskValues(key)[last];
        container.hidden = !riskLabels[risk];
        badge.textContent = riskLabels[risk] || '';
        badge.className = `chart-risk-badge chart-risk-${risk || 'unknown'}`;
    }
    function draw(canvas, empty, key) {
        const metric = metrics[key];
        const hasData = metric.fields.some(([field]) => hasValues(data[field]));
        const available = typeof Chart !== 'undefined';
        canvas.parentElement.hidden = !hasData || !available;
        empty.hidden = hasData && available;
        empty.textContent = !hasData ? 'Немає вимірювань за вибраний період.' : 'Не вдалося завантажити графік. Оновіть сторінку.';
        if (!hasData || !available) return null;
        const options = createOptions();
        if (key === 'pressure') {
            options.scales.y.suggestedMin = 0;
            options.scales.y.suggestedMax = 180;
            options.scales.y.ticks.stepSize = 30;
        }
        options.scales.x.ticks.callback = function (value) { return this.getLabelForValue(value).split(' ')[0]; };
        return new Chart(canvas, {
            type: 'line',
            data: { labels: data.labels, datasets: metric.fields.map(([field, label, color]) => createDataset({
                label, values: data[field], risks: riskValues(key), color, unit: metric.unit, fill: true, tension: 0.2,
            })) },
            options,
        });
    }
    const overviewCharts = new Map();
    function updateOverview() {
        document.querySelectorAll('[data-overview-metric]').forEach(panel => {
            overviewCharts.get(panel)?.destroy();
            const key = panel.dataset.overviewMetric;
            const averages = metrics[key].fields.map(([field]) => {
                const value = average(data[field]);
                return (key === 'pressure' || key === 'heart_rate') && value !== null ? Math.round(value) : value;
            });
            panel.querySelector('[data-average]').textContent = valuesText(averages);
            if (key === 'pressure') {
                panel.querySelector('[data-systolic]').textContent = valuesText([averages[0]]);
                panel.querySelector('[data-diastolic]').textContent = valuesText([averages[1]]);
            }
            assessment(panel.querySelector('[data-assessment]'), panel.querySelector('[data-risk]'), key);
            overviewCharts.set(panel, draw(panel.querySelector('canvas'), panel.querySelector('.analytics-chart-empty'), key));
        });
    }
    function updateParameters() {
        document.querySelectorAll('[data-parameter]').forEach(card => {
            const key = card.dataset.parameter;
            const measured = indices(key);
            const last = measured.at(-1);
            if (last === undefined) {
                card.querySelector('[data-value]').textContent = '—';
                card.querySelector('[data-date]').textContent = '';
                card.querySelector('[data-risk]').textContent = '';
                card.querySelector('[data-change]').textContent = 'Немає даних';
                return;
            }
            const current = metrics[key].fields.map(([field]) => data[field][last]);
            card.querySelector('[data-value]').textContent = valuesText(current);
            card.querySelector('[data-date]').textContent = data.labels[last];
            card.querySelector('[data-risk]').textContent = riskLabels[riskValues(key)[last]] || '';
            const previous = measured.at(-2);
            card.querySelector('[data-change]').textContent = previous === undefined ? 'Перше вимірювання' : metrics[key].fields.map(([field], index) => {
                const delta = current[index] - data[field][previous];
                return `${delta > 0 ? '+' : ''}${formatNumber(delta)}`;
            }).join('/') + ` ${metrics[key].unit}`;
        });
    }
    let chart;
    let currentMetric = 'temperature';
    function showMetric(key) {
        const metric = metrics[key];
        if (!metric) return;
        currentMetric = key;
        if (chart) chart.destroy();
        document.getElementById('chart-title').textContent = metric.title;
        const averages = metric.fields.map(([field]) => {
            const value = average(data[field]);
            return (key === 'pressure' || key === 'heart_rate') && value !== null ? Math.round(value) : value;
        });
        document.getElementById('chart-average').textContent = valuesText(averages);
        document.getElementById('chart-unit').textContent = metric.unit;
        document.getElementById('pressure-chart-icon').hidden = key !== 'pressure';
        document.getElementById('chart-pressure-details').hidden = key !== 'pressure';
        document.getElementById('chart-systolic').textContent = valuesText([averages[0]]);
        document.getElementById('chart-diastolic').textContent = key === 'pressure' ? valuesText([averages[1]]) : '—';
        assessment(document.getElementById('chart-assessment'), document.getElementById('chart-risk-badge'), key);
        document.querySelectorAll('[data-metric][aria-pressed]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.metric === key)));
        const canvas = document.getElementById('home-health-chart');
        canvas.setAttribute('aria-label', `Динаміка: ${metric.title}`);
        chart = draw(canvas, document.getElementById('chart-empty'), key);
    }
    document.querySelectorAll('[data-metric]').forEach(button => button.addEventListener('click', () => {
        if (button.dataset.metric === 'other') {
            const other = document.querySelector('.analytics-other');
            other.hidden = !other.hidden;
            button.setAttribute('aria-expanded', String(!other.hidden));
        } else showMetric(button.dataset.metric);
    }));
    const periodLinks = document.querySelectorAll('.analytics-page .dynamics-periods a');
    const periodStatus = document.getElementById('chart-period-status');
    const page = document.querySelector('.analytics-page');
    let periodController;
    let periodRequestId = 0;
    function updateStatistics(rows) {
        const body = document.querySelector('.analytics-statistics tbody');
        const number = new Intl.NumberFormat('uk-UA', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
        body.replaceChildren(...rows.map(row => {
            const tr = document.createElement('tr');
            const heading = document.createElement('th');
            heading.scope = 'row';
            heading.textContent = `${row.label}, ${row.unit}`;
            tr.append(heading);
            ['average', 'minimum', 'maximum'].forEach(field => {
                const cell = document.createElement('td');
                cell.textContent = row[field] === null ? '—' : number.format(Number(row[field]));
                tr.append(cell);
            });
            return tr;
        }));
    }
    periodLinks.forEach(link => link.addEventListener('click', async event => {
        if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        periodController?.abort();
        const controller = new AbortController();
        periodController = controller;
        const requestId = ++periodRequestId;
        const url = new URL(link.href);
        url.searchParams.set('format', 'json');
        periodStatus.textContent = 'Завантаження показників…';
        page.setAttribute('aria-busy', 'true');
        try {
            const response = await fetch(url, {
                signal: controller.signal, credentials: 'same-origin', cache: 'no-store',
                headers: { Accept: 'application/json' },
            });
            if (!response.ok) throw new Error('Не вдалося отримати дані.');
            const result = await response.json();
            if (requestId !== periodRequestId) return;
            const scrollX = window.scrollX;
            const scrollY = window.scrollY;
            data = result.chart_data;
            updateOverview();
            updateParameters();
            updateStatistics(result.stat_rows);
            document.getElementById('analytics-empty').hidden = result.has_records;
            showMetric(currentMetric);
            periodLinks.forEach(periodLink => {
                const active = new URL(periodLink.href).searchParams.get('period') === result.period;
                if (active) periodLink.setAttribute('aria-current', 'true');
                else periodLink.removeAttribute('aria-current');
            });
            const pageUrl = new URL(window.location.href);
            pageUrl.searchParams.set('period', result.period);
            pageUrl.searchParams.delete('format');
            window.history.replaceState(null, '', pageUrl);
            periodStatus.textContent = '';
            window.scrollTo({ left: scrollX, top: scrollY, behavior: 'instant' });
        } catch (error) {
            if (error.name === 'AbortError' || requestId !== periodRequestId) return;
            periodStatus.textContent = 'Не вдалося оновити дані. Спробуйте ще раз.';
        } finally {
            if (requestId === periodRequestId) page.removeAttribute('aria-busy');
        }
    }));
    updateOverview();
    updateParameters();
    showMetric(currentMetric);
})();
