Feature: Ricerca ricette in base al tempo di preparazione (user story 24)

  Scenario: Ricerca di ricette che rientrano nel tempo selezionato
    Given un utente nella pagina delle ricette random
    When seleziona “60” min in Max Time nella sezione Filtri
    And clicca il bottone “cerca ricetta”
    Then dovrebbe visualizzare una lista di ricette eseguibili in un tempo <= a quello selezionato