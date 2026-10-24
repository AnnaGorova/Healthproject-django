function togglePassword(inputId = 'password') {
    const passwordInput = document.getElementById(inputId);
    
    if (!passwordInput) {
        console.error('Поле не знайдено:', inputId);
        return;
    }
    
    const wrapper = passwordInput.parentElement;
    const toggleIcon = wrapper.querySelector('.toggle-password');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.add('is-visible');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('is-visible');
    }
}

const loginForm = document.querySelector('.login-form-panel form');
const loginLoading = document.getElementById('login-loading');
const loginSubmit = loginForm?.querySelector('.login-submit');

if (loginForm && loginLoading && loginSubmit) {
    let submitting = false;

    loginForm.addEventListener('submit', (event) => {
        event.preventDefault();

        if (submitting) {
            return;
        }

        submitting = true;
        loginSubmit.disabled = true;
        loginForm.setAttribute('aria-busy', 'true');
        loginLoading.showModal();

        // Даємо браузеру відобразити вікно перед надсиланням.
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                HTMLFormElement.prototype.submit.call(loginForm);
            });
        });
    });

    // Під час перевірки не закриваємо індикатор клавішею Esc.
    loginLoading.addEventListener('cancel', (event) => {
        event.preventDefault();
    });

    // Відновлюємо форму після повернення кнопкою браузера «Назад».
    window.addEventListener('pageshow', () => {
        submitting = false;
        loginSubmit.disabled = false;
        loginForm.removeAttribute('aria-busy');

        if (loginLoading.open) {
            loginLoading.close();
        }
    });
}
