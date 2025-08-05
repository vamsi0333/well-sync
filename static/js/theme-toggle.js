// Enhanced Theme Toggle Functionality
document.addEventListener('DOMContentLoaded', function() {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const themeToggleLightIcon = document.getElementById('theme-toggle-light-icon');
    const themeToggleDarkIcon = document.getElementById('theme-toggle-dark-icon');
    
    // Function to update theme and UI
    function updateTheme(isDark) {
        // Add transition classes
        document.documentElement.classList.add('transition-colors');
        document.documentElement.classList.add('duration-300');
        
        // Update theme
        if (isDark) {
            document.documentElement.classList.add('dark');
            themeToggleDarkIcon.classList.remove('hidden');
            themeToggleLightIcon.classList.add('hidden');
            localStorage.theme = 'dark';
        } else {
            document.documentElement.classList.remove('dark');
            themeToggleLightIcon.classList.remove('hidden');
            themeToggleDarkIcon.classList.add('hidden');
            localStorage.theme = 'light';
        }
        
        // Add animation to theme toggle button
        themeToggleBtn.classList.add('scale-110');
        setTimeout(() => {
            themeToggleBtn.classList.remove('scale-110');
        }, 200);
        
        // Remove transition classes after animation
        setTimeout(() => {
            document.documentElement.classList.remove('transition-colors');
        }, 300);
    }
    
    // Set initial theme
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const savedTheme = localStorage.getItem('theme');
    
    // Initialize theme based on saved preference or system preference
    if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
        updateTheme(true);
    } else {
        updateTheme(false);
    }
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.theme) {
            updateTheme(e.matches);
        }
    });
    
    // Toggle theme on button click
    themeToggleBtn.addEventListener('click', () => {
        updateTheme(!document.documentElement.classList.contains('dark'));
    });
    
    // Add hover effect
    themeToggleBtn.addEventListener('mouseover', () => {
        themeToggleBtn.classList.add('scale-105');
    });
    
    themeToggleBtn.addEventListener('mouseout', () => {
        themeToggleBtn.classList.remove('scale-105');
    });
});
