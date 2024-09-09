Feature: Pubblicazione commento e valutazione (user story 31)

  Background: utente registrato in pagina ricetta
    Given che mi sono precedentemente registrato, sono un utente con username "Jack", email "giaco.barcellona@gmail.com", password "MicroDario24." ed ho eseguito l’accesso come user
    And sono sulla pagina della ricetta con id="634141"

  Scenario: Successo
    When scrivo nella sezione Aggiungi un commento "Ricetta facile e gustosa"
    And valuto "4" stelline la ricetta nella sezione Il tuo voto
    And clicco il bottone invia
    Then dovrebbe apparire un messaggio di successo
    And dovrei vedere il mio commento "Ricetta facile e gustosa" con la mia valutazione "4" stelline in fondo alla sezione commenti sotto il nome "Jack"
    And chiudo il browser

  Scenario Outline: Insuccesso
    When scrivo nella sezione Aggiungi un commento "<commento>"
    And valuto "<valutazione>" stelline la ricetta nella sezione Il tuo voto
    And clicco il bottone invia
    Then il commento non viene inviato e dovrei visualizzare un messaggio di errore "<errore>"
    And chiudo il browser

    Examples:
      | commento                 | valutazione | errore                                                         |
      |                          |             | È necessario scrivere un commento ed esprimere una valutazione |
      | Ricetta facile e gustosa |             | È necessario esprimere una valutazione                         |
      |                          | 4           | È necessario scrivere un commento                              |
      | aaaaaaaaaa               | 4           | Inserire un commento valido                                    |


