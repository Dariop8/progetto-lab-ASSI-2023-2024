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

    // function checkPasswordStrength() {
    //     const password = passwordInput.value;
    //     let strengthMessage = '';
    //     let strengthClass = '';

    //     if (isStrongPassword(password)) {
    //         strengthMessage = 'La password è resistente';
    //         strengthClass = 'strong';
    //     } else {
    //         strengthMessage = 'La password è debole';
    //         strengthClass = 'weak';
    //     }

    //     passwordStrength.textContent = strengthMessage;
    //     passwordStrength.className = 'password-strength ' + strengthClass;
    // }

    // function isStrongPassword(password) {
    //     const minLength = 10;
    //     const hasUpperCase = /[A-Z]/.test(password);
    //     const hasLowerCase = /[a-z]/.test(password);
    //     const hasNumber = /\d/.test(password);
    //     const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

    //     return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
    // }

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
            strengthMessage = 'Molto debole (istantaneamente decifrabile)';
        } else if (length <= 6) {
            strengthClass = 'weak';
            strengthMessage = 'Debole (istantaneamente decifrabile)';
        } else if (length <= 8) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in pochi minuti)';
            } else {
                strengthClass = 'weak';
                strengthMessage = 'Debole (decifrabile in pochi secondi)';
            }
        } else if (length <= 10) {
            if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'weak';
                strengthMessage = 'Debole (decifrabile in pochi minuti)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in ore o giorni)';
            }
        } else if (length <= 11) {
            if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'weak';
                strengthMessage = 'Debole (decifrabile in pochi minuti)';
            } else if (hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar) {
                strengthClass = 'strong';
                strengthMessage = 'Forte (decifrabile in settimane o mesi)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in ore o giorni)';
            }
        } else if (length <= 13) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'strong';
                strengthMessage = 'Forte (decifrabile in settimane o mesi)';
            } else {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in ore o giorni)';
            }
        } else if (length <= 16) {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'very-strong';
                strengthMessage = 'Molto forte (decifrabile in anni)';
            } else if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in ore o giorni)';
            } else {
                strengthClass = 'strong';
                strengthMessage = 'Forte (decifrabile in settimane o mesi)';
            }
        } else {
            if (hasUpperCase && hasLowerCase) {
                strengthClass = 'extremely-strong';
                strengthMessage = 'Estremamente forte (decifrabile in millenni o mai)';
            } else if (hasNumber && !hasUpperCase && !hasLowerCase && !hasSpecialChar) {
                strengthClass = 'moderate';
                strengthMessage = 'Moderata (decifrabile in ore o giorni)';
            } else {
                strengthClass = 'very-strong';
                strengthMessage = 'Molto forte (decifrabile in anni)';
            }
        }
    
        return { message: strengthMessage, className: strengthClass };
    }    
});
