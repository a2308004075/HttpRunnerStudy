
# HttpRunner

[![downloads](https://pepy.tech/badge/httprunner)](https://pepy.tech/project/httprunner)
[![unittest](https://github.com/httprunner/httprunner/workflows/unittest/badge.svg
)](https://github.com/httprunner/httprunner/actions)
[![integration-test](https://github.com/httprunner/httprunner/workflows/integration_test/badge.svg
)](https://github.com/httprunner/httprunner/actions)
[![codecov](https://codecov.io/gh/httprunner/httprunner/branch/master/graph/badge.svg)](https://codecov.io/gh/httprunner/httprunner)
[![pypi version](https://img.shields.io/pypi/v/httprunner.svg)](https://pypi.python.org/pypi/httprunner)
[![pyversions](https://img.shields.io/pypi/pyversions/httprunner.svg)](https://pypi.python.org/pypi/httprunner)
[![TesterHome](https://img.shields.io/badge/TTF-TesterHome-2955C5.svg)](https://testerhome.com/github_statistics)

*HttpRunner* is a simple & elegant, yet powerful HTTP(S) testing framework. Enjoy! ✨ 🚀 ✨

> 欢迎参加 HttpRunner [用户调研问卷][survey]，你的反馈将帮助 HttpRunner 更好地成长！

## Design Philosophy

- Convention over configuration
- ROI matters
- Embrace open source, leverage [`requests`][requests], [`pytest`][pytest], [`pydantic`][pydantic], [`allure`][allure] and [`locust`][locust].

## Key Features

- [x] Inherit all powerful features of [`requests`][requests], just have fun to handle HTTP(S) in human way.
- [x] Define testcase in YAML or JSON format, run with [`pytest`][pytest] in concise and elegant manner.
- [x] Record and generate testcases with [`HAR`][HAR] support.
- [x] Supports `variables`/`extract`/`validate`/`hooks` mechanisms to create extremely complex test scenarios.
- [x] With `debugtalk.py` plugin, any function can be used in any part of your testcase.
- [x] With [`jmespath`][jmespath], extract and validate json response has never been easier.
- [x] With [`pytest`][pytest], hundreds of plugins are readily available.
- [x] With [`allure`][allure], test report can be pretty nice and powerful.
- [x] With reuse of [`locust`][locust], you can run performance test without extra work.
- [x] CLI command supported, perfect combination with `CI/CD`.

