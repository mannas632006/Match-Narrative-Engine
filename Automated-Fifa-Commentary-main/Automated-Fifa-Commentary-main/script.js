// ==========================================
// AI FIFA Commentary Engine — Interactive JS
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    initNavScroll();
    initTerminalAnimation();
    initScrollAnimations();
    initCounterAnimations();
});

// === Smooth Nav on Scroll ===
function initNavScroll() {
    const nav = document.getElementById('nav');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.scrollY;
        if (currentScroll > 50) {
            nav.classList.add('scrolled');
        } else {
            nav.classList.remove('scrolled');
        }
        lastScroll = currentScroll;
    });
}

// === Terminal Typing Animation ===
function initTerminalAnimation() {
    const terminal = document.getElementById('terminal');
    const typingCmd = document.getElementById('typing-cmd');
    const cursor = document.querySelector('.cursor');

    const lines = [
        { type: 'command', text: 'python run_standalone.py match.mp4', delay: 50 },
        { type: 'output', text: '', delay: 600, class: '' },
        { type: 'output', text: 'Initializing Standalone FIFA Commentary System...', delay: 400, class: 'info' },
        { type: 'output', text: 'Loaded YOLO model: yolov8n', delay: 300, class: 'success' },
        { type: 'output', text: 'GPT-4 Vision enabled for event classification', delay: 300, class: 'success' },
        { type: 'output', text: 'OpenAI GPT enabled for commentary generation', delay: 300, class: 'success' },
        { type: 'output', text: 'OpenAI TTS enabled for speech synthesis', delay: 300, class: 'success' },
        { type: 'output', text: 'Pipeline ready!', delay: 200, class: 'accent' },
        { type: 'output', text: '', delay: 200, class: '' },
        { type: 'output', text: '--- Starting processing: match.mp4 ---', delay: 400, class: 'info' },
        { type: 'output', text: 'Video info: 4500 frames, 30 fps', delay: 300, class: '' },
        { type: 'output', text: '', delay: 100, class: '' },
        { type: 'output', text: '[Frame 0] Detected 14 objects', delay: 200, class: '' },
        { type: 'output', text: '[Frame 0] Events: possession (0.72)', delay: 200, class: '' },
        { type: 'output', text: '[Frame 90] Detected 16 objects', delay: 200, class: '' },
        { type: 'output', text: '[Frame 90] Events: pass (0.84)', delay: 200, class: 'warn' },
        { type: 'output', text: '[Frame 180] Detected 15 objects', delay: 200, class: '' },
        { type: 'output', text: '[Frame 180] Events: shot_on_goal (0.91)', delay: 200, class: 'warn' },
        { type: 'output', text: '[Frame 270] Events: goal (0.95) 🥅', delay: 300, class: 'success' },
        { type: 'output', text: '', delay: 100, class: '' },
        { type: 'output', text: '[Generated Commentary]', delay: 400, class: 'accent' },
        { type: 'output', text: '"And it\'s IN! GOAL! An absolute screamer', delay: 100, class: 'success' },
        { type: 'output', text: ' from the edge of the box!"', delay: 100, class: 'success' },
        { type: 'output', text: '', delay: 200, class: '' },
        { type: 'output', text: 'Playing commentary audio... 🔊', delay: 400, class: 'info' },
        { type: 'output', text: 'Exporting final video to outputs/match_with_commentary.mp4', delay: 300, class: '' },
        { type: 'output', text: '✓ Success! Final video saved.', delay: 400, class: 'success' },
    ];

    let lineIndex = 0;
    let charIndex = 0;

    function typeCommand() {
        const line = lines[0];
        if (charIndex < line.text.length) {
            typingCmd.textContent += line.text[charIndex];
            charIndex++;
            setTimeout(typeCommand, line.delay);
        } else {
            cursor.style.display = 'none';
            setTimeout(() => {
                lineIndex = 1;
                showOutputLines();
            }, 500);
        }
    }

    function showOutputLines() {
        if (lineIndex >= lines.length) {
            // Loop after a pause
            setTimeout(() => {
                resetTerminal();
            }, 5000);
            return;
        }

        const line = lines[lineIndex];
        const div = document.createElement('div');
        div.className = 'terminal-line';

        if (line.text === '') {
            div.innerHTML = '&nbsp;';
        } else {
            const span = document.createElement('span');
            span.className = `output ${line.class || ''}`;
            span.textContent = line.text;
            div.appendChild(span);
        }

        terminal.appendChild(div);
        terminal.scrollTop = terminal.scrollHeight;

        lineIndex++;
        setTimeout(showOutputLines, line.delay);
    }

    function resetTerminal() {
        // Clear all lines except the first command line
        while (terminal.children.length > 1) {
            terminal.removeChild(terminal.lastChild);
        }
        typingCmd.textContent = '';
        cursor.style.display = '';
        charIndex = 0;
        lineIndex = 0;
        setTimeout(typeCommand, 500);
    }

    // Start the animation
    setTimeout(typeCommand, 1000);
}

// === Scroll-triggered Animations ===
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.delay || 0;
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, parseInt(delay));
            }
        });
    }, observerOptions);

    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        observer.observe(card);
    });

    // Observe video cards
    document.querySelectorAll('.video-card').forEach((card, i) => {
        card.dataset.delay = i * 200;
        observer.observe(card);
    });

    // Observe pipeline steps
    document.querySelectorAll('.pipeline-step').forEach((step, i) => {
        step.dataset.delay = i * 100;
        observer.observe(step);
    });
}

// === Counter Animation ===
function initCounterAnimations() {
    const counters = document.querySelectorAll('.stat-number');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.dataset.target);
                animateCounter(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(element, target) {
    let current = 0;
    const increment = target / 30;
    const duration = 1000;
    const stepTime = duration / 30;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current);
        }
    }, stepTime);
}

// === Copy Code Button ===
function copyCode(button) {
    const codeBlock = button.closest('.code-block');
    const code = codeBlock.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.style.color = 'var(--accent-green)';
        button.style.borderColor = 'var(--accent-green)';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.color = '';
            button.style.borderColor = '';
        }, 2000);
    }).catch(() => {
        // Fallback
        const textarea = document.createElement('textarea');
        textarea.value = code;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
        button.textContent = 'Copied!';
        setTimeout(() => { button.textContent = 'Copy'; }, 2000);
    });
}
