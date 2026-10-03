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