// Спільні функції графіків головної сторінки та детальної аналітики.
window.HealthCharts = (() => {
    'use strict';
    const riskColors = { green: '#34D399', yellow: '#FBBF24', red: '#EF4444', unknown: '#9CA3AF' };
    const riskLabels = {
        green: 'У межах заданих порогів',
        yellow: 'Помірний рівень за заданими порогами',
        red: 'Вихід за задані пороги',
    };

    // Перевіряє наявність числових вимірювань, включно з нулем.
    function hasValues(values) {
        return Array.isArray(values) && values.some(Number.isFinite);
    }

    // Середнє лише за заповненими числовими значеннями.
    function average(values) {
        const numbers = (values || []).filter(Number.isFinite);
        if (numbers.length === 0) return null;
        return numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
    }

    // Український формат із максимум одним десятковим знаком.
    function formatNumber(value) {
        return new Intl.NumberFormat('uk-UA', { maximumFractionDigits: 1 }).format(value);
    }

    // Оцінки обчислює Django; тут лише вибираємо відповідні кольори.
    function getPointColors(risks) {
        if (!Array.isArray(risks)) return riskColors.unknown;
        return risks.map((risk) => riskColors[risk] || riskColors.unknown);
    }

    // Градієнт перераховується за актуальною висотою області графіка.
    function gradientFill(context) {
        const { ctx, chartArea } = context.chart;
        if (!chartArea) return 'transparent';
        const color = context.dataset.borderColor;
        const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
        gradient.addColorStop(0, `${color}40`);
        gradient.addColorStop(1, `${color}00`);
        return gradient;
    }

    // Створює одну лінію, зберігаючи пропуски даних та оцінки точок.
    function createDataset({ label, values, risks = null, color, unit = '', fill = false, pointRadius = 3, tension = 0 }) {
        return {
            label, data: values, unit, riskData: risks, borderColor: color,
            backgroundColor: fill ? gradientFill : `${color}20`,
            pointBackgroundColor: getPointColors(risks),
            pointBorderColor: 'transparent', pointBorderWidth: 0,
            borderWidth: 2, pointRadius, pointHoverRadius: pointRadius + 2,
            tension, spanGaps: false, fill,
        };
    }

    // Формує новий об'єкт налаштувань для кожного графіка.
    function createOptions({ legend = false, maintainAspectRatio = false, textColor = '#64748B', gridColor = '#dfe9e2', unit = '' } = {}) {
        return {
            responsive: true, maintainAspectRatio, animation: false,
            plugins: {
                legend: { display: legend, labels: { color: textColor } },
                tooltip: {
                    callbacks: {
                        // Підпис точки: назва, значення й одиниця вимірювання.
                        label(context) {
                            const value = context.parsed.y;
                            if (!Number.isFinite(value)) return '';
                            const suffix = context.dataset.unit;
                            return `${context.dataset.label}: ${formatNumber(value)}` + (suffix ? ` ${suffix}` : '');
                        },
                        // Оцінка конкретної точки, отримана з моделі HealthRecord.
                        afterLabel(context) {
                            const risk = context.dataset.riskData?.[context.dataIndex];
                            return riskLabels[risk] || '';
                        },
                    },
                },
            },
            scales: {
                x: { ticks: { color: textColor, maxTicksLimit: 7, maxRotation: 0 }, grid: { color: gridColor } },
                y: { ticks: { color: textColor }, grid: { color: gridColor }, title: { display: Boolean(unit), text: unit, color: textColor } },
            },
        };
    }
    return { hasValues, average, formatNumber, createDataset, createOptions };
})();
