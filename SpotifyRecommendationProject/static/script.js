document.addEventListener("mousemove", function(event) {
    // Get the overlay element
    var overlay = document.querySelector(".overlay");

    // Calculate the position of the mouse
    var mouseX = event.clientX;
    var mouseY = event.clientY;

    // Calculate the position of the overlay
    var overlayX = (mouseX / window.innerWidth) * 100;
    var overlayY = (mouseY / window.innerHeight) * 100;

    // Update the overlay's background position
    overlay.style.backgroundPosition = overlayX + "% " + overlayY + "%";
});