(() => {
    'use strict';
    const element = document.getElementById('chart-data');
    if (!element || !window.HealthCharts) return;
    const data = JSON.parse(element.textContent);
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
    document.querySelectorAll('[data-overview-metric]').forEach(panel => {
        const key = panel.dataset.overviewMetric;
        const averages = metrics[key].fields.map(([field]) => average(data[field]));
        panel.querySelector('[data-average]').textContent = valuesText(averages);
        if (key === 'pressure') {
            panel.querySelector('[data-systolic]').textContent = valuesText([averages[0]]);
            panel.querySelector('[data-diastolic]').textContent = valuesText([averages[1]]);
        }
        assessment(panel.querySelector('[data-assessment]'), panel.querySelector('[data-risk]'), key);
        draw(panel.querySelector('canvas'), panel.querySelector('.analytics-chart-empty'), key);
    });
    document.querySelectorAll('[data-parameter]').forEach(card => {
        const key = card.dataset.parameter;
        const measured = indices(key);
        const last = measured.at(-1);
        if (last === undefined) return;
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
    let chart;
    function showMetric(key) {
        const metric = metrics[key];
        if (!metric) return;
        if (chart) chart.destroy();
        document.getElementById('chart-title').textContent = metric.title;
        const averages = metric.fields.map(([field]) => average(data[field]));
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
    showMetric('temperature');
})();
