document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButton = document.getElementById('theme-toggle-button');
    const currentTheme = localStorage.getItem('theme');

    if (currentTheme) {
        document.body.classList.add(currentTheme);
    }

    themeToggleButton.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');

        let theme = 'dark-theme';
        if (document.body.classList.contains('light-theme')) {
            theme = 'light-theme';
        }
        localStorage.setItem('theme', theme);
    });
}); 