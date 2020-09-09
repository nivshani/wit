# Upload 177
from datetime import datetime
import os
import random
import shutil
import sys

from graphviz import Digraph


class witNotFound(Exception):
    'raised wen .wit not found'
    def __str__(self):
        return '.wit not found'


def init():
    path = os.getcwd()
    path = os.path.join(path, '.wit')
    try:
        os.makedirs(path)
    except OSError:
        print('Usage: python <filename> <param1> <param2> [...]')
    else:
        os.makedirs(os.path.join(path, 'images'))
        os.makedirs(os.path.join(path, 'staging_area'))
        set_active_branch('master')
        with open(os.path.join(path, 'references.txt'), 'w') as f:  # just craete the file for later
            f.write('Head=None\nmaster=0\n')


def add(path):
    if path == os.getcwd() or not os.path.exists(os.path.join(os.getcwd(), path)):
        print('failed')
        return
    loc = folder_creator(path)
    loc = os.path.join(loc, os.path.split(path)[1])
    if os.path.isdir(path):
        if os.path.exists(loc):
            shutil.rmtree(loc)
        shutil.copytree(path, loc)
    else:
        if os.path.exists(os.path.join(loc, os.path.split(path)[1])):
            os.remove(os.path.join(loc, os.path.split(path)[1]))
        shutil.copy2(path, loc)


def commit(nearest_wit, message=None):
    path_to_images = os.path.join(nearest_wit, 'images')
    commit_id = get_random_alphanumeric_string()
    os.makedirs(os.path.join(path_to_images, commit_id))
    parent = last_commit()
    with open(os.path.join(path_to_images, f'{commit_id}.txt'), 'w') as f:
        f.write(f'parent={parent} \ndate={datetime.now()} \nmessage={message}')
    for file in os.listdir(os.path.join(nearest_wit, 'staging_area')):
        file_path = os.path.join(nearest_wit, 'staging_area', file)
        if os.path.isdir(file_path):
            shutil.copytree(file_path, os.path.join(path_to_images, commit_id, file))
        else:
            shutil.copy2(file_path, os.path.join(path_to_images, commit_id))
    master = get_master()
    if all_branches()[get_active_branch()] == parent:
        edit_branch(get_active_branch(), commit_id)
        if master == parent or master == '0':
            master = commit_id
    if master == '0':
        master = commit_id
    with open(os.path.join(nearest_wit, 'references.txt'), 'r+') as f:
        f.write(f'HEAD={commit_id}\nmaster={master}\n')


def last_commit():
    nearest_wit = find_nearest_wit()
    try:
        with open(os.path.join(nearest_wit, 'references.txt'), 'r') as f:
            file = f.readlines()
    except (OSError, IndexError):
        parent = 'None'
    else:
        parent = file[0].split('=')[1].strip()
    return parent


def get_master():
    nearest_wit = find_nearest_wit()
    try:
        with open(os.path.join(nearest_wit, 'references.txt'), 'r') as f:
            file = f.readlines()
    except (OSError, IndexError):
        print('no master found')
        master = 0
    else:
        master = file[1].split('=')[1].strip()
    return master


def status():
    print('commit id:', last_commit())
    print('changes_to_be_comited:', *changes_to_be_comited())
    print('changes_not_stage_for_commit:', *changes_not_stage_for_commit())
    print('untracked_files:', *untracked_files())


def changes_to_be_comited():
    head = last_commit()
    changes_to_be_comited = []
    files_in_staging = [file.split('staging_area')[-1].strip(os.sep) for file in all_files_in_folder(os.path.join(nearest_wit, 'staging_area'))]
    files_in_images = [file.split(head)[-1].strip(os.sep) for file in all_files_in_folder(os.path.join(nearest_wit, 'images', head))]
    for file in files_in_staging:
        change_time = os.path.getmtime(os.path.join(nearest_wit, 'staging_area', file))
        if file not in files_in_images:
            changes_to_be_comited.append(file)
        else:
            change_time_2 = os.path.getmtime(os.path.join(nearest_wit, 'images', head, file))
            if change_time != change_time_2:
                changes_to_be_comited.append(file)
    return changes_to_be_comited


def changes_not_stage_for_commit():
    changes_not_stage_for_commit = []
    reg_path = os.path.dirname(nearest_wit)
    files_in_staging = [file.split('staging_area')[-1].strip(os.sep) for file in all_files_in_folder(os.path.join(nearest_wit, 'staging_area'))]
    for file in files_in_staging:
        change_time = os.path.getmtime(os.path.join(nearest_wit, 'staging_area', file))
        if change_time != os.path.getmtime(os.path.join(reg_path, file)):
            changes_not_stage_for_commit.append(file)
    return changes_not_stage_for_commit


def untracked_files():
    untracked_files = []
    reg_path = os.path.dirname(nearest_wit)
    all_files = [file.split(os.path.split(reg_path)[1])[-1].strip(os.sep) for file in all_files_in_folder(reg_path) if '.wit' not in file]
    for file in all_files:
        if not os.path.exists(os.path.join(nearest_wit, 'staging_area', file)):
                untracked_files.append(file)
    return untracked_files


def all_files_in_folder(path):
    files = []
    for file in os.listdir(path):
        path_to_file = os.path.join(path, file)
        if os.path.isdir(path_to_file):
            files.extend(all_files_in_folder(path_to_file))
        else:
            files.append(path_to_file)
    return files


def folder_creator(path):
    nearest_wit = find_nearest_wit()
    path_to_check = os.path.join(nearest_wit, 'staging_area')
    files = os.listdir(path_to_check)
    path = os.path.abspath(path)[len(os.path.dirname(nearest_wit)) + 1:]
    for folder in path.split(os.sep)[:-1]:
        if folder not in files:
            os.makedirs(os.path.join(path_to_check, folder))
        path_to_check = os.path.join(path_to_check, folder)
        files = os.listdir(path_to_check)
    return path_to_check


def find_nearest_wit():
    working_file = os.getcwd()
    nearest_wit = working_file
    while True:
        if nearest_wit == os.path.join(os.path.splitdrive(working_file)[0], os.sep):
            raise witNotFound
        if '.wit' in os.listdir(nearest_wit):
            nearest_wit = os.path.join(nearest_wit, '.wit')
            return nearest_wit
        else:
            nearest_wit = os.path.dirname(nearest_wit)


def get_random_alphanumeric_string():
    to_choose = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
    result_str = ''.join((random.choice(to_choose) for i in range(40)))
    return result_str


def checkout(nearest_wit, commit_id):
    working_folder = os.path.dirname(nearest_wit)
    untracked = untracked_files()
    master = get_master()
    branches = all_branches()
    if commit_id == 'master':
        commit_id = master
    if commit_id in branches:
        set_active_branch(commit_id)
        commit_id = branches[commit_id]
    else:
        set_active_branch('master')
    commit_folder = os.path.join(nearest_wit, 'images', commit_id)
    if len(changes_not_stage_for_commit()) != 0 or len(changes_to_be_comited()) != 0 or not os.path.exists(commit_folder):
        print('failed')
        return
    commit_files = [file.split(commit_id)[-1].strip(os.sep) for file in all_files_in_folder(commit_folder) if file.split(commit_id)[-1] not in untracked]
    for file in commit_files:
        loc = os.path.join(commit_folder, file)
        des = os.path.join(working_folder, os.path.dirname(file))
        if os.path.exists(os.path.join(working_folder, file)):
            os.remove(os.path.join(working_folder, file))
        shutil.copy2(loc, des)
    print('success')
    with open(os.path.join(nearest_wit, 'references.txt'), 'r+') as f:
        f.write(f'HEAD={commit_id}\nmaster={master}\n')
    print(f'current id {commit_id}')
    shutil.rmtree(os.path.join(nearest_wit, 'staging_area'))
    shutil.copytree(commit_folder, os.path.join(nearest_wit, 'staging_area'))


def all_parents(commit_id):
    parents = []
    parents.append(commit_id)
    parent = get_perent(commit_id)
    for p in parent:
        parents.extend(all_parents(p))
    return parents


def branch(nearest_wit, name):
    with open(os.path.join(nearest_wit, 'references.txt'), 'a') as f:
        f.write(f'{name}={last_commit()}\n')


def all_branches():
    with open(os.path.join(find_nearest_wit(), 'references.txt'), 'r') as f:
        file = f.readlines()
    return {branch.split('=')[0]: branch.split('=')[1].strip() for branch in file[1:]}


def set_active_branch(branch_name):
    with open(os.path.join(find_nearest_wit(), 'activated.txt'), 'w') as f:
        f.write(branch_name)


def get_active_branch():
    with open(os.path.join(find_nearest_wit(), 'activated.txt'), 'r') as f:
        branch = f.readline()
    return branch


def edit_branch(branch_name, new_id):
    with open(os.path.join(find_nearest_wit(), 'references.txt'), 'r+') as f:
        file = f.readlines()
        new_file = []
        for line in file:
            if line.split('=')[0] == branch_name:
                new_file.append(line.split('=')[0] + f'={new_id}\n')
            else:
                new_file.append(line)
        f.seek(0)
        f.write(''.join(new_file))


def merge(nearest_wit, branch_to_merge):
    branches = all_branches()
    head = last_commit()
    if branch_to_merge not in branches:
        print('not valid branch')
        return
    base_id = find_common_base(head, branches[branch_to_merge])
    to_copy = updated_files_for_merge(base_id, branches[branch_to_merge])
    to_copy.extend(updated_files_for_merge(base_id, head))
    to_copy = set(to_copy)
    commit_id = get_random_alphanumeric_string()
    parent = head + ',' + branches[branch_to_merge]
    path_to_new_commit = os.path.join(nearest_wit, 'images', commit_id)
    with open(path_to_new_commit + '.txt', 'w') as f:
        f.write(f'parent={parent} \ndate={datetime.now()} \nmessage=merge')
    for file in to_copy:
        loc = os.path.join(path_to_new_commit, f'{os.sep}'.join(file.split(os.sep)[len(path_to_new_commit.split(os.sep)):]))
        try:
            os.makedirs(os.path.split(loc)[0])
        except FileExistsError:
            pass
        finally:
            shutil.copy2(file, loc)
    shutil.rmtree(os.path.join(nearest_wit, 'staging_area'))
    shutil.copytree(path_to_new_commit, os.path.join(nearest_wit, 'staging_area'))
    with open(os.path.join(nearest_wit, 'references.txt'), 'r+') as f:
        f.write(f'HEAD={commit_id}\nmaster={get_master()}\n')
    edit_branch(get_active_branch(), commit_id)


def updated_files_for_merge(base, branch_or_head):
    to_copy = all_files_in_folder(os.path.join(nearest_wit, 'images', base))
    branch_or_head_files = all_files_in_folder(os.path.join(nearest_wit, 'images', branch_or_head))
    for file in branch_or_head_files:
        file_to_check = file.split(branch_or_head)[1].strip(os.sep)
        path_to_check = os.path.join(nearest_wit, 'images', base, file_to_check)
        if os.path.exists(path_to_check):
            if os.path.getmtime(path_to_check) < os.path.getmtime(file):
                to_copy.remove(path_to_check)
                to_copy.append(file)
    return to_copy


def find_common_base(id1, id2):
    id1_parents = all_parents(id1)
    id2_parents = all_parents(id2)
    for parent in id1_parents:
        if parent in id2_parents:
            return parent


def graph(nearest_wit):
    g = Digraph(strict=True)  # strict prevent duplication
    draw_commit(g, last_commit())
    g.node('head', 'head', shape='plaintext')
    g.edge('head', last_commit())
    g.view()


def draw_commit(g, commit_id):
    if commit_id == get_master():
        g.node('master', 'master', shape='plaintext')
        g.edge('master', commit_id)
    g.node(commit_id, commit_id, shape='circle')
    for p in get_perent(commit_id):
        p_node = draw_commit(g, p)
        g.edge(commit_id, p_node)
    return commit_id


def get_perent(commit_id):
    with open(os.path.join(find_nearest_wit(), 'images', f'{commit_id}.txt'), 'r') as f:
        file = f.readlines()
    parents = file[0].split('=')[1].strip()
    if parents == 'None':
        return []
    return parents.split(',')


if len(sys.argv) > 1:
    if sys.argv[1] == 'init':
        init()

    elif sys.argv[1] == 'add':
        add(sys.argv[2])

    elif sys.argv[1] == 'commit':
        nearest_wit = find_nearest_wit()
        if len(sys.argv) >= 3:
            commit(nearest_wit, sys.argv[2])
        else:
            commit(nearest_wit)

    elif sys.argv[1] == 'status':
        nearest_wit = find_nearest_wit()
        status()

    elif sys.argv[1] == 'checkout':
        nearest_wit = find_nearest_wit()
        if len(sys.argv) >= 3:
            checkout(nearest_wit, sys.argv[2])
        else:
            print("plese enter commit id")

    elif sys.argv[1] == 'graph':
        nearest_wit = find_nearest_wit()
        graph(nearest_wit)

    elif sys.argv[1] == 'branch':
        nearest_wit = find_nearest_wit()
        if len(sys.argv) >= 3:
            branch(nearest_wit, sys.argv[2])

    elif sys.argv[1] == 'merge':
        nearest_wit = find_nearest_wit()
        if len(sys.argv) >= 3:
            merge(nearest_wit, sys.argv[2])