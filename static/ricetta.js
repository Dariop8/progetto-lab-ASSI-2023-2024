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

    function populateRecipePage(recipe, instructions) {
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
        recipeIngredients.forEach(ingredient => {
            if (ingredientsArray.some(ingredientItem => ingredient.name.includes(ingredientItem))) {
                recipeHTML += `
                    <li class="possessed">
                        ${ingredient.name}
                        <span class="checkmark">✔</span>
                        <button class="add-to-shopping-list" data-ingredient="${ingredient.name}">Aggiungi alla lista della spesa</button></li>
    
                    
                `;
            } else {
                recipeHTML += `
                    <li class="to-buy">${ingredient.name}
                    <button class="add-to-shopping-list" data-ingredient="${ingredient.name}">Aggiungi alla lista della spesa</button></li>
                `;
            }      
        });
        
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

        let formattedTitle = recipe.title.toLowerCase().replace(/[^a-z\s]/g, '').replace(/\s+/g, '-');           
        let recipeLink = `https://spoonacular.com/recipes/${formattedTitle}-${recipe.id}`;

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
    
    function addToShoppingList(ingredient) {
        $.ajax({
            type: 'POST',
            url: '/update_shopping_list',
            data: { ingredient: ingredient },
            success: function(response) {
                const button = document.querySelector(`button[data-ingredient="${ingredient}"]`);
                button.textContent = "Aggiunto";
                
                button.disabled = true;

            },
            error: function() {
                alert('Errore durante l\'aggiunta dell\'ingrediente alla lista della spesa.\n UN MESSAGGIO COSI FA CAGARE, FARE IN MODO DIVERSO');
            }
        });
    }

    const formcommenti = document.querySelector('.comment-form')
    formcommenti.innerHTML = `
        <h3>Aggiungi un commento:</h3>
        <form id="commentForm" action="/submit-comment" method="post">
            <input type="hidden" name="recipe_id" value="${recipeId}">
            <label for="comment">Commento:</label>
            <textarea id="comment" name="comment" rows="4" required></textarea>
            <button type="submit">Invia</button>
        </form>`;      
});


document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const recipeId = urlParams.get('id');
    
    if (recipeId) {
        loadComments(recipeId);
    }

    function loadComments(recipeId) {
        $.ajax({
            url: `/get-comments/${recipeId}`,
            method: 'GET',
            success: function(comments) {
                const commentListDiv = document.querySelector('.comment-list');
                commentListDiv.innerHTML = ''; // Clear existing comments

                if (comments.length > 0) {
                    comments.forEach(comment => {
                        const commentDiv = document.createElement('div');
                        commentDiv.classList.add('comment');
                        commentDiv.innerHTML = `<p><strong>${comment.username}:</strong> ${comment.comment}</p><p>${comment.timestamp}</p>`;
                        commentListDiv.appendChild(commentDiv);
                    });
                } else {
                    commentListDiv.innerHTML = '<p>No comments yet. Be the first to comment!</p>';
                }
            },
            error: function(error) {
                console.error('Error loading comments:', error);
            }
        });
    }
});

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
    }

    function stopTimer() {
        clearInterval(timer);
    }

    function resetTimer() {
        stopTimer();
        minutes = 0;
        seconds = 0;
        updateTimerDisplay();
    }

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




// document.getElementById('commentForm').addEventListener('submit', function(e) {
//     e.preventDefault();

//     const formData = $(this).serialize();

//     $.ajax({
//         url: '/submit-comment',
//         method: 'POST',
//         data: formData,
//         xhrFields: {
//             withCredentials: true // Includo i cookie di sessione
//         },
//         success: function(response) {
//             alert(response.message);
//             loadComments(recipeId); // Ricarico i commenti dopo l'invio
//             document.getElementById('comment').value = ''; // Pulisco il form
//         },
//         error: function(error) {
//             console.error('Error submitting comment:', error);
//             alert('Errore durante l\'invio del commento.'); // messaggio di errore
//         }
//     });
// });

