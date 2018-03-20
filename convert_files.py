import argparse
import os
import pandas as pd
from lxml import etree as ET

from toxml import findBestMatchingRow, injectMetadata, \
    injectTextField


def convert(args):
    args.input_directory = os.path.abspath(args.input_directory)
    args.output_directory = os.path.abspath(args.output_directory)

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    xlsx = pd.read_excel(args.xlsx_path, header=None)
    columnIndexToTagName = {columnIndex: tagName for columnIndex, tagName in xlsx.iloc[0].items() if isinstance(tagName, str)}
    tagNameToColumnIndex = {value: key for key, value in columnIndexToTagName.items()}
    columnIndexToTextFieldName = {columnIndex: tagName for columnIndex, tagName in xlsx.iloc[1].items() if isinstance(tagName, str)}
    textFieldNameToColumnIndex = {value: key for key, value in columnIndexToTextFieldName.items()}
    data = xlsx[4:]

    xlm_filenames = [filename
                 for filename in os.listdir(args.input_directory)
                 if os.path.splitext(filename)[-1].lower() == '.xml']

    print('Processing files from directory "{}" into directory "{}".'.format(
        args.input_directory,
        args.output_directory
    ))
    for filename in xlm_filenames:
        print('\nProcessing file "{}" ...'.format(filename))
        rowId, rowData = findBestMatchingRow(filename, data, tagNameToColumnIndex)
        inputPath = os.path.join(args.input_directory, filename)
        outputPath = os.path.join(args.output_directory,
                                  os.path.basename(filename))
        xmlTree = ET.parse(inputPath)
        injectMetadata(xmlTree, rowData, tagNameToColumnIndex)
        injectTextField(xmlTree, rowData, textFieldNameToColumnIndex)
        xmlTree.write(outputPath)

    print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update XML song files '
                                                 'with metadata '
                                                 'from XLSX file')
    parser.add_argument('--input_directory', type=str, default='./input',
                        help='Directory path containing XML files to convert')
    parser.add_argument('--xlsx_path', type=str,
                        default='./metadata_v15.xlsx',
                        # default='./metadata_tel_train.xlsx',
                        help='Path to the XLSX file containing metadata about '
                             'songs')
    parser.add_argument('--output_directory', type=str, default='./output',
                        help='Directory path where to store the new XML files')
    args = parser.parse_args()
    convert(args)
