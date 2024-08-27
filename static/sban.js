document.addEventListener('DOMContentLoaded', function() {
    const requestsContainer = document.getElementById('requests-container');

    fetch('/get-requests')
        .then(response => response.json())
        .then(data => {
            if (data.length === 0) {
                requestsContainer.innerHTML = '<p>Nessuna richiesta di sblocco trovata.</p>';
            } else {
                let content = '';
                data.forEach(request => {
                    content += `
                        <div class="request-item">
                            <p><strong>ID Utente:</strong> ${request.id_utente}</p>
                            <p><strong>Email:</strong> ${request.email}</p>
                            <p><strong>Commento Offensivo:</strong> ${request.commento_offensivo}</p>
                            <p><strong>Ricetta Interessata:</strong> ${request.ricetta_interessata}</p>
                            <p><strong>Data Blocco:</strong> ${request.data_blocco}</p>
                            <p><strong>Testo Richiesta:</strong> ${request.testo_richiesta}</p>
                        </div>
                        <hr>
                    `;
                });
                requestsContainer.innerHTML = content;
            }
        })
        .catch(error => {
            console.error('Errore nel caricamento delle richieste:', error);
            requestsContainer.innerHTML = '<p>Errore nel caricamento delle richieste.</p>';
        });
});
