// Дані передає Django через безпечний JSON-блок у шаблоні.
const chartDataElement = document.getElementById('home-chart-data');
const chartCanvas = document.getElementById('home-health-chart');

// На сторінках інших ролей графіка немає — нічого не запускаємо.
if (chartDataElement && chartCanvas) {
    const data = JSON.parse(chartDataElement.textContent);
    const title = document.getElementById('chart-title');
    const averageText = document.getElementById('chart-average');
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

    // Обчислює середнє лише з чисел; пропуски null не враховує.
    function average(values) {
        const numbers = values.filter(Number.isFinite);
        if (numbers.length === 0) return null;
        return numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
    }

    // Форматує число українською з максимум одним десятковим знаком.
    function formatNumber(value) {
        return new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 1 }).format(value);
    }

    // Оновлює заголовок, середнє значення, стан кнопок і сам графік.
    function showMetric(key) {
        const metric = metrics[key];
        title.textContent = metric.title;
        chartCanvas.setAttribute('aria-label', `Динаміка показника: ${metric.title}`);
        buttons.forEach((button) => {
            button.setAttribute('aria-pressed', String(button.dataset.metric === key));
        });

        // Знищуємо попередній графік перед повторним використанням canvas.
        if (chart) {
            chart.destroy();
            chart = null;
        }
        const hasData = metric.fields.some(([field]) => data[field].some(Number.isFinite));
        emptyMessage.textContent = 'Немає вимірювань цього показника за вибраний період.';
        emptyMessage.hidden = hasData;
        chartContainer.hidden = !hasData;
        if (!hasData) {
            averageText.textContent = '';
            return;
        }

        // Для тиску обчислюємо середні систолічного і діастолічного окремо.
        const averages = metric.fields.map(([field, label]) => {
            const value = average(data[field]);
            return value === null
                ? `${label}: немає даних`
                : `${label}: ${formatNumber(value)} ${metric.unit}`;
        });
        averageText.textContent = `Середнє за період — ${averages.join('; ')}`;

        // Якщо CDN недоступний, замість помилки JavaScript пояснюємо ситуацію.
        if (typeof Chart === 'undefined') {
            chartContainer.hidden = true;
            emptyMessage.hidden = false;
            emptyMessage.textContent = 'Не вдалося завантажити графік. Спробуйте оновити сторінку.';
            return;
        }

        // Створюємо адаптивний графік. Пропуски не замінюємо нулями.
        chart = new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: metric.fields.map(([field, label, color]) => ({
                    label, data: data[field], borderColor: color,
                    backgroundColor: `${color}18`, fill: true,
                    borderWidth: 2, pointRadius: 3, tension: 0.2, spanGaps: false,
                })),
            },
            options: {
                responsive: true, maintainAspectRatio: false, animation: false,
                plugins: {
                    legend: { display: metric.fields.length > 1 },
                    tooltip: {
                        callbacks: {
                            // Підказка над точкою містить значення та одиниці вимірювання.
                            label(context) {
                                return `${context.dataset.label}: ${formatNumber(context.parsed.y)} ${metric.unit}`;
                            },
                        },
                    },
                },
                scales: {
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 7, maxRotation: 0 } },
                    y: { title: { display: true, text: metric.unit }, grid: { color: '#dfe9e2' } },
                },
            },
        });
    }

    // Перемикаємо показник без перезавантаження сторінки.
    buttons.forEach((button) => {
        button.addEventListener('click', () => showMetric(button.dataset.metric));
    });

    // За замовчуванням відкриваємо артеріальний тиск.
    showMetric('pressure');
}
