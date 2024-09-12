document.addEventListener('DOMContentLoaded', function() {
    const requestsContainer = document.getElementById('requests-container');

    fetch('/get-requests')
        .then(response => response.json())
        .then(data => {

            if (data.length === 0) {
                requestsContainer.innerHTML = '<p style="margin-bottom: 8px;">No unlock requests found.</p>';
            } else {

                let content = '';
                data.forEach((request, index) => {
                    content += `
                        <div class="request-item">
                            <p><strong>ID Utente:</strong> ${request.id_utente}</p>
                            <p><strong>Email:</strong> ${request.email}</p>
                            <p><strong>Offensive Comment:</strong> ${request.commento_offensivo}</p>
                            <p><strong>Recipe Affected:</strong> ${request.ricetta_interessata}</p>
                            <p><strong>Blocking Date:</strong> ${request.data_blocco}</p>
                            <p><strong>Request Text:</strong> ${request.testo_richiesta}</p>
                        </div>
                    `;

                    if (index < data.length - 1) {
                        content += '<hr>';
                    }
                    
                });
                requestsContainer.innerHTML = content;
            }
        })
        .catch(error => {
            console.error('Errore caricamento richieste:', error);
            requestsContainer.innerHTML = '<p>Error.</p>';
        });
});
