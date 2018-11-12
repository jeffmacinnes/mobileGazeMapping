# How to contribute

Thanks for your interest in making this tool better! We welcome your contributions. Below you'll find details that will help organize and structure new contributions.

# Issues

Feel free to submit issues and feature requests via the GitHub page. For tips on formatting your issue submission, please see `ISSUES_TEMPLATE.md` in this same directory

# Contributing

Please follow the "fork-and-pull" workflow for submitting your contributions.

1. **Fork** the repo
2. **Clone** the project to your local machine
3. **Commit** changes to your local branch
4. **Push** your changes back to your forked repo
5. Submit a **Pull request** so that we can review changes and incorporate them into the master branch of the repo.

# Testing

Whenever you make changes to the repo (and in particular, the `mapGaze.py` file, make sure your changes pass the tests on the sample data:

From the top-level directory from the repository, run:

> pytest

If your modifications to the code are successful, you should see output like:

```
Test session starts (platform: darwin, Python 3.6.4, pytest 3.9.3, pytest-sugar 0.9.1)
rootdir: ####/mobileGazeMapping, inifile:
plugins: xdist-1.23.0, sugar-0.9.1, forked-0.2

 tests/test_mapGaze.py ✓                                                                                      100% ██████████

Results (6.81s):
       1 passed
```

# Code conventions

To ensure readability and consistency in code stylinh, please use a tool like [flake8](http://flake8.pycqa.org/en/latest/) to ensure your changes conform to PEP8 style guidelines


# Contributor Code of Conduct

As contributors and maintainers of this project, we pledge to respect all people who contribute through reporting issues, posting feature requests, updating documentation, submitting pull requests or patches, and other activities.

We are committed to making participation in this project a harassment-free experience for everyone, regardless of level of experience, gender, gender identity and expression, sexual orientation, disability, personal appearance, body size, race, ethnicity, age, or religion.

Examples of unacceptable behavior by participants include the use of sexual language or imagery, derogatory comments or personal attacks, trolling, public or private harassment, insults, or other unprofessional conduct.

Project maintainers have the right and responsibility to remove, edit, or reject comments, commits, code, wiki edits, issues, and other contributions that are not aligned to this Code of Conduct. Project maintainers who do not follow the Code of Conduct may be removed from the project team.

Instances of abusive, harassing, or otherwise unacceptable behavior may be reported by opening an issue or contacting one or more of the project maintainers.

This Code of Conduct is adapted from the Contributor Covenant (http://contributor-covenant.org), version 1.0.0, available at http://contributor-covenant.org/version/1/0/0/
