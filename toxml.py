import shutil
from lxml import etree as ET
import difflib
import pandas as pd  # xlsx requires xlrd (pip install xlrd)
import os
import math

from parameters import columns_names


def safe_child(parent, child_name):
    """
    :rtype: object: the child of a parent if it exists, a new one otherwise
    """
    child = parent.find('./{}'.format(child_name))
    if child is None:
        child = ET.SubElement(parent, child_name)
    return child


def find_or_create_with_values(parent, children_tag_names, attr_to_text):
    """Find children of the given parent having the proper tag.
    For each attribute from attr_to_text, find a child and set its text,
    or create a new child.
    :param parent: the parent xml tag
    :param children_tag_names: tag of the children to be found in the parent
    :param attr_to_text: a Dict<string, string> mapping tag attribute names
    to the value of the text"""
    already_handled_keys = []
    for child in parent.findall('./{}'.format(children_tag_names)):
        same_key = set(attr_to_text.keys()).intersection(set(child.attrib.values()))
        if same_key:
            child.text = attr_to_text[next(iter(same_key))]

    not_yet_handled = set(attr_to_text.keys()).difference(set(already_handled_keys))
    for key in not_yet_handled:
        child = ET.SubElement(parent, children_tag_names)
        child.set(key, key)
        child.text = attr_to_text[key]


def convert_one_file(xlsx, input_path, output_path):
    filename = os.path.basename(input_path)  # extract the end of file path
    print('Processing {} ...'.format(filename))
    filename = os.path.splitext(filename)[0]  # remove the extension from the name
    result = sorted(xlsx.iterrows(),
                    key=lambda row: difflib.SequenceMatcher(None, row[1][
                        columns_names['original_title']], filename).ratio(),
                    reverse=True  # see https://stackoverflow.com/a/17903726
                    # This might be a better approach: https://stackoverflow.com/a/36132391
                    )  # sort row of xlsx to get the row
    # which has the title closest to the filename

    song_id, song_data = result[0]  # take the first (best) result

    def safe_value(key):
        """Deals with unset columns, resulting in NaN values"""
        value = song_data[columns_names[key]]
        if not isinstance(value, str) and math.isnan(value):
            value = ' '  # TODO: make sure this placeholder is a good idea
        return str(value)

    print('Selected XLSX row {} ({}): "{}"'.format(
        song_id, safe_value('work-number'), safe_value('work-title')
    ))


    # update xml file
    tree = ET.parse(input_path)
    root = tree.getroot()

    work = safe_child(root, 'work')
    work_number = safe_child(work, 'work-number')
    work_number.text = safe_value('work-number')
    work_title = safe_child(work, 'work-title')
    work_title.text = safe_value('work-title')

    identification = safe_child(root, 'identification')
    find_or_create_with_values(identification, 'creator', {
        'composer': safe_value('composer'),
        'lyricist': safe_value('lyricist'),
        'arranger': safe_value('arranger'),
    })

    rights = safe_child(identification, 'rights')
    rights.text = safe_value('rights')

    # Save the result to a file
    tree.write(output_path)


if __name__ == '__main__':
    frozen_sib2muse_simple_path = '/Users/matthieu/Documents/perso/GCN/friday/test Matthieu/Allez, Dieu vous envoie Brut A4 Sib7 importé dans MuseScore puis exporté en XML.xml'
    tmp_sib2muse_simple_path = 'sib2muse_simple.xml'
    shutil.copyfile(frozen_sib2muse_simple_path, tmp_sib2muse_simple_path)

    # find data in xlsx
    xlsx_path = '/Users/matthieu/Documents/perso/GCN/dimanche/MetadonneesCARNET_ORANGE_2017etLiturgie2018.xlsx'
    xlsx = pd.read_excel(xlsx_path, skiprows=1)
    # for row_id, row_values in xlsx.iterrows():
    #     print(row_values['Par Défaut'])
    # for filename in [
    #     "Allez, Dieu vous envoie Brut.xml",
    #     "Allez, Dieu vous envoie.xml",
    #     'Allez, Dieu vous envoie Brut A4 Sib7 importé dans MuseScore puis exporté en XML.xml',
    #     'Que le Seigneur nous benisse.xml',
    #     'que le Seigneur nous benisse.xml',
    # ]:
    #     filename = os.path.splitext(filename)[0]
    #     res = sorted(xlsx.iterrows(), key=lambda row: difflib.SequenceMatcher(None, row[1]['Par Défaut'], filename).ratio(),
    #            reverse=True)  # see https://stackoverflow.com/a/17903726
    #     print('\n'.join([row[1]['Par Défaut'] for row in res[:3]]))
    #     print()
    filename = os.path.basename(frozen_sib2muse_simple_path)  # extract the end of file path
    filename = os.path.splitext(filename)[0]  # remove the extension from the name
    result = sorted(xlsx.iterrows(),
                    key=lambda row: difflib.SequenceMatcher(None, row[1][
                        columns_names['original_title']], filename).ratio(),
                    reverse=True  # see https://stackoverflow.com/a/17903726
                    # This might be a better approach: https://stackoverflow.com/a/36132391
                    )  # sort row of xlsx to get the row
    # which has the title closest to the filename

    song_id, song_data = result[0]  # take the first (best) result


    def safe_value(key):
        """Deals with unset columns, resulting in NaN values"""
        value = song_data[columns_names[key]]
        if not isinstance(value, str) and math.isnan(value):
            value = ' '  # TODO: make sure this placeholder is a good idea
        return str(value)

    # update xml file
    tree = ET.parse(tmp_sib2muse_simple_path)
    root = tree.getroot()

    work = safe_child(root, 'work')
    work_number = safe_child(work, 'work-number')
    work_number.text = safe_value('work-number')
    work_title = safe_child(work, 'work-title')
    work_title.text = safe_value('work-title')

    identification = safe_child(root, 'identification')
    find_or_create_with_values(identification, 'creator', {
        'composer': safe_value('composer'),
        'lyricist': safe_value('lyricist'),
        'arranger': safe_value('arranger'),
    })

    rights = safe_child(identification, 'rights')
    rights.text = safe_value('rights')

    # Save the result to a file
    tree.write(tmp_sib2muse_simple_path)
    # Another way of writing the new content to a file:
    # with open(tmp_sib2muse_simple_path, 'w') as file_handle:
    #     file_handle.write(
    #         ET.tostring(tree, pretty_print=True, encoding='utf8').decode('utf8'))



