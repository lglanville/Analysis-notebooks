import os
import bagit
import sys
import shutil
import csv


def filter_info(info):
    new = {}
    k = [
        'identifier', 'carrier', 'Bag-Software-Agent', 'Bagging-Date',
        'Payload-Oxum', 'title']
    for key, value in info.items():
        if key in k:
            new[key] = value
    return(new)


def find_droid(directory):
    for file in os.listdir(directory):
        if file.endswith('droid.csv'):
            with open(os.path.join(directory, file), encoding='utf-8') as f:
                droid = csv.DictReader(f.readlines())
                d = list(droid)
                return(d)


def path_to_uri(path):
    uri = 'file:/'+path.replace('\\', '/')
    return uri


def strip_manifests(bag):
    bagname = os.path.split(bag.path)[1]
    sub = os.path.join(
        bag.path,
        'data/metadata/submissionDocumentation')
    entries = bag.payload_entries()
    droid = find_droid(sub)
    id_map = {}
    man_lines = {alg: [] for alg in bag.algorithms}
    for line in droid:
        if line['FILE_PATH'] != '':
            hashes = entries.get(
                os.path.normpath('data'+line['FILE_PATH'].split('data')[1]))
            if line['PARENT_ID'] == '':
                path = os.path.normpath(
                    f'/corpus/{bagname}/data/{line["TYPE"]}_{line["ID"]}')
                line['URI'] = path_to_uri(path)
                line['FILE_PATH'] = path
                line['NAME'] = f'{line["TYPE"]}_{line["ID"]}'
                id_map[line['ID']] = path
            else:
                path = os.path.join(
                    id_map[line['PARENT_ID']], f'{line["TYPE"]}_{line["ID"]}')
                line['FILE_PATH'] = path
                line['URI'] = path_to_uri(path)
                line['NAME'] = f'{line["TYPE"]}_{line["ID"]}'
                id_map[line['ID']] = path
            if hashes is not None:
                for alg, hash in hashes.items():
                    man_lines[alg].append(
                        f'{hash}  {"data"+path.split("data")[1]}\n')
    return droid, man_lines


for root, _, files in os.walk(sys.argv[1]):
    for file in files:
        if file == 'bagit.txt':
            obj = os.path.join(root, 'data/objects')
            if os.listdir(obj) != []:
                b = bagit.Bag(root)
                target = os.path.join(sys.argv[2], os.path.split(root)[1])
                os.mkdir(target)
                shutil.copy(os.path.join(root, 'bag-info.txt'), target)
                shutil.copy(os.path.join(root, 'bagit.txt'), target)
                droid, man_lines = strip_manifests(b)
                d_name = os.path.join(target, 'droid.csv')
                with open(d_name, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=droid[1].keys())
                    writer.writeheader()
                    writer.writerows(droid)
                for alg, lines in man_lines.items():
                    man_name = os.path.join(target, f'manifest-{alg}.txt')
                    with open(man_name, 'w', encoding='utf-8') as f:
                        lines = set(lines)
                        f.writelines(lines)
                btwo = bagit.Bag(target)
                btwo.info = filter_info(btwo.info)
                btwo.save()
