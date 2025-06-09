function init() {
    var imgDefer = document.getElementsByClassName('gallery');
    for (var i = 0; i < imgDefer.length; i++) {
        if (imgDefer[i].getAttribute('data-src') && !imgDefer[i].classList.contains('loaded')) {
            imgDefer[i].onload = function () {
                this.classList.add('loaded');
            };
            imgDefer[i].setAttribute('src', imgDefer[i].getAttribute('data-src'));
        }
    }
}
window.onload = init;

document.body.addEventListener('htmx:afterSwap', function(evt) {
    init();
});