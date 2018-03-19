import shutil
from lxml import etree as ET
import difflib
import pandas as pd  # xlsx requires xlrd (pip install xlrd)
import os
import math

from parameters import column_infos_from_header


def isNan(value):
    return not isinstance(value, str) and math.isnan(value)


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


def row_to_field(base_name, row, column_info, default=None):
    column_names, various_names_to_tag = column_info
    data = row[1]
    base_name_dot = base_name + '.'
    titles = [name for name in column_names if (name == base_name or base_name_dot in name) and not isNan(data.loc[name])]
    if len(titles) == 0:
        return default
    elif len(titles) == 1:
        return titles[0]
    else:
        beginning_of_digits = len(base_name_dot)
        maxTitle = None
        maxValue = 0
        for title in titles:
            try:
                value = int(title[beginning_of_digits:])
            except ValueError:
                value = 0
            if value > maxValue:
                maxValue = value
                maxTitle = title
        return maxTitle


def columnBaseNamesFromColumnInfo(column_info):
    column_names, various_names_to_tag = column_info
    nameToBaseName = {
        name: name.split('.')[0]
        for name in column_names
    }
    baseNameToNames = {}
    for name, base_name in nameToBaseName.items():
        if base_name not in baseNameToNames:
            baseNameToNames[base_name] = [base_name]
        if not name in baseNameToNames[base_name]:
            baseNameToNames[base_name].append(name)
    return baseNameToNames, nameToBaseName


def convert_one_file(xlsx, column_info, input_path, output_path):
    column_names, various_names_to_tag = column_info
    filename = os.path.basename(input_path)  # extract the end of file path
    print('Processing {} ...'.format(filename))
    filename = os.path.splitext(filename)[0]  # remove the extension from the name
    result = sorted(xlsx.iterrows(),
                    key=lambda row: difflib.SequenceMatcher(None,
                        # row[1][column_names['original_title']], # uncomment this line and comment the next one to match files with main title instead of local name
                        row_to_field('titre', row, column_info, default='titre'),
                        filename).ratio(),
                    reverse=True  # see https://stackoverflow.com/a/17903726
                    # This might be a better approach: https://stackoverflow.com/a/36132391
                    )  # sort row of xlsx to get the row
    # which has the title closest to the filename
    row = result[0]
    song_id, song_data = row  # take the first (best) result

    # print('Selected XLSX row {} ({}): "{}"'.format(
    #     song_id, safe_value('work-number'), safe_value('work-title')
    # ))


    # update xml file
    tree = ET.parse(input_path)
    root = tree.getroot()

    work = safe_child(root, 'work')

    # convert legacy tag names into new tag names
    def convert_if_exist(parent, child_name, new_child_name):
        """
        """
        try:
            child = parent.find('./{}'.format(child_name))
        except KeyError:
            child = None

        if child is None:
            pass
        else:
            child.tag = new_child_name
        return child

    identification = safe_child(root, 'identification')
    for legacy_name, new_name in various_names_to_tag.items():
        convert_if_exist(work, legacy_name, new_name)
        convert_if_exist(identification, legacy_name, new_name)

    # fill tags with proper metadata, or with ' ' placeholder
    baseNameToNames, nameToBaseName = columnBaseNamesFromColumnInfo(column_info)
    for baseName in baseNameToNames:
        xml_elem = safe_child(identification, baseName)
        overloading_column_name = row_to_field(baseName, row,
                                               column_info, baseName)
        value = song_data[overloading_column_name]
        if not isinstance(value, str) and math.isnan(value):
            value = ' '
        xml_elem.text = str(value)


    # work_number = safe_child(work, 'work-number')
    # work_number.text = safe_value('work-number')
    # work_title = safe_child(work, 'work-title')
    # work_title.text = safe_value('work-title')
    #
    # identification = safe_child(root, 'identification')
    # find_or_create_with_values(identification, 'creator', {
    #     'composer': safe_value('composer'),
    #     'lyricist': safe_value('lyricist'),
    #     'arranger': safe_value('arranger'),
    # })
    #
    # rights = safe_child(identification, 'rights')
    # rights.text = safe_value('rights')

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



