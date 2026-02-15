/**
 * ============================================================================
 * BRIDGEHIVE ENTERPRISE CORE ENGINE v5.1 (Build 2026.1.26)
 * Target System: High-Performance Intergenerational Learning Platform
 * Author: Nanyang Polytechnic Project Team
 * License: Proprietary / Enterprise
 * ============================================================================
 */

/* ============================================================================
   1. CORE SYSTEM & CONFIGURATION
   ============================================================================ */
const AppConfig = {
    debug: true,
    version: '5.1.0',
    apiBase: '/lib/api/v1',
    animationSpeed: 300,
    toastDuration: 4000,
    physics: {
        particleCount: 80,
        connectionDistance: 150,
        mouseRadius: 200,
        baseColor: 'rgba(60, 79, 99, 0.05)',
        accentColor: 'rgba(104, 132, 166, 0.28)'
    },
    breakpoints: {
        mobile: 576,
        tablet: 768,
        desktop: 992
    }
};

/**
 * Central State Store (Redux-like pattern)
 */
const Store = {
    state: {
        user: { id: 1, role: 'admin', name: 'Instructor' },
        currentRoute: window.location.pathname,
        isLoading: false,
        activeToasts: [],
        courseProgress: 0,
        courses: []
    },
    
    listeners: {},
    
    on(event, callback) {
        if (!this.listeners[event]) this.listeners[event] = [];
        this.listeners[event].push(callback);
    },
    
    emit(event, payload) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(cb => cb(payload));
        }
    },
    
    setLoading(status) {
        this.state.isLoading = status;
        const loader = document.getElementById('globalLoader');
        if (loader) loader.style.display = status ? 'flex' : 'none';
    }
};

/* ============================================================================
   2. VISUAL PHYSICS ENGINE (CANVAS)
   ============================================================================ */
class ParticleEngine {
    constructor() {
        this.canvas = document.createElement('canvas');
        this.ctx = this.canvas.getContext('2d');
        this.particles = [];
        this.mouse = { x: null, y: null };
        
        this.initDOM();
        this.resize();
        this.createParticles();
        this.bindEvents();
        this.animate();
        
        console.log('[System] Physics Engine Initialized');
    }

    initDOM() {
        this.canvas.id = 'bg-canvas';
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.zIndex = '-1';
        this.canvas.style.pointerEvents = 'none';
        document.body.prepend(this.canvas);
    }

    bindEvents() {
        window.addEventListener('resize', () => this.resize());
        window.addEventListener('mousemove', (e) => {
            this.mouse.x = e.clientX;
            this.mouse.y = e.clientY;
        });
        window.addEventListener('mouseout', () => {
            this.mouse.x = null;
            this.mouse.y = null;
        });
    }

    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        const area = (this.canvas.width * this.canvas.height) / 10000;
        const targetCount = Math.floor(area * 4);
        if (this.particles.length < targetCount) {
            const diff = targetCount - this.particles.length;
            for (let i = 0; i < diff; i++) {
                this.particles.push(this.createParticle());
            }
        }
    }

    createParticle() {
        return {
            x: Math.random() * this.canvas.width,
            y: Math.random() * this.canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5,
            radius: Math.random() * 1.5 + 0.5
        };
    }

    createParticles(count = 80) {
        for (let i = 0; i < count; i++) {
            this.particles.push(this.createParticle());
        }
    }

    draw() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        for (let i = 0; i < this.particles.length; i++) {
            const p = this.particles[i];
            
            p.x += p.vx;
            p.y += p.vy;
            
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;
            
            if (this.mouse.x !== null) {
                const dx = this.mouse.x - p.x;
                const dy = this.mouse.y - p.y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                if (distance < AppConfig.physics.mouseRadius) {
                    const force = (AppConfig.physics.mouseRadius - distance) / AppConfig.physics.mouseRadius;
                    p.vx -= (dx / distance) * force * 2;
                    p.vy -= (dy / distance) * force * 2;
                }
            }
            
            this.ctx.fillStyle = AppConfig.physics.baseColor;
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.connect(p, this.particles.slice(i + 1));
        }
    }

    connect(p1, others) {
        for (let p2 of others) {
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance < AppConfig.physics.connectionDistance) {
                this.ctx.strokeStyle = AppConfig.physics.accentColor;
                this.ctx.lineWidth = 0.5;
                this.ctx.beginPath();
                this.ctx.moveTo(p1.x, p1.y);
                this.ctx.lineTo(p2.x, p2.y);
                this.ctx.stroke();
            }
        }
    }

    animate() {
        this.draw();
        requestAnimationFrame(() => this.animate());
    }
}

/* ============================================================================
   3. USER INTERFACE CONTROLLER
   ============================================================================ */
class UIController {
    static init() {
        this.createToastContainer();
        this.bindGlobalInteractions();
    }

    static createToastContainer() {
        if (!document.getElementById('toast-container-ent')) {
            const container = document.createElement('div');
            container.id = 'toast-container-ent';
            container.style.cssText = 'position: fixed; top: 2rem; right: 2rem; z-index: 9999; display: flex; flex-direction: column; gap: 1rem;';
            document.body.appendChild(container);
        }
    }

    static showToast(message, type = 'success') {
        const container = document.getElementById('toast-container-ent');
        const id = 'toast-' + Date.now();
        
        const icons = {
            success: 'fa-check-circle',
            danger: 'fa-exclamation-circle',
            warning: 'fa-exclamation-triangle',
            info: 'fa-info-circle'
        };

        const html = `
            <div id="${id}" class="toast align-items-center text-white bg-${type} border-0 show shadow-lg rounded-3" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center">
                        <i class="fas ${icons[type]} fa-lg me-3"></i>
                        <span class="fw-medium">${message}</span>
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        const wrapper = document.createElement('div');
        wrapper.innerHTML = html;
        container.appendChild(wrapper.firstElementChild);

        const toastElement = document.getElementById(id);
        setTimeout(() => {
            toastElement?.remove();
        }, AppConfig.toastDuration);
    }

    static bindGlobalInteractions() {
        document.addEventListener('click', (e) => {
            if (e.target.tagName === 'A' && !e.target.download) {
                const href = e.target.getAttribute('href');
                if (href && href.startsWith('/')) {
                    console.log(`[Navigation] → ${href}`);
                }
            }
        });
    }
}

/* ============================================================================
   4. REAL-TIME LIBRARY FILTER & MANAGER
   ============================================================================ */
class LibraryManager {
    static init() {
        this.bindEvents();
        this.loadInitialData();
    }

    static bindEvents() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.search(e.target.value));
        }

        document.querySelectorAll('[data-filter]').forEach(btn => {
            btn.addEventListener('click', () => this.filter(btn.dataset.filter));
        });
    }

    static search(term) {
        const items = document.querySelectorAll('.course-item');
        let visibleCount = 0;

        items.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes(term.toLowerCase()) || term === '') {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        const emptyState = document.getElementById('emptyState');
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 && term ? 'block' : 'none';
        }
    }

    static filter(category) {
        const items = document.querySelectorAll('.course-item');
        let visibleCount = 0;

        items.forEach(item => {
            if (category === 'all' || item.dataset.category === category) {
                item.style.display = '';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        const emptyState = document.getElementById('emptyState');
        if (emptyState) {
            emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
        }
    }

    static loadInitialData() {
        fetch('/lib/api/v1/courses')
            .then(res => res.json())
            .then(data => {
                Store.state.courses = data;
                console.log('[Library] Loaded', data.length, 'courses');
            })
            .catch(err => console.warn('[Library] API not available', err));
    }
}

/* ============================================================================
   5. ASSESSMENT ENGINE (Quiz)
   ============================================================================ */
class AssessmentEngine {
    constructor() {
        this.quizContainer = document.getElementById('quizApp');
        if (!this.quizContainer) return;

        this.currentIndex = 0;
        this.score = 0;
        this.selectedOption = null;

        this.ui = {
            qText: document.getElementById('questionText'),
            opts: document.getElementById('optionsContainer'),
            next: document.getElementById('nextBtn'),
            nums: { cur: document.getElementById('currentNum'), tot: document.getElementById('totalNum') },
            prog: document.getElementById('progressBar'),
            main: document.getElementById('questionArea'),
            res: document.getElementById('resultArea'),
            foot: document.getElementById('quizFooter')
        };

        this.init();
    }

    init() {
        if (this.ui.next) this.ui.next.addEventListener('click', () => this.handleNext());
        if (document.getElementById('quitBtn')) {
            document.getElementById('quitBtn').addEventListener('click', () => window.location.href = '/library');
        }
        this.loadQuestion();
    }

    loadQuestion() {
        const data = window.quizData ? window.quizData[this.currentIndex] : null;
        if (!data) return;

        this.ui.qText.innerText = data.q;
        this.ui.opts.innerHTML = '';
        this.ui.next.classList.add('disabled');
        this.selectedOption = null;

        this.ui.nums.cur.innerText = this.currentIndex + 1;
        this.ui.prog.style.width = `${((this.currentIndex + 1) / window.quizData.length) * 100}%`;

        data.options.forEach((opt, idx) => {
            const div = document.createElement('div');
            div.className = 'option-card';
            div.dataset.idx = idx;
            div.innerHTML = `<div class="fw-bold me-3 text-muted">${String.fromCharCode(65 + idx)}</div><div class="fs-5">${opt}</div>`;
            
            div.addEventListener('click', () => this.selectOption(div, idx));
            this.ui.opts.appendChild(div);
        });
    }

    selectOption(div, idx) {
        document.querySelectorAll('.option-card').forEach(c => c.classList.remove('selected'));
        div.classList.add('selected');
        this.selectedOption = idx;
        this.ui.next.classList.remove('disabled');
    }

    handleNext() {
        if (this.selectedOption === null) return;
        
        if (this.selectedOption === window.quizData[this.currentIndex].a) {
            this.score++;
        }

        this.currentIndex++;
        if (this.currentIndex < window.quizData.length) {
            this.loadQuestion();
        } else {
            this.showResults();
        }
    }

    showResults() {
        this.ui.main.classList.add('d-none');
        this.ui.foot.classList.add('d-none');
        this.ui.res.classList.remove('d-none');
        this.ui.res.classList.add('d-flex');

        const percentage = Math.round((this.score / window.quizData.length) * 100);
        document.getElementById('scoreText').innerText = `${percentage}%`;

        if (percentage > 70) this.triggerConfetti();
    }

    triggerConfetti() {
        for (let i = 0; i < 50; i++) {
            const c = document.createElement('div');
            c.className = 'confetti';
            c.style.left = Math.random() * 100 + 'vw';
            c.style.animationDuration = (Math.random() * 3 + 2) + 's';
            c.style.backgroundColor = ['#f2d74e', '#95c3de', '#ff9a91'][Math.floor(Math.random() * 3)];
            document.body.appendChild(c);
        }
    }
}

/* ============================================================================
   6. LEARNING ENVIRONMENT PLAYER
   ============================================================================ */
class LearningPlayer {
    constructor() {
        this.init();
    }

    init() {
        const tabButtons = document.querySelectorAll('[data-bs-toggle="tab"]');
        if (tabButtons.length > 0) {
            console.log('[Player] Learning Environment Initialized');
        }
    }
}

/* ============================================================================
   7. MAIN ENTRY POINT
   ============================================================================ */
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 BridgeHive System Starting...');
    
    UIController.init();
    console.log('✓ UI Controller Ready');
    
    if (!document.getElementById('no-particles')) {
        new ParticleEngine();
    }
    
    const path = window.location.pathname;

    if (path.includes('/library')) {
        LibraryManager.init();
        console.log('✓ Library Manager Ready');
    } else if (path.includes('/quiz')) {
        new AssessmentEngine();
        console.log('✓ Assessment Engine Ready');
    } else if (path.includes('/course')) {
        new LearningPlayer();
        console.log('✓ Learning Player Ready');
    }

    console.log(`✓ System Ready. Route: ${path}`);
    Store.emit('system-ready', { version: AppConfig.version });
});

window.addEventListener('error', (e) => {
    console.error('[Error]', e.error);
    UIController.showToast('An error occurred. Please try again.', 'danger');
});

window.addEventListener('offline', () => {
    UIController.showToast('You are offline. Some features may be unavailable.', 'warning');
});

window.addEventListener('online', () => {
    UIController.showToast('Connection restored!', 'success');
});
