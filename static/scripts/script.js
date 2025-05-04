const searchToggle = document.getElementById('search-toggle');
const searchWrapper = document.getElementById('search-wrapper');
const searchClose = document.getElementById('search-close');
const navActions = document.getElementById('nav-actions');

searchToggle.addEventListener('click', () => {
searchWrapper.classList.remove('hidden');
navActions.classList.add('hidden');
searchToggle.classList.add('hidden');
});

searchClose.addEventListener('click', () => {
searchWrapper.classList.add('hidden');
navActions.classList.remove('hidden');
searchToggle.classList.remove('hidden');
});