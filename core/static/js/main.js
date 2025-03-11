(function ($) {
 "use strict";
	// jQuery MeanMenu
	jQuery('nav#dropdown').meanmenu();
	//menu a active jquery
	var pgurl = window.location.href.substr(window.location.href
		.lastIndexOf("/")+1);
		$("ul li a").each(function(){
		if($(this).attr("href") == pgurl || $(this).attr("href") == '' )
		$(this).addClass("active");
	$('header ul li ul li a.active').parent('li').addClass('parent-li');
	$('header ul li ul li.parent-li').parent('ul').addClass('parent-ul');
	$('header ul li ul.parent-ul').parent('li').addClass('parent-active');
	})
	//search bar exprnd
	$('.header-top-two .right button').on('click',function(){
		$('.header-top-two .right').toggleClass('widthfull');
	});
	//search bar border color
	$('.middel-top .center').on('click',function(){
		$('.middel-top .center').toggleClass('bordercolor');
	});
	//color select jquery
	$('.color-select > span').on('click',function(){
		$('.color-select > span').toggleClass('outline');
        $(this).addClass("outline").siblings().removeClass("outline");
	});
/*----------------------------
 nivoSlider active
------------------------------ */
	$('#mainSlider').nivoSlider({
		
		prevText: '<i class="mdi mdi-chevron-left"></i>',
		nextText: '<i class="mdi mdi-chevron-right"></i>'
	});
/*----------------------------
 plus-minus-button
------------------------------ */
	$(".qtybutton").on("click", function() {
		var $button = $(this);
		var oldValue = $button.parent().find("input").val();
		if ($button.text() == "+") {
			var newVal = parseFloat(oldValue) + 1;
		} else {
			// Don't allow decrementing below zero
			if (oldValue > 0) {
				var newVal = parseFloat(oldValue) - 1;
			} else {
				newVal = 0;
			}
		}
		$button.parent().find("input").val(newVal);
	});
/*----------------------------
 price-slider active
------------------------------ */  
	$( "#slider-range" ).slider({
		range: true,
		min: 40,
		max: 600,
		values: [ 150, 399 ],
		slide: function( event, ui ) {
		$( "#amount" ).val( "$" + ui.values[ 0 ] + " - $" + ui.values[ 1 ] );
		}
	});
	$( "#amount" ).val( "$" + $( "#slider-range" ).slider( "values", 0 ) +
	" - $" + $( "#slider-range" ).slider( "values", 1 ) );
/*--------------------------
 scrollUp
---------------------------- */	
	$.scrollUp({
        scrollText: '<i class="mdi mdi-chevron-up"></i>',
        easingType: 'linear',
        scrollSpeed: 900,
        animation: 'fade'
    });
/*--------------------------
 // simpleLens
 ---------------------------- */
	$('.simpleLens-image').simpleLens({
		
	});
	
})(jQuery); 

// Enhanced Background Slideshow
document.addEventListener('DOMContentLoaded', function() {
    const slides = document.querySelectorAll('.hero-slideshow .slide');
    let currentSlide = 0;

    // Array of background images
    const backgroundImages = [
        'https://images.unsplash.com/photo-1581092580497-e0d23cbdf1dc',
        'https://images.unsplash.com/photo-1604328727766-a151d1045ab4',
        'https://images.unsplash.com/photo-1587582583465-beb350b46fd8',
        'https://images.unsplash.com/photo-1587582345426-bf07d6f884e4',
        'https://images.unsplash.com/photo-1587582345426-bf07d6f884e5'
    ];

    // Initialize slides with background images
    slides.forEach((slide, index) => {
        slide.style.backgroundImage = `url(${backgroundImages[index]})`;
    });

    function showSlide(index) {
        slides.forEach(slide => {
            slide.classList.remove('active');
            slide.style.zIndex = '0';
        });
        slides[index].classList.add('active');
        slides[index].style.zIndex = '1';
    }

    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }

    // Show first slide
    showSlide(0);

    // Auto advance slides with smoother transition
    setInterval(nextSlide, 6000); // Increased duration for better viewing

    // Add fade transition between slides
    slides.forEach(slide => {
        slide.addEventListener('transitionend', function() {
            if (!this.classList.contains('active')) {
                this.style.zIndex = '0';
            }
        });
    });
});

// Enhance scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
            entry.target.style.opacity = '1';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.category-card, .product-card, .feature-card').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
}); 