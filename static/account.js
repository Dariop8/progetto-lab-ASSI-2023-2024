document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('preferences-form');
    const saveButton = document.getElementById('save-button');

    const initialState = {
        diet: Array.from(document.querySelectorAll('input[name="diet"]')).map(cb => cb.checked),
        allergies: Array.from(document.querySelectorAll('input[name="allergies"]')).map(cb => cb.checked),
        twofa: document.querySelector('input[name="attiva-2fa"]').checked,
    };

    function checkChanges() {
        const currentState = {
            diet: Array.from(document.querySelectorAll('input[name="diet"]')).map(cb => cb.checked),
            allergies: Array.from(document.querySelectorAll('input[name="allergies"]')).map(cb => cb.checked),
            twofa: document.querySelector('input[name="attiva-2fa"]').checked,
        };

        const dietChanged = !initialState.diet.every((value, index) => value === currentState.diet[index]);
        const allergiesChanged = !initialState.allergies.every((value, index) => value === currentState.allergies[index]);
        const twofaChanged = initialState.twofa !== currentState.twofa;

        saveButton.disabled = !(dietChanged || allergiesChanged || twofaChanged);
    }

    form.addEventListener('change', checkChanges);

    checkChanges();
});


document.addEventListener('DOMContentLoaded', function() {
    // modale eliminazione account
    var deleteModal = document.getElementById("deleteModal");
    var openDeleteBtn = document.getElementById("openDeleteModal");
    var closeDeleteModal = deleteModal.querySelector(".close");
    var cancelDeleteBtn = deleteModal.querySelector(".cancel-delete");

    openDeleteBtn.onclick = function() {
        deleteModal.style.display = "block";
    }

    closeDeleteModal.onclick = function() {
        deleteModal.style.display = "none";
    }

    cancelDeleteBtn.onclick = function() {
        deleteModal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target == deleteModal) {
            deleteModal.style.display = "none";
        }
    }

    // modale cambio password
    var changePasswordModal = document.getElementById('changePasswordModal');
    var openChangePasswordBtn = document.getElementById('changePasswordBtn');
    var closeChangePasswordModal = changePasswordModal.querySelector('.close');

    openChangePasswordBtn.onclick = function() {
        changePasswordModal.style.display = 'block';
    }

    closeChangePasswordModal.onclick = function() {
        changePasswordModal.style.display = 'none';
    }

    window.onclick = function(event) {
        if (event.target == changePasswordModal) {
            changePasswordModal.style.display = 'none';
        }
    }

    // validazione password uguali
    document.getElementById('new_password').oninput = function() {
        const newPassword = document.getElementById('new_password').value;
        const confirmNewPassword = document.getElementById('confirm_new_password').value;
        document.getElementById('save-password-button').disabled = newPassword !== confirmNewPassword;
    }

    document.getElementById('confirm_new_password').oninput = function() {
        const newPassword = document.getElementById('new_password').value;
        const confirmNewPassword = document.getElementById('confirm_new_password').value;
        document.getElementById('save-password-button').disabled = newPassword !== confirmNewPassword;
    }


    var resetTokenModal = document.getElementById("resetTokenModal");
    var resetTokenSpan = document.getElementsByClassName("close")[0];

    document.getElementById('resetPasswordLink').onclick = function() {
        resetTokenModal.style.display = "block";
        changePasswordModal.style.display = "none";
    
        fetch('/reset_password_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'  
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);  
            if (data.success) {
                alert(data.message); 
            } else {
                alert(data.message); 
            }
        })
        .catch(error => console.error('Errore:', error));
    };

    resetTokenSpan.onclick = function() {
        resetTokenModal.style.display = "none";
    };

    window.onclick = function(event) {
        if (event.target == resetTokenModal) {
            resetTokenModal.style.display = "none";
        }
    };

    const closeElements = document.querySelectorAll('.close');
    closeElements.forEach(element => {
        element.addEventListener('click', function() {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                modal.style.display = "none";
            });
        });
    });
});
