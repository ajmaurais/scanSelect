
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


def process_file(fname, scans, inplace=False, output_dir=None,
                 sufix='_short', verbose=False):
    '''
    
    Parameters
    ----------
    fname: str
        Path to mzML file.
    scans: list
        List of scans to select from mzML file.
    output_dir: str
        Path to ouput directory.
        This argument takes precedence over arguments for 'inplace' and 'sufix'.
    inplace: bool
        Should input file be overwritten?
    sufix: str
        Sufix to add to end of output file.
    verbose: bool
        Print verbose output?
    '''

    if len(scans) == 0:
        sys.stderr.write('\n\tWARN: No scans in tsv for file {}\n'.format(fname))
        return
    
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
    if output_dir:
        ofname = '{}{}.mzML'.format(os.path.splitext(fname)[0], sufix)
        ofname = '{}/{}'.format(output_dir, ofname)
    elif inplace:
        ofname = fname
    else:
        ofname = '{}{}.mzML'.format(os.path.splitext(fname)[0], sufix)
    if verbose:
        sys.stdout.write('\tWriting {}...\n'.format(ofname))
    pyopenms.MzMLFile().store(ofname, newExp)

    if verbose:
        sys.stdout.write('\tDone!\n')


def main():
    parser = argparse.ArgumentParser(description='Select scans and precursors in "scanNum" column from mzML file.')

    parser.add_argument('--scanCol', default='scanNum',
                        help='Column in tsv_file to get ms2 scan numbers from. Default is "scanNum".')
    parser.add_argument('--fileCol', default='precursorFile',
                        help='Column in tsv_file to get mzML file names from. Default is "precursorFile".')
    parser.add_argument('-s', '--sufix', default=None,
                        help='Sufix to add to shortened files. Default is "_short".')
    parser.add_argument('-d', '--outputDir', default=None,
                        help='Destination directory for output file(s)')
    parser.add_argument('--inplace', action='store_true', default=False,
                        help='Overwrite mzML files.')
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Print verbose output.')
    parser.add_argument('tsv_file', help='Path to tsv file with "scanNum" column.')
    parser.add_argument('mzML_files', nargs='+', help='mzML file(s) to extract scans from.')

    args = parser.parse_args()

    # read dat
    dat = pd.read_csv(args.tsv_file, sep='\t')
    scansDict = dict()
    for fname in args.mzML_files:
        # set dict entry to the list of scans for the current fname
        scansDict[fname] = dat[dat[args.fileCol].apply(lambda x: bool(re.match('{}\.\w+$'.format(os.path.splitext(fname)[0]), x)))][args.scanCol].to_list()
    
    # make mzML output directory if applicable
    if args.outputDir:
        if not os.path.isdir(args.outputDir):
            if args.verbose:
                sys.stdout.write('Creating directory: {}'.format(args.outputDir))
            os.mkdir(args.outputDir)
        _sufix = '' if args.sufix is None else args.sufix
    else:
        _sufix = '_short' if args.sufix is None else args.sufix

    for fname, scans in scansDict.items():
        # get a list of scans in current mzML file
        if args.verbose:
            sys.stdout.write('Working on {}...\n'.format(fname))
        process_file(fname, scans, output_dir = args.outputDir,
                     inplace=args.inplace, sufix=_sufix, verbose=args.verbose)

if __name__ == '__main__':
    main()

