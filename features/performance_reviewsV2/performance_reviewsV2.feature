Feature: Performance Reviews V2 on dev2
  End-to-end проверка: авторизация и создание review session.

  Scenario: Create and verify review session on dev2
    Given I authenticate on dev2 as "maxim.lvov+admin@bonrepublic.com" with password "1qaz@WSX"
    When I create a review session on dev2 with payload:
      """
      {
        "analytics_visibility_type": 1,
        "approve_analytics_timedelta": null,
        "description": "",
        "allow_peers_selection": false,
        "end_date": "2025-08-30T22:00:00.000Z",
        "is_open": true,
        "participants": [
          {
            "reviewer": "94b0d335-9b79-413d-95f5-caaab17a6611",
            "review_role": "manager",
            "is_anonymous": true,
            "description": "<p>1</p>",
            "title": "Maxim Lvov Manager Feedback für Maxim Lvov Regular"
          },
          {
            "reviewer": "35544b65-8feb-434f-aae3-d02525bf5ca7",
            "review_role": "stakeholder",
            "is_anonymous": true,
            "description": "<p>1</p>",
            "title": "Maxim Lvov Admin Feedback für Maxim Lvov Regular"
          },
          {
            "reviewer": "8b2b2f6b-3ffa-4bf3-be8c-b8e22d495c67",
            "review_role": "self_reviewer",
            "is_anonymous": true,
            "description": "<p>1</p>",
            "title": "Selbstreflexion für Maxim Lvov Regular"
          }
        ],
        "is_periodic": false,
        "reviewee": "8b2b2f6b-3ffa-4bf3-be8c-b8e22d495c67",
        "start_date": "2025-08-19T15:27:00.000Z",
        "template_ids": ["27e03bde-6cfc-4a07-a6dd-8206c40f5283"],
        "name": "Feedback session for Maxim Lvov Regular 19.08.2025"
      }
      """
    Then the response status code should be 201
    When I fetch the created review session on dev2
    Then the response status code should be 200
    And one of participants has title exactly "Maxim Lvov Manager Feedback für Maxim Lvov Regular"
    When I delete the created review session on dev2
    Then the response status code should be 204
