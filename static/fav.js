function populateRecipesList(recipeIds) {
    const recipeListDiv = document.querySelector('.recipes');
    
    recipeListDiv.innerHTML = '<h1>LE TUE RICETTE SALVATE:</h1>';

    if (recipeIds.length === 0) {
        recipeListDiv.innerHTML = '<h2>Non hai nessuna ricetta salvata!</h2>';
        return;
    }

    recipeIds.forEach(recipeId => {
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

        $.ajax(settings).done(function(response) {
            const recipe = response;
            let typesString = recipe.dishTypes.join(', ');
            if (recipe.dishTypes.length > 3) {
                typesString = recipe.dishTypes.slice(0, 3).join(', ') + ', ...';
            } else if (recipe.dishTypes.length === 0) {
                typesString = 'non specificato';
            }

            const recipeElement = document.createElement('div');
            recipeElement.classList.add('recipe');

            let recipeString = `
                <div class="recipe-info">
                    <div id="recipe-${recipe.id}">
                        <span class="recipe-name">${recipe.title}</span>
                        <div class="recipe-details">
                            <span class="time">🕒 ${recipe.readyInMinutes}min</span>
                            <span class="type">Tipo: ${typesString}</span>
                            <span class="calories">Calorie: ${recipe.nutrition.nutrients[0].amount}kcal</span>
                        </div>
                    </div>
                </div> 
                <div class="recipe-note">
                    <textarea id="note-${recipe.id}" placeholder="Aggiungi una nota..."></textarea>
                    <button onclick="saveNote('${recipe.id}')">Salva Nota</button>
                </div>
            `;

            if (recipe.image !== "") {
                recipeString += `<img src="${recipe.image}" alt="Immagine Ricetta" class="recipe-image"></img>`;
            }
            recipeElement.innerHTML = recipeString;

            recipeListDiv.appendChild(recipeElement);

            recipeElement.addEventListener('click', function() {
                window.location.href = `/ricetta?id=${recipe.id}`;
            });
            //blocca l'event listener sulle note
            const recipeNote = recipeElement.querySelector('.recipe-note');
            if (recipeNote) {
                recipeNote.addEventListener('click', function(event) {
                    event.stopPropagation();
                });
            }

            loadNoteForRecipe(recipe.id);
        }).fail(function(error) {
            console.error('Error fetching the recipe:', error);
        });
    });
}

function saveNote(recipeId) {
    const el = document.getElementById(`note-${recipeId}`)
    const note = document.getElementById(`note-${recipeId}`).value;

    $.ajax({
        type: 'POST',
        url: '/update_note',
        data: {
            recipe_id: recipeId,
            note: note
        },
        success: function(response) {
            el.style.border = "2px solid green";
            // alert('Nota salvata con successo!');
        },
        error: function(xhr, status, error) {
            // alert('Errore durante il salvataggio della nota.');
            el.style.border = "2px solid green";
        }
    });
}

function loadNoteForRecipe(recipeId) {
    $.ajax({
        type: 'POST',
        url: '/get_note',
        contentType: 'application/json',
        data: JSON.stringify({ recipe_id: recipeId }),
        success: function(response) {
            const textarea = document.getElementById(`note-${response.recipe_id}`);
            if (textarea) {
                textarea.value = response.note;
            }
        },
        error: function(xhr, status, error) {
            // console.error('Error loading note:', error);
            const textarea = document.getElementById(`note-${response.recipe_id}`);
            if (textarea) {
                textarea.value = "Errore nel caricamento della nota";
            }
        }
    });
}





$(document).ready(function() {
    const recipeIdsInput = document.getElementById('recipe-ids');
    const recipeIds = JSON.parse(recipeIdsInput.value || '[]');
    populateRecipesList(recipeIds);
});
