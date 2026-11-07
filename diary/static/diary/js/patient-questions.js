(() => {
    // Відкриваємо питання, на яке веде посилання з пошуку.
    function openQuestionFromHash() {
        const id = window.location.hash.slice(1);
        if (!id.startsWith("question-")) return;
        const question = document.getElementById(id);
        if (question?.matches("details.patient-question")) {
            question.open = true;
            question.scrollIntoView({ block: "start" });
        } else if (question?.closest('[data-patient-inbox]')) {
            const link = question.querySelector('.doctor-inbox-card-footer a');
            if (link) window.location.replace(link.href);
        }
    }

    openQuestionFromHash();

    // Обробляємо перехід до іншого питання на тій самій сторінці.
    window.addEventListener("hashchange", openQuestionFromHash);

    const dialogs = document.querySelectorAll('[data-question-url]');
    const states = new WeakMap();

    function renderMessages(container, messages) {
        const fragment = document.createDocumentFragment();
        messages.forEach(message => {
            const article = document.createElement('article');
            article.className = 'question-message';
            if (message.is_doctor) article.classList.add('question-message-doctor');
            const author = document.createElement('p');
            author.className = 'question-message-author';
            author.textContent = `${message.is_doctor ? 'Лікар ' : ''}${message.author}`;
            if (message.date) author.textContent += ` · ${message.date}`;
            const text = document.createElement('p');
            text.className = 'question-message-text';
            text.textContent = message.text;
            article.append(author, text);
            fragment.append(article);
        });
        container.replaceChildren(fragment);
    }

    function updateDialog(dialog, result) {
        const state = states.get(dialog);
        const container = dialog.querySelector('[data-question-messages]');
        const signature = JSON.stringify(result.messages);
        if (state.signature !== signature) {
            const followLatest = container.hasAttribute('data-follow-latest') && (
                state.signature === null ||
                container.scrollHeight - container.scrollTop - container.clientHeight < 40
            );
            const scrollTop = container.scrollTop;
            renderMessages(container, result.messages);
            container.scrollTop = followLatest ? container.scrollHeight : scrollTop;
            state.signature = signature;
        }
        const status = dialog.querySelector('[data-question-status]');
        if (status) status.textContent = result.status_label;
        const reply = dialog.querySelector('[data-question-reply]');
        if (reply) reply.hidden = !result.can_reply;
        const closed = dialog.querySelector('[data-question-closed]');
        if (closed) {
            closed.hidden = result.status !== 'closed' && result.doctor_active;
            closed.textContent = result.doctor_active
                ? 'Питання закрито.'
                : 'Лікар більше не приймає звернення. Листування доступне для перегляду.';
        }
        const answer = dialog.querySelector('[data-question-answer]');
        if (answer) answer.hidden = result.status === 'closed';
        const doctorForm = dialog.querySelector('[data-doctor-answer-form]');
        if (doctorForm) doctorForm.hidden = !result.can_answer;
        const doctorClosed = dialog.querySelector('[data-doctor-closed]');
        if (doctorClosed) doctorClosed.hidden = result.can_answer;
        state.notice.textContent = '';
    }

    async function refreshDialog(dialog) {
        const state = states.get(dialog);
        if (state.pending || state.stopped || state.sending) return;
        state.pending = true;
        const version = state.version;
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 10000);
        try {
            const response = await fetch(dialog.dataset.questionUrl, {
                credentials: 'same-origin',
                cache: 'no-store',
                signal: controller.signal,
                headers: { Accept: 'application/json' },
            });
            if ([403, 404].includes(response.status) || response.redirected) {
                state.stopped = true;
                state.notice.textContent = 'Оновіть сторінку, щоб перевірити доступ до листування.';
                return;
            }
            if (!response.ok) throw new Error('Не вдалося отримати повідомлення');
            const result = await response.json();
            if (version !== state.version) return;
            updateDialog(dialog, result);
        } catch {
            if (version === state.version) {
                state.notice.textContent = 'Не вдалося оновити листування. Повторюємо спробу…';
            }
        } finally {
            window.clearTimeout(timeout);
            state.pending = false;
        }
    }

    dialogs.forEach(dialog => {
        const notice = document.createElement('p');
        notice.className = 'question-sync-status';
        notice.setAttribute('role', 'status');
        dialog.querySelector('[data-question-messages]').after(notice);
        const history = dialog.querySelector('[data-follow-latest]');
        if (history) history.scrollTop = history.scrollHeight;
        states.set(dialog, { signature: null, pending: false, stopped: false, sending: false, version: 0, notice });
        const form = dialog.querySelector('[data-doctor-answer-form], [data-question-reply]');
        if (form) {
            form.addEventListener('submit', async event => {
                event.preventDefault();
                const state = states.get(dialog);
                if (state.sending) return;
                const textarea = form.querySelector('textarea');
                const draft = textarea.value;
                const payload = new FormData(form);
                const button = form.querySelector('button[type="submit"], button:not([type])');
                state.sending = true;
                state.version++;
                button.disabled = true;
                form.setAttribute('aria-busy', 'true');
                notice.textContent = 'Надсилання…';
                try {
                    const response = await fetch(form.action || window.location.href, {
                        method: 'POST',
                        credentials: 'same-origin',
                        body: payload,
                        headers: {
                            Accept: 'application/json',
                            'X-CSRFToken': payload.get('csrfmiddlewaretoken'),
                        },
                    });
                    if (response.redirected) throw new Error('Оновіть сторінку та увійдіть знову.');
                    const result = await response.json();
                    if (!response.ok) throw new Error(result.error || 'Не вдалося надіслати повідомлення.');
                    const scrollX = window.scrollX;
                    const scrollY = window.scrollY;
                    updateDialog(dialog, result);
                    if (textarea.value === draft) textarea.value = '';
                    const history = dialog.querySelector('[data-question-messages]');
                    history.scrollTop = history.scrollHeight;
                    window.scrollTo({ left: scrollX, top: scrollY, behavior: 'instant' });
                    notice.textContent = 'Повідомлення надіслано.';
                } catch (error) {
                    notice.textContent = error.message || 'Не вдалося надіслати повідомлення. Перевірте з’єднання.';
                } finally {
                    state.sending = false;
                    button.disabled = false;
                    form.removeAttribute('aria-busy');
                }
            });
        }
        if (dialog.matches('details')) {
            dialog.addEventListener('toggle', () => {
                if (dialog.open) refreshDialog(dialog);
            });
        }
    });

    async function pollMessages() {
        if (!document.hidden) {
            await Promise.all(Array.from(dialogs, dialog => refreshDialog(dialog)));
        }
        window.setTimeout(pollMessages, 5000);
    }

    if (dialogs.length) {
        pollMessages();
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) dialogs.forEach(dialog => refreshDialog(dialog));
        });
    }

    const inbox = document.querySelector('[data-question-inbox]');
    if (inbox) {
        const results = inbox.querySelector('[data-inbox-results]');
        const notice = inbox.querySelector('[data-inbox-sync]');
        let stopped = false;
        async function refreshInbox() {
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 10000);
            try {
                if (document.hidden || results.contains(document.activeElement)) return;
                const response = await fetch(window.location.href, {
                    credentials: 'same-origin', cache: 'no-store', signal: controller.signal,
                });
                if (response.redirected || [403, 404].includes(response.status)) {
                    stopped = true;
                    notice.textContent = 'Оновіть сторінку, щоб перевірити доступ до звернень.';
                    return;
                }
                if (!response.ok) throw new Error('Не вдалося отримати звернення');
                const page = new DOMParser().parseFromString(await response.text(), 'text/html');
                const updated = page.querySelector('[data-inbox-results]');
                if (!updated) throw new Error('Не вдалося отримати список');
                if (results.innerHTML !== updated.innerHTML) results.replaceChildren(...updated.childNodes);
                notice.textContent = '';
            } catch {
                notice.textContent = 'Не вдалося оновити звернення. Повторюємо спробу…';
            } finally {
                window.clearTimeout(timeout);
                if (!stopped) window.setTimeout(refreshInbox, 5000);
            }
        }
        window.setTimeout(refreshInbox, 5000);
    }
})();
