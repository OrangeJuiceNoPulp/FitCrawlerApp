// Designed by Brendon Wolfe on February 25th

document.addEventListener("DOMContentLoaded", function () {
    const profileButton = document.querySelector('.js-profile');
    const popup = document.getElementById('js-popup');

    // this is used to display the popup when clicking the profile button

    profileButton.addEventListener('click', function (event) {
        popup.style.display = "flex";
    });

    // these are to close the popup when pressing esc or clicking outside of the popup

    document.addEventListener('click', function (event) {
        if (!popup.contains(event.target) && !profileButton.contains(event.target)) {
            popup.style.display = "none";
        }
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            popup.style.display = "none";
        }
    });
});
