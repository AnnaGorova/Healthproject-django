/**
 * Analytics — графіки здоров'я (Chart.js)
 * 
 * Кольорові точки за ризиком:
 * 🟢 зелений — норма
 * 🟡 жовтий — помірний
 * 🔴 червоний — високий ризик
 *  */

(function () {
    'use strict';

    const dataElement = document.getElementById('chart-data');
    if (!dataElement) return;

    let chartData;
    try {
        chartData = JSON.parse(dataElement.textContent);
    } catch (e) {
        console.error('Помилка парсингу chart data:', e);
        return;
    }

    const RISK_COLORS = {
        'green': '#34D399',
        'yellow': '#FBBF24',
        'red': '#EF4444',
        'null': '#9CA3AF', // ⚪ сірий
    };

    function getPointColors(risks) {
        if (!risks || !Array.isArray(risks)) {
            return RISK_COLORS['null']; 
        }
        return risks.map(risk => RISK_COLORS[risk] || RISK_COLORS['null']);
    }

    const commonOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    afterLabel: function (context) {
                        const risks = context.dataset.riskData;
                        if (!risks) return '';
                        const risk = risks[context.dataIndex];
                        if (!risk) return '';
                        const labels = {
                            'green': '🟢 Норма',
                            'yellow': '🟡 Помірний ризик',
                            'red': '🔴 Високий ризик',
                        };
                        return labels[risk] || '';
                    },
                },
            },
        },
        scales: {
            x: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { color: 'rgba(255,255,255,0.1)' } },
            y: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { color: 'rgba(255,255,255,0.1)' } },
        },
    };

    let visibleChartsCount = 0; // Лічильник видимих графіків

    function createChart(canvasId, label, data, risks, lineColor) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        // Ховаємо графік, якщо всі значення null
        if (!data || data.length === 0 || data.every(val => val === null || val === undefined)) {
            canvas.parentElement.style.display = 'none';
            return;
        }

        visibleChartsCount++; // Збільшуємо лічильник, бо графік буде намальовано
        const pointColors = getPointColors(risks);

        new Chart(canvas, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: label,
                    data: data,
                    borderColor: lineColor,
                    backgroundColor: lineColor + '20',
                    tension: 0,
                    spanGaps: false,
                    pointRadius: 6,
                    pointHoverRadius: 9,
                    pointBackgroundColor: pointColors,
                    pointBorderColor: 'transparent',
                    pointBorderWidth: 0,
                    riskData: risks,
                }],
            },
            options: commonOptions,
        });
    }

    // Малюємо графіки
    createChart('tempChart', 'Температура', chartData.temperature, chartData.temperature_risk, '#F87171');
    createChart('hrChart', 'Пульс', chartData.heart_rate, chartData.heart_rate_risk, '#EF4444');
    createChart('spo2Chart', 'SpO2', chartData.spo2, chartData.spo2_risk, '#60A5FA');
    createChart('sugarChart', 'Цукор', chartData.blood_sugar, chartData.blood_sugar_risk, '#FBBF24');
    
    // Вага
    createChart('weightChart', 'Вага', chartData.weight, null, '#34D399');

    // Тиск
    const bpCanvas = document.getElementById('bpChart');
    if (bpCanvas) {
        const sysData = chartData.pressure_systolic;
        if (!sysData || sysData.length === 0 || sysData.every(val => val === null || val === undefined)) {
            bpCanvas.parentElement.style.display = 'none';
        } else {
            visibleChartsCount++; // Збільшуємо лічильник для тиску
            const bpPointColors = getPointColors(chartData.pressure_risk);

            new Chart(bpCanvas, {
                type: 'line',
                data: {
                    labels: chartData.labels,
                    datasets: [
                        {
                            label: 'Систолічний',
                            data: sysData,
                            borderColor: '#A78BFA',
                            backgroundColor: '#A78BFA20',
                            tension: 0,
                            spanGaps: false,
                            pointRadius: 6,
                            pointHoverRadius: 9,
                            pointBackgroundColor: bpPointColors,
                            pointBorderColor: 'transparent',
                            pointBorderWidth: 0,
                            riskData: chartData.pressure_risk,
                        },
                        {
                            label: 'Діастолічний',
                            data: chartData.pressure_diastolic,
                            borderColor: '#34D399',
                            backgroundColor: '#34D39920',
                            tension: 0,
                            spanGaps: false,
                            pointRadius: 6,
                            pointHoverRadius: 9,
                            pointBackgroundColor: bpPointColors,
                            pointBorderColor: 'transparent',
                            pointBorderWidth: 0,
                            riskData: chartData.pressure_risk,
                        },
                    ],
                },
                options: {
                    ...commonOptions,
                    plugins: {
                        ...commonOptions.plugins,
                        legend: { display: true, labels: { color: 'rgba(255,255,255,0.7)' } },
                    },
                },
            });
        }
    }

    // ===== ПЕРЕВІРКА: чи є хоч один графік =====
    if (visibleChartsCount === 0) {
        const msgElement = document.getElementById('no-charts-message');
        if (msgElement) {
            msgElement.style.display = 'block'; // Показуємо повідомлення
        }
    }

})();