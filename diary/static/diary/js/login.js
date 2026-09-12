function togglePassword() {
    const passwordInput = document.getElementById('password');
    const toggleIcon = document.querySelector('.toggle-password');

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.add('is-visible');
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('is-visible');
    }
}