"""
<<doc:dashit-reads-filter>>
"""
import argparse
import logging
import os
from datetime import datetime
from ash import filter_offtarget_2
from ash.build import fetch_with_retries
import re
import subprocess
import signal
import sys
from ash import flash
from pathlib import Path
from tqdm import tqdm
from collections import defaultdict

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def filter_sites_poor_structure(sequences, filtered_sites, filter_parms):
    """
    <<doc:filter_sites_poor_structure>>

    Parameters
    ----------
    sequences : list of `common.Gene`
	the input sequences with CRISPR targets identified
    filtered_sites : dict
	dict containing which sites have been filtered
    filter_parms : dict
	parameters controlling poor structure filtering,
	see `flash.poor_structure`
    """

    log.info('filtering sites for poor structure '
	     'with parms {}'.format(filter_parms))

    initial_num_filtered = len(filtered_sites)

    for target in tqdm(sequences):
        reasons = flash.poor_structure(target, True, filter_parms)
        if len(reasons) > 0:
            filtered_sites[target[0]] = "; ".join(reasons)

    log.info('removed {} sites from consideration due to poor '
	     'structure'.format(len(filtered_sites) - initial_num_filtered))

def launch_offtarget_server(offtarget_filename):
    """
    <<doc:launch_offtarget_server>>

    Parameters
    ----------
    offtarget_filename : str
	filename containing off target CRISPR sites, as generated by
	`special_ops_crispr_tools/crispr_sites`

    Returns
    -------
    `subprocess.Popen` the off target server launched as a child process
    """

    offtarget_env = os.environ.copy()
    offtarget_env['HOST'] = 'file://' + str(Path(offtarget_filename).resolve())

    log.info('Launching offtarget with HOST = {}'.format(offtarget_env['HOST']))

    proc = subprocess.Popen(['/usr/bin/env', 'offtarget'], env=offtarget_env)

    proc = check_offtarget_alive(proc)

    if proc is None:
        log.error('Error launching offtarget. Is offtarget in your path? '
                  'Is {} an off target CRISPR sites file generated by '
                  'crispr_sites?'.format(Path(offtarget_filename).resolve()))

    # Set the offtarget's  stdout and stderr to  non-blocking reads so
    # we can check in on them
    # fd = proc.stderr.fileno()
    # fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    # fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    # fd = proc.stdout.fileno()
    # fl = fcntl.fcntl(fd, fcntl.F_GETFL)
    # fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    return proc

def check_offtarget_alive(offtarget_proc):
    """
    <<doc:check_offtarget_alive>>

    Parameters
    ----------
    offtarget_proc : `subprocess.Popen`
	offtarget server process, as returned by `launch_offtarget_server`

    Returns
    -------
    `subprocess.Popen`

    Returns `offtarget_proc` if the process is running, else return `None`
    """

    if offtarget_proc is None:
        return None

    if offtarget_proc.poll() is not None:
        log.error('offtarget server exited unexpectedly with code '
                  '{}\n\n'.format(offtarget_proc.returncode))

        return None
    else:
        return offtarget_proc

def parse_offtarget_server_response(response):
    """
    <<doc:parse_offtarget_server_response>>

    Parameters
    ----------
    response : dict
	response from offtarget server, as returned by
	`filter_offtarget.fetch_all_offtargets`

    Returns
    -------
    offtargets : defaultdict

    dictionary where `offtargets[site] == True` if `site` is an
    offtarget
    """

    offtargets = defaultdict(bool)

    for radius in response:
        for r in response[radius]:
            for line in r.text.split('\n'):
                if line[-4:] == 'true':
                    offtargets[line[0:20]] = True

    return offtargets

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filter guides in a '
                                     'sites-to-reads file based on offtargets '
                                     'and quality')

    parser.add_argument('input', type=str, help='input sites-to-reads file to '
                        'filter. Generated by crispr_sites -r')

    parser.add_argument('--filtered_explanation', type=str,
                        help='output file listing which guides were '
                        'disqualified and why. CSV format.')

    offtarget_group = parser.add_argument_group('offtarget filtering',
                                                'options to filter offtargets')
    
    offtarget_group.add_argument('--offtarget', type=str,
			         help='File containing off target CRISPR sites, as '
			         'generated by crispr_sites')

    offtarget_group.add_argument('--offtarget_radius', type=str, default='5_10_19',
			         help='Radius used for matching an off target. '
                                 'Specify this as L_M_N which means remove a '
                                 'guide for hitting an off target if L, M, N '
                                 'nucleotides in the first 5, 10 and 20 '
                                 'positions of the guide, respectively, match '
			         'the off target. e.g., 5_10_20 to require '
                                 'perfect matches; 5_9_18 to allow up to one '
                                 'mismatch in positions 6-10 positions and to '
                                 'allow up to 2 mismatches in the last 10 '
                                 'positions')

    filtering_group = parser.add_argument_group('quality filtering',
						'options for how guides are '
                                                'filtered for poor structure '
                                                'reasons')

    filtering_group.add_argument('--gc_freq_min', type=int, default=5,
				 help='filter guide if # of Gs or Cs is '
				 'strictly less than this number')

    filtering_group.add_argument('--gc_freq_max', type=int, default=15,
				 help='filter guide if # of Gs or Cs is '
				 'strictly greater than this number')

    filtering_group.add_argument('--homopolymer', type=int, default=5,
				 help='filter guide if strictly more than '
				 'this number of a single consecutive '
				 'nucleotide appears, e.g., AAAAA')

    filtering_group.add_argument('--dinucleotide_repeats', type=int, default=3,
				 help='filter guide if strictly more than '
				 'this number of a single dinucleotide repeats '
				 'occur, e.g. ATATAT')

    filtering_group.add_argument('--hairpin_min_inner', type=int, default=3,
				 help='filter guide if a hairpin occurs with >='
				 'this inner hairpin spacing, e.g., '
				 'oooooIIIooooo, where the o are reverse '
				 'complements and III is the inner hairpin '
				 'spacing')

    filtering_group.add_argument('--hairpin_min_outer', type=int, default=5,
				 help='filter guide if a hairpin occurs with >='
				 'this outer hairpin width, e.g., '
				 'oooooIIIooooo, where the o are reverse '
				 'complements and ooooo is the outer hairpin')


    start_time = datetime.now()

    args = parser.parse_args()

    filter_parms = { 'gc_frequency': (args.gc_freq_min, args.gc_freq_max),
		     'homopolymer': args.homopolymer,
		     'dinucleotide_repeats': args.dinucleotide_repeats,
		     'hairpin': { 'min_inner': args.hairpin_min_inner,
				  'min_outer': args.hairpin_min_outer } }

    if args.offtarget is not None:
        offtarget_proc = launch_offtarget_server(args.offtarget)

	# Catch SIGTERM/SIGINT to shutdown the offtarget server
        def handler(signal, frame):
            global offtarget_proc
            log.info('Killing offtarget server')
            offtarget_proc.kill()
            sys.exit(1)

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
    else:
        log.info('offtarget file not specified with --offtarget, will not '
                 'perform any offtarget filtering')
        offtarget_proc = None

    # Check/wait that offtarget server has started
    if args.offtarget is not None:
        try:
            log.info("Poking offtarget server.  Timeout 10 seconds.")
            fetch_with_retries(["ACGT" * 5], 5, 9, 18, max_attempts=20, timeout=10)
            log.info("Offtarget server is alive.")
        except:
            log.error('Error starting offtarget server, see messages above')
            sys.exit(-1)

    with open(args.input, 'r') as input_handle:
        num_reads_line = input_handle.readline()

        # Parse how many reads are represented in the sites-to-reads file
        match = re.search(r': (\d)+', num_reads_line)
        if match is None:
            log.error('{} is missing the total number of reads on line 1, '
                      're-run crispr_sites -r'.format(args.input))
            if offtarget_proc is not None:
                offtarget_proc.kill()
                
            sys.exit(1)

        num_reads = int(match.group(1))

        log.info('Reading in candidate guides from {}'.format(args.input))

        candidate_guides = []
        
        for line in input_handle.readlines():
            candidate_guides.append(line[0:20])

        initial_num_candidate_guides = len(candidate_guides)
        
        filtered_guides = {}
            
        # Do offtarget filtering
        if offtarget_proc is not None:
            log.info('Filtering offtarget guides')
            results = filter_offtarget_2.fetch_all_offtargets(
                candidate_guides, [args.offtarget_radius])
            offtargets = parse_offtarget_server_response(results)

            for guide in offtargets:
                filtered_guides[guide] = ('offtarget against '
                                          '{}'.format(args.offtarget))
                candidate_guides.remove(guide)

            log.info('{} guides matched against offtargets '
                     'in {}'.format(len(filtered_guides), args.offtarget))
            
        # Do quality filtering
        log.info('Filtering guides for quality')

        filter_sites_poor_structure(candidate_guides, filtered_guides, filter_parms)

        log.info('Done filtering, removed {} out of {} '
                 'guides'.format(len(filtered_guides), initial_num_candidate_guides))

        input_handle.seek(0)

        # Write out first line always
        sys.stdout.write(input_handle.readline())

        for line in input_handle.readlines():
            if line[0:20] not in filtered_guides:
                sys.stdout.write(line)
        
        if args.filtered_explanation is not None:
            with open(args.filtered_explanation, 'w') as output_handle:
                output_handle.write('candidate guide, why it was filtered out\n')
                for guide in filtered_guides:
                    output_handle.write('{}, {}\n'.format(guide, filtered_guides[guide]))
