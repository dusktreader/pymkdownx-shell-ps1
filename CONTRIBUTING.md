# Contributing guidelines

## Security concerns

Before any further discussion, a point about security needs to be addressed:

> [!WARNING]
> If you find a serious security vulnerability that could affect current users, please report it to maintainers via
> email or some form of private communication. For other issue reports, see below.


## Thanks

Thank you for your interest in contributing to superfences-ps1! Even though this is mostly a personal project,
all contributions help and are appreciated.


## Contact

The maintainers of superfences-ps1 can be reached most easily via email:

- **Tucker Beck**: [tucker.beck@gmail.com](mailto:tucker.beck@gmail.com)


## Conduct

Everyone's conduct should be respectful and friendly. The superfences-ps1 project expects contributors to adhere
to the [Code of Conduct](./CONDUCT.md). Any issues working with other contributors should be reported to the
maintainers.


## Contribution recommendations


### GitHub issues

The first and primary source of contributions is opening issues on GitHub. Please feel free to open issues when you
find problems or wish to request a feature. All issues will be treated seriously and taken under consideration.
However, maintainers may disregard or close issues at their discretion.

Issues are most helpful when they contain specifics about the problem they address. Specific error messages, references
to specific lines of code, environment contexts, and such are extremely helpful.


### Code contributions

Code contributions should be submitted via pull requests on GitHub. Project maintainers will review pull requests and
may test new features. All merge requests should come with commit messages that describe the changes as well as a
reference to the issue that the code addresses. Commit messages should adhere to
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

Code contributions should follow best practices where possible. All code must pass the QA suite:

```shell
make qa/full
```

Adding additional dependencies should be limited except where needed functionality can be easily added through pip
packages. Please include development-only dependencies in the dev dependency list. Packages should only be added if
they are:

- Actively maintained
- Widely used
- Hosted on pypi.org
- Have source code on a public repository
- Include tests
- Include a software license


### Documentation

Help with documentation is always welcome. Documentation should be clear, include examples where possible, and
reference source material as much as possible.


## Non-preferred contributions

The following types of contribution are not welcome:

- Complaints without suggestion
- Criticism about the overall approach
- Copied code without attribution
- Promotion of personal packages or projects without due need
- Sarcasm or ridicule of contributions or design choices
