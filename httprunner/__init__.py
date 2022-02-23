__version__ = "3.1.6"
__description__ = "One-stop solution for HTTP(S) testing."

# import firstly for monkey patch if needed
from httprunner.ext.locust import main_locusts
from httprunner.parser import parse_parameters as Parameters
from httprunner.runner import HttpRunner
from httprunner.testcase import Config, Step, RunRequest, RunTestCase

"""
若定义了__all__属性，则只有__all__内指定的属性、方法、类可被导入.
若没定义，则导入模块内的所有公有属性，方法和类。
"""
__all__ = [
    "__version__",
    "__description__",
    "HttpRunner",
    "Config",
    "Step",
    "RunRequest",
    "RunTestCase",
    "Parameters",
]
