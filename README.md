# Repository Workflow Guidelines


## Branching and Pull Requests

- The **main** branch is protected. Only the repository owner (maintainer) can push directly to it.
- All contributors are encouraged to:
  - Create **new branches** off of the main branch for any changes or new features.
  - Push commits to their own branches (not main).
  - Open a **Pull Request (PR)** from their branch to the `main` branch when ready for review.
- Pull requests will be reviewed by the maintainer before being merged into main.
- Do not push directly to the main branch; all changes must go through a pull request.

## How to Contribute

1. **Fork** the repository (if you do not have write access) or create a branch (if you do).
2. Create a descriptive branch name, e.g., `module_name/feature` or `module_name/bug`.
3. Commit your code changes to your branch.
4. Push your branch to your fork or this repository.
5. Open a pull request targeting the `main` branch.
6. Engage in code review and update your PR as needed.
7. Once approved, the maintainer will merge your PR into `main`.

## Summary

| Action                | Branch         | Who can do it  |
|-----------------------|----------------|----------------|
| Push commits          | New branches   | Anyone         |
| Direct push           | main           | Maintainer only|
| Open Pull Request     | Any branch     | Anyone         |
| Merge Pull Request    | main           | Maintainer only|


