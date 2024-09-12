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

    document.getElementById('download-btn').addEventListener('click', () => {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();
    
        const header = "YOUR SHOPPING LIST:";
        const headerFontSize = 16;
        const normalFontSize = 14;
        
        doc.setFontSize(headerFontSize);
        doc.text(header, 15, 15);
        let y = 15 + headerFontSize + 5;
    
        doc.setFontSize(normalFontSize);
    
        const itemBox = document.querySelector('.item-box');
        const clone = itemBox.cloneNode(true);
        clone.querySelectorAll('.remove-item').forEach(button => button.remove());
        clone.querySelectorAll('.download').forEach(button => button.remove());
    
        const itemList = clone.querySelector('.item-details').innerText;
        const lines = itemList.split('\n');
        const margin = -15;
        const lineHeight = 2;
        const pageHeight = 280;
    
        lines.forEach(line => {
            if (y + lineHeight > pageHeight) {
                doc.addPage();
                doc.setFontSize(normalFontSize);
                y = margin;
            }
            doc.text(line, margin, y);
            y += lineHeight;
        });
    
        doc.save('shopping_list.pdf');
    });
    
});
