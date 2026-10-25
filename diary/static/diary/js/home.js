// Дані передає Django через безпечний JSON-блок у шаблоні.
const chartDataElement = document.getElementById('home-chart-data');
const chartCanvas = document.getElementById('home-health-chart');

// На сторінках інших ролей графіка немає — нічого не запускаємо.
if (chartDataElement && chartCanvas) {
    const { hasValues, average, formatNumber, createDataset, createOptions } = window.HealthCharts;
    let data = JSON.parse(chartDataElement.textContent);
    const title = document.getElementById('chart-title');
    const averageText = document.getElementById('chart-average');
    const unitText = document.getElementById('chart-unit');
    const assessment = document.getElementById('chart-assessment');
    const riskBadge = document.getElementById('chart-risk-badge');
    const pressureDetails = document.getElementById('chart-pressure-details');
    const systolicText = document.getElementById('chart-systolic');
    const diastolicText = document.getElementById('chart-diastolic');
    const emptyMessage = document.getElementById('chart-empty');
    const chartContainer = document.getElementById('chart-container');
    const buttons = document.querySelectorAll('.dynamics-selector [data-metric]');

    // Назви, одиниці та лінії кожного показника. Для тиску — дві лінії.
    const metrics = {
        pressure: {
            title: 'Артеріальний тиск', unit: 'мм рт. ст.',
            fields: [
                ['pressure_systolic', 'Систолічний', '#218b70'],
                ['pressure_diastolic', 'Діастолічний', '#35c9a0'],
            ],
        },
        heart_rate: { title: 'Пульс', unit: 'уд/хв', fields: [['heart_rate', 'Пульс', '#c97979']] },
        temperature: { title: 'Температура', unit: '°C', fields: [['temperature', 'Температура', '#48b99b']] },
        spo2: { title: 'SpO₂', unit: '%', fields: [['spo2', 'SpO₂', '#6f98be']] },
        blood_sugar: { title: 'Глюкоза', unit: 'ммоль/л', fields: [['blood_sugar', 'Глюкоза', '#ac76bf']] },
    };
    let chart;
    let currentMetric = 'pressure';
    let periodController = null;
    let periodRequestId = 0;
    const periodLinks = document.querySelectorAll('.dynamics-periods [data-period]');
    const periodStatus = document.getElementById('chart-period-status');

    // Оновлює велике середнє значення та плашки артеріального тиску.
    function updateSummary(key, metric) {
        const averages = metric.fields.map(([field]) => average(data[field]));
        averageText.textContent = averages
            .map((value) => value === null ? '—' : formatNumber(value)).join('/');
        unitText.textContent = averages.some((value) => value !== null) ? metric.unit : '';
        pressureDetails.hidden = key !== 'pressure' || averages.every((value) => value === null);
        if (key === 'pressure') {
            systolicText.textContent = averages[0] === null ? '—' : formatNumber(averages[0]);
            diastolicText.textContent = averages[1] === null ? '—' : formatNumber(averages[1]);
        }
    }

    // Оцінює останнє вимірювання у вибраному періоді за готовою оцінкою Django.
    // Середнє значення не використовується для визначення оцінки.
    function updateAssessment(key, metric) {
        const riskField = key === 'pressure' ? 'pressure_risk' : `${key}_risk`;
        const risks = data[riskField] || [];
        let latestRisk = null;
        for (let index = data.labels.length - 1; index >= 0; index--) {
            const hasMeasurement = metric.fields.some(([field]) => Number.isFinite(data[field][index]));
            if (hasMeasurement) {
                latestRisk = risks[index];
                break;
            }
        }
        const labels = {
            green: 'У межах заданих порогів',
            yellow: 'Помірний рівень',
            red: 'Вихід за задані пороги',
        };
        assessment.hidden = !labels[latestRisk];
        riskBadge.textContent = labels[latestRisk] || '';
        riskBadge.className = 'chart-risk-badge';
        if (labels[latestRisk]) riskBadge.classList.add(`chart-risk-${latestRisk}`);
    }

    // Оновлює заголовок, середнє значення, стан кнопок і сам графік.
    function showMetric(key) {
        // Зберігаємо показник при перемиканні періоду.
        currentMetric = key;
        const metric = metrics[key];
        title.textContent = metric.title;
        // Сердечко відображаємо лише для графіка артеріального тиску.
        document.getElementById('pressure-chart-icon').hidden = key !== 'pressure';
        chartCanvas.setAttribute('aria-label', `Динаміка показника: ${metric.title}`);
        buttons.forEach((button) => {
            button.setAttribute('aria-pressed', String(button.dataset.metric === key));
        });

        // Знищуємо попередній графік перед повторним використанням canvas.
        if (chart) {
            chart.destroy();
            chart = null;
        }
        const hasData = metric.fields.some(([field]) => hasValues(data[field]));
        updateSummary(key, metric);
        updateAssessment(key, metric);
        emptyMessage.textContent = 'Немає вимірювань цього показника за вибраний період.';
        emptyMessage.hidden = hasData;
        chartContainer.hidden = !hasData;
        if (!hasData) {
            return;
        }

        // Якщо CDN недоступний, замість помилки JavaScript пояснюємо ситуацію.
        if (typeof Chart === 'undefined') {
            chartContainer.hidden = true;
            emptyMessage.hidden = false;
            emptyMessage.textContent = 'Не вдалося завантажити графік. Спробуйте оновити сторінку.';
            return;
        }

        // Створюємо адаптивний графік. Пропуски не замінюємо нулями.
        const riskField = key === 'pressure' ? 'pressure_risk' : `${key}_risk`;
        const options = createOptions({ legend: false, unit: metric.unit });
        // Орієнтир шкали тиску з макета без обрізання більших значень.
        if (key === 'pressure') {
            options.scales.y.suggestedMin = 0;
            options.scales.y.suggestedMax = 180;
            options.scales.y.ticks.stepSize = 30;
        }
        // Скорочуємо лише підписи осі; підказки зберігають дату й час.
        options.scales.x.ticks.callback = function (value) {
            return this.getLabelForValue(value).split(' ')[0];
        };
        // Плашки над графіком замінюють легенду; сітка — пунктирна.
        options.scales.x.grid.display = true;
        options.scales.x.border = { dash: [3, 3], color: '#dfe9e2' };
        options.scales.y.border = { dash: [3, 3], color: '#dfe9e2' };
        chart = new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: metric.fields.map(([field, label, color]) => createDataset({
                    label, values: data[field], risks: data[riskField],
                    color, unit: metric.unit, fill: true, tension: 0.2,
                })),
            },
            options,
        });
    }

    // Перемикаємо показник без перезавантаження сторінки.
    buttons.forEach((button) => {
        button.addEventListener('click', () => showMetric(button.dataset.metric));
    });

    // Завантажуємо новий період без переходу на іншу сторінку.
    periodLinks.forEach((link) => {
        link.addEventListener('click', async (event) => {
            // Не змінюємо стандартне відкриття посилання в новій вкладці.
            if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) {
                return;
            }
            event.preventDefault();

            // Скасовуємо попередній запит і відстежуємо актуальну відповідь.
            periodController?.abort();
            const controller = new AbortController();
            periodController = controller;
            const requestId = ++periodRequestId;
            const url = new URL(link.href);
            url.searchParams.set('format', 'json');
            periodStatus.textContent = 'Завантаження показників…';
            chartContainer.setAttribute('aria-busy', 'true');

            try {
                const response = await fetch(url, {
                    signal: controller.signal,
                    credentials: 'same-origin',
                    cache: 'no-store',
                    headers: { Accept: 'application/json' },
                });
                if (!response.ok) throw new Error('Не вдалося отримати дані.');
                const result = await response.json();
                if (requestId !== periodRequestId) return;

                data = result.chart_data;
                periodLinks.forEach((periodLink) => {
                    if (periodLink.dataset.period === result.period) {
                        periodLink.setAttribute('aria-current', 'true');
                    } else {
                        periodLink.removeAttribute('aria-current');
                    }
                });

                // Оновлюємо адресу, не перезавантажуючи сторінку.
                const pageUrl = new URL(window.location.href);
                pageUrl.searchParams.set('period', result.period);
                pageUrl.searchParams.delete('format');
                window.history.replaceState(null, '', pageUrl);
                showMetric(currentMetric);
                periodStatus.textContent = '';
            } catch (error) {
                if (error.name === 'AbortError' || requestId !== periodRequestId) return;
                // При помилці залишаємо попередній графік доступним.
                periodStatus.textContent = 'Не вдалося оновити дані. Спробуйте ще раз.';
            } finally {
                if (requestId === periodRequestId) {
                    chartContainer.removeAttribute('aria-busy');
                }
            }
        });
    });

    // За замовчуванням відкриваємо артеріальний тиск.
    showMetric('pressure');
}
