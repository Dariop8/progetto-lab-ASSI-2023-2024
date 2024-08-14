document.addEventListener("DOMContentLoaded", function() {
    document.getElementById('github-button').addEventListener("click", function() {
        window.location.href = "/github_login/github";
    });

    document.getElementById('facebook-button').addEventListener("click", function() {
        window.location.href = "/login/facebook";
    });

    document.getElementById('google-button').addEventListener("click", function() {
        window.location.href = "/google_login";
    });
});