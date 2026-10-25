(function () {
    'use strict';
    const dataElement = document.getElementById('chart-data');
    if (!dataElement || !window.HealthCharts) return;

    let data;
    // Зчитуємо JSON, сформований Django для поточного пацієнта.
    try {
        data = JSON.parse(dataElement.textContent);
    } catch (error) {
        console.error('Помилка читання даних аналітики:', error);
        return;
    }
    const { hasValues, createDataset, createOptions } = window.HealthCharts;
    let visibleChartsCount = 0;

    // Створює окремий графік або приховує блок без даних.
    function showChart(canvasId, datasets) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        const hasData = datasets.some((dataset) => hasValues(dataset.data));
        if (!hasData || typeof Chart === 'undefined') {
            canvas.parentElement.style.display = 'none';
            return;
        }
        new Chart(canvas, {
            type: 'line',
            data: { labels: data.labels, datasets },
            options: createOptions({
                legend: datasets.length > 1,
                maintainAspectRatio: true,
                // Зберігаємо оформлення осей наявної сторінки аналітики.
                textColor: 'rgba(255,255,255,0.7)',
                gridColor: 'rgba(255,255,255,0.1)',
            }),
        });
        visibleChartsCount++;
    }

    // Конфігурація графіків з однією лінією; вага не має оцінки ризику.
    const singleCharts = [
        ['tempChart', 'temperature', 'Температура', '°C', '#F87171'],
        ['hrChart', 'heart_rate', 'Пульс', 'уд/хв', '#EF4444'],
        ['spo2Chart', 'spo2', 'SpO₂', '%', '#60A5FA'],
        ['sugarChart', 'blood_sugar', 'Глюкоза', 'ммоль/л', '#FBBF24'],
        ['weightChart', 'weight', 'Вага', 'кг', '#34D399'],
    ];
    singleCharts.forEach(([canvasId, field, label, unit, color]) => {
        showChart(canvasId, [createDataset({
            label, values: data[field], risks: data[`${field}_risk`] || null,
            color, unit, pointRadius: 6,
        })]);
    });

    // Обидві лінії тиску використовують оцінку відповідного вимірювання.
    showChart('bpChart', [
        createDataset({ label: 'Систолічний', values: data.pressure_systolic, risks: data.pressure_risk, color: '#A78BFA', unit: 'мм рт. ст.', pointRadius: 6 }),
        createDataset({ label: 'Діастолічний', values: data.pressure_diastolic, risks: data.pressure_risk, color: '#34D399', unit: 'мм рт. ст.', pointRadius: 6 }),
    ]);

    // Повідомляємо про відсутні дані або недоступність Chart.js.
    if (visibleChartsCount === 0) {
        const message = document.getElementById('no-charts-message');
        if (message) {
            message.style.display = 'block';
            if (typeof Chart === 'undefined') {
                message.textContent = 'Не вдалося завантажити графіки. Оновіть сторінку.';
            }
        }
    }
})();
