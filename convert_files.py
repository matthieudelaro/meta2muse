import argparse
import os


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update XML song files '
                                                 'with metadata '
                                                 'from XLSX file')
    parser.add_argument('--input_directory', type=str, default='./input',
                        help='Directory path containing XML files to convert')
    parser.add_argument('--parameters_directory', type=str,
                        default='./parameters',
                        # default='./metadata_tel_train.xlsx',
                        help='Directory path containing metadata.xlsm, '
                             'mapping.xlsx, etc')
    # parser.add_argument('--xlsx_path', type=str,
    #                     default='./metadata_v15.xlsm',
    #                     # default='./metadata_tel_train.xlsx',
    #                     help='Path to the XLSX file containing metadata about '
    #                          'songs')
    parser.add_argument('--output_directory', type=str, default='./output',
                        help='Directory path where to store the new XML files')
    parser.add_argument('--do_not_auto_upgrade', type=bool, default=False,

                        help='Will download all ther requirements, upgrade pip, ...')
    args = parser.parse_args()
    if not args.do_not_auto_upgrade:
        import upgrade
        upgrade.checkRequirements()


import zipfile
import shutil
import pandas as pd
from lxml import etree as ET

from toxml import findBestMatchingRow, injectMetadata, \
    injectTextField, safe_child

import logger
from logger import print
import trans


def convert(args):
    args.input_directory = os.path.abspath(args.input_directory)
    args.output_directory = os.path.abspath(args.output_directory)
    tmp_directory = os.path.abspath(os.path.join(args.output_directory, 'temp'))

    for path in [args.output_directory, tmp_directory, args.parameters_directory]:
        if not os.path.exists(path):
            os.makedirs(path)

    # clean up tmp folder
    shutil.rmtree(tmp_directory)
    os.makedirs(tmp_directory)

    logger_output_filepath = os.path.abspath(os.path.join(tmp_directory, 'logs.txt'))
    logger.config(logger_output_filepath)

    xlsx_filepath = os.path.abspath(os.path.join(args.parameters_directory, 'metadata.xlsm'))
    xlsx = pd.read_excel(xlsx_filepath, header=None)
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
    # TODO: load mapping from file
    # TODO: for each file, check if already mapped. Otherwise compute mapping
    # TODO: persist mapping
    # TODO: process files
    conversion_list = []
    for filename in mscz_filenames:
        print('')
        print('Processing file "{}" ...'.format(filename))
        rowId, rowData = findBestMatchingRow(filename, data, tagNameToColumnIndex)
        inputMsczPath = os.path.join(args.input_directory, filename)
        outputMsczPath = os.path.join(args.output_directory,
                                  os.path.basename(filename))
        conversion_list.append({
            'inputMsczPath': inputMsczPath,
            'outputMsczPath': outputMsczPath,
        })
        filename_extensionless = os.path.splitext(filename)[0]
        tmp_unzipped_path = os.path.join(tmp_directory, filename_extensionless)
        # https://stackoverflow.com/questions/1807063/extract-files-with-invalid-characters-in-filename-with-python
        with zipfile.ZipFile(inputMsczPath, "r") as zip_ref:
            zip_ref.extractall(tmp_unzipped_path)
        mscx_filenames = [filename
                          for filename in os.listdir(tmp_unzipped_path)
                          if os.path.splitext(filename)[-1].lower() == '.mscx']
        original_mscx_filename = mscx_filenames[0]
        # ascii_mscx_filename = trans.trans(original_mscx_filename)
        ascii_mscx_filename = trans.trans('{}.mscx'.format(filename_extensionless))
        original_tmp_mscx_path = os.path.join(tmp_unzipped_path, original_mscx_filename)
        safe_tmp_mscx_path = os.path.join(tmp_unzipped_path, ascii_mscx_filename)
        os.rename(original_tmp_mscx_path, safe_tmp_mscx_path)
        print('Working on temporary {} file...'.format(safe_tmp_mscx_path))


        xmlTree = ET.parse(safe_tmp_mscx_path)
        injectMetadata(xmlTree, rowData, tagNameToColumnIndex)
        injectTextField(xmlTree, rowData, textFieldNameToColumnIndex)

        xmlTree.write(safe_tmp_mscx_path)

        # update container metadata to take the safe filename into account
        metadata_file_path = os.path.join(tmp_unzipped_path, 'META-INF/container.xml')
        metadataTree = ET.parse(metadata_file_path)
        rootfileTag = safe_child(metadataTree.getroot(), 'rootfile')
        rootfileTag.set('full-path', ascii_mscx_filename)

        # create the new mscz archive
        shutil.make_archive(outputMsczPath, 'zip', tmp_unzipped_path)
        os.rename('{}.zip'.format(outputMsczPath), outputMsczPath)
        pass

    print('Done')


if __name__ == '__main__':
    convert(args)
