// Enhanced 3D Effects and Performance Optimizations
document.addEventListener('DOMContentLoaded', function() {
    // Initialize 3D parallax effect
    const parallaxElements = document.querySelectorAll('[data-depth]');
    const cursorInteractive = document.querySelectorAll('.cursor-interactive');
    let mouseX = 0, mouseY = 0;
    
    // Performance optimization using requestAnimationFrame
    let ticking = false;

    // Handle mouse movement for parallax effect
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;

        if (!ticking) {
            requestAnimationFrame(() => {
                updateParallax();
                updateCursorInteraction();
                ticking = false;
            });
            ticking = true;
        }
    });

    // Update parallax elements
    function updateParallax() {
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        
        parallaxElements.forEach(element => {
            const depth = parseFloat(element.getAttribute('data-depth'));
            const shiftX = (mouseX - centerX) * depth;
            const shiftY = (mouseY - centerY) * depth;
            
            element.style.transform = `translate3d(${shiftX}px, ${shiftY}px, 0) scale3d(1.1, 1.1, 1.1)`;
        });
    }

    // Update cursor-interactive elements
    function updateCursorInteraction() {
        cursorInteractive.forEach(element => {
            const rect = element.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            const angleX = (mouseY - centerY) / 30;
            const angleY = (mouseX - centerX) / -30;
            
            element.style.transform = `rotateX(${angleX}deg) rotateY(${angleY}deg)`;
        });
    }

    // Initialize particle system
    if (document.getElementById('particlesLayer')) {
        initParticles();
    }

    // Initialize constellation effect
    if (document.getElementById('constellationLayer')) {
        initConstellations();
    }

    // Initialize sparkles canvas
    const sparklesCanvas = document.getElementById('sparklesCanvas');
    if (sparklesCanvas) {
        initSparkles(sparklesCanvas);
    }
});

// Particle system initialization
function initParticles() {
    const particlesLayer = document.getElementById('particlesLayer');
    // Create and animate particles using transform3d for better performance
    for (let i = 0; i < 50; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle transform-gpu';
        particle.style.setProperty('--random-x', Math.random());
        particle.style.setProperty('--random-y', Math.random());
        particlesLayer.appendChild(particle);
    }
}

// Constellation effect
function initConstellations() {
    const constellationLayer = document.getElementById('constellationLayer');
    // Create constellation points and lines
    for (let i = 0; i < 20; i++) {
        const point = document.createElement('div');
        point.className = 'constellation-point transform-gpu';
        point.style.setProperty('--point-x', Math.random() * 100 + '%');
        point.style.setProperty('--point-y', Math.random() * 100 + '%');
        constellationLayer.appendChild(point);
    }
}

// Sparkles effect using Canvas for better performance
function initSparkles(canvas) {
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const sparkles = [];
    
    function createSparkle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2 + 1,
            velocity: Math.random() * 0.5 + 0.1
        };
    }

    // Initialize sparkles
    for (let i = 0; i < 50; i++) {
        sparkles.push(createSparkle());
    }

    // Animate sparkles
    function animateSparkles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        sparkles.forEach(sparkle => {
            ctx.beginPath();
            ctx.arc(sparkle.x, sparkle.y, sparkle.size, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fill();
            
            sparkle.y -= sparkle.velocity;
            if (sparkle.y < 0) {
                Object.assign(sparkle, createSparkle(), { y: canvas.height });
            }
        });
        
        requestAnimationFrame(animateSparkles);
    }
    
    animateSparkles();
}

// Handle window resize
window.addEventListener('resize', () => {
    if (document.getElementById('sparklesCanvas')) {
        const canvas = document.getElementById('sparklesCanvas');
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
});
