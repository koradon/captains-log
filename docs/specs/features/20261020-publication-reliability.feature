Feature: Reliable and observable commit publication
  Scenario: A live lock prevents publication without hiding the local save
    Given an isolated source repo and log clone backed by a local bare remote
    And the log clone has a recent index lock
    When update_log records a source commit
    Then the entry is saved locally and the remote is unchanged
    And update_log exits 1 with timestamp, run, source repo, SHA, and lock stage
    And a durable pending record identifies the unpublished entry
    And a manual entry command warns about unpublished runs

  Scenario: The next run publishes all earlier pending files
    Given earlier locally saved entries whose publication failed
    When the log lock is released and a new entry is recorded
    Then one new log commit publishes all pending files
    And the saved runs' pending records for that destination are cleared

  Scenario: An abandoned lock can be recovered conservatively
    Given a regular lock unchanged for at least 24 hours
    And a successful ownership inspection finds no open holder
    When the next publication runs
    Then the unchanged lock is removed and recovery is reported
    And pending local entries are published

  Scenario: An old lock with an owner or uncertain evidence is preserved
    Given an old lock with an open holder or unavailable ownership inspection
    When the next publication runs
    Then the lock is preserved and publication failure remains visible

  Scenario: A previously committed entry is retried from a clean worktree
    Given a committed local entry whose push failed
    When a later automatic run succeeds
    Then the existing commit is pushed even when no new file changes exist

  Scenario: Installed hooks capture the commit that supplied the message
    Given setup or install-precommit-hooks has installed hooks in a temporary home
    When a new source commit is created and log publication fails
    Then the source commit still succeeds
    And the saved log records that new commit's SHA with its subject
    And correlated diagnostics and pending state expose the publication failure
