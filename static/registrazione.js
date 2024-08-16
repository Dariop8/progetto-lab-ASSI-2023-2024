document.addEventListener("DOMContentLoaded", function() {
    const passwordInput = document.getElementById('password');
    const passwordStrength = document.getElementById('password-strength');

    passwordInput.addEventListener('input', function() {
        const password = passwordInput.value;
        let strengthMessage = '';
        let strengthClass = '';

        if (isStrongPassword(password)) {
            strengthMessage = 'La password è resistente';
            strengthClass = 'strong';
        } else {
            strengthMessage = 'La password è debole';
            strengthClass = 'weak';
        }

        passwordStrength.textContent = strengthMessage;
        passwordStrength.className = 'password-strength ' + strengthClass;
    });

    function isStrongPassword(password) {
        const minLength = 10;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
    }
});
