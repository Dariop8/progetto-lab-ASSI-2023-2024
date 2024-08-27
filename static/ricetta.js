document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    recipeId = urlParams.get('id');
    const ingredientsUrl = urlParams.get('ingredients');
    let ingredientsArray;
    if (ingredientsUrl != null) {
        ingredientsArray = ingredientsUrl.split(',');
    } else {
        ingredientsArray = [];
    }
    

    const settings = {
        async: true,
        crossDomain: true,
        url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/${recipeId}/information?includeNutrition=true`,
        method: 'GET',
        headers: {
            'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
            'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
        }
    };
    
    $.ajax(settings).done(function (response1) {
        //console.log(response1);
        const settings = {
            async: true,
            crossDomain: true,
            url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/${recipeId}/analyzedInstructions?stepBreakdown=true`,
            method: 'GET',
            headers: {
                'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
                'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
            }
        };
        
        $.ajax(settings).done(function (response2) {
            //console.log(response2);
            populateRecipePage(response1, response2); 
        });
    }).fail(function (error) {
        console.error('Error fetching the recipe:', error);
    });


    function isInList(ingredientName) {
        return fetch(`/check_lista?ingredient=${encodeURIComponent(ingredientName)}`)
            .then(response => response.json())
            .then(data => {
                return data.in_in_list;
            })
            .catch(error => {
                console.error('Errore durante la verifica dell\'ingrediente nella lista:', error);
                return false;
            });
    }

    async function populateRecipePage(recipe, instructions) {
        const recipeDetailsDiv = document.querySelector('.recipe-details');
    
        let recipeHTML = `
            <h1>Nome Ricetta: ${recipe.title}</h1>
            <div class="recipe-actions">
                <button id="share-button" class="share-button">Condividi</button>
                <div class="favorite-star">
                    <span class="star inactive">&#9734;</span> 
                </div>
            </div>
            <div class="recipe-info">
                <span>Tempo: ${recipe.readyInMinutes} minuti</span>
                <span>Tipo: ${recipe.dishTypes ? recipe.dishTypes.join(', ') : 'non specificato'}</span>
                <span>Calorie: ${recipe.nutrition.nutrients[0].amount} kcal</span>
            </div>
            <div class="recipe-image">
                <img src="${recipe.image}" alt="Immagine della Ricetta">
            </div>
            <div class="recipe-description">
                <p>${recipe.summary}</p>
            </div>
            <div class="recipe-instructions">
                <h2>Istruzioni:</h2>
                <div class="ingredients">
                    <p><strong>Ingredienti:</strong></p>
                    <ul class="ingredientsUl"> 
        `;
    
        const recipeIngredients = recipe.extendedIngredients;
        let substitutesMap = new Map(); // Mappa per memorizzare i sostituti

        const uniqueIngredients = new Set();
        const ingredientPromises = recipeIngredients.map(async ingredient => {
            if (uniqueIngredients.has(ingredient.name)) {
                return '';
            }
            uniqueIngredients.add(ingredient.name);
            
            const settings = {
                async: true,
                crossDomain: true,
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/ingredients/substitutes?ingredientName=${ingredient.name}`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
                    'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
                }
            }; 
            await $.ajax(settings).done(function (response) {
                //console.log(ingredient);
                //console.log(response);
                if (Array.isArray(response.substitutes)) {
                    substitutesMap.set(ingredient.name, response.substitutes);
                }
            }).fail(function() {
                console.error('Errore nel recupero dei sostituti per l\'ingrediente:', ingredient.name);
            });

            const isIngredientInList = await isInList(ingredient.name);

            let substituteButton = `<button class="substitute-button" data-ingredient="${ingredient.name}">Vedere un sostituto</button>`;
            
            if (ingredientsArray.some(ingredientItem => ingredient.name.includes(ingredientItem))) {
                if (isIngredientInList) {
                    return `
                        <li class="possessed">
                            <span class="ingr_name">${ingredient.name}</span>
                            <span class="checkmark">✔</span>
                            <button class="add-to-shopping-list" data-ingredient="${ingredient.name}" disabled style="background-color: grey">Aggiunto</button>
                            ${substituteButton}
                        </li>
                    `;
                } else {
                    return `
                        <li class="possessed">
                            <span class="ingr_name">${ingredient.name}</span>
                            <span class="checkmark">✔</span>
                            <button class="add-to-shopping-list" data-ingredient="${ingredient.name}">Aggiungi alla lista della spesa</button>
                            ${substituteButton}
                        </li>
                    `;
                }
            } else {
                if (isIngredientInList) {
                    return `
                        <li class="to-buy">
                        <span class="ingr_name">${ingredient.name}</span>
                        <button class="add-to-shopping-list" data-ingredient="${ingredient.name}" disabled style="background-color: grey">Aggiunto</button>
                        ${substituteButton}
                    </li>
                    `;
                } else {
                    return `
                        <li class="to-buy">
                        <span class="ingr_name">${ingredient.name}</span>
                        <button class="add-to-shopping-list" data-ingredient="${ingredient.name}">Aggiungi alla lista della spesa</button>
                        ${substituteButton}
                    </li>
                    `;
                }
            }
        });
    

        const ingredientListItems = await Promise.all(ingredientPromises);
        recipeHTML += ingredientListItems.join('');
    
        
        recipeHTML += `
                    </ul>
                </div>
                <div class="steps">
                    <ul>
        `;
    
        if (instructions.length > 0) {
            const firstStepGroup = instructions[0];
            firstStepGroup.steps.forEach(step => {
                recipeHTML += `
                    <li>
                        <strong>Step ${step.number}:</strong> ${step.step}
                    </li>`;
            });
        } else {
            recipeHTML += `
                <li class="no-steps">
                    <div class="no-steps-content">
                        <p class="no-steps-title">Nessuna istruzione disponibile</p>
                        <p>Siamo spiacenti, ma non ci sono istruzioni disponibili per questa ricetta.</p>
                    </div>
                </li>`;
        }
    
        recipeHTML += `
                    </ul>
                </div>
            </div>
        `;
    
        recipeDetailsDiv.innerHTML = recipeHTML;
         
        //Caricamento form commento e rating
        const formcommenti = document.querySelector('.comment-form')
        formcommenti.innerHTML = `
            <h3>Aggiungi un commento:</h3>
            <form id="commentForm" action="/submit-comment" method="post">
                <input type="hidden" name="recipe_id" value="${recipeId}">
                <textarea id="comment" name="comment" rows="4" required minlength="10" maxlength="400" placeholder="Fai sapere agli altri cosa ne pensi..."></textarea>
                <div class="rating-container">
                    <p>Il tuo voto: </p>
                    <div class="rating">
                        <input type="radio" id="star5" name="rating" value="5" required/><label for="star5" >★</label>
                        <input type="radio" id="star4" name="rating" value="4" required/><label for="star4" >★</label>
                        <input type="radio" id="star3" name="rating" value="3" required/><label for="star3" >★</label>
                        <input type="radio" id="star2" name="rating" value="2" required/><label for="star2" >★</label>
                        <input type="radio" id="star1" name="rating" value="1" required/><label for="star1" >★</label>
                    </div>
                </div>
                
                <button type="submit">Invia</button>
            </form>`;
            
            //Caricamento commenti degli altri utenti
            let ruoloUtente = null;
            let userEmail = null;
            if (recipeId) {
                // Recupero il ruolo dell'utente e l'email, poi carico i commenti
                fetch('/get-user-info')
                    .then(response => response.json())
                    .then(data => {
                        ruoloUtente = data.ruolo_utente;
                        userEmail = data.user_email;  
                        loadComments(recipeId);
                    })
                    .catch(error => console.error('Errore nel recupero del ruolo utente:', error));
            }
        
            function loadComments(recipeId) {
                $.ajax({
                    url: `/get-comments/${recipeId}`,
                    method: 'GET',
                    success: function(comments) {
                        const commentListDiv = document.querySelector('.comment-list');
                        commentListDiv.innerHTML = '<h2>Commenti:</h2>'; 
        
                        if (comments.length > 0) {
                            comments.forEach(comment => {
                                const commentDiv = document.createElement('div');
                                commentDiv.classList.add('boxcommento');
                                let deleteButton = '';
                                let blockButton = '';
                                let notifyButton = '';

                                if (ruoloUtente >= 2 && userEmail !== comment.email) {  
                                    deleteButton = `
                                        <form action="/elimina_commento/${comment.comment_id}" method="post">
                                            <input type="hidden" name="recipe_id" value="${recipeId}">
                                            <button type="submit" class="delete-button">Elimina</button>
                                        </form>
                                    `;
                                    blockButton = `
                                        <form action="/blocca_utente/${comment.comment_id}" method="post">
                                            <input type="hidden" name="recipe_id" value="${recipeId}">
                                            <button type="submit" class="block-button">Elimina e blocca utente</button>
                                        </form>
                                    `;
                                    if (comment.segnalazione === 0) {
                                        notifyButton = `
                                            <form action="/invia_segnalazione/${comment.comment_id}" method="post">
                                                <input type="hidden" name="recipe_id" value="${recipeId}">
                                                <button type="submit" class="notify-button">Invia segnalazione</button>
                                            </form>
                                        `;
                                    }
                                } else if (ruoloUtente >= 2 && userEmail === comment.email) {
                                    deleteButton = `
                                        <form action="/elimina_commento/${comment.comment_id}" method="post" style="display:inline;">
                                            <input type="hidden" name="recipe_id" value="${recipeId}">
                                            <button type="submit" class="delete-button">Elimina</button>
                                        </form>
                                    `;
                                }

                                commentDiv.innerHTML = `
                                    <div class="comment">
                                        <div class="comment-sx">
                                            <p><strong>${comment.username}:</strong><br> ${comment.comment}</p>
                                            <p><i>Valutazione: </i>${stampaStelle(comment.rating)}</p>
                                            <p>${comment.timestamp}</p>
                                        </div>
                                        <div class="comment-dx">
                                            ${deleteButton}
                                            ${blockButton}
                                            ${notifyButton}
                                        </div>
                                    </div>
                                `;
                                commentListDiv.appendChild(commentDiv);
                            });
                        } else {
                            commentListDiv.innerHTML = '<p>Ancora nessun commento. Sii il primo a commentare!!</p>';
                        }
                    },
                    error: function(error) {
                        console.error('Error loading comments:', error);
                    }
                });
            }

        let formattedTitle = recipe.title.toLowerCase().replace(/[^a-z\s]/g, '').replace(/\s+/g, '-');           
        let recipeLink = `https://spoonacular.com/recipes/${formattedTitle}-${recipe.id}`;

        //Condivisione
        document.getElementById('share-button').addEventListener('click', async () => {
            if (navigator.share) {
                try {
                    await navigator.share({
                        title: `Link alla ricetta:${recipe.title}`,
                        text: `Link alla ricetta:${recipe.title} sul sito Spoonacular, link destinato alla condivisione`,
                        url: recipeLink, 
                    });
                    console.log('Link condiviso con successo');
                } catch (error) {
                    console.error('Errore nella condivisione', error);
                }
            } else {
                navigator.clipboard.writeText(recipeLink).then(() => {
                    alert('Link copiato negli appunti!');
                }, (err) => {
                    console.error('Errore durante la copia del link: ', err);
                });
            }
        });
    
        //Shopping list
        document.querySelectorAll('.add-to-shopping-list').forEach(button => {
            button.addEventListener('click', function() {
                const ingredient = this.getAttribute('data-ingredient');
                addToShoppingList(ingredient);
            });
        });
        //controllo se è gia aggiunto a preferito
        if (recipeId) {
            checkIfFavourite(recipeId);
        }


        function checkIfFavourite(recipeId) {
            fetch(`/check_favourite?recipe_id=${recipeId}`)
                .then(response => response.json())
                .then(data => {
                    const starElement = document.querySelector('.favorite-star .star');
                    if (data.is_favourite) {
                        starElement.classList.remove('inactive');
                        starElement.classList.add('active');
                        starElement.innerHTML = '&#9733;';
                    } else {
                        starElement.classList.remove('active');
                        starElement.classList.add('inactive');
                        starElement.innerHTML = '&#9734;';
                    }
                })
                .catch(error => {
                    console.error('Errore durante il controllo dei preferiti:', error);
                });
        }

        //Sostituti degli ingredienti
        document.addEventListener('click', function(event) {
            if (event.target.classList.contains('substitute-button')) {
                const ingredientName = event.target.getAttribute('data-ingredient');
                let substitutes = substitutesMap.get(ingredientName) || [];
                
                // Aggiungi l'ingrediente originale all'inizio dell'array dei sostituti
                substitutes = [ingredientName, ...substitutes];

                if (substitutes.length > 1) {
                    const currentIndex = parseInt(event.target.getAttribute('data-index')) || 0;
                    const nextIndex = (currentIndex + 1) % substitutes.length;
                    const substitute = substitutes[nextIndex];
        
                    // Aggiorna l'HTML per mostrare il sostituto
                    const listItem = event.target.closest('li');
                    listItem.querySelector('.ingr_name').textContent = substitute;
        
                    // Aggiorna l'indice del sostituto
                    event.target.setAttribute('data-index', nextIndex);
                } else {
                    const noSubstituteText = document.createElement('span');
                    noSubstituteText.textContent = 'Non ha sostituti';
                    noSubstituteText.classList.add('no-substitute-text');
                    event.target.replaceWith(noSubstituteText);
                }
            }
        });
    
        //Preferiti
        document.querySelector('.favorite-star .star').addEventListener('click', function() {
            const starElement = this;
    
            if (starElement.classList.contains('inactive')) {
                // Aggiungi ai preferiti
                fetch('/add_to_favourites', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ recipe_id: recipeId }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        starElement.classList.remove('inactive');
                        starElement.classList.add('active');
                        starElement.innerHTML = '&#9733;';
                        console.log('Ricetta aggiunta ai preferiti con successo');
                    } else {
                        console.error('Errore nell\'aggiungere la ricetta ai preferiti:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Errore nella richiesta:', error);
                });
    
            } else if (starElement.classList.contains('active')) {
                // Rimuovi dai preferiti
                fetch('/remove_from_favourites', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ recipe_id: recipeId }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        starElement.classList.remove('active');
                        starElement.classList.add('inactive');
                        starElement.innerHTML = '&#9734;';
                        console.log('Ricetta rimossa dai preferiti con successo');
                    } else {
                        console.error('Errore nel rimuovere la ricetta dai preferiti:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Errore nella richiesta:', error);
                });
            }
        });
    

    }
    
    // Funzione per aggiuta a lista spesa
    function addToShoppingList(ingredient) {
        $.ajax({
            type: 'POST',
            url: '/update_shopping_list',
            data: { ingredient: ingredient },
            success: function(response) {
                const button = document.querySelector(`button[data-ingredient="${ingredient}"]`);
                button.textContent = "Aggiunto";
                button.style.backgroundColor = "grey";
                button.disabled = true;

            },
            error: function() {
                alert('Errore durante l\'aggiunta dell\'ingrediente alla lista della spesa.\n UN MESSAGGIO COSI FA CAGARE, FARE IN MODO DIVERSO');
            }
        });
    }

    //VINI CONSIGLIATI

    const nowine = ["wine", "alcoholic drink", "ingredient", "sparkling wine", "food product category", "dessert wine", "drink", "champagne", "moscato", "menu item type", "port"];
        
    const settings2 = {
        async: true,
        crossDomain: true,
        url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/${recipeId}/information?includeNutrition=true`,
        method: 'GET',
        headers: {
            'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
            'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
        }
    };

    $.ajax(settings2).done(function (response1) {
        const recipeTitle = response1.title;
        const words =  recipeTitle.toLowerCase().split(' ');
        let wineSet = new Set();
        console.log(words);

        let promises = words.map(word => {
            const settings = {
                async: true,
                crossDomain: true,
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/wine/pairing?food=${word}`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
                    'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
                }
            };
            return $.ajax(settings).done(function (response) {
                console.log(response);
                if (Array.isArray(response.pairedWines)) {
                    response.pairedWines.forEach(wine => {
                        wineSet.add(wine.toLowerCase()); // Aggiungi ogni vino all'insieme, in minuscolo per uniformità
                    });
                }
                console.log(wineSet);
            });
        });

        Promise.all(promises).then(() => {
            // Rimuovi i vini che sono presenti nell'array `nowine`
            nowine.forEach(item => {
                wineSet.delete(item.toLowerCase());
            });

            const listwines = document.querySelector('.wines-list')
            listwines.innerHTML = ''; // Pulisci il contenuto precedente
            
            if (wineSet.size > 0) {
                wineSet.forEach(wine => {
                    const wineItem = document.createElement('li');
                    const wineName = document.createElement('span');
                    wineName.textContent = wine;

                    // Crea un pulsante per la descrizione
                    const descriptionButton = document.createElement('button');
                    descriptionButton.textContent = 'Descrizione';
                    descriptionButton.style.marginLeft = '10px';
                    descriptionButton.style.marginLeft = '0px';
                    descriptionButton.classList.add('wine-description');

                    // Crea un elemento per la descrizione (inizialmente nascosto)
                    const description = document.createElement('p');
                    description.style.display = 'none'; // Nascondi la descrizione all'inizio

                    // Aggiungi l'evento click al pulsante
                    descriptionButton.addEventListener('click', () => {
                        
                        if (description.style.display === 'none') {
                            // Fai una richiesta per ottenere la descrizione del vino (se disponibile)
                            const settings = {
                                async: true,
                                crossDomain: true,
                                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/wine/description?wine=${wine}`,
                                method: 'GET',
                                headers: {
                                    'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
                                    'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
                                }
                            };
                            
                            $.ajax(settings).done(function (response) {
                                description.textContent = response.wineDescription || 'Descrizione non disponibile';
                                description.style.display = 'block'; // Mostra la descrizione
                            }).fail(function () {
                                description.textContent = 'Descrizione non disponibile (errore)';
                                description.style.display = 'block';
                            });
                        } else {
                            description.style.display = 'none'; // Nascondi la descrizione se già visibile
                        }
                    });

                    // Appendi il nome del vino, il pulsante e la descrizione all'elemento listwines
                    wineItem.appendChild(wineName);
                    wineItem.appendChild(description);
                    wineItem.appendChild(descriptionButton);
                    listwines.appendChild(wineItem);
                });
            } else {
                listwines.innerHTML = '<p>No wines found for this food pairing.</p>';
            }

        }).catch(error => {
            console.error("Errore durante l'esecuzione delle chiamate AJAX:", error);
        });  
    });

});


function stampaStelle(rating) {
    let stars = '';
    for (let i = 1; i <= 5; i++) {
        if (rating >= i) {
            stars += '★'; 
        } else {
            stars += '☆'; 
        }
    }
    return stars;
}



// timer
document.addEventListener('DOMContentLoaded', function() {
    let timer;
    let minutes = 0;
    let seconds = 0;

    const minutesElement = document.getElementById('minutes');
    const secondsElement = document.getElementById('seconds');
    const playButton = document.getElementById('play-button');
    const stopButton = document.getElementById('stop-button');
    const resetButton = document.getElementById('reset-button');

    function updateTimerDisplay() {
        minutesElement.textContent = minutes < 10 ? '0' + minutes : minutes;
        secondsElement.textContent = seconds < 10 ? '0' + seconds : seconds;
    }

    function startTimer() {
        timer = setInterval(function() {
            seconds++;
            if (seconds === 60) {
                seconds = 0;
                minutes++;
            }
            updateTimerDisplay();
        }, 1000);
        playButton.disabled = true;
        playButton.style.backgroundColor = "grey";
        stopButton.disabled = false;
        stopButton.style.backgroundColor = "#5cb85c";
    }

    function stopTimer() {
        clearInterval(timer);
        playButton.disabled = false;
        playButton.style.backgroundColor = "#5cb85c";
        stopButton.disabled = true;
        stopButton.style.backgroundColor = "grey";
    }

    function resetTimer() {
        stopTimer();
        minutes = 0;
        seconds = 0;
        updateTimerDisplay();
        playButton.disabled = false;
        playButton.style.backgroundColor = "#5cb85c";
        stopButton.disabled = true;
        stopButton.style.backgroundColor = "grey";
    }

    playButton.disabled = false;
    stopButton.disabled = true;
    stopButton.style.backgroundColor = "grey";
    playButton.style.backgroundColor = "#5cb85c";
    

    playButton.addEventListener('click', function() {
        startTimer();
    });

    stopButton.addEventListener('click', function() {
        stopTimer();
    });

    resetButton.addEventListener('click', function() {
        resetTimer();
    });
});

