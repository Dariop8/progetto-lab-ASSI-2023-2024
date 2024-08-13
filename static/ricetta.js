document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    recipeId = urlParams.get('id');
    const ingredientsUrl = urlParams.get('ingredients');
    const ingredientsArray = ingredientsUrl.split(',');

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
    
    $.ajax(settings).done(function (response) {
        //console.log(response); 
        populateRecipePage(response); 
    }).fail(function (error) {
        console.error('Error fetching the recipe:', error);
    });

    function populateRecipePage(recipe) {
        const recipeDetailsDiv = document.querySelector('.recipe-details');
    
        let recipeHTML = `
            <h1>Nome Ricetta: ${recipe.title}</h1>
            <div class="recipe-info">
                <span>Tempo: ${recipe.readyInMinutes} minuti</span>
                <span>Tipo: ${recipe.dishTypes ? recipe.dishTypes.join(', ') : 'Non specificato'}</span>
                <span>Calorie: ${recipe.aggregateLikes ? recipe.aggregateLikes * 10 : 'Non disponibile'} kcal</span>
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
            if (ingredientsArray.includes(ingredient.name)){
                recipeHTML += `
                    <li class="possessed">
                        ${ingredient.name}
                        <span class="checkmark">✔</span> 
                    </li>
                `;
            } else {
                recipeHTML += `
                    <li class="to-buy">${ingredient.name}</li>
                `;
            }
        });

        recipeHTML += `
                    </ul>
                </div>
                <div class="steps">
                    <ul>
                        <li>Step 1: Preparare il ragù alla bolognese cuocendo carne macinata, cipolla, carota e sedano in una pentola con olio d'oliva. Aggiungere passata di pomodoro, vino rosso e cuocere a fuoco lento per almeno 2 ore.</li>
                        <li>Step 2: Preparare la besciamella sciogliendo burro in una casseruola, aggiungere farina e mescolare fino a ottenere un roux. Aggiungere latte caldo poco alla volta, mescolando continuamente fino a ottenere una salsa liscia e densa. Condire con sale, pepe e noce moscata.</li>
                        <li>Step 3: Cuocere la pasta all'uovo per lasagna in abbondante acqua salata per qualche minuto, quindi scolarla e stenderla su un canovaccio per farla asciugare.</li>
                        <li>Step 4: Preriscaldare il forno a 180°C. Iniziare a comporre la lasagna in una teglia, alternando strati di pasta, ragù, besciamella e parmigiano. Ripetere fino a esaurire gli ingredienti, terminando con uno strato di besciamella e una generosa spolverata di parmigiano.</li>
                        <li>Step 5: Coprire la teglia con un foglio di alluminio e cuocere in forno per 30 minuti. Rimuovere il foglio di alluminio e cuocere per altri 10-15 minuti, o fino a quando la superficie sarà dorata e croccante.</li>
                        <li>Step 6: Lasciare riposare la lasagna per qualche minuto prima di tagliarla e servirla. Questo permetterà ai sapori di amalgamarsi e renderà più facile il taglio.</li>
                        <li>Step 7: Servire la lasagna calda, accompagnata da un'insalata verde o da un bicchiere di vino rosso.</li>
                    </ul>
                </div>
            </div>
        `;

        recipeDetailsDiv.innerHTML = recipeHTML;
    }
});

