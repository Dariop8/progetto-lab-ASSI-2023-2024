document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.remove-item').forEach(button => {
        button.addEventListener('click', () => {
            const ingredient = button.getAttribute('data-ingredient');

            fetch('/remove_from_shopping_list', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ingredient: ingredient })
            })
            .then(response => response.json())
            .then(data => {
                if (data.message === 'success') {
                    button.parentElement.remove();
                } else {
                    alert('Errore durante la rimozione dell\'ingrediente alla lista della spesa.\n UN MESSAGGIO COSI FA CAGARE, FARE IN MODO DIVERSO');
                }
            })
            .catch(error => console.error('Errore:', error));
        });
    });
});
