document.addEventListener('DOMContentLoaded', function() {
    const settings = {
        async: true,
        crossDomain: true,
        url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/random?number=2`,
        method: 'GET',
        headers: {
            'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
            'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
        }
    };

    $.ajax(settings).done(function (response) {
        console.log(response); 
        populateRecipesList(response.recipes); 
    }).fail(function (error) {
        console.error('Error fetching ingredients:', error);
    });
});

function populateRecipesList(recipes) {
    const recipeListDiv = document.querySelector('.recipes');

    recipeListDiv.innerHTML='<h1>RICETTE RANDOM</h1>';

    recipes.forEach(recipe => {
        const recipeElement = document.createElement('div');
        recipeElement.classList.add('recipe');

        recipeElement.innerHTML = `
            <div id="recipe-${recipe.id}">
                <span class="recipe-name">${recipe.title}</span>
                <div class="recipe-details">
                    <span class="time">🕒 Tempo</span>
                    <span class="type">Tipo</span>
                    <span class="calories">Calorie</span>
                </div>
            </div>
        `;

        recipeListDiv.appendChild(recipeElement);
    });
}