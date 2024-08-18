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
            `;

            if (recipe.image !== "") {
                recipeString += `<img src="${recipe.image}" alt="Immagine Ricetta" class="recipe-image"></img>`;
            }
            recipeElement.innerHTML = recipeString;

            recipeListDiv.appendChild(recipeElement);

            recipeElement.addEventListener('click', function() {
                window.location.href = `/ricetta?id=${recipe.id}`;
            });
        }).fail(function(error) {
            console.error('Error fetching the recipe:', error);
        });
    });
}

$(document).ready(function() {
    const recipeIdsInput = document.getElementById('recipe-ids');
    const recipeIds = JSON.parse(recipeIdsInput.value || '[]');
    populateRecipesList(recipeIds);
});
