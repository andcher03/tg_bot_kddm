document.addEventListener("DOMContentLoaded", () => {
    const countEl = document.getElementById("channelMemberCount");
    const changeEl = document.getElementById("channelNetChange");
    const arrowEl = document.getElementById("channelNetArrow");
    const valueEl = document.getElementById("channelNetValue");
    const lastEventEl = document.getElementById("channelLastEvent");
    const openButton = document.getElementById("channelHistoryOpen");
    const dialog = document.getElementById("channelHistoryDialog");
    const closeButton = document.getElementById("channelHistoryClose");
    const periodButtons = document.querySelectorAll("[data-history-days]");
    const historyStatus = document.getElementById("channelHistoryStatus");
    const historyChart = document.getElementById("channelHistoryChart");
    const historySummary = document.getElementById("channelHistorySummary");
    const historyCurrent = document.getElementById("channelHistoryCurrent");
    const historyChange = document.getElementById("channelHistoryChange");

    if (!countEl || !changeEl || !arrowEl || !valueEl || !lastEventEl) {
        return;
    }

    function renderNet(value) {
        changeEl.classList.remove(
            "dashboard-change-up",
            "dashboard-change-down",
            "dashboard-change-neutral"
        );

        if (value > 0) {
            changeEl.classList.add("dashboard-change-up");
            arrowEl.textContent = "↑";
            valueEl.textContent = `+${value}`;
        } else if (value < 0) {
            changeEl.classList.add("dashboard-change-down");
            arrowEl.textContent = "↓";
            valueEl.textContent = String(value);
        } else {
            changeEl.classList.add("dashboard-change-neutral");
            arrowEl.textContent = "—";
            valueEl.textContent = "0";
        }
    }

    function renderLastEvent(event) {
        const message = document.createElement("span");

        if (!event) {
            message.className = "dashboard-channel-last-neutral";
            message.textContent = "Последних изменений пока нет";
        } else if (event.event_type === "join") {
            message.className = "dashboard-channel-last-join";
            message.textContent = `↑ Последнее изменение: подписка · ${event.time}`;
        } else {
            message.className = "dashboard-channel-last-leave";
            message.textContent = `↓ Последнее изменение: отписка · ${event.time}`;
        }

        lastEventEl.replaceChildren(message);
    }

    function renderStats(data) {
        if (data.total !== null && data.total !== undefined) {
            countEl.textContent = Number(data.total).toLocaleString("ru-RU");
            countEl.classList.remove("dashboard-metric-value-muted");
        }

        renderNet(Number(data.today || 0));
        renderLastEvent(data.last_event || null);
    }

    async function refreshStats() {
        try {
            const response = await fetch("/api/dashboard/channel-stats", {
                cache: "no-store"
            });

            if (response.ok) {
                renderStats(await response.json());
            }
        } catch (error) {
            console.debug("Channel live refresh skipped", error);
        }
    }

    function formatDate(value) {
        return new Intl.DateTimeFormat("ru-RU", {
            day: "2-digit",
            month: "2-digit"
        }).format(new Date(`${value}T12:00:00`));
    }

    function formatLongDate(value) {
        return new Intl.DateTimeFormat("ru-RU", {
            day: "numeric",
            month: "long",
            year: "numeric"
        }).format(new Date(`${value}T12:00:00`));
    }

    function renderSummary(points) {
        const first = points[0].count;
        const current = points[points.length - 1].count;
        const change = current - first;

        historyCurrent.textContent = current.toLocaleString("ru-RU");
        historyChange.classList.remove("positive", "negative", "neutral");

        if (change > 0) {
            historyChange.textContent = `+${change.toLocaleString("ru-RU")}`;
            historyChange.classList.add("positive");
        } else if (change < 0) {
            historyChange.textContent = change.toLocaleString("ru-RU");
            historyChange.classList.add("negative");
        } else {
            historyChange.textContent = "0";
            historyChange.classList.add("neutral");
        }

        historySummary.hidden = false;
    }

    function renderChart(points) {
        const width = 820;
        const height = 340;
        const margin = {top: 24, right: 24, bottom: 54, left: 68};
        const plotWidth = width - margin.left - margin.right;
        const plotHeight = height - margin.top - margin.bottom;
        const counts = points.map((point) => point.count);
        const dataMin = Math.min(...counts);
        const dataMax = Math.max(...counts);
        const padding = Math.max(1, Math.ceil((dataMax - dataMin || dataMax) * 0.05));
        const minValue = Math.max(0, dataMin - padding);
        const maxValue = dataMax + padding;
        const range = Math.max(1, maxValue - minValue);

        const xFor = (index) => {
            if (points.length === 1) {
                return margin.left + plotWidth / 2;
            }
            return margin.left + (index / (points.length - 1)) * plotWidth;
        };

        const yFor = (count) => (
            margin.top + ((maxValue - count) / range) * plotHeight
        );

        const coordinates = points.map((point, index) => ({
            ...point,
            x: xFor(index),
            y: yFor(point.count)
        }));

        const linePath = coordinates
            .map((point, index) => `${index === 0 ? "M" : "L"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
            .join(" ");

        const areaPath = points.length > 1
            ? `${linePath} L ${coordinates.at(-1).x.toFixed(2)} ${(margin.top + plotHeight).toFixed(2)} L ${coordinates[0].x.toFixed(2)} ${(margin.top + plotHeight).toFixed(2)} Z`
            : "";

        const yTicks = Array.from({length: 5}, (_, index) => {
            const ratio = index / 4;
            const value = Math.round(maxValue - ratio * range);
            const y = margin.top + ratio * plotHeight;
            return {value, y};
        });

        const labelCount = Math.min(6, points.length);
        const xLabelIndexes = [...new Set(
            Array.from({length: labelCount}, (_, index) => (
                Math.round(index * (points.length - 1) / Math.max(1, labelCount - 1))
            ))
        )];

        const grid = yTicks.map((tick) => `
            <line class="channel-chart-grid" x1="${margin.left}" y1="${tick.y}" x2="${width - margin.right}" y2="${tick.y}"></line>
            <text class="channel-chart-y-label" x="${margin.left - 12}" y="${tick.y + 4}" text-anchor="end">${tick.value.toLocaleString("ru-RU")}</text>
        `).join("");

        const xLabels = xLabelIndexes.map((index) => `
            <text class="channel-chart-x-label" x="${coordinates[index].x}" y="${height - 20}" text-anchor="middle">${formatDate(points[index].date)}</text>
        `).join("");

        const circles = coordinates.map((point) => `
            <circle class="channel-chart-point" cx="${point.x}" cy="${point.y}" r="4.5">
                <title>${formatLongDate(point.date)}: ${point.count.toLocaleString("ru-RU")} подписчиков</title>
            </circle>
        `).join("");

        historyChart.innerHTML = `
            <svg viewBox="0 0 ${width} ${height}" aria-hidden="true" focusable="false">
                <defs>
                    <linearGradient id="channelHistoryArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="currentColor" stop-opacity="0.20"></stop>
                        <stop offset="100%" stop-color="currentColor" stop-opacity="0"></stop>
                    </linearGradient>
                </defs>
                ${grid}
                ${areaPath ? `<path class="channel-chart-area" d="${areaPath}"></path>` : ""}
                ${points.length > 1 ? `<path class="channel-chart-line" d="${linePath}"></path>` : ""}
                ${circles}
                ${xLabels}
            </svg>
        `;

        historyChart.setAttribute(
            "aria-label",
            `График подписчиков с ${formatLongDate(points[0].date)} по ${formatLongDate(points.at(-1).date)}`
        );
        historyChart.hidden = false;
    }

    async function loadHistory(days) {
        historyStatus.hidden = false;
        historyStatus.textContent = "Загружаем историю…";
        historyChart.hidden = true;
        historySummary.hidden = true;

        try {
            const response = await fetch(
                `/api/dashboard/channel-history?days=${days}`,
                {cache: "no-store"}
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.configured) {
                historyStatus.textContent = "Сначала настройте Telegram-канал в kddm.env.";
                return;
            }

            if (!data.points.length) {
                historyStatus.textContent = "История появится после первой синхронизации подписчиков.";
                return;
            }

            historyStatus.hidden = true;
            renderSummary(data.points);
            renderChart(data.points);
        } catch (error) {
            console.error("Channel history loading failed", error);
            historyStatus.textContent = "Не удалось загрузить историю. Попробуйте ещё раз.";
        }
    }

    if (openButton && dialog && closeButton) {
        openButton.addEventListener("click", () => {
            dialog.showModal();
            loadHistory(30);
        });

        closeButton.addEventListener("click", () => dialog.close());

        dialog.addEventListener("click", (event) => {
            const rect = dialog.getBoundingClientRect();
            const inside = (
                event.clientX >= rect.left
                && event.clientX <= rect.right
                && event.clientY >= rect.top
                && event.clientY <= rect.bottom
            );

            if (!inside) {
                dialog.close();
            }
        });

        periodButtons.forEach((button) => {
            button.addEventListener("click", () => {
                periodButtons.forEach((item) => item.classList.remove("active"));
                button.classList.add("active");
                loadHistory(Number(button.dataset.historyDays));
            });
        });
    }

    refreshStats();
    window.setInterval(refreshStats, 3000);
});
