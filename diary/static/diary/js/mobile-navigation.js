(() => {
    const navigation = document.querySelector('.mobile-navigation');
    if (!navigation) return;
    const mobileLayout = window.matchMedia('(max-width: 768px)');

    function updateNavigation() {
        if (!mobileLayout.matches || navigation.classList.contains('is-visible')) return;
        const pageFits = document.documentElement.scrollHeight <= window.innerHeight + 1;
        if (window.scrollY > 0 || pageFits) {
            navigation.classList.add('is-visible');
        }
    }

    window.addEventListener('scroll', updateNavigation, { passive: true });
    window.addEventListener('load', updateNavigation);
    mobileLayout.addEventListener('change', updateNavigation);

    const toggle = document.querySelector('.mobile-menu-toggle');
    if (toggle) {
        toggle.hidden = false;
        toggle.addEventListener('click', () => {
            toggle.setAttribute('aria-expanded', String(toggle.getAttribute('aria-expanded') !== 'true'));
        });
    }
})();
