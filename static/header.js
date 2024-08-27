document.addEventListener("DOMContentLoaded", function() {
    fetch('/get-user-info')
        .then(response => response.json())
        .then(data => {
            const ruoloUtente = data.ruolo_utente;
            if (ruoloUtente >= 2) {
                const sbanLinkContainer = document.getElementById('sban-link-container');
                const sbanLink = document.createElement('a');
                sbanLink.href = '/sban';
                sbanLink.textContent = 'Area moderatore';
                sbanLinkContainer.appendChild(sbanLink);
            }
        })
        .catch(error => {
            console.error('Errore durante il recupero delle informazioni utente:', error);
        });
});