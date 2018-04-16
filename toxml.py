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
        child.set('name', key)
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
                        str(row[1][tagNameToColumnIndex['workTitle']]),
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
    scoreElem = safe_child(rootElem, 'Score')

    def safeValue(tagName):
        """Deals with unset columns, resulting in NaN values"""
        value = rowData[tagNameToColumnIndex[tagName]]
        if not isinstance(value, str) and math.isnan(value):
            value = ' '
        return str(value)

    for tagName in sorted(tagNameToColumnIndex.keys()):
        find_or_create_with_values(scoreElem, 'metaTag', {
            tagName: safeValue(tagName),
        })


def injectTextField(xmlTree, rowData, textFieldNameToColumnIndex):
    pass
