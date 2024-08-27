document.addEventListener('DOMContentLoaded', function() {

    fetch(`/get_block_info`)
        .then(response => response.json())
        .then(data => {

            document.getElementById('info').innerHTML = `
                <p><strong>Email:</strong> ${data.email}</p>
                <p><strong>Username:</strong> ${data.username}</p>
                <p><strong>Commento Offensivo:</strong> ${data.commento_offensivo}</p>
                <p><strong>Ricetta Interessata:</strong> ${data.ricetta_interessata}</p>
                <p><strong>Data di Blocco:</strong> ${data.data_blocco}</p>
            `;

            if (!data.richiesta_effettuata) {
                document.getElementById('richiesta-container').innerHTML = `
                    <form id="richiestaForm" action="/blocked?email=${data.email}" method="post">
                        <label for="testo_richiesta">Motivo della Richiesta di Sblocco:</label>
                        <textarea id="testo_richiesta" name="testo_richiesta" placeholder="Scrivi qui la tua richiesta" minlength="10" maxlength="400" required></textarea>
                        <button type="submit">Invia Richiesta</button>
                    </form>
                `;
            } else {
                document.getElementById('richiesta-container').innerHTML = '<p>Hai già inviato una richiesta di sblocco. Ti preghiamo di attendere che venga esaminata.</p>';
            }
        })
        .catch(error => {
            document.getElementById('info').innerHTML = `<p>Errore: ${error.message}</p>`;
        });
});
