import os
from importlib import import_module

import_list = [
    'pyrate-limiter'
]
# 判断依赖库是否安装,未安装则安装对应依赖库
sourcestr = "https://pypi.tuna.tsinghua.edu.cn/simple/"  # 镜像源


def GetPackage(PackageName):
    comand = "pip install " + PackageName + " -i " + sourcestr
    # 正在安装
    print("------------------正在安装" + str(PackageName) + " ----------------------")
    print(comand + "\n")
    os.system(comand)


for v in import_list:
    try:
        import_module(v)
    except ImportError:
        print("Not find " + v + " now install")
        GetPackage(v)


if __name__ == '__main__':
    for v in import_list:
        try:
            import_module(v)
        except ImportError:
            print("Not find " + v + " now install")
            GetPackage(v)

