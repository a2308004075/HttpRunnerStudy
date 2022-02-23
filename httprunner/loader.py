# 加载文件内容的方法
"""
这个文件主要是：
    对yaml,json用例加载转换成用例模型、套件模型
    预置函数加载成方法字典，
    项目路径加载
    变量写入环境
可用资料
    [importlib]. https://docs.python.org/zh-cn/3/library/importlib.html
    [funcitons]. https://docs.python.org/zh-cn/3/library/functions.html
    借助impotlib 动态导入module， vars内置函数解析module中的信息，
    并将其处理和加入方法字典中name 作为 key， 函数对象作为value，来完成调用扩展函数的上半部分内容
"""
import csv  # 内置库：csv 读取
import importlib    # 内置库 处理动态导包
import json     # 内置库 json 处理
import os       # 内置库 操作系统
import sys      # 内置库 系统相关的参数和函数
import types        # 内置库 动态类型创建和内置类型名称
from typing import Tuple, Dict, Union, Text, List, Callable

import yaml     # 处理yaml文件 pyyaml
from loguru import logger
from pydantic import ValidationError        # 异常

from httprunner import builtin, utils       # builtin 中存在预置的函数
from httprunner import exceptions       # 自定义的失败，错误逻辑
from httprunner.models import TestCase, ProjectMeta, TestSuite

# pyyaml 异常处理
try:
    # PyYAML version >= 5.1
    # ref: https://github.com/yaml/pyyaml/wiki/PyYAML-yaml.load(input)-Deprecation
    """
        执行yaml.load()出现警告信息:YAMLLoadWarning: callingyaml.load() without Loader=...
        yaml5.1版本后弃用了yaml.load(file)这个用法，因为觉得很不安全，5.1版本之后就修改了需要指定Loader，
    通过默认加载器（FullLoader）禁止执行任意函数。
    通过下面两种方式处理：
        1、yaml.load(a, Loader=yaml.FullLoader)
        2、yaml.warnings({'YAMLLoadWarning': False})
        Loader的几种加载方式：
            BaseLoader--仅加载最基本的YAML。
            SafeLoader--安全地加载YAML语言的子集。建议用于加载不受信任的输入。
            FullLoader--加载完整的YAML语言。避免任意代码执行。这是当前（PyYAML 5.1）默认加载器调yaml.load(input)（发出警告后）。
            UnsafeLoader--（也称为Loader向后兼容性）原始的Loader代码，可以通过不受信任的数据输入轻松利用。
    """
    yaml.warnings({"YAMLLoadWarning": False})
except AttributeError:
    pass

# project_meta 信息为None
project_meta: Union[ProjectMeta, None] = None


def _load_yaml_file(yaml_file: Text) -> Dict:
    """
    读取yaml文件并检查文件内容格式
    """
    with open(yaml_file, mode="rb") as stream:
        try:
            # 核心代码，读取yaml文件
            yaml_content = yaml.load(stream)
        except yaml.YAMLError as ex:
            err_msg = f"YAMLError:\nfile: {yaml_file}\nerror: {ex}"
            logger.error(err_msg)
            raise exceptions.FileFormatError

        return yaml_content


def _load_json_file(json_file: Text) -> Dict:
    """
    读取json文件并检查文件内容格式
    """
    with open(json_file, mode="rb") as data_file:
        try:
            # 核心代码。读取json文件
            json_content = json.load(data_file)
        except json.JSONDecodeError as ex:
            err_msg = f"JSONDecodeError:\nfile: {json_file}\nerror: {ex}"
            raise exceptions.FileFormatError(err_msg)

        return json_content


def load_test_file(test_file: Text) -> Dict:
    """
    读取testcase/testsuite文件内容，并返回文件内容
    """
    if not os.path.isfile(test_file):
        raise exceptions.FileNotFound(f"test file not exists: {test_file}")

    # os.path.splitext(test_file) 获取路径中文件后缀转换小写
    file_suffix = os.path.splitext(test_file)[1].lower()
    if file_suffix == ".json":
        test_file_content = _load_json_file(test_file)
    elif file_suffix in [".yaml", ".yml"]:
        test_file_content = _load_yaml_file(test_file)
    else:
        # '' or 其他后缀
        raise exceptions.FileFormatError(
            f"testcase/testsuite file should be YAML/JSON format, invalid format file: {test_file}"
        )

    return test_file_content


def load_testcase(testcase: Dict) -> TestCase:
    """
        将字典转成 TestCase对象
        """
    try:
        # 使用pydantic TestCase模型进行验证
        # 当成实例化操作就行 TestCase.parse_obj(testcase)
        # TestCase(**testcase) 和上面等效
        # 核心代码。将字典转成 TestCase对象
        testcase_obj = TestCase.parse_obj(testcase)
    except ValidationError as ex:
        err_msg = f"TestCase ValidationError:\nerror: {ex}\ncontent: {testcase}"
        raise exceptions.TestCaseFormatError(err_msg)

    return testcase_obj


def load_testcase_file(testcase_file: Text) -> TestCase:
    """
    读取 testcase 文件 并且 使用pydantic模块校验
    将测试用例文件转成TestCase对象
    """
    # 1. 测试用例文件路径转成字典
    testcase_content = load_test_file(testcase_file)
    # 2. 字典转成 TestCase 对象
    testcase_obj = load_testcase(testcase_content)
    # 3. 将文件路径赋值给 对象里面的config下的path
    testcase_obj.config.path = testcase_file
    # 4. 返回TestCase对象
    return testcase_obj


def load_testsuite(testsuite: Dict) -> TestSuite:
    """
    测试套件，将套件字典 加载成TestSuite对象
    """
    path = testsuite["config"]["path"]
    try:
        # 使用pydantic TestCase模型进行验证
        # 核心代码。将套件字典 加载成TestSuite对象
        testsuite_obj = TestSuite.parse_obj(testsuite)
    except ValidationError as ex:
        err_msg = f"TestSuite ValidationError:\nfile: {path}\nerror: {ex}"
        raise exceptions.TestSuiteFormatError(err_msg)

    return testsuite_obj


def load_dot_env_file(dot_env_path: Text) -> Dict:
    """
    读取.env文件内容转成字典并 设置到 环境变量
    Args:
        dot_env_path (str): .env file path

    Returns:
        dict: environment variables mapping

            {
                "UserName": "debugtalk",
                "Password": "123456",
                "PROJECT_KEY": "ABCDEFGH"
            }

    Raises:
        exceptions.FileFormatError: If .env file format is invalid.

    """
    if not os.path.isfile(dot_env_path):
        return {}

    logger.info(f"Loading environment variables from {dot_env_path}")
    env_variables_mapping = {}

    with open(dot_env_path, mode="rb") as fp:
        for line in fp:
            # maxsplit=1
            if b"=" in line:
                variable, value = line.split(b"=", 1)
            elif b":" in line:
                variable, value = line.split(b":", 1)
            else:
                raise exceptions.FileFormatError(".env format error")

            # 字典env_variables_mapping进行key-value的复制操作
            # strip() 方法用于移除字符串头尾指定的字符（默认为空格或换行符）或字符序列。
            env_variables_mapping[
                variable.strip().decode("utf-8")
            ] = value.strip().decode("utf-8")

    # 将字典设置到当前系统里
    utils.set_os_environ(env_variables_mapping)
    return env_variables_mapping


def load_csv_file(csv_file: Text) -> List[Dict]:
    """
    读取csv文件并检查文件内容格式
    Args:
        csv_file (str): csv file path, csv file content is like below:

    Returns:
        list: list of parameters, each parameter is in dict format

    Examples:
        >>> cat csv_file
        username,password
        test1,111111
        test2,222222
        test3,333333

        >>> load_csv_file(csv_file)
        [
            {'username': 'test1', 'password': '111111'},
            {'username': 'test2', 'password': '222222'},
            {'username': 'test3', 'password': '333333'}
        ]

    """
    if not os.path.isabs(csv_file):
        global project_meta
        if project_meta is None:
            raise exceptions.MyBaseFailure("load_project_meta() has not been called!")

        # 让 Windows/Linux兼容
        csv_file = os.path.join(project_meta.RootDir, *csv_file.split("/"))

    if not os.path.isfile(csv_file):
        # 文件路径不存在
        raise exceptions.CSVNotFound(csv_file)

    csv_content_list = []

    with open(csv_file, encoding="utf-8") as csvfile:
        # 核心代码。读取csv文件，DictReader会将第一行的内容（类标题）作为key值，第二行开始才是数据内容。
        reader = csv.DictReader(csvfile)
        for row in reader:
            csv_content_list.append(row)

    return csv_content_list


def load_folder_files(folder_path: Text, recursive: bool = True) -> List:
    """
    加载目录下的文件，返回文件后缀.yml/.yaml/.json/_test.py，并放入list中
    Args:
        folder_path (str): 指定用于加载的目录路径
        recursive (bool): 如果为True，递归加载文件

    Returns:
        list: files endswith yml/yaml/json
    """
    if isinstance(folder_path, (list, set)):
        files = []
        # set()创建一个无序不重复元素集，可进行关系测试，删除重复数据，还可以计算交集、差集、并集等。
        for path in set(folder_path):
            # list.extend()以追加的方式扩展list
            files.extend(load_folder_files(path, recursive))

        return files

    if not os.path.exists(folder_path):
        return []

    file_list = []
    # os.walk() 生成目录树中的文件名
    for dirpath, dirnames, filenames in os.walk(folder_path):
        filenames_list = []

        for filename in filenames:
            # 核心代码。判断文件后缀是否以".yml", ".yaml", ".json", "_test.py"结尾
            if not filename.lower().endswith((".yml", ".yaml", ".json", "_test.py")):
                continue

            filenames_list.append(filename)

        for filename in filenames_list:
            file_path = os.path.join(dirpath, filename)
            file_list.append(file_path)

        if not recursive:
            break

    return file_list


def load_module_functions(module) -> Dict[Text, Callable]:
    """
    加载一个模块的方法返回一个方法字典， 自定义函数实现的一部分
    Args:
        module: python module

    Returns:
        dict: functions mapping for specified python module

            {
                "func1_name": func1,
                "func2_name": func2
            }
        {
        'equal': <function equal at 0x000001729137D430>,
        'greater_than': <function greater_than at 0x000001729137D550>,
        'less_than': <function less_than at 0x000001729137D5E0>,
        'greater_or_equals': <function greater_or_equals at 0x000001729137D670>,
        'less_or_equals': <function less_or_equals at 0x000001729137D700>,
        'not_equal': <function not_equal at 0x000001729137D790>,
        'string_equals': <function string_equals at 0x000001729137D820>,
        'length_equal': <function length_equal at 0x000001729137D8B0>,
        'length_greater_than': <function length_greater_than at 0x000001729137D940>,
        'length_greater_or_equals': <function length_greater_or_equals at 0x000001729137D9D0>,
        'length_less_than': <function length_less_than at 0x000001729137DA60>,
        'length_less_or_equals': <function length_less_or_equals at 0x000001729137DAF0>,
        'contains': <function contains at 0x000001729137DB80>,
        'contained_by': <function contained_by at 0x000001729137DC10>,
        'type_match': <function type_match at 0x000001729137DCA0>,
        'regex_match': <function regex_match at 0x000001729137DD30>,
        'startswith': <function startswith at 0x000001729137DDC0>,
        'endswith': <function endswith at 0x000001729137DE50>}
    """
    module_functions = {}
    # vars() 函数返回对象object的属性和属性值的字典对象
    for name, item in vars(module).items():
        # types.FunctionType 函数类型
        if isinstance(item, types.FunctionType):
            # 方法名称 作为key 函数对象作为value
            module_functions[name] = item

    return module_functions


def load_builtin_functions() -> Dict[Text, Callable]:
    """
    加载内置方法
    """
    return load_module_functions(builtin)


def locate_file(start_path: Text, file_name: Text) -> Text:
    """
        定位文件名并返回文件绝对路径.
        向上递归搜索，指定系统根路径
    Args:
        file_name (str): target locate file name
        start_path (str): start locating path, maybe file path or directory path

    Returns:
        str: located file path. None if file not found.

    Raises:
        exceptions.FileNotFound: If failed to locate file.

    """
    if os.path.isfile(start_path):
        start_dir_path = os.path.dirname(start_path)
    elif os.path.isdir(start_path):
        start_dir_path = start_path
    else:
        raise exceptions.FileNotFound(f"invalid path: {start_path}")

    file_path = os.path.join(start_dir_path, file_name)
    if os.path.isfile(file_path):
        # ensure absolute
        return os.path.abspath(file_path)

    # system root dir
    # Windows, e.g. 'E:\\'
    # Linux/Darwin, '/'
    parent_dir = os.path.dirname(start_dir_path)
    if parent_dir == start_dir_path:
        raise exceptions.FileNotFound(f"{file_name} not found in {start_path}")

    # locate recursive upward
    return locate_file(parent_dir, file_name)


def locate_debugtalk_py(start_path: Text) -> Text:
    """ locate debugtalk.py file
    找到debugtalk.py 绝对路径
    Args:
        start_path (str): start locating path,
            maybe testcase file path or directory path

    Returns:
        str: debugtalk.py file path, None if not found

    """
    try:
        # locate debugtalk.py file.
        debugtalk_path = locate_file(start_path, "debugtalk.py")
    except exceptions.FileNotFound:
        debugtalk_path = None

    return debugtalk_path


def locate_project_root_directory(test_path: Text) -> Tuple[Text, Text]:
    """ locate debugtalk.py path as project root directory
    找到项目根目录路径， 和 debugtalk.py 的路径
    Args:
        test_path: specified testfile path

    Returns:
        (str, str): debugtalk.py path, project_root_directory

    """

    def prepare_path(path):
        if not os.path.exists(path):
            err_msg = f"path not exist: {path}"
            logger.error(err_msg)
            raise exceptions.FileNotFound(err_msg)

        if not os.path.isabs(path):
            path = os.path.join(os.getcwd(), path)

        return path

    test_path = prepare_path(test_path)

    # locate debugtalk.py file
    debugtalk_path = locate_debugtalk_py(test_path)

    if debugtalk_path:
        # The folder contains debugtalk.py will be treated as project RootDir.
        project_root_directory = os.path.dirname(debugtalk_path)
    else:
        # debugtalk.py not found, use os.getcwd() as project RootDir.
        project_root_directory = os.getcwd()

    return debugtalk_path, project_root_directory


def load_debugtalk_functions() -> Dict[Text, Callable]:
    """
        加载项目 debugtalk.py模块里的 functions
        debugtalk.py应该位于项目根目录

    Returns:
        dict: debugtalk module functions mapping
            {
                "func1_name": func1,
                "func2_name": func2
            }

    """
    # 加载 debugtalk.py模块
    try:
        # 动态导入包
        imported_module = importlib.import_module("debugtalk")
    except Exception as ex:
        logger.error(f"error occurred in debugtalk.py: {ex}")
        sys.exit(1)

    # 重新加载用于更新先前加载的module
    # 避免有修改的情况 重载包
    imported_module = importlib.reload(imported_module)
    # 返回方法字典
    return load_module_functions(imported_module)


def load_project_meta(test_path: Text, reload: bool = False) -> ProjectMeta:
    """ load testcases, .env, debugtalk.py functions.

        testcases folder is relative to project_root_directory
        by default, project_meta will be loaded only once, unless set reload to true.

    Args:
        test_path (str): test file/folder path, locate project RootDir from this path.
        reload: reload project meta if set true, default to false

    Returns:
        project loaded api/testcases definitions,
            environments and debugtalk.py functions.

    """
    global project_meta
    if project_meta and (not reload):
        return project_meta

    # 实例化
    project_meta = ProjectMeta()

    if not test_path:
        return project_meta

    debugtalk_path, project_root_directory = locate_project_root_directory(test_path)

    # 添加项目根目录到sys.path
    sys.path.insert(0, project_root_directory)

    # load .env file
    # NOTICE:
    # environment variable maybe loaded in debugtalk.py
    # thus .env file should be loaded before loading debugtalk.py
    dot_env_path = os.path.join(project_root_directory, ".env")
    dot_env = load_dot_env_file(dot_env_path)
    if dot_env:
        project_meta.env = dot_env
        project_meta.dot_env_path = dot_env_path

    if debugtalk_path:
        # load debugtalk.py functions
        debugtalk_functions = load_debugtalk_functions()
    else:
        debugtalk_functions = {}

    # 定位项目根目录 并 加载debugtalk.py的方法
    project_meta.RootDir = project_root_directory
    project_meta.functions = debugtalk_functions
    project_meta.debugtalk_path = debugtalk_path

    return project_meta


def convert_relative_project_root_dir(abs_path: Text) -> Text:
    """
        基于project_meta.RootDir，绝对路径转为相对(项目根目录)路径
    Args:
        abs_path: absolute path

    Returns: relative path based on project_meta.RootDir

    """
    _project_meta = load_project_meta(abs_path)
    if not abs_path.startswith(_project_meta.RootDir):
        raise exceptions.ParamsError(
            f"failed to convert absolute path to relative path based on project_meta.RootDir\n"
            f"abs_path: {abs_path}\n"
            f"project_meta.RootDir: {_project_meta.RootDir}"
        )

    # 核心代码，通过切片方式
    return abs_path[len(_project_meta.RootDir) + 1:]