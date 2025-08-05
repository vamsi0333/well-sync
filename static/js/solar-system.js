// Premium Solar System Effects
document.addEventListener('DOMContentLoaded', function() {
    // Create background elements
    const backgroundElements = `
        <div class="stars"></div>
        <div class="nebula"></div>
        <div class="orbital-system">
            <div class="planet"></div>
            <div class="planet"></div>
            <div class="planet"></div>
        </div>
        <div class="shooting-star"></div>
        <div class="shooting-star"></div>
        <div class="shooting-star"></div>
    `;
    
    // Add elements to body
    const container = document.createElement('div');
    container.innerHTML = backgroundElements;
    container.style.position = 'fixed';
    container.style.top = '0';
    container.style.left = '0';
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.zIndex = '-1';
    container.style.overflow = 'hidden';
    document.body.prepend(container);

    // Dynamic star creation
    function createStars(count) {
        const starContainer = document.querySelector('.stars');
        for (let i = 0; i < count; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            star.style.left = `${Math.random() * 100}%`;
            star.style.top = `${Math.random() * 100}%`;
            star.style.animationDelay = `${Math.random() * 3}s`;
            starContainer.appendChild(star);
        }
    }

    // Create random shooting stars
    function createShootingStar() {
        const star = document.createElement('div');
        star.className = 'shooting-star';
        star.style.top = `${Math.random() * 50}%`;
        star.style.left = '-100px';
        document.body.appendChild(star);

        star.addEventListener('animationend', () => {
            star.remove();
            setTimeout(createShootingStar, Math.random() * 3000);
        });
    }

    // Initialize effects
    createStars(50);
    for (let i = 0; i < 3; i++) {
        setTimeout(createShootingStar, i * 2000);
    }

    // Parallax effect on mouse move
    document.addEventListener('mousemove', (e) => {
        const planets = document.querySelectorAll('.planet');
        const moveX = (e.clientX - window.innerWidth / 2) * 0.01;
        const moveY = (e.clientY - window.innerHeight / 2) * 0.01;

        planets.forEach((planet, index) => {
            const speed = (index + 1) * 0.5;
            planet.style.transform = `translate(${moveX * speed}px, ${moveY * speed}px)`;
        });
    });
});
