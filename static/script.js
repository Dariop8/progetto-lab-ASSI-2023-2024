document.getElementById('search-button').addEventListener('click', function() {
    const input = document.getElementById('ingredient-input')
    const query = input.value;
    input.value = '';

    if (query.trim() === '') {
        updateIngredientList();
        return;
    }

    // configurazione della richiesta API
    const settings = {
        async: true,
        crossDomain: true,
        url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/food/ingredients/search?query=${query}&offset=0&number=100`,
        method: 'GET',
        headers: {
            'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
            'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
        }
    };

    // richiesta AJAX
    $.ajax(settings).done(function (response) {
        //console.log(response); 
        populateIngredientList(response.results); 
    }).fail(function (error) {
        console.error('Error fetching ingredients:', error);
    });
});

document.getElementById('search-recipe-button').addEventListener('click', function() {
    const ingredientListDiv = document.querySelector('.ingredient-list');
    const labelsForSearch = [];

    for (const label of ingredientListDiv.children) {
        if (label.tagName === 'LABEL') {
            const checkbox = label.querySelector('input[type="checkbox"]');
            if (checkbox.checked) {
                labelsForSearch.push(checkbox.value); 
            }
        }
    }

    if (labelsForSearch.length > 0) {
        document.querySelector('.recipes').style.display = 'block';
        document.querySelector('.no-recipes').style.display = 'none';

        // converto l'array nella stringa adeguata
        const ingredients = labelsForSearch.map(encodeURIComponent).join('%2C');

        const settings = {
            async: true,
            crossDomain: true,
            url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/findByIngredients?ingredients=${ingredients}&number=20&ignorePantry=false&ranking=1`,
            method: 'GET',
            headers: {
                'x-rapidapi-key': 'ec8475a6eamshde7b5569a35c096p1b0addjsnc9c0a6b52687',
                'x-rapidapi-host': 'spoonacular-recipe-food-nutrition-v1.p.rapidapi.com'
            }
        };

        $.ajax(settings).done(function (response) {
            //console.log(response);
            populateRecipesList(response, labelsForSearch); 
        }).fail(function (error) {
            console.error('Error fetching recipes:', error);
        });

    }
});

function updateIngredientList() {
    const ingredientListDiv = document.querySelector('.ingredient-list');
    const labelsToRemove = [];

    for (const label of ingredientListDiv.children) {
        if (label.tagName === 'LABEL') {
            const checkbox = label.querySelector('input[type="checkbox"]');
            if (!checkbox.checked) {
                labelsToRemove.push(label);
            }
        }
    }

    for (const label of labelsToRemove) {
        ingredientListDiv.removeChild(label);
    }
}

function populateIngredientList(ingredients) {
    const ingredientListDiv = document.querySelector('.ingredient-list');

    updateIngredientList();

    const existingCheckboxValues = new Set();
    const existingCheckboxes = ingredientListDiv.querySelectorAll('input[type="checkbox"]');
    existingCheckboxes.forEach(checkbox => existingCheckboxValues.add(checkbox.value));

    ingredients.forEach(ingredient => {
        if (!existingCheckboxValues.has(ingredient.name)) {
            const articoloIngredient = document.createElement('label');
            articoloIngredient.classList.add('articoloIngredient');

            articoloIngredient.innerHTML = `
                <input type="checkbox" value="${ingredient.name}">
                ${ingredient.name}
            `;

            ingredientListDiv.appendChild(articoloIngredient);

            existingCheckboxValues.add(ingredient.name);
        }
    });
}

function populateRecipesList(recipes, ingredients) {
    const recipeListDiv = document.querySelector('.recipes');

    recipeListDiv.innerHTML='';

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

        recipeElement.addEventListener('click', function() {
            const ingredientsQueryString = ingredients.join(',');
            window.location.href = `/ricetta?id=${recipe.id}&ingredients=${encodeURIComponent(ingredientsQueryString)}`;
        });
    });
}

