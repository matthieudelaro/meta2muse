# -*- coding: utf-8 -*-
from datetime import datetime
from collections import OrderedDict

from logger import print
import os
import pandas as pd

import toxml

filenameToData = {}
tagNameToColumnIndex = None
LOGS='logs'
ROW_DATA='ROW_DATA'
ID_TAG='ID'
WORK_TITLE_TAG='workTitle'
TITRE_ORIGINAL_TAG='titre_original'
ROW_ID='ROW_ID'
SEPARATOR_COLUMN_NAME = '>> info >>'
FILTER_NAME='FILTER_NAME'
FILENAME='filename'
DEFAULT_FILTERNAME=WORK_TITLE_TAG
FILTER_NAME_VALUE=DEFAULT_FILTERNAME


def load(args):
    global filenameToData
    global FILTER_NAME_VALUE
    try:
        xlsx_filepath = os.path.abspath(
            os.path.join(args.parameters_directory, 'mapping.xlsx'))
        xlsx = pd.read_excel(xlsx_filepath, header=None)
        columnIndexToTagName = {columnIndex: tagName for columnIndex, tagName in
                                xlsx.iloc[0].items() if
                                isinstance(tagName, str)}
        tagNameToColumnIndex = {value: key for key, value in
                                columnIndexToTagName.items()}
        columnIndexToTextFieldName = {columnIndex: tagName for
                                      columnIndex, tagName in
                                      xlsx.iloc[1].items() if
                                      isinstance(tagName, str)}
        textFieldNameToColumnIndex = {value: key for key, value in
                                      columnIndexToTextFieldName.items()}
        FILTER_NAME_VALUE = columnIndexToTagName[2]
        data = xlsx[1:]
        for rowId, rowData in data.iterrows():
            filename = rowData[tagNameToColumnIndex[FILENAME]]
            fileData = {
                FILENAME: filename,
                FILTER_NAME_VALUE: rowData[tagNameToColumnIndex[FILTER_NAME_VALUE]],
            }
            filenameToData[filename] = fileData
    except FileNotFoundError as e:
        filenameToData = {}


def checkFile(filename, data, tagNameToColumnIndexParam):
    global filenameToData
    global tagNameToColumnIndex
    tagNameToColumnIndex = tagNameToColumnIndexParam
    if not filename in filenameToData:
        rowId, rowData = toxml.findBestMatchingRow(filename, data, tagNameToColumnIndex)
        fileData = {
            FILENAME: filename,
            FILTER_NAME_VALUE: rowData[tagNameToColumnIndex[FILTER_NAME_VALUE]],
        }
        filenameToData[filename] = fileData
        print('Added mapping {} => {} ({})'.format(
            filename,
            rowData[tagNameToColumnIndex[FILTER_NAME_VALUE]],
            rowData[tagNameToColumnIndex[TITRE_ORIGINAL_TAG]],
        ))

    fileData = filenameToData[filename]
    searchResult = data.loc[
        data[tagNameToColumnIndex[FILTER_NAME_VALUE]] ==
        fileData[FILTER_NAME_VALUE]
        ]
    fileData[LOGS] = ''
    if len(searchResult) == 0:
        fileData[LOGS] += 'Could not find metadata with mapping. ' \
                          'Searching anew...!\n'
        rowId, rowData = toxml.findBestMatchingRow(filename, data,
                                                   tagNameToColumnIndex)
    else:
        rowId, rowData = next(searchResult.iterrows())
    if len(searchResult) != 1:
        fileData[LOGS] += 'Found {} rows in metadata. Taking {}' \
                          '\n'.format(len(searchResult), rowId)
    fileData[ROW_DATA] = rowData
    fileData[ROW_ID] = rowId
    return fileData


def persist(args):
    global filenameToData
    global tagNameToColumnIndex
    outputPath = os.path.abspath(
            os.path.join(args.parameters_directory,
                         'auto_generated_mapping_{}.xlsx'.format(str(datetime.now()).replace(':', '_'))))

    rows = []
    for filename, fileData in filenameToData.items():
        row = OrderedDict()
        row[FILENAME] = filename
        try:
            row[FILTER_NAME_VALUE] = fileData[ROW_DATA][tagNameToColumnIndex[FILTER_NAME_VALUE]]
        except KeyError:
            try:
                row[FILTER_NAME_VALUE] = fileData[FILTER_NAME_VALUE]
            except KeyError:
                row[FILTER_NAME_VALUE] = ''
        row[SEPARATOR_COLUMN_NAME] = ' _ => _ '
        try:
            row[ID_TAG] = fileData[ROW_DATA][tagNameToColumnIndex[ID_TAG]]
        except KeyError:
            row[ID_TAG] = ''
        try:
            row[ROW_ID] = fileData[ROW_ID]
        except KeyError:
            row[ROW_ID] = ''
        try:
            row[TITRE_ORIGINAL_TAG] = fileData[ROW_DATA][tagNameToColumnIndex[TITRE_ORIGINAL_TAG]]
        except KeyError:
            row[TITRE_ORIGINAL_TAG] = ''
        try:
            row[LOGS] = fileData[LOGS]
        except KeyError:
            row[LOGS] = 'Could not find data about this file\n'
        rows.append(row)
    dataframe = pd.DataFrame.from_records(rows)
    with pd.ExcelWriter(outputPath) as writer:
        dataframe.to_excel(writer, 'mapping')
    return outputPath
