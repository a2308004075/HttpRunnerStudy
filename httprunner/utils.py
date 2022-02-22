# 一些工具函数
"""
可用资料
    sentry_sdk: https://docs.sentry.io/platforms/python/
    os: https://docs.python.org/zh-cn/3/library/os.html?highlight=os#module-os
"""
import collections
import copy
import json
import os.path
import platform
import uuid
from multiprocessing import Queue
import itertools
from typing import Dict, List, Any, Union, Text

import sentry_sdk
from loguru import logger

from httprunner import __version__
from httprunner import exceptions
from httprunner.models import VariablesMapping


def init_sentry_sdk():
    """
    项目在部署到测试、生产环境后，我们便不可能像在开发时那样容易的及时发现处理错误了。一般我们都是在错误发生一段时间后，
    错误信息才会传递到开发人员那里，然后一顿操作查看程序运行的日志，就熟练使用awk和grep去分析日志，但是往往我们会因为
    日志中缺少上下文关系，导致很难分析真正的错误是什么。
    Sentry由此应运而生成为了解决这个问题的一个很好的工具，设计了诸多特性帮助开发者更快、更方面、更直观的监控错误信息。
    """
    sentry_sdk.init(
        dsn="https://460e31339bcb428c879aafa6a2e78098@sentry.io/5263855",
        release="httprunner@{}".format(__version__),
    )
    with sentry_sdk.configure_scope() as scope:
        scope.set_user({"id": uuid.getnode()})


def set_os_environ(variables_mapping):
    """
    设置 variables 映射到 os.environ
    """
    for variable in variables_mapping:
        os.environ[variable] = variables_mapping[variable]
        logger.debug(f"Set OS environment variable: {variable}")


def unset_os_environ(variables_mapping):
    """
    把variables从os.environ删除
    """
    for variable in variables_mapping:
        os.environ.pop(variable)
        logger.debug(f"Unset OS environment variable: {variable}")


def get_os_environ(variable_name):
    """
    从os.environ通过key获取value

    Args:
        variable_name(str): variable name

    Returns:
        value of environment variable.

    Raises:
        exceptions.EnvNotFound: If environment variable not found.

    """
    try:
        return os.environ[variable_name]
    except KeyError:
        raise exceptions.EnvNotFound(variable_name)


def lower_dict_keys(origin_dict):
    """
    把字典的key转换为小写

    Args:
        origin_dict (dict): mapping data structure

    Returns:
        dict: mapping with all keys lowered.

    Examples:
        >>> origin_dict = {
            "Name": "",
            "Request": "",
            "URL": "",
            "METHOD": "",
            "Headers": "",
            "Data": ""
        }
        >>> lower_dict_keys(origin_dict)
            {
                "name": "",
                "request": "",
                "url": "",
                "method": "",
                "headers": "",
                "data": ""
            }

    """
    if not origin_dict or not isinstance(origin_dict, dict):
        return origin_dict

    return {key.lower(): value for key, value in origin_dict.items()}


def print_info(info_mapping):
    """ 打印字典信息.

    Args:
        info_mapping (dict): input(variables) or output mapping.

    Examples:
        >>> info_mapping = {
                "var_a": "hello",
                "var_b": "world"
            }
        >>> info_mapping = {
                "status_code": 500
            }
        >>> print_info(info_mapping)
        ==================== Output ====================
        Key              :  Value
        ---------------- :  ----------------------------
        var_a            :  hello
        var_b            :  world
        ------------------------------------------------

    """
    if not info_mapping:
        return

    content_format = "{:<16} : {:<}\n"
    content = "\n==================== Output ====================\n"
    content += content_format.format("Variable", "Value")
    content += content_format.format("-" * 16, "-" * 29)

    for key, value in info_mapping.items():
        # 判断value 是 元组 或者 deque： 类似列表(list)的容器，实现了在两端快速添加(append)和弹出(pop)
        if isinstance(value, (tuple, collections.deque)):
            continue
        # 判断value 是 字典 或者 列表
        elif isinstance(value, (dict, list)):
            # 核心代码。将字典转化为字符串
            value = json.dumps(value)
        elif value is None:
            value = "None"
        # 核心代码。拼接字符串
        content += content_format.format(key, value)

    content += "-" * 48 + "\n"
    logger.info(content)


def omit_long_data(body, omit_len=512):
    """
    省略过长的数据

    eg: body = "123456789"
        l = omit_long_data(body,omit_len=5)
        print(l)    # 12345 ... OMITTED 6 CHARACTORS ...


    """
    if not isinstance(body, (str, bytes)):
        return body

    body_len = len(body)
    if body_len <= omit_len:
        return body

    # 截取前0-omit_len个字符
    omitted_body = body[0:omit_len]

    appendix_str = f" ... OMITTED {body_len - omit_len} CHARACTORS ..."
    if isinstance(body, bytes):
        appendix_str = appendix_str.encode("utf-8")

    return omitted_body + appendix_str


def get_platform():
    """
    platform.platform(): 系统版本信息
    platform.python_version()： Python信息
    python_implementation(): python 解释器版本？CPython
    """
    return {
        "httprunner_version": __version__,
        "python_version": "{} {}".format(
            platform.python_implementation(), platform.python_version()
        ),
        "platform": platform.platform(),
    }


def sort_dict_by_custom_order(raw_dict: Dict, custom_order: List):
    """
    通过自定义顺序 对 字典排序
    """
    def get_index_from_list(lst: List, item: Any):
        """
        获取list中指定元素坐标
        """
        print(2222)
        try:
            return lst.index(item)
        except ValueError:
            # item is not in lst
            return len(lst) + 1
    """
    g = lambda x,y: x + y + 1
    print(g(1,2))    # 4
    
    lambda后面为 变量  x  y
    :号后面为 方法体
    """

    return dict(
        sorted(raw_dict.items(), key=lambda i: get_index_from_list(custom_order, i[0]))
    )


class ExtendJSONEncoder(json.JSONEncoder):
    """
    特别用于安全把json数据dump成python 对象, 例如 MultipartEncoder（上传文件模块）

    json.JSONEncoder用于dict类型转换成标准Json字符串
    """

    def default(self, obj):
        try:
            return super(ExtendJSONEncoder, self).default(obj)
        except (UnicodeDecodeError, TypeError):
            # repr() 返回对象的规范字符串表示形式
            return repr(obj)


def merge_variables(
    variables: VariablesMapping, variables_to_be_overridden: VariablesMapping
) -> VariablesMapping:
    """
    合并两个变量映射，第一个优先级更高
    """
    step_new_variables = {}
    for key, value in variables.items():
        if f"${key}" == value or "${" + key + "}" == value:
            # e.g. {"base_url": "$base_url"}
            # or {"base_url": "${base_url}"}
            continue

        step_new_variables[key] = value

    # 浅复制了字典 并把其中的内容都弄过来了
    merged_variables = copy.copy(variables_to_be_overridden)
    # 更新了复制出来的字典， 原字典不会改变
    merged_variables.update(step_new_variables)
    return merged_variables


def is_support_multiprocessing() -> bool:
    """
    判断是否支持多进程，如：Android termux
    """
    try:
        Queue()
        return True
    except (ImportError, OSError):
        # system that does not support semaphores(dependency of multiprocessing), like Android termux
        return False


def gen_cartesian_product(*args: List[Dict]) -> List[Dict]:
    """ generate cartesian product for lists
        生成笛卡尔积,估计是参数化用的

    Args:
        args (list of list): lists to be generated with cartesian product

    Returns:
        list: cartesian product in list

    Examples:

        >>> arg1 = [{"a": 1}, {"a": 2}]
        >>> arg2 = [{"x": 111, "y": 112}, {"x": 121, "y": 122}]
        >>> args = [arg1, arg2]
        >>> gen_cartesian_product(*args)
        >>> # same as below
        >>> gen_cartesian_product(arg1, arg2)
            [
                {'a': 1, 'x': 111, 'y': 112},
                {'a': 1, 'x': 121, 'y': 122},
                {'a': 2, 'x': 111, 'y': 112},
                {'a': 2, 'x': 121, 'y': 122}
            ]

    """
    if not args:
        return []
    elif len(args) == 1:
        return args[0]

    product_list = []
    # product 笛卡尔积，相当于嵌套的for循环
    for product_item_tuple in itertools.product(*args):
        product_item_dict = {}
        for item in product_item_tuple:
            product_item_dict.update(item)

        product_list.append(product_item_dict)

    return product_list

if __name__ == '__main__':
    arg1 = [{"a": 1}, {"a": 2}]
    arg2 = [{"x": 111, "y": 112}, {"x": 121, "y": 122}]
    args = [arg1, arg2]

    product_list = []

    for product_item_tuple in itertools.product(*args):
        print(product_item_tuple)

