// per disattivare il bottone salva modifiche se non è stato cambiato nessun flag

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('preferences-form');
    const saveButton = document.getElementById('save-button');

    const initialState = {
        diet: Array.from(document.querySelectorAll('input[name="diet"]')).map(cb => cb.checked),
        allergies: Array.from(document.querySelectorAll('input[name="allergies"]')).map(cb => cb.checked),
    };

    function checkChanges() {
        const currentState = {
            diet: Array.from(document.querySelectorAll('input[name="diet"]')).map(cb => cb.checked),
            allergies: Array.from(document.querySelectorAll('input[name="allergies"]')).map(cb => cb.checked),
        };

        const dietChanged = !initialState.diet.every((value, index) => value === currentState.diet[index]);
        const allergiesChanged = !initialState.allergies.every((value, index) => value === currentState.allergies[index]);

        saveButton.disabled = !(dietChanged || allergiesChanged);
    }

    form.addEventListener('change', checkChanges);

    checkChanges();
});

// per il modale
document.addEventListener('DOMContentLoaded', function() {
    var modal = document.getElementById("deleteModal");

        var btn = document.getElementById("openDeleteModal");
        
        var span = document.getElementsByClassName("close")[0];
        
        var cancelBtn = document.getElementsByClassName("cancel-delete")[0];
        
        btn.onclick = function() {
          modal.style.display = "block";
        }
        
        span.onclick = function() {
          modal.style.display = "none";
        }
        
        cancelBtn.onclick = function() {
          modal.style.display = "none";
        }
        
        window.onclick = function(event) {
          if (event.target == modal) {
            modal.style.display = "none";
          }
        }
});