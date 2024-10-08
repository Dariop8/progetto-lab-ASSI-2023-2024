fetch('/api/keys')
    .then(response => response.json())
    .then(data => {
        
        const apiKey = data.rapid_api_key;
        const apiHost = data.rapid_api_host;

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
                'x-rapidapi-key': apiKey,
                'x-rapidapi-host': apiHost
            }
        };

        // richiesta AJAX
        $.ajax(settings).done(function (response) {
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

            const ingredients = labelsForSearch.map(encodeURIComponent).join('%2C');

            const dietValue = document.getElementById('user-diet').textContent;
            const intolerancesValue = document.getElementById('user-intolerances').textContent;
            
            let dietArray = JSON.parse(dietValue);
            let intolerancesArray = JSON.parse(intolerancesValue);
            
            function cleanArray(arr) {
                if (arr.length === 0 || (arr.length === 1 && arr[0] === "")) {
                    return [];
                }
                return arr;
            }

            dietArray = cleanArray(dietArray);
            intolerancesArray = cleanArray(intolerancesArray);

            const dietString = dietArray.length ? `diet=${dietArray[0]}&` : '';
            const intolerancesString = intolerancesArray.length ? `intolerances=${intolerancesArray.join('%2C%20')}&` : '';

            const settings = {
                async: true,
                crossDomain: true,
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch?${dietString}${intolerancesString}includeIngredients=${ingredients}&instructionsRequired=true&fillIngredients=false&addRecipeInformation=false&addRecipeInstructions=false&addRecipeNutrition=false&ignorePantry=false&sort=max-used-ingredients&offset=0&number=20`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': apiKey,
                    'x-rapidapi-host': apiHost
                }
            };
            

            $.ajax(settings).done(function (response) {
                populateRecipesList(response.results, labelsForSearch); 
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

        if (ingredients.length === 0) {
            document.getElementById('errore-ingredients').style.display = "block";
        } else { 
            document.getElementById('errore-ingredients').style.display = "none";

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
    }

    function populateRecipesList(recipes, ingredients) {
        const recipeListDiv = document.querySelector('.recipes');

        recipeListDiv.innerHTML=`
                    <div class="error-message" id="errore-recipe">
                        <p>Unfortunately, your search did not return any results.</p>
                    </div>
                    `;

        if (recipes.length === 0) {
            document.getElementById('errore-recipe').style.display = "block";
        } else { 
            document.getElementById('errore-recipe').style.display = "none";

            recipes.forEach(recipe => {

                const settings = {
                    async: true,
                    crossDomain: true,
                    url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/${recipe.id}/information?includeNutrition=true`,
                    method: 'GET',
                    headers: {
                        'x-rapidapi-key': apiKey,
                        'x-rapidapi-host': apiHost
                    }
                };

                $.ajax(settings).done(function (response) {
                    const recipe=response;
                    
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
                                    <span class="type">Type: ${typesString}</span>
                                    <span class="calories">Calories: ${recipe.nutrition.nutrients[0].amount}kcal</span>
                                </div>
                            </div>
                        </div> 
                    `;

                    if (recipe.image !== "") {
                        recipeString += `<img src="${recipe.image}" alt="Recipe Image" class="recipe-image"></img> `;
                    }
                    recipeElement.innerHTML = recipeString;
                    
                    recipeListDiv.appendChild(recipeElement);

                    recipeElement.addEventListener('click', function() {
                        const ingredientsQueryString = ingredients.join(',');
                        window.location.href = `/ricetta?id=${recipe.id}&ingredients=${encodeURIComponent(ingredientsQueryString)}`;
                    });
                }).fail(function (error) {
                    console.error('Error fetching the recipe:', error);
                });
            });

        }
    }

});