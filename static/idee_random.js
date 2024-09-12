document.addEventListener('DOMContentLoaded', function() {

    fetch('/api/keys')
        .then(response => response.json())
        .then(data => {
            
        const apiKey = data.rapid_api_key;
        const apiHost = data.rapid_api_host;

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
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch?${dietString}${intolerancesString}instructionsRequired=true&fillIngredients=false&addRecipeInformation=false&addRecipeInstructions=false&addRecipeNutrition=false&ignorePantry=false&sort=max-used-ingredients&offset=0&number=50`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': apiKey,
                    'x-rapidapi-host': apiHost
                }
            };

            $.ajax(settings).done(function (response) {
                populateRecipesList(response.results); 
            }).fail(function (error) {
                console.error('Error fetching recipes:', error);
            });

        document.getElementById('search-recipe-button').addEventListener('click', function() {
            let stringType = document.getElementById('type').value;
            let selectedType = '';
            if (stringType !== '') {  
                stringType = stringType.replace(/ /g, "%20");
                selectedType = 'type=' + stringType + '&';
            }
            let stringMaxTime = document.getElementById('max-time').value;
            let selectedMaxTime = '';
            if (stringMaxTime !== '') {  
                stringMaxTime = stringMaxTime.replace(/ /g, "%20");
                selectedMaxTime = 'maxReadyTime=' + stringMaxTime + '&';
            }
            let stringMaxCalories = document.getElementById('max-cal').value;
            let selectedMaxCalories = '';
            if (stringMaxCalories !== '') {  
                stringMaxCalories = stringMaxCalories.replace(/ /g, "%20");
                selectedMaxCalories = 'maxCalories=' + stringMaxCalories + '&';
            }
            let recipeName = document.getElementById('selected-recipe').value;
            let query = '';
            if (recipeName !== '') {  
                recipeName = recipeName.replace(/ /g, "%20");
                query = 'query=' + recipeName + '&';
            //  document.getElementById('selected-recipe').value='';
            }

            const cuisinesListDiv = document.querySelector('.checkbox-group');
            const labelsForSearch = [];

            for (const label of cuisinesListDiv.children) {
                if (label.tagName === 'LABEL') {
                    const checkbox = label.querySelector('input[type="checkbox"]');
                    if (checkbox.checked) {
                        labelsForSearch.push(checkbox.value); 
                    }
                }
            }

            let selectedCuisines = "";
            if (labelsForSearch.length > 0) {
                selectedCuisines = labelsForSearch.map(encodeURIComponent).join('%2C');
                selectedCuisines = selectedCuisines.replace(/ /g, "%20");
                selectedCuisines = 'cuisine=' + selectedCuisines + '&';
            }
            const settings = {
                async: true,
                crossDomain: true,
                url: `https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch?${query}${selectedCuisines}${dietString}${intolerancesString}${selectedType}instructionsRequired=true&fillIngredients=false&addRecipeInformation=false&addRecipeInstructions=false&addRecipeNutrition=false&${selectedMaxTime}ignorePantry=false&sort=max-used-ingredients&${selectedMaxCalories}offset=0&number=20`,
                method: 'GET',
                headers: {
                    'x-rapidapi-key': apiKey,
                    'x-rapidapi-host': apiHost
                }
            };
            
            $.ajax(settings).done(function (response) {
                populateRecipesList(response.results); 
            }).fail(function (error) {
                console.error('Error fetching recipes:', error);
            });
        });

        function populateRecipesList(recipes) {
            const orderBy = document.getElementById('orderBy').value;
            const recipeListDiv = document.querySelector('.recipes');
        
            const idsArg = recipes.map(recipe => recipe.id).join(';');
        
            if (orderBy !== 'null') {
                $.ajax({
                    url: `/recipes?orderBy=${orderBy}&idsArg=${idsArg}`,
                    method: 'GET',
                    success: function(response) {
                        let recipe_ids = response;  // Sostituisci le ricette con quelle ordinate
                        console.log("solo id appena entrato")
                        console.log(recipe_ids)
        
                        // Trova le ricette presenti in "recipes" ma non in "response" (recipe_ids)
                        const missingRecipes = recipes.filter(recipe => !recipe_ids.includes(recipe.id));
                        
                        // Aggiungi le ricette mancanti alla fine della variabile "response"
                        recipe_ids = [...recipe_ids, ...missingRecipes.map(recipe => recipe.id)];
                        
                        console.log("Recipe IDs dopo aver aggiunto quelle mancanti:", recipe_ids);
        
                        // Filtra e ordina la variabile "recipes" in base agli "recipe_ids" ordinati
                        const orderedRecipes = recipe_ids.map(id => {
                            return recipes.find(recipe => recipe.id === id);
                        });
                        console.log("ordered Repices")
                        console.log(orderedRecipes);
        
                        // Sostituisci recipes con le ricette ordinate
                        recipes = orderedRecipes.filter(recipe => recipe !== undefined); // Esclude eventuali undefined
                        renderRecipes();
                    },
                    error: function(error) {
                        console.error('Error fetching sorted recipes:', error);
                    }
                });
            } else {
                // Mescola casualmente le ricette se l'ordinamento non è specificato
                recipes = recipes.sort(() => Math.random() - 0.5);
                console.log("DENTRO")
        
                renderRecipes();
            }
        
            function renderRecipes() {
        
                recipeListDiv.innerHTML=`
                                <h1>RANDOM RECIPES</h1>
                                <div class="error-message" id="errore-recipe">
                                    <p>Unfortunately your search returned no results.</p>
                                </div>
                                `;
        
                if (recipes.length === 0) {
                    document.getElementById('errore-recipe').style.display = "block";
                } else { 
                    document.getElementById('errore-recipe').style.display = "none";
                    
                    console.log(recipes)
        
                    const ajaxCalls = recipes.map(recipe => {
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
                
                        // Ritorna una Promise per ogni chiamata AJAX
                        return $.ajax(settings).then(response => {
                            return { recipe: response, id: recipe.id };
                        });
                    });
                
                    // Usa Promise.all per attendere tutte le chiamate AJAX
                    Promise.all(ajaxCalls)
                        .then(results => {
                            // Ordina i risultati in base all'ordine degli ID delle ricette
                            const orderedResults = results.sort((a, b) => {
                                return recipes.findIndex(r => r.id === a.id) - recipes.findIndex(r => r.id === b.id);
                            });
                            console.log(orderedResults)
                            // Ora puoi iterare sugli orderedResults in ordine e appendere gli elementi
                            orderedResults.forEach(result => {
                                const recipe = result.recipe;
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
                                    recipeString += `<img src="${recipe.image}" alt="Img Recipe" class="recipe-image"></img> `;
                                }
                                recipeElement.innerHTML = recipeString;
        
                                recipeListDiv.appendChild(recipeElement);
        
                                recipeElement.addEventListener('click', function() {
                                    window.location.href = `/ricetta?id=${recipe.id}`;
                                });
                            }).catch(function (error) {
                                console.error('Error fetching the recipe:', error);
                            });
                        });
                }
            }
        }
    })
    .catch(error => {
        console.error('Errore nel recupero delle chiavi:', error);
    });
});
