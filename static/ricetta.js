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
    
        document.querySelectorAll('.add-to-shopping-list').forEach(button => {
            button.addEventListener('click', function() {
                const ingredient = this.getAttribute('data-ingredient');
                addToShoppingList(ingredient);
            });
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
});

