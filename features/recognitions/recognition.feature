Feature: Recognition API

  Scenario: Get recognition templates
    Given I authenticate as "maxim.lvov+admin@bonrepublic.com" with password "1qaz@WSX"
    When I send a GET request to recognition templates
    Then the response status code should be 200