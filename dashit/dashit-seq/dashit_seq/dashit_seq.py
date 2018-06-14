#!/usr/bin/env python3
"""
DASHit-seq: Guide design by covering an input sequence.

Given an input sequence and off targets, create a DASH library by
optimally covering the input while avoiding off targets.

*Optimally* means:
1. guides are chosen to reasonably cover the input, e.g. every 200bp
2. guides aren't spaced too closely, e.g. no closer than 50bp
"""
import argparse
from ash import flash
import pysam
import logging
import os
import subprocess
import fcntl
import time
from ash import filter_offtarget
import sys
import signal
from datetime import datetime
from socket import gethostname

from Bio import SeqIO
from Bio import SeqRecord
from Bio.Seq import Seq
from ortools.linear_solver import pywraplp
from ash.common import Gene, Target
from pathlib import Path
from ash.build import fetch_with_retries

from collections import defaultdict

from jinja2 import Environment, FileSystemLoader

__version__ = "1.0"

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def initialize_solver(sequences, filtered_sites):
    """
    Creates & initializes a solver object for guide optimization.

    Parameters
    ----------
    sequences : list of `Gene`
	input sequences that we're designing guides format
    filtered_sites : dict
	CRISPR sites to ignore in optimization (e.g., offtargets)

    Returns
    -------
    (`ortools.linear_solver.pywraplp.Solver`, dict, dict)

    The initialized solver object, a dictionary mapping CRISPR sites
    to optimization variables, a dictionary mapping CRISPR sites to
    targets within the input sequence.

    Note: This method does not add any constraints. See `add_constraints`.
    """

    solver = pywraplp.Solver('SolveIntegerProblem',
			     pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    objective = solver.Objective()

    sites_to_targets = defaultdict(list)

    for gene in sequences:
        for target_seq, target_loc in gene.targets:
            if target_seq in filtered_sites:
                continue
            if target_seq not in sites_to_targets:
                sites_to_targets[target_seq].append((gene, (target_seq,
                                                            target_loc)))

    site_variables = {}

    for i, target_seq in enumerate(sites_to_targets):
        if target_seq in filtered_sites:
            continue
        site_variables[target_seq] = solver.IntVar(0, 1, 'x_{}'.format(i))
        objective.SetCoefficient(site_variables[target_seq], 1)

    objective.SetMinimization()

    return solver, site_variables, sites_to_targets

def add_spacing_constraints(sequences, solver, site_variables, filtered_sites,
			    min_spacing, max_spacing):
    """
    Add minimum & maximum separation constraints to cover sequences
    without bunching up.
    
    Adds constraints to the provided solver instance.

    Parameters
    ----------
    sequences : list of `Gene`
	sequences we wish to cover with CRISPR sites
    solver : `ortools.linear_solver.pywraplp.Solver`
	initialized solver, as returned from `initialize_solver`
    site_variables : list
	optimization solver variables, as returned from `initialize_solver`
    filtered_sites : dict
	CRISPR sites that should be ignored for optimization, e.g. offtargets
    min_spacing, max_spacing : int
	ensure at least `min_spacing` between selected guides, and
	ensure that at least one guide appears in every window of
	width `max_spacing`

    Returns
    -------
    (spacing_constraints, coverage_constraints) : tuple of set

    `spacing_constraints`, ensuring minimum spacing, and
    `coverage_constraints` ensuring the target sequence is covered

    This method already adds these constraints to `solver`, but the
    return value is useful for debugging.
    """

    # Rather than have fancy logic below to ensure we add each
    # constraint only once, we're lazy and rely on set() to uniquefy
    # our list of constraints
    coverage_constraints = set()
    spacing_constraints = set()

    for sequence in sequences:
        for i, (seq, cut_loc) in enumerate(sequence.targets):
            if seq in filtered_sites:
                continue

            nearby_targets = [ s for s, l in sequence.targets if l != cut_loc and
                               not (s in filtered_sites) and
                               abs(l - cut_loc) < min_spacing ]

            if len(nearby_targets) > 0:
                spacing_constraints.add(tuple(s for s in
                                              nearby_targets + [seq]))

            nearby_targets = [ s for s, l in sequence.targets if l != cut_loc and
                               not (s in filtered_sites) and
                               abs(l - cut_loc) < max_spacing ]

            if len(nearby_targets) > 0:
                coverage_constraints.add(tuple(s for s in
                                               nearby_targets + [seq]))

    for constraint in spacing_constraints:
        new_constraint = solver.Constraint(0, 1)
        for site in constraint:
            new_constraint.SetCoefficient(site_variables[site], 1)

    for constraint in coverage_constraints:
        new_constraint = solver.Constraint(1, solver.Infinity())
        for site in constraint:
            new_constraint.SetCoefficient(site_variables[site], 1)

    return spacing_constraints, coverage_constraints

def filter_sites_offtarget(sequences, filtered_sites, filter_radius):
    """
    Takes a list of sequences with identified CRISPR targets and filters
    those that are offtarget.
    
    This function adds off target CRISPR sites to =filtered_sites=.

    Parameters
    ----------
    sequences : list of `common.Gene`
	the input sequences with CRISPR sites identified
    filtered_sites : dict
	dict containing which sites have been filtered
    filter_radius : str
	string of the form L_M_N where L, M, N are the number of
	required matches in the first 5, 10 and 20 positions to
	declare a CRISPR site offtarget
    """

    log.info('filtering offtarget CRISPR sites from {} input '
	     'sequences with radius {}'.format(len(sequences),
					       filter_radius))

    # We may have duplicates in this list, if a single CRISPR site
    # occurs multiple times in the input sequences
    all_targets = []

    for sequence in sequences:
        for target in sequence.targets:
            all_targets.append(target[0])

    results = filter_offtarget.fetch_all_offtargets(all_targets, [filter_radius])

    offtargets = parse_offtarget_server_response(results)

    log.info('removed {} sites from consideration because they hit off '
	     'targets'.format(len(offtargets)))

    for site in offtargets:
        filtered_sites[site] = "offtarget"

def filter_sites_poor_structure(sequences, filtered_sites, filter_parms):
    """
    Filter CRISPR sites due to poor structural reasons.
    
    A site will be removed if any of the following are true:
    
    1. G/C frequency too high (> 15/20) or too low (< 5/20)
    2. /Homopolymer/: more than 5 consecutive repeated nucleotides
    3. /Dinucleotide repeats/: the same two nucelotides alternate for > 3
       repeats
    4. /Hairpin/: complementary subsequences near the start and end of a
       site can bind, causing a hairpin

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

    for sequence in sequences:
        for target in sequence.targets:
            reasons = flash.poor_structure(target[0], True, filter_parms)
            if len(reasons) > 0:
                filtered_sites[target[0]] = "; ".join(reasons)

    log.info('removed {} sites from consideration due to poor '
	     'structure'.format(len(filtered_sites) - initial_num_filtered))

def parse_offtarget_server_response(response):
    """
    Parse the HTTP request returned from the off target server and return
    which CRISPR sites were filtered.

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

def launch_offtarget_server(offtarget_filename):
    """
    Launch the off target filtering server.

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
    Check that the offtarget server process is running. Log errors if not.

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

	# outs, errs = offtarget_proc.communicate()
	# log.error('off_target stdout:\n\n{}\n\n'.format(outs.decode()))
	# log.error('off_target stderr:\n\n{}\n\n'.format(errs.decode()))

        return None
    else:
        return offtarget_proc

def check_offtarget_ready(offtarget_proc):
    """
    Check that the offtarget server is ready and waiting for requests.

    Parameters
    ----------
    offtarget_proc : `subprocess.Popen`
	offtarget server process, as returned by `launch_offtarget_server`

    Returns
    -------
    bool or None

    True if offtarget server is ready, False if offtarget server is
    still starting, None if `offtarget_proc` died or is None
    """

    offtarget_proc = check_offtarget_alive(offtarget_proc)

    if offtarget_proc is None:
        return None

    while True:
        line = offtarget_proc.stderr.readline()

        if line != b'':
            print(line)
            if 'starting server' in line.decode():
                log.info('offtarget server ready and waiting')
                # Disable the subprocess' STDOUT and STDERR to prevent
                # it from deadlocking by writing too much to stdout
                # that doesn't get read
                return True
        else:
            break

    return False

def read_sequences_from_file(filename):
    """
    Generate Gene objects from an input file and identify CRISPR targets.

    Parameters
    ----------
    filename : str
	input filename, FASTA format

    Returns
    -------
    list of `Gene` objects, with identified CRISPR targets
    """

    input_sequences = SeqIO.parse(open(filename, 'r'), 'fasta')

    sequences = []

    for i, sequence in enumerate(input_sequences):
        if i >= 1:
            raise NotImplementedError('Input sequence file can only contain a '
                                      'single sequence')

        new_sequence = Gene('Input Sequence {}'.format(i))
        new_sequence.name = sequence.name
        new_sequence.seq = sequence.seq
        new_sequence.targets = []

        for i in flash.kmers_range(new_sequence.seq, 23):
            if 'G' == new_sequence.seq[i+21] == new_sequence.seq[i+22]:
                new_sequence.targets.append(
                    Target(flash.forward_20mer_at(new_sequence.seq, i, 'F'),
                           flash.cut_location((i, 'F'))))
            if 'C' == sequence.seq[i] == sequence.seq[i+1]:
                new_sequence.targets.append(
                    Target(flash.forward_20mer_at(new_sequence.seq, i, 'R'),
                           flash.cut_location((i, 'R'))))

        sequences.append(new_sequence)
    return sequences
