import argparse
import os
import pandas as pd

from toxml import convert_one_file
from parameters import column_infos_from_header


def convert(args):
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    xlsx = pd.read_excel(args.xlsx_path)
    xlsx = xlsx[3:]
    header = pd.read_excel(args.xlsx_path)

    column_info = column_infos_from_header(header)

    for filename in os.listdir(args.input_directory):
        if os.path.splitext(filename)[-1].lower() == '.xml':
            convert_one_file(
                xlsx=xlsx,
                column_info=column_info,
                input_path=os.path.join(args.input_directory, filename),
                output_path=os.path.join(args.output_directory,
                                      os.path.basename(filename))
            )
        print('')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update XML song files '
                                                 'with metadata '
                                                 'from XLSX file')
    parser.add_argument('--input_directory', type=str, default='./input',
                        help='Directory path containing XML files to convert')
    parser.add_argument('--xlsx_path', type=str,
                        default='./metadata_v13.xlsx',
                        # default='./metadata_tel_train.xlsx',
                        help='Path to the XLSX file containing metadata about '
                             'songs')
    parser.add_argument('--output_directory', type=str, default='./output',
                        help='Directory path where to store the new XML files')
    args = parser.parse_args()
    convert(args)
