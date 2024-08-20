document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('github-button').addEventListener("click", function() {
        window.location.href = "/github_login";
    });

    document.getElementById('facebook-button').addEventListener("click", function() {
        window.location.href = "/facebook_login";
    });

    document.getElementById('google-button').addEventListener("click", function() {
        window.location.href = "/google_login";
    });
});

//animazione spaghetti
const div1 = document.getElementById("spaghetti");

function myFunction() {
        div1.style.animation = "spaghettiAnim 9s 1 ease-in-out forwards";
        i++;
}