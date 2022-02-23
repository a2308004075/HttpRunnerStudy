from httprunner.cli import main

"""
(1) 如果你希望 python 将一个文件夹作为 Package 对待，那么这个文件夹中必须包含一个名为 __init__.py 的文件，即使它是空的。

(2) 如果你需要 python 将一个文件夹作为 Package 执行，那么这个文件夹中必须包含一个名为 __main__.py 的文件。

参考：https://www.cnblogs.com/dangkai/p/10758056.html
执行方式  python httprunner  或 python -m httprunner
"""
if __name__ == "__main__":
    main()
