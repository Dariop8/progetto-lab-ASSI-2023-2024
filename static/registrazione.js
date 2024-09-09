document.addEventListener("DOMContentLoaded", function() {
    const passwordInput = document.getElementById('password');
    const passwordInputConf = document.getElementById('password_conf');
    const passwordStrength = document.getElementById('password-strength');
    const suggestPasswordBtn = document.getElementById('suggest-password-btn');

    passwordInput.addEventListener('input', function() {
        checkPasswordStrength();
    });

    suggestPasswordBtn.addEventListener('click', function() {
        fetch('/generate_password')
            .then(response => response.json())
            .then(data => {
                passwordInput.value = data.password;
                passwordInputConf.value = data.password;
                checkPasswordStrength();
            });
    });

    function checkPasswordStrength() {
        const password = passwordInput.value;
        const strengthInfo = getPasswordStrength(password);
        
        passwordStrength.textContent = strengthInfo.message;
        passwordStrength.className = 'password-strength ' + strengthInfo.className;
    }

    function getPasswordStrength(password) {
        const length = password.length;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
        let strengthClass = '';
        let strengthMessage = '';
    
        if (length <= 4) {
            strengthClass = 'very-weak';
            strengthMessage = 'Very weak (instantly crackable)';
        } else if (length <= 6) {
            strengthClass = 'weak';
            strengthMessage = 'Weak (instantly crackable)';
        } else if (length <= 8) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in a few minutes)';
            } else {
                strengthClass = 'weak';
                strengthMessage = 'Weak (crackable in a few seconds)';
            }
        } else if (length <= 10) {
            if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'weak';
                strengthMessage = 'Weak (crackable in a few minutes)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in hours or days)';
            }
        } else if (length <= 11) {
            if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'weak';
                strengthMessage = 'Weak (crackable in a few minutes)';
            } else if (hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar) {
                strengthClass = 'strong';
                strengthMessage = 'Strong (crackable in weeks or months)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in hours or days)';
            }
        } else if (length <= 13) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'strong';
                strengthMessage = 'Strong (crackable in weeks or months)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in hours or days)';
            }
        } else if (length <= 16) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'very-strong';
                strengthMessage = 'Very strong (crackable in years)';
            } else if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in hours or days)';
            } else {
                strengthClass = 'strong';
                strengthMessage = 'Strong (crackable in weeks or months)';
            }
        } else {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'extremely-strong';
                strengthMessage = 'Extremely strong (crackable in millennia or never)';
            } else if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderate (crackable in hours or days)';
            } else {
                strengthClass = 'very-strong';
                strengthMessage = 'Very strong (crackable in years)';
            }
        }
    
        return { message: strengthMessage, className: strengthClass };
    }    
});
