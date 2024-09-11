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
        },
        error: function(xhr, status, error) {
            el.style.border = "2px solid green";
        }
    });
}

fetch('/api/keys')
    .then(response => response.json())
    .then(data => {
        
        const apiKey = data.rapid_api_key;
        const apiHost = data.rapid_api_host;
        
        function populateRecipesList(recipeIds) {
        const recipeListDiv = document.querySelector('.recipes');
        
        recipeListDiv.innerHTML = '<h1>YOUR SAVED RECIPES:</h1>';

        if (recipeIds.length === 0) {
            recipeListDiv.innerHTML = '<h2>You don\'t have any recipes saved!</h2>';
            return;
        }

        recipeIds.forEach(recipeId => {
            const settings = {
                async: true,
                crossDomain: true,
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/${recipeId}/information?includeNutrition=true`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': apiKey,
                    'x-rapidapi-host': apiHost
                }
            };

            $.ajax(settings).done(function(response) {
                const recipe = response;
                let typesString = recipe.dishTypes.join(', ');
                if (recipe.dishTypes.length > 3) {
                    typesString = recipe.dishTypes.slice(0, 3).join(', ') + ', ...';
                } else if (recipe.dishTypes.length === 0) {
                    typesString = 'Not specified';
                }

                const recipeElement = document.createElement('div');
                recipeElement.classList.add('recipe');

                let recipeString = `
                    <div class="recipe-info">
                        <div id="recipe-${recipe.id}">
                            <span class="recipe-name">${recipe.title}</span>
                            <div class="recipe-details">
                                <span class="time">🕒 ${recipe.readyInMinutes}min</span>
                                <span class="type">Type: ${typesString}</span>
                                <span class="calories">Calories: ${recipe.nutrition.nutrients[0].amount}kcal</span>
                            </div>
                        </div>
                    </div> 
                    <div class="recipe-note">
                        <textarea id="note-${recipe.id}" placeholder=" Add a note..."></textarea>
                        <button onclick="saveNote('${recipe.id}')">Save Note</button>
                    </div>
                `;

                if (recipe.image !== "") {
                    recipeString += `<img src="${recipe.image}" alt="Img Recipe" class="recipe-image"></img>`;
                }
                recipeElement.innerHTML = recipeString;

                recipeListDiv.appendChild(recipeElement);

                recipeElement.addEventListener('click', function() {
                    window.location.href = `/ricetta?id=${recipe.id}`;
                });
                
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
});