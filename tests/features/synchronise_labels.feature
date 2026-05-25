Feature: Synchronise GitHub labels
  Scenario: Create and update configured labels
    Given a repository with an existing "risk: low" label
    And a label configuration containing "risk: low" and "risk: high"
    When the labels are synchronised
    Then the existing "risk: low" label is updated
    And the missing "risk: high" label is created
