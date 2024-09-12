document.addEventListener("DOMContentLoaded", function() {
    fetch('/get-user-info')
        .then(response => response.json())
        .then(data => {
            const ruoloUtente = data.ruolo_utente;
            if (ruoloUtente >= 2) {
                const sbanLinkContainer = document.getElementById('sban-link-container');
                const sbanLink = document.createElement('a');
                sbanLink.href = '/sban';
                sbanLink.textContent = 'Moderator Area';
                sbanLinkContainer.appendChild(sbanLink);
            }
            if(ruoloUtente == 3){
                const admin_tools_cont = document.getElementById('admin-tools');
                const admin_tools = document.createElement('a');
                admin_tools.href = '/admin';
                admin_tools.textContent = 'Admin Tools';
                admin_tools_cont.appendChild(admin_tools);
            }
        })
        .catch(error => {
            console.error('Errore recupero informazioni utente:', error);
        });
});