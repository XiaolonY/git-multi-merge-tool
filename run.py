#-*- coding: UTF-8 -*-
#!/usr/bin/python3

import getopt
import os
import sys
import time

from git import repo
from git.repo import Repo
from gitdb.db import git
from gitdb.util import to_bin_sha

from repo_config import project_dict_list


def clone_repo(local_path, repo_url):
    """
    克隆工程到本地
    """
    if not os.path.exists(local_path) :
        Repo.clone_from(repo_url, to_path=local_path)

    repo = Repo(local_path)
    g = repo.git
    g.pull()
    return repo

def diff_repo(local_path, repo_url, from_branch, to_branch):
    repo = clone_repo(local_path, repo_url)
    g = repo.git
    g.pull()
    try:
        command = "origin/{}..origin/{}".format(to_branch, from_branch);
        r = g.log(command)
        return r != None and r != '', repo
    except Exception as e:
        return False, repo

def merge_repo(local_path, repo_url, from_branch, to_branch):
    diff, repo = diff_repo(local_path, repo_url, from_branch, to_branch)
    if not diff:
        return True
    g = repo.git
    g.checkout(to_branch)
    g.pull()

    bak_branch = to_branch + '_bak' + time.strftime('%Y%m%d', time.localtime(time.time()))
    delete_branch(repo, bak_branch)
    # 提交备份分支
    g.branch(bak_branch)
    g.checkout(bak_branch)
    g.push('origin', bak_branch)

    merge_branch = "origin/{}".format(from_branch)
    try:
        g.checkout(to_branch)
        g.pull()
        g.merge(merge_branch)
        g.push('origin', to_branch)
        return True
    except Exception as e:
        g.merge('--abort')
        delete_branch(repo, bak_branch)
        print('合并异常', e)
        return False

def delete_branch(repo, branch_name):
    g = repo.git
    try:
        g.branch('-D', branch_name)
    except Exception as e:
        print('删除{}本地分支异常'.format(branch_name))
    try:
        g.push('origin', '--delete', branch_name)
    except Exception as e:
        print('删除{}远程分支异常'.format(branch_name))

def push_repo(local_path, branch):
    """
    推送代码到git
    """
    if os.path.exists(local_path) :
        repo = Repo(local_path)
        g = repo.git
        g.checkout(branch)
        g.push('origin', branch)
        print('{} - {}代码推送成功'.format(local_path, branch))

def main(argv):
    command_info = '''
    run.py -f <from_branch> -t <to_branch> -o <option>
    ------------------------------------------
    -o <option>
        diff 差分分支差异
        init 初始化
        merge 合并差异分支
    '''
                        
    try:
        opts, args = getopt.getopt(argv,"hf:t:o:",["from_branch=","to_branch=","option="])
    except getopt.GetoptError:
        print(command_info)
        sys.exit(2)
    
    from_branch = ''
    to_branch = ''
    option = ''
    for opt, arg in opts:
        if opt == '-h':
            print(command_info)
            sys.exit()
        elif opt in ("-f", "--from_branch"):
            from_branch = arg
        elif opt in ("-t", "--to_branch"):
            to_branch = arg
        elif opt in ("-o", "--option"):
            option = arg
    
    option_list = ['diff', 'init', 'merge']
    if option == None or option == '':
        option = 'diff'
    else:
        if option not in option_list:
            print("无效option参数")
            sys.exit()

    if option != 'init':
        if from_branch == None or from_branch == '':
            print('未指定源分支')
            sys.exit()
        if to_branch == None or to_branch == '':
            print('未指定目标分支')
            sys.exit()

    handler_count = 0
    handler_total = len(project_dict_list)
    start_time = time.time()
    res_list = []
    for project_dict in project_dict_list:
        handler_count = handler_count + 1
        p = round(handler_count * 100 / handler_total)

        repo_path = project_dict['path'];
        repo_url = project_dict['repo'];
        temp_repo_path = os.path.join('repo', repo_path)
        if option == 'diff':
            r, repo = diff_repo(temp_repo_path, repo_url, from_branch, to_branch)
            if r:
                res_list.append(repo_path)
        elif option == 'init':
            clone_repo(temp_repo_path, repo_url)
        elif option == 'merge':
            r = merge_repo(temp_repo_path, repo_url, from_branch, to_branch)
            if not r:
                res_list.append(repo_path)
        
        print('{} 已处理完成'.format(repo_path))
        print('当前进度: {}%'.format(p))
    
    if option == 'diff':
        if len(res_list) > 0:
            print("存在差异的工程：\n", res_list)
        else:
            print("无差异")
    elif option == 'merge':
        if len(res_list) > 0:
            print("需要手动合并的工程：\n", res_list)
        else:
            print("全部合并完成")
    elif option == 'init':
        print('初始化完成')
    
    end_time = time.time()
    print('执行时间：%.8s s' % (end_time - start_time))


if __name__ == '__main__':
    main(sys.argv[1:])
