(() => {
    const input = document.getElementById("patient-search-input");
    const results = document.getElementById("patient-search-results");
    const status = document.getElementById("patient-search-status");
    if (!input || !results || !status) return;

    let timer;
    let controller;
    let requestNumber = 0;

    // Закриває список і скасовує незавершений пошук.
    function closeSearch() {
        clearTimeout(timer);
        controller?.abort();
        requestNumber++;
        results.hidden = true;
        status.textContent = "";
    }

    // Виводить повідомлення як текст, без вставлення HTML.
    function showMessage(text) {
        const message = document.createElement("p");
        message.className = "patient-search-message";
        message.textContent = text;
        results.replaceChildren(message);
        results.hidden = false;
        status.textContent = text;
    }

    // Створює посилання та заголовки категорій.
    function renderResults(items) {
        results.replaceChildren();
        if (items.length === 0) {
            showMessage("Нічого не знайдено.");
            return;
        }
        let currentGroup = "";
        for (const item of items) {
            if (item.group !== currentGroup) {
                const heading = document.createElement("h2");
                heading.className = "patient-search-group";
                heading.textContent = item.group;
                results.append(heading);
                currentGroup = item.group;
            }
            const link = document.createElement("a");
            link.href = item.url;
            const title = document.createElement("strong");
            title.textContent = item.title;
            const description = document.createElement("span");
            description.textContent = item.description;
            link.append(title, description);
            results.append(link);
        }
        results.hidden = false;
        status.textContent = `Знайдено результатів: ${items.length}.`;
    }

    // Стара відповідь не повинна замінювати новий пошук.
    async function search(query, currentRequest) {
        controller = new AbortController();
        try {
            const url = new URL(input.dataset.url, window.location.origin);
            url.searchParams.set("q", query);
            const response = await fetch(url, {
                signal: controller.signal,
                headers: { Accept: "application/json" },
                cache: "no-store",
            });
            if (!response.ok || response.redirected) throw new Error("Search failed");
            const data = await response.json();
            if (currentRequest !== requestNumber) return;
            renderResults(data.results);
        } catch (error) {
            if (error.name !== "AbortError" && currentRequest === requestNumber) {
                showMessage("Не вдалося виконати пошук. Спробуйте ще раз.");
            }
        }
    }

    // Коротка пауза після введення зменшує кількість запитів.
    input.addEventListener("input", () => {
        clearTimeout(timer);
        controller?.abort();
        const currentRequest = ++requestNumber;
        const query = input.value.trim();
        results.replaceChildren();
        results.hidden = true;
        status.textContent = "";
        if (query.length < 2) return;
        timer = setTimeout(() => {
            status.textContent = "Пошук…";
            search(query, currentRequest);
        }, 300);
    });

    // Стрілка вниз переводить фокус на перший результат.
    input.addEventListener("keydown", (event) => {
        if (event.key === "ArrowDown" && !results.hidden) {
            const firstLink = results.querySelector("a");
            if (firstLink) {
                event.preventDefault();
                firstLink.focus();
            }
        }
        if (event.key === "Escape") closeSearch();
    });

    // Стрілки переміщують фокус; Enter відкриває звичайне посилання.
    results.addEventListener("keydown", (event) => {
        const links = [...results.querySelectorAll("a")];
        const index = links.indexOf(document.activeElement);
        if (event.key === "Escape") {
            closeSearch();
            input.focus();
            return;
        }
        if (index < 0) return;
        if (event.key === "ArrowDown") {
            event.preventDefault();
            links[Math.min(index + 1, links.length - 1)].focus();
        }
        if (event.key === "ArrowUp") {
            event.preventDefault();
            if (index === 0) input.focus();
            else links[index - 1].focus();
        }
    });

    // Натискання поза пошуком закриває підказки.
    document.addEventListener("click", (event) => {
        if (!event.target.closest(".patient-search")) closeSearch();
    });
})();
