import shutil

# if __name__ == '__main__':
#     shutil.copytree('D:\githubProjects\movie-bot-dev\mbot', 'D:\githubProjects\mr_plugins\mbot', symlinks=True)
#     shutil.copytree('D:\githubProjects\movie-bot-api\moviebotapi', 'D:\githubProjects\mr_plugins\movie-bot-api', symlinks=True)
#     # sock5()


if __name__ == '__main__':
    list = [
        {'count': 10, 'cn': True},
        {'count': 20, 'cn': False},
        {'count': 30, 'cn': True},
        {'count': 40, 'cn': True},
        {'count': 50, 'cn': False},
        {'count': 50, 'cn': False},
        {'count': 60, 'cn': False},
        {'count': 70, 'cn': True},
        {'count': 80, 'cn': False},
        {'count': 90, 'cn': True},
        {'count': 100, 'cn': False},
    ]
    sort_list = sorted(list, key=lambda x: x['count'], reverse=True)
    sort_list = sorted(sort_list, key=lambda x: x['cn'], reverse=True)
    print(sort_list)
