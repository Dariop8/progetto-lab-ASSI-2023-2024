from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# STEPS USER STORY 24

@given('un utente nella pagina delle ricette random')
def step_given_user_on_random_recipes_page(context):
    context.browser = webdriver.Chrome()
    context.browser.get('http://localhost:5000/idee_rand')
    context.wait = WebDriverWait(context.browser, 15)


@when('seleziona “{time}” min in Max Time nella sezione Filtri')
def step_when_select_max_time(context, time):
    context.wait = WebDriverWait(context.browser, 15)
    max_time_select = context.browser.find_element(By.ID, 'max-time')
    select = Select(max_time_select)
    select.select_by_value(time)


@when('clicca il bottone “cerca ricetta”')
def step_when_click_search_button(context):
    context.wait = WebDriverWait(context.browser, 15)
    search_button = WebDriverWait(context.browser, 10).until(
        EC.element_to_be_clickable((By.ID, 'search-recipe-button'))
    )
    search_button.click()



@then('dovrebbe visualizzare una lista di ricette eseguibili in un tempo <= a quello selezionato')
def step_then_verify_recipes_list(context):
    context.wait = WebDriverWait(context.browser, 15)
    recipe_infos = context.browser.find_elements(By.CSS_SELECTOR, '.recipe-info')

    for recipe_info in recipe_infos:
        time_element = recipe_info.find_element(By.CSS_SELECTOR, '.recipe-details .time')

        time_text = time_element.text
        time_value = int(time_text.replace('🕒', '').replace('min', '').strip())

        assert time_value <= 60, f"Il tempo della ricetta '{recipe_info.find_element(By.CSS_SELECTOR, '.recipe-name').text}' è {time_value} min, che supera il tempo massimo selezionato"