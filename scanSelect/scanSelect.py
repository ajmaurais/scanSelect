
import argparse
import pyopenms
import sys
import os
import pandas as pd
import re

SCAN_RE = re.compile('scan=([0-9]+)')

def getScanMap(scans):
    scan_index = dict()
    precursor_map = dict()

    current_precursor = 0
    for i, scan in enumerate(scans):
        current_level = scan.getMSLevel()
        match = SCAN_RE.search(scan.getNativeID().decode('utf-8'))
        if match:
            scan_num = int(match.group(1))
            if current_level == 1:
                current_precursor = scan_num
            elif current_level == 2:
                precursor_map[scan_num] = current_precursor
            scan_index[scan_num] = i
        else:
            sys.stderr.write('WARN: Could not parse native ID: {}'.format(scan.getNativeID()))
    return scan_index, precursor_map


def main():
    parser = argparse.ArgumentParser(description='Select scans and precursors in "scanNum" column from mzML file.')

    parser.add_argument('--scanCol', default='scanNum',
                        help='Column in tsv_file to get ms2 scan numbers from. Default is "scanNum".')
    parser.add_argument('-s', '--sufix', default='_short',
                        help='Sufix to add to shortened files. Default is "_short".')
    parser.add_argument('--inplace', action='store_true', default=False,
                        help='Overwrite mzML files.')
    parser.add_argument('tsv_file', help='Path to tsv file with "scanNum" column.')
    parser.add_argument('mzML_files', nargs='+', help='mzML file(s) to extract scans from.')

    args = parser.parse_args()

    # read dat
    dat = pd.read_csv(args.tsv_file, sep='\t')

    for fname in args.mzML_files:
        sys.stdout.write('Working on {}...\n'.format(fname))

        # get a list of scans in current mzML file
        file_base = os.path.splitext(fname)[0]
        scans = dat[dat['precursorFile'].apply(lambda x: bool(re.match('{}\.\w+$'.format(file_base), x)))][args.scanCol].to_list()
        if len(scans) == 0:
            sys.stderr.write('\n\tWARN: No scans in tsv for file {}\n'.format(fname))
            continue
        
        # load mzML file and get spectra and scan maps
        exp = pyopenms.MSExperiment()
        pyopenms.MzMLFile().load(fname, exp)
        if not exp.isSorted():
            exp.sortSpectra(True)
        spectra = exp.getSpectra()
        scan_index, precursor_map = getScanMap(spectra)

        # construct list of scans to select
        scans_index = list() # list of index of scans to select
        for scan in scans:
            # add precursor
            scans_index.append(scan_index[precursor_map[int(scan)]])

            # add ms2s
            scans_index.append(scan_index[int(scan)])

        # subset scan list
        spectra_subset = [spectra[i] for i in scans_index]
        newExp = pyopenms.MSExperiment()
        newExp.setSpectra(spectra_subset)
        newExp.sortSpectra(True)

        # write subset mzML file
        ofname = str()
        if args.inplace:
            ofname = fname
        else:
            ofname = '{}{}.mzML'.format(file_base, args.sufix)
        sys.stdout.write('\tWriting {}...\n'.format(ofname))
        pyopenms.MzMLFile().store(ofname, newExp)

        sys.stdout.write('\tDone!\n')


if __name__ == '__main__':
    main()

