---
allowed-tools: Bash(docker-compose exec:*)
description: Run backend tests — full suite, module, or specific test
---

## Task

Run pytest using the argument provided to determine the scope:

- **No argument** → full suite:
  ```bash
  docker-compose exec api pytest
  ```

- **Module name** (e.g. `gym_tracker`) → module tests:
  ```bash
  docker-compose exec api pytest app/modules/<arg>/tests -v
  ```

- **File path** (e.g. `gym_tracker/tests/test_workouts.py`) → specific file:
  ```bash
  docker-compose exec api pytest app/modules/<arg> -v
  ```

- **Class or function** (e.g. `test_workouts.py::TestWorkoutService::test_start`) → specific test:
  ```bash
  docker-compose exec api pytest app/modules/<arg> -v
  ```

After running, summarize: how many passed, how many failed, and if there are failures show the relevant error output.
