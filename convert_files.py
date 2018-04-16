import argparse
import os
import pandas as pd
from lxml import etree as ET
import zipfile
import shutil

from toxml import findBestMatchingRow, injectMetadata, \
    injectTextField


def convert(args):
    args.input_directory = os.path.abspath(args.input_directory)
    args.output_directory = os.path.abspath(args.output_directory)
    tmp_directory = os.path.abspath(os.path.join(args.output_directory, 'temp'))

    for path in [args.output_directory, tmp_directory]:
        if not os.path.exists(path):
            os.makedirs(path)

    xlsx = pd.read_excel(args.xlsx_path, header=None)
    columnIndexToTagName = {columnIndex: tagName for columnIndex, tagName in xlsx.iloc[0].items() if isinstance(tagName, str)}
    tagNameToColumnIndex = {value: key for key, value in columnIndexToTagName.items()}
    columnIndexToTextFieldName = {columnIndex: tagName for columnIndex, tagName in xlsx.iloc[1].items() if isinstance(tagName, str)}
    textFieldNameToColumnIndex = {value: key for key, value in columnIndexToTextFieldName.items()}
    data = xlsx[4:]

    mscz_filenames = [filename
                 for filename in os.listdir(args.input_directory)
                 if os.path.splitext(filename)[-1].lower() == '.mscz']

    print('Processing files from directory "{}" into directory "{}".'.format(
        args.input_directory,
        args.output_directory
    ))
    for filename in mscz_filenames:
        print('\nProcessing file "{}" ...'.format(filename))
        rowId, rowData = findBestMatchingRow(filename, data, tagNameToColumnIndex)
        inputMsczPath = os.path.join(args.input_directory, filename)
        outputMsczPath = os.path.join(args.output_directory,
                                  os.path.basename(filename))
        filename_extensionless = os.path.splitext(filename)[0]
        tmp_unzipped_path = os.path.join(tmp_directory, filename_extensionless)
        with zipfile.ZipFile(inputMsczPath, "r") as zip_ref:
            zip_ref.extractall(tmp_unzipped_path)
        mscx_filenames = [filename
                          for filename in os.listdir(tmp_unzipped_path)
                          if os.path.splitext(filename)[-1].lower() == '.mscx']
        tmp_mscx_path = os.path.join(tmp_unzipped_path, mscx_filenames[0])
        print('Working on temporary {} file...'.format(tmp_mscx_path))
        xmlTree = ET.parse(tmp_mscx_path)
        injectMetadata(xmlTree, rowData, tagNameToColumnIndex)
        injectTextField(xmlTree, rowData, textFieldNameToColumnIndex)
        xmlTree.write(tmp_mscx_path)
        shutil.make_archive(outputMsczPath, 'zip', tmp_unzipped_path)
        os.rename('{}.zip'.format(outputMsczPath), outputMsczPath)
        pass

    print('Done')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update XML song files '
                                                 'with metadata '
                                                 'from XLSX file')
    parser.add_argument('--input_directory', type=str, default='./input',
                        help='Directory path containing XML files to convert')
    parser.add_argument('--xlsx_path', type=str,
                        default='./metadata_v16.xlsx',
                        # default='./metadata_tel_train.xlsx',
                        help='Path to the XLSX file containing metadata about '
                             'songs')
    parser.add_argument('--output_directory', type=str, default='./output',
                        help='Directory path where to store the new XML files')
    args = parser.parse_args()
    convert(args)
