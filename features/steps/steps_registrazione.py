from behave import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import sqlite3

@given('sono nella pagina di registrazione')
def step_given_nella_pagina_registrazione(context):
    context.browser = webdriver.Chrome()
    context.browser.get("http://localhost:5000/registrazione")
    context.wait = WebDriverWait(context.browser, 10)

@when('mi registro con email "{email}", username "{username}", password "{password}" e password di conferma "{password_conf}"')
def step_when_registro(context, email, username, password, password_conf):

    context.conn = sqlite3.connect('C:/Users/Utente/Desktop/Project_Assi/progetto-lab-ASSI-2023-2024/instance/db.sqlite')
    context.cursor = context.conn.cursor()
    context.cursor.execute("SELECT COUNT(*) FROM users WHERE email=?", (email,))
    count = context.cursor.fetchone()[0]
    if count > 0 and username == 'JackNew':
        context.cursor.execute("DELETE FROM users WHERE email=?", (email,))
        context.conn.commit()
    context.conn.close()

    context.wait = WebDriverWait(context.browser, 15)
    context.browser.find_element(By.ID, 'email').send_keys(email)
    context.browser.find_element(By.ID, 'username').send_keys(username)
    context.browser.find_element(By.ID, 'password').send_keys(password)
    context.browser.find_element(By.ID, 'password_conf').send_keys(password_conf)
    context.browser.find_element(By.ID, 'birthdate').send_keys("1995-07-15")


@when('clicco su Sign Up')
def step_when_click_signup(context):
    context.wait = WebDriverWait(context.browser, 15)
    context.browser.find_element(By.ID, 'signup').click()

@then('dovrei essere nella pagina principale')
def step_then_nella_pagina_principale(context):
    context.wait = WebDriverWait(context.browser, 15)
    print(context.browser.current_url)
    context.wait.until(EC.url_to_be("http://localhost:5000/"))

@then('dovrei vedere il mio username "{username}" nell header')
def step_then_vedo_username(context, username):
    context.wait = WebDriverWait(context.browser, 15)
    username_display = context.wait.until(EC.presence_of_element_located((By.ID, 'name')))
    assert username in username_display.text

@then('dovrei vedere un messaggio di errore "{message}"')
def step_then_vedo_messaggio_errore(context, message):
    context.wait = WebDriverWait(context.browser, 15)
    error_message = context.browser.find_element(By.ID, 'errmess')
    assert message in error_message.text

@then('dovrei visualizzare il messaggio di robustezza della password "{strength_message}"')
def step_then_messaggio_robustezza(context, strength_message):
    context.wait = WebDriverWait(context.browser, 5)
    password_strength = context.browser.find_element(By.ID, 'password-strength')
    print(strength_message)
    print(password_strength.text)
    assert strength_message in password_strength.text

@when('inserisco la password "{password}"')
def step_when_inserisco_password(context, password):
    context.wait = WebDriverWait(context.browser, 15)
    context.browser.find_element(By.ID, 'password').send_keys(password)