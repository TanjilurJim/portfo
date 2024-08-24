document.addEventListener("DOMContentLoaded", function () {
    type();  // Make sure this function is defined elsewhere
    movingBackgroundImage();  // Make sure this function is defined elsewhere
    lasttime();  // This function is called when the DOM is fully loaded
});

function lasttime() {
    document.getElementById('lasttime').innerHTML = new Date(document.lastModified).toLocaleString();
}
