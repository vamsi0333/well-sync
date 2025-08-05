/* Ultra-premium effects and animations */
const cursor = {
    init: () => {
        const cursor = document.createElement('div');
        cursor.className = 'custom-cursor';
        document.body.appendChild(cursor);
        
        document.addEventListener('mousemove', (e) => {
            cursor.style.transform = `translate(${e.clientX}px, ${e.clientY}px)`;
        });
        
        document.querySelectorAll('a, button, input').forEach(el => {
            el.addEventListener('mouseenter', () => cursor.classList.add('cursor-hover'));
            el.addEventListener('mouseleave', () => cursor.classList.remove('cursor-hover'));
        });
    }
};

const particles = {
    init: () => {
        const container = document.querySelector('.particles-container');
        const particleCount = 100;
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            particle.style.setProperty('--delay', `${Math.random() * 5}s`);
            particle.style.setProperty('--size', `${Math.random() * 3 + 1}px`);
            container.appendChild(particle);
        }
    }
};

const parallax = {
    init: () => {
        window.addEventListener('mousemove', (e) => {
            const cards = document.querySelectorAll('.card-parallax');
            const mouseX = e.clientX / window.innerWidth - 0.5;
            const mouseY = e.clientY / window.innerHeight - 0.5;
            
            cards.forEach(card => {
                const rect = card.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const distanceX = (e.clientX - centerX) / 20;
                const distanceY = (e.clientY - centerY) / 20;
                
                card.style.transform = `
                    perspective(1000px)
                    rotateY(${distanceX}deg)
                    rotateX(${-distanceY}deg)
                    translateZ(20px)
                `;
            });
        });
    }
};

// Initialize effects
document.addEventListener('DOMContentLoaded', () => {
    cursor.init();
    particles.init();
    parallax.init();
});
