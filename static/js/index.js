document.addEventListener('DOMContentLoaded', function() {
    //Carrossel
    const carouselImages = document.querySelector('.carousel-images');
    const images = document.querySelectorAll('.carousel-images .carousel-image');

    let currentIndex = 0;
    const totalImages = images.length;
    let autoSlideInterval;

    function showImage(index) {
        if (index >= totalImages) {
            currentIndex = 0; 
        } else if (index < 0) {
            currentIndex = totalImages - 1; 
        } else {
            currentIndex = index;
        }
        const offset = -currentIndex * 100;
        carouselImages.style.transform = `translateX(${offset}%)`;

        images.forEach((img, i) => {
            img.classList.remove('active');
            if (i === currentIndex) {
                img.classList.add('active');
            }
        });
    }

    function nextImage() {
        showImage(currentIndex + 1);
    }

    function startAutoSlide() {
        clearInterval(autoSlideInterval);
        autoSlideInterval = setInterval(nextImage, 4000); 
    }

    if (carouselImages) {
        carouselImages.addEventListener('mouseenter', () => clearInterval(autoSlideInterval));
        carouselImages.addEventListener('mouseleave', startAutoSlide);
    }

    showImage(currentIndex);
    startAutoSlide();
});

const flashMessages = document.querySelectorAll('.flash-message');
flashMessages.forEach(function(message) {
    setTimeout(() => {
        message.classList.add('fade-out');
        setTimeout(() => {
            message.style.display = 'none';
        }, 600); 

    }, 2000); //2 segundos
});