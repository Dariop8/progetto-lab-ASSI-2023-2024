Feature: Registrazione dell'utente (user story 1)

  Scenario: Registrazione con successo
    Given sono nella pagina di registrazione
    When mi registro con email "giaco.barcellonanew@gmail.com", username "JackNew", password "MicroDario24." e password di conferma "MicroDario24."
    And clicco su Sign Up
    Then dovrei essere nella pagina principale
    And dovrei vedere il mio username "JackNew" nell header
    And chiudo il browser

  Scenario: Email già utilizzata
    Given sono nella pagina di registrazione
    When mi registro con email "giaco.barcellona@gmail.com", username "Jack", password "MicroDario24." e password di conferma "MicroDario24."
    And clicco su Sign Up
    Then dovrei vedere un messaggio di errore "User already registered."
    And chiudo il browser

  Scenario: Password troppo semplice
    Given sono nella pagina di registrazione
    When mi registro con email "giaco.barcellonanew@gmail.com", username "JackNew", password "1234" e password di conferma "1234"
    And clicco su Sign Up
    Then dovrei vedere un messaggio di errore "Password is too weak."
    And chiudo il browser

  Scenario: Le password non combaciano
    Given sono nella pagina di registrazione
    When mi registro con email "giaco.barcellonanew@gmail.com", username "JackNew", password "abc123DEF!@" e password di conferma "abc123DEF!@2482"
    And clicco su Sign Up
    Then dovrei vedere un messaggio di errore "Passwords do not match."
    And chiudo il browser

  Scenario Outline: Valutazione della robustezza della password
    Given sono nella pagina di registrazione
    When inserisco la password "<password>"
    Then dovrei visualizzare il messaggio di robustezza della password "<strength_message>"
    And chiudo il browser

    Examples:
      | password               | strength_message                                   |
      | abcd                   | Very weak (instantly crackable)                    |
      | abc123                 | Weak (instantly crackable)                         |
      | abc123DEF              | Moderate (crackable in hours or days)              |
      | abc123DEF!@            | Strong (crackable in weeks or months)              |
      | abc123DEF!@#GHIJ       | Very strong (crackable in years)                   |
      | abc123DEF!@#GHIJKLMNOP | Extremely strong (crackable in millennia or never) |
