import shutil
from lxml import etree as ET
import difflib
import pandas as pd  # xlsx requires xlrd (pip install xlrd)
import os
import math


def safe_child(parent, child_name, rightAfterElem=None, rightBeforeElem=None,
               appendFront=False, forceNew=False):
    """
    :rtype: object: the child of a parent if it exists, a new one otherwise
    """
    child = None
    if not forceNew:
        child = parent.find('./{}'.format(child_name))
    if child is None:
        child = ET.Element(child_name)
        if rightAfterElem is not None:  # cf https://stackoverflow.com/a/7475897
            # contentnav = tree.find(".//div[@id='content_nav']")
            # parent = rightAfterElem.getparent()
            parent.insert(parent.index(rightAfterElem) + 1, child)
        elif rightBeforeElem is not None:
            parent.insert(parent.index(rightBeforeElem), child)
        elif appendFront:
            parent.insert(0, child)
        else:
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
        # child = ET.SubElement(parent, children_tag_names)
        child = safe_child(parent, children_tag_names, appendFront=True, forceNew=True)
        child.set('type', key)
        child.text = attr_to_text[key]


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


def findBestMatchingRow(filename, data, tagNameToColumnIndex):
    search_results = sorted(data.iterrows(),
                    key=lambda row: difflib.SequenceMatcher(None,
                        row[1][tagNameToColumnIndex['workTitle']],
                        filename).ratio(),
                    reverse=True  # see https://stackoverflow.com/a/17903726
                    # This might be a better approach: https://stackoverflow.com/a/36132391
                    )  # sort row of xlsx to get the row

    selection = search_results[0]
    print('Selected XLSX row {}: "{}"'.format(
        selection[0], selection[1][tagNameToColumnIndex['workTitle']]
    ))
    return selection


def injectMetadata(xmlTree, rowData, tagNameToColumnIndex):
    rootElem = xmlTree.getroot()
    workElem = safe_child(rootElem, 'work')
    identificationElem = safe_child(rootElem, 'identification')
    encodingElem = safe_child(identificationElem, 'encoding')

    def safeValue(tagName):
        """Deals with unset columns, resulting in NaN values"""
        value = rowData[tagNameToColumnIndex[tagName]]
        if not isinstance(value, str) and math.isnan(value):
            value = ' '  # TODO: make sure this placeholder is a good idea
        return str(value)

    for tagName in sorted(tagNameToColumnIndex.keys()):
        if tagName in ['creationDate', 'originalFormat', 'platform']:
            print('Warning: tag "{}" will be lost when importing '
                  'to MuseScore'.format(tagName))
        elif tagName == 'arranger':
            find_or_create_with_values(identificationElem, 'creator', {
                'arranger': safeValue('arranger'),
            })
        elif tagName == 'workTitle':
            elem = safe_child(workElem, 'work-title')
            elem.text = safeValue(tagName)
        elif tagName == 'workNumber':
            elem = safe_child(workElem, 'work-number', appendFront=True)
            elem.text = safeValue(tagName)
        elif tagName == 'composer':
            find_or_create_with_values(identificationElem, 'creator', {
                'composer': safeValue('composer'),
            })
        elif tagName == 'copyright':
            elem = safe_child(identificationElem, 'rights')
            elem.text = safeValue(tagName)
        elif tagName == 'lyricist':
            find_or_create_with_values(identificationElem, 'creator', {
                'lyricist': safeValue('lyricist'),
            })
        elif tagName == 'movementNumber':
            elem = safe_child(rootElem, 'movement-number', rightAfterElem=workElem)
            elem.text = safeValue(tagName)
        elif tagName == 'movementTitle':
            elem = safe_child(rootElem, 'movement-title', rightBeforeElem=identificationElem)
            elem.text = safeValue(tagName)
        elif tagName == 'poet':
            find_or_create_with_values(identificationElem, 'creator', {
                'poet': safeValue('poet'),
            })
        elif tagName == 'source':
            elem = safe_child(identificationElem, 'source', rightAfterElem=encodingElem)
            elem.text = safeValue(tagName)
        elif tagName == 'translator':
            find_or_create_with_values(identificationElem, 'creator', {
                'translator': safeValue('translator'),
            })
        else:
            print('Warning: tag {} is unknown.'.format(tagName))


def injectTextField(xmlTree, rowData, textFieldNameToColumnIndex):
    pass


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



