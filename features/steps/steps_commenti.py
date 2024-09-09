from behave import given, when, then
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# STEPS USER STORY 31

@given('che mi sono precedentemente registrato, sono un utente con username "{username}", email "{email}", password "{password}" ed ho eseguito l’accesso come user')
def step_given_user_logged_in(context, username, email, password):
    context.browser = webdriver.Chrome()
    context.browser.get('http://localhost:5000/login')

    context.browser.find_element(By.ID, 'username_input').send_keys(username)
    context.browser.find_element(By.ID, 'password_input').send_keys(password)
    context.browser.find_element(By.ID, 'login-button').click()

@given('sono sulla pagina della ricetta con id="{recipe_id}"')
def step_given_on_recipe_page(context, recipe_id):
    context.browser.get(f'http://localhost:5000/ricetta?id={recipe_id}')

@when('scrivo nella sezione Aggiungi un commento "{commento}"')
def step_when_write_comment(context, commento):
    wait = WebDriverWait(context.browser, 15)
    comment_field = wait.until(EC.presence_of_element_located((By.ID, 'comment')))
    comment_field.clear()

    if commento:
        comment_field.send_keys(commento)

@when('valuto "{valutazione}" stelline la ricetta nella sezione Il tuo voto')
def step_when_rate_recipe(context, valutazione):
    if valutazione:

        valutazione = int(valutazione)

        if valutazione == 1:
            star_id = 's1'
        elif valutazione == 2:
            star_id = 's2'
        elif valutazione == 3:
            star_id = 's3'
        elif valutazione == 4:
            star_id = 's4'
        elif valutazione == 5:
            star_id = 's5'
        else:
            raise ValueError("Valutazione non valida. Deve essere un numero tra 1 e 5.")

        wait = WebDriverWait(context.browser, 15)
        rating_field = wait.until(EC.element_to_be_clickable((By.ID, star_id)))

        rating_field.click()

@when('clicco il bottone invia')
def step_when_click_submit_button(context):
    wait = WebDriverWait(context.browser, 15)
    submit_button = wait.until(EC.element_to_be_clickable((By.ID, 'submit_button')))
    submit_button.click()

@then(u'dovrebbe apparire un messaggio di successo')
def step_then_success_message(context):
    wait = WebDriverWait(context.browser, 15)
    success_message = wait.until(EC.visibility_of_element_located((By.ID, 'mess')))
    assert success_message.is_displayed(), "Il messaggio di successo non è visibile"


def get_star_string(rating):
    return '★' * rating + '☆' * (5 - rating)

@then('dovrei vedere il mio commento "{commento}" con la mia valutazione "{valutazione}" stelline in fondo alla sezione commenti sotto il nome "{username}"')
def step_then_verify_comment(context, commento, valutazione, username):
    wait = WebDriverWait(context.browser, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.comment-list .boxcommento')))
    comment_sections = context.browser.find_elements(By.CSS_SELECTOR, '.comment-sx')

    for comment_section in comment_sections:
        username_element = comment_section.find_element(By.CSS_SELECTOR, 'p.p1 strong')

        if username_element.text == username:
            comment_element = comment_section.find_element(By.CSS_SELECTOR, 'p.p1')

            if commento in comment_element.text:
                rating_element = comment_section.find_element(By.CSS_SELECTOR, 'p.p2')
                expected_rating_text = get_star_string(int(valutazione))

                if expected_rating_text in rating_element.text:
                    return

    assert False, f"Commento di '{username}' con valutazione '{valutazione}' e testo '{commento}' non trovato"


@then('il commento non viene inviato e dovrei visualizzare un messaggio di errore "{errore}"')
def step_then_error_message(context, errore):
    wait = WebDriverWait(context.browser, 15)

    if errore == 'È necessario scrivere un commento ed esprimere una valutazione':
        error_message = wait.until(EC.presence_of_element_located((By.ID, 'errore1')))
    elif errore == 'È necessario scrivere un commento':
        error_message = wait.until(EC.presence_of_element_located((By.ID, 'errore2')))
    elif errore == 'È necessario esprimere una valutazione':
        error_message = wait.until(EC.presence_of_element_located((By.ID, 'errore3')))
    elif errore == 'Inserire un commento valido':
        error_message = wait.until(EC.presence_of_element_located((By.ID, 'errore4')))
    else:
        assert False, f"Errore non riconosciuto: {errore}"

    assert error_message.is_displayed(), "Il messaggio di errore non è visibile"


@when(u'scrivo nella sezione Aggiungi un commento ""')
def step_impl(context):
    return

@when(u'valuto "" stelline la ricetta nella sezione Il tuo voto')
def step_impl(context):
    return

@then('chiudo il browser')
def step_then_close_browser(context):
    try:
        if hasattr(context, 'browser'):
            context.browser.close()
    except Exception as e:
        print(f"Errore durante la chiusura del browser: {e}")
        context.browser.quit()








