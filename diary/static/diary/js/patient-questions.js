(() => {
    // Відкриваємо питання, на яке веде посилання з пошуку.
    function openQuestionFromHash() {
        const id = window.location.hash.slice(1);
        if (!id.startsWith("question-")) return;
        const question = document.getElementById(id);
        if (question?.matches("details.patient-question")) {
            question.open = true;
            question.scrollIntoView({ block: "start" });
        }
    }

    openQuestionFromHash();

    // Обробляємо перехід до іншого питання на тій самій сторінці.
    window.addEventListener("hashchange", openQuestionFromHash);
})();
