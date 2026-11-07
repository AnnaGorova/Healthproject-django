console.log("main.js завантажено!");

// Вирівнюємо меню з нижнім краєм вмісту вибраних сторінок на широких екранах.
const profileCard = document.querySelector('.patient-profile, .admin-user-editor, .about-page, .admin-home-errors');
const profileSidebar = document.querySelector('.health-theme .sidebar');

if (profileCard && profileSidebar) {
    const desktopLayout = window.matchMedia('(min-width: 769px)');

    function alignProfileSidebar() {
        if (!desktopLayout.matches) {
            profileSidebar.style.removeProperty('min-height');
            return;
        }

        const height = profileCard.getBoundingClientRect().bottom
            - profileSidebar.getBoundingClientRect().top;
        profileSidebar.style.minHeight = `${Math.ceil(height)}px`;
    }

    const profileLayoutObserver = new ResizeObserver(alignProfileSidebar);
    profileLayoutObserver.observe(profileCard);
    profileLayoutObserver.observe(profileCard.closest('.main-content'));
    window.addEventListener('resize', alignProfileSidebar);
    alignProfileSidebar();
}

const menuScrollKey = 'sidebarNavigationScroll';

// Відновлюємо прокрутку після переходу через меню.
const savedScroll = sessionStorage.getItem(menuScrollKey);

if (savedScroll !== null) {
    sessionStorage.removeItem(menuScrollKey);

    const scrollY = Number(savedScroll);

    if (Number.isFinite(scrollY)) {
        window.addEventListener('load', () => {
            window.scrollTo({
                top: scrollY,
                left: 0,
                behavior: 'instant',
            });
        }, { once: true });
    }
}

// Запам’ятовуємо прокрутку перед переходом.
document.querySelectorAll('.sidebar-nav a.nav-link').forEach((link) => {
    link.addEventListener('click', (event) => {
        if (
            event.button !== 0 ||
            event.ctrlKey ||
            event.metaKey ||
            event.shiftKey ||
            event.altKey ||
            link.target === '_blank'
        ) {
            return;
        }

        const destination = new URL(link.href);

        if (
            destination.origin === window.location.origin &&
            !destination.pathname.startsWith('/admin/')
        ) {
            sessionStorage.setItem(menuScrollKey, String(window.scrollY));
        }
    });
});
