class HeroSlideshow {
    constructor() {
        this.slides = document.querySelectorAll('.hero-slideshow .slide');
        this.dots = document.querySelectorAll('.slideshow-nav .nav-dot');
        this.currentSlide = 0;
        this.isTransitioning = false;
        this.slideInterval = null;
        this.transitionDuration = 1000; // 1 second for transitions
        this.slideDuration = 5000;      // 5 seconds between slides

        this.init();
    }

    init() {
        // Add click events to dots
        this.dots.forEach((dot, index) => {
            dot.addEventListener('click', () => this.goToSlide(index));
        });

        // Start the slideshow
        this.showSlide(0, true);
        this.startSlideshow();

        // Pause on hover
        const heroSection = document.querySelector('.hero-section');
        heroSection.addEventListener('mouseenter', () => this.pauseSlideshow());
        heroSection.addEventListener('mouseleave', () => this.startSlideshow());
    }

    showSlide(index, immediate = false) {
        if (this.isTransitioning && !immediate) return;
        this.isTransitioning = true;

        // Handle index bounds
        if (index >= this.slides.length) index = 0;
        if (index < 0) index = this.slides.length - 1;

        // Remove active class from current slide and dot
        const currentActive = document.querySelector('.slide.active');
        if (currentActive) {
            currentActive.style.opacity = '0';
            currentActive.classList.remove('active');
        }
        this.dots.forEach(dot => dot.classList.remove('active'));

        // Add active class to new slide and dot after a short delay
        setTimeout(() => {
            this.slides[index].style.opacity = '1';
            this.slides[index].classList.add('active');
            this.dots[index].classList.add('active');
            this.currentSlide = index;
            this.isTransitioning = false;
        }, immediate ? 0 : 50);
    }

    goToSlide(index) {
        if (this.currentSlide === index) return;
        this.showSlide(index);
        this.startSlideshow(); // Reset interval when manually changing slides
    }

    nextSlide() {
        this.showSlide(this.currentSlide + 1);
    }

    startSlideshow() {
        if (this.slideInterval) clearInterval(this.slideInterval);
        this.slideInterval = setInterval(() => this.nextSlide(), this.slideDuration);
    }

    pauseSlideshow() {
        if (this.slideInterval) {
            clearInterval(this.slideInterval);
            this.slideInterval = null;
        }
    }
}

// Initialize slideshow when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HeroSlideshow();
});