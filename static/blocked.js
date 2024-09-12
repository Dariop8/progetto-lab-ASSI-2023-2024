document.addEventListener('DOMContentLoaded', function() {

    fetch(`/get_block_info`)
        .then(response => response.json())
        .then(data => {

            document.getElementById('info').innerHTML = `
                <p><strong>Email:</strong> ${data.email}</p>
                <p><strong>Username:</strong> ${data.username}</p>
                <p><strong>Offensive Comment:</strong> ${data.commento_offensivo}</p>
                <p><strong>Recipe Affected:</strong> ${data.ricetta_interessata}</p>
                <p><strong>Block Date:</strong> ${data.data_blocco}</p>
            `;

            if (!data.richiesta_effettuata) {
                document.getElementById('richiesta-container').innerHTML = `
                    <form id="richiestaForm" action="/blocked?email=${data.email}" method="post">
                        <label for="testo_richiesta" class="label_richiesta">Unlock Request:</label>
                        <textarea id="testo_richiesta" name="testo_richiesta" placeholder="Write your request here..." minlength="10" maxlength="400" required></textarea>
                        <button type="submit">Submit Request</button>
                    </form>
                `;
            } else {
                document.getElementById('richiesta-container').innerHTML = '<p style="font-size: 18px;">You have already submitted an unlock request. Please wait for it to be reviewed.</p>';
            }
        })
        .catch(error => {
            console.error('Errore dati blocco', error);
        });
});
