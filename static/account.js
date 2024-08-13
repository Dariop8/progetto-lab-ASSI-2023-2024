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