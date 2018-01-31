#!/usr/bin/env python3

"""*****************************************************************************
 *   Authors: Camille Marchet  Pierre Morisse Antoine Limasset
 *   Contact: camille.marchet@irisa.fr, IRISA/Univ Rennes/GenScale, Campus de Beaulieu, 35042 Rennes Cedex, France
 *   Source: https://github.com/kamimrcht/benchmark-long-read-correction
 *
 *
 *  This program is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU Affero General Public License as
 *  published by the Free Software Foundation, either version 3 of the
 *  License, or (at your option) any later version.
 *
 *  This program is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU Affero General Public License for more details.
 *
 *  You should have received a copy of the GNU Affero General Public License
 *  along with this program.  If not, see <http://www.gnu.org/licenses/>.
*****************************************************************************"""

from Bio import SeqIO
import time
import argparse
import sys
import os
import shlex, subprocess
from subprocess import Popen, PIPE, STDOUT
import re 

#Launches subprocess
def subprocessLauncher(cmd, argstdout=None, argstderr=None, argstdin=None):
        args = shlex.split(cmd)
        p = subprocess.Popen(args, stdin = argstdin, stdout = argstdout, stderr = argstderr).communicate()
        return p

# format MECAT headers
def formatMecat(correctedReads, uncorrectedReads):
	fCor = open(correctedReads)
	fUnco = open(uncorrectedReads)
	fNewCor = open(correctedReads + "_tmp", 'w')

	i = 0
	hCor = fCor.readline().split("_")[0]
	hUnco = fUnco.readline()
	while hCor != "":
		sCor = fCor.readline()
		id = int(hCor.split(">")[1])
		while i != id:
			sUnco = fUnco.readline()
			hUnco = fUnco.readline()
			i = i + 1
		hCor = fCor.readline().split("_")[0]
		fNewCor.write(hUnco + sCor)

	cmdMv = "mv " + correctedReads + "_tmp " + correctedReads
	subprocess.check_output(['bash', '-c', cmdMv])
	fCor.close()
	fUnco.close()
	fNewCor.close()

# format daccord headers
def formatDaccord(correctedReads, uncorrectedReads, daccordDb):
	#dump database
	cmdDumpDb = "DBdump -rh " + daccordDb
	dumpedDb = open("daccord_dumpedDb", 'w')
	subprocessLauncher(cmdDumpDb, dumpedDb)
	fCor = open(correctedReads)
	dumpedDb.close()

	fDump = open("daccord_dumpedDb")
	lDump = fDump.readline()
	while lDump != "" and (lDump[0] == '+' or lDump[0] == '@'):
		lDump = fDump.readline()
	fUnco = open(uncorrectedReads)
	newCorrectedReads = open(correctedReads + "_tmp", 'w')
	curRead = 0
	hUnco = fUnco.readline()
	sUnco = fUnco.readline()

	hCor = fCor.readline()
	if hCor != '':
		hCor = hCor.split("/")[0].split(">")[1]
	while hCor != '':
		sCor = fCor.readline()
		while lDump != '' and lDump.split(" ")[1][:-1] != hCor:
			lDump = fDump.readline()
			lDump = fDump.readline()
			lDump = fDump.readline()
		lDump = fDump.readline()
		lDump = fDump.readline()
		readId = int(lDump.split(" ")[1])
		while curRead != readId:
			hUnco = fUnco.readline()
			sUnco = fUnco.readline()
			curRead = curRead + 1
		newCorrectedReads.write(hUnco + sCor)
		newHCor = fCor.readline()
		if newHCor != '':
			newHCor = newHCor.split("/")[0].split(">")[1]
		while newHCor == hCor:
			sCor = fCor.readline()
			newCorrectedReads.write(hUnco + sCor)
			newHCor = fCor.readline()
			if newHCor != '':
				newHCor = newHCor.split("/")[0].split(">")[1]
		hCor = newHCor
		lDump = fDump.readline()
	cmdMv = "mv " + correctedReads + "_tmp " + correctedReads
	subprocess.check_output(['bash', '-c', cmdMv])
	fCor.close()
	fUnco.close()
	fDump.close()
	newCorrectedReads.close()


# sort read file by increasing order of headers, return occurrence of each corrected read
def readAndSortFasta(infileName, outfileName):
	handle = open(infileName, "rU")
	l = SeqIO.parse(handle, "fasta")
	#TOVERIFY
	#sortedList = [f for f in sorted(l, key=lambda x : int(x.description))]
	sortedList = [f for f in sorted(l, key=lambda x : (x.description))]
	occurrenceEachRead = dict()
	outfile = open(outfileName, 'w')
	prevHeader = ""
	for record in sortedList:
		outfile.write(">" + record.description+"\n")
		outfile.write(str(record.seq)+"\n")
		if record.description == prevHeader:
			occurrenceEachRead[record.description] += 1
		else:
			occurrenceEachRead[record.description] = 1
			prevHeader = record.description
	return occurrenceEachRead


# duplicate reference and uncorrected sequences when there are several corrected reads with the same header
def duplicateRefReads(reference, uncorrected, occurrenceEachRead, size, newUncoName, newRefName):
	if occurrenceEachRead != [1]*size:
		refer = open(reference, 'r')
		refLines = refer.readlines()
		uncorr = open(uncorrected, 'r')
		uncoLines = uncorr.readlines()
		newUnco = open(newUncoName, 'w')
		newRef = open(newRefName, 'w')
		#TOVERIFY
		#i = 0
		for unco,ref in zip(uncoLines, refLines):
			if not ">" in ref:
			#if str(i) in occurrenceEachRead.keys():
			#		for times in range(occurrenceEachRead[str(i)]):
				if header in occurrenceEachRead.keys():
					for times in range(occurrenceEachRead[header]):
						newRef.write(">" + header + "_" + str(times) + "\n")
						newRef.write(ref.rstrip() + "\n" )
						newUnco.write(">" + header + "_" + str(times) + "\n")
						newUnco.write(unco.rstrip() + "\n")
				#i += 1
			else:
				header = ref.rstrip()[1:]
		return newRefName, newUncoName
	else:
		return reference, uncorrected

# format corrected reads headers
def formatHeader(corrector, correctedReads, uncorrectedReads, daccordDb):
	if corrector == "daccord":
		formatDaccord(correctedReads, uncorrectedReads, daccordDb)
	elif corrector == "hg-color":
		cmdFormatHeader = "sed -i 's/_[0-9]*$\|_[0-9]*_[0-9]*$//g' " + correctedReads
		subprocess.check_output(['bash', '-c', cmdFormatHeader])
	elif corrector == "lorma":
		cmdFormatHeader = "sed -i 's/_[0-9]*$//g' " + correctedReads
		subprocess.check_output(['bash', '-c', cmdFormatHeader])
	elif corrector == "pbdagcon":
		pass
	elif corrector == "mecat":
		#TOVERIFY
		#if uncorrectedReads.endswith(".fastq") or uncorrectedReads.endswith("fq"):
		#	cmdFormatHeader = "paste -d '\n' <(grep -i '^@' " + uncorrectedReads + ") <(grep -v '^>' " + correctedReads + ") > output && mv output " + correctedReads
		#elif uncorrectedReads.endswith(".fasta") or uncorrectedReads.endswith(".fa"):
		#	cmdFormatHeader = "paste -d '\n' <(grep -i '^>' " + uncorrectedReads + ") <(grep -v '^>' " + correctedReads + ") > output && mv output " + correctedReads
		#subprocess.check_output(['bash', '-c', cmdFormatHeader])
		formatMecat(correctedReads, uncorrectedReads)



	
def convertSimulationOutputToRefFile():
	pass
	#todo : get output of the simulator and retrieve the references sequences to compare with

# main function
def processReadsForAlignment(corrector, reference, uncorrected, corrected, size, soft, daccordDb):
	#1- correctly format the headers to be able to identify and sort the corrected reads
	formatHeader(corrector, corrected, uncorrected, daccordDb)
	#2- count occurences of each corrected reads(in case of trimmed/split) and sort them
	#TOVERIFY
	if soft is not None:
		newCorrectedFileName = "corrected_sorted_by_" + soft + ".fa"
		sortedUncoFileName = "uncorrected_sorted_" + soft + ".fa"
		newUncoFileName =  "uncorrected_sorted_duplicated_" + soft + ".fa"
		sortedRefFileName = "reference_sorted_" + soft + ".fa"
		newRefFileName =  "reference_sorted_duplicated_" + soft + ".fa"
	else:
		newCorrectedFileName = "corrected_sorted.fa"
		sortedUncoFileName = "uncorrected_sorted.fa"
		newUncoFileName =  "uncorrected_sorted_duplicated.fa"
		sortedRefFileName = "reference_sorted.fa"
		newRefFileName =  "reference_sorted_duplicated.fa"
	readAndSortFasta(uncorrected, sortedUncoFileName)
	readAndSortFasta(reference, sortedRefFileName)
	occurrenceEachRead = readAndSortFasta(corrected, newCorrectedFileName)
	#3- duplicate reference and uncorrected reads files to prepare for POA (we want as many triplets as there are corrected reads)
	duplicateRefReads(sortedRefFileName, sortedUncoFileName, occurrenceEachRead, size, newUncoFileName, newRefFileName)

