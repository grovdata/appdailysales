#!/usr/bin/python
#
# appdailysales.py
#
# iTunes Connect Daily Sales Reports Downloader
# Copyright 2008-2011 Kirby Turner
#
# Version 3.0
#
# Latest version and additional information available at:
#   http://appdailysales.googlecode.com/
#
#
# This script will download yesterday's daily sales report from
# the iTunes Connect web site.  The downloaded file is stored
# in the same directory containing the script file.  Note: if
# the download file already exists then it will be overwritten.
#
# As of version 3.0, this script uses Apple's Autoingestion Java
# program. As such, it no longer does screen scraping.
#
#
# Contributors:
#   Leon Ho
#   Rogue Amoeba Software, LLC
#   Keith Simmons
#   Andrew de los Reyes
#   Maarten Billemont
#   Daniel Dickison
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.


# -- Change the following to match your credentials --
# -- or use the command line options.               --
appleId = 'Your Apple Id'
password = 'Your Password'
vendorId = 'Your Vendor Id'
outputDirectory = ''
unzipFile = False
verbose = False
daysToDownload = 1
dateToDownload = None
outputFormat = None
debug = False
# ----------------------------------------------------

import datetime
import getopt
import sys
import os
import gzip
import getpass
import subprocess


class ITCException(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value);


# The class ReportOptions defines a structure for passing
# report options to the download routine. The expected
# data attributes are:
#   appleId
#   password
#   outputDirectory
#   unzipFile
#   verbose
#   daysToDownload
#   dateToDownload
#   outputFormat
#   debug
# Note that the class attributes will default to the global
# variable value equivalent.
class ReportOptions:
    def __getattr__(self, attrname):
        if attrname == 'appleId':
            return appleId
        elif attrname == 'password':
            return password
        elif attrname == 'vendorId':
            return vendorId
        elif attrname == 'outputDirectory':
            return outputDirectory
        elif attrname == 'unzipFile':
            return unzipFile
        elif attrname == 'verbose':
            return verbose
        elif attrname == 'daysToDownload':
            return daysToDownload
        elif attrname == 'dateToDownload':
            return dateToDownload
        elif attrname == 'outputFormat':
            return outputFormat
        elif attrname == 'debug':
            return debug
        else:
            raise AttributeError, attrname


def usage():
    print '''usage: %s [options]
Options and arguments:
-h     : print this help message and exit (also --help)
-a uid : your apple id (also --appleId)
-p pwd : your password (also --password)
-V vid : your vendor id (also --vendorId)
-P     : read the password from stdin (also --passwordStdin)
-o dir : directory where download file is stored, default is the current working directory (also --outputDirectory)
-v     : verbose output, default is off (also --verbose)
-u     : unzip download file, default is off (also --unzip)
-d num : number of days to download, default is 1 (also --days)
-D mm/dd/yyyy : report date to download, -d option is ignored when -D is used (also --date)
-f format : output file name format (see strftime; also --format)
--debug : debug output, default is off''' % sys.argv[0]


def processCmdArgs():
    global appleId
    global password
    global vendorId
    global outputDirectory
    global unzipFile
    global verbose
    global daysToDownload
    global dateToDownload
    global outputFormat
    global debug

    # Check for command line options. The command line options
    # override the globals set above if present.
    try: 
        opts, args = getopt.getopt(sys.argv[1:], 'ha:p:V:Po:uvd:D:f:', ['help', 'appleId=', 'password=', 'vendorId=', 'passwordStdin', 'outputDirectory=', 'unzip', 'verbose', 'days=', 'date=', 'format=', 'debug'])
    except getopt.GetoptError, err:
        #print help information and exit
        print str(err)  # will print something like "option -x not recongized"
        usage()
        return 2

    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            return 2
        elif o in ('-a', '--appleId'):
            appleId = a
        elif o in ('-p', '--password'):
            password = a
        elif o in ('-V', '--venderId'):
            vendorId = a
        elif o in ('-P', '--passwordStdin'):
            password = getpass.getpass()
        elif o in ('-o', '--outputDirectory'):
            outputDirectory = a
        elif o in ('-u', '--unzip'):
            unzipFile = True
        elif o in ('-v', '--verbose'):
            verbose = True
        elif o in ('-d', '--days'):
            daysToDownload = a
        elif o in ('-D', '--date'):
            dateToDownload = a
        elif o in ('-f', '--format'):
            outputFormat = a
        elif o in ('--debug'):
            debug = True
            verbose = True # Turn on verbose if debug option is on.
        else:
            assert False, 'unhandled option'


def downloadFile(options):
    if options.verbose:
        print '-- begin script --'

    if (options.outputDirectory != '' and not os.path.exists(options.outputDirectory)):
        os.makedirs(options.outputDirectory)

    # Set the list of report dates.
    # A better approach is to grab the list of available dates
    # from the web site instead of generating the dates. Will
    # consider doing this in the future.
    reportDates = []
    if options.dateToDownload == None:
        for i in range(int(options.daysToDownload)):
            today = datetime.date.today() - datetime.timedelta(i + 1)
            reportDates.append( today )
    else:
        reportDates = [datetime.datetime.strptime(options.dateToDownload, '%m/%d/%Y').date()]

    if options.debug:
        print 'reportDates: ', reportDates


    ####
    if options.verbose:
        print 'Downloading daily sales reports.'
    unavailableCount = 0
    filenames = []
    for downloadReportDate in reportDates:
        dateString = downloadReportDate.strftime('%Y%m%d')
        path = os.path.realpath(os.path.dirname(sys.argv[0]))
        
        output = subprocess.check_output(['java', '-cp', path, 'Autoingestion', appleId, password, vendorId, 'Sales', 'Daily', 'Summary', dateString])
        print output
        lines = output.split('\n')
        
        if len(lines) >= 2 and lines[1].lower().startswith('file downloaded successfully'):
            gzfile = lines[0]
            # Check for an override of the file name. If found then set the file
            # name to match the outputFormat.
            if (options.outputFormat):
                filename = downloadReportDate.strftime(options.outputFormat)
            else:
                filename = gzfile
            
            if options.unzipFile:
                if options.verbose:
                    print 'Unzipping archive file: ', gzfile
                infile = gzip.GzipFile(gzfile)
            else:
                infile = open(gzfile, 'rb')
            
            filename = os.path.join(options.outputDirectory, filename)
            if options.unzipFile and filename[-3:] == '.gz': #Chop off .gz extension if not needed
                filename = os.path.splitext( filename )[0]

            if options.verbose:
                print 'Saving download file:', filename

            downloadFile = open(filename, 'wb')
            downloadFile.write(infile.read())
            downloadFile.close()
            infile.close()
            
            if options.verbose:
                print 'Deleting archive file: ', gzfile
            os.remove(gzfile)

            filenames.append( filename )
        else:
            print 'Report failed to download for', downloadReportDate
            unavailableCount += 1
    # End for downloadReportDate in reportDates:
    ####

    if unavailableCount > 0:
        raise ITCException, '%i report(s) not available - try again later' % unavailableCount

    if options.debug:
        os.remove(os.path.join(options.outputDirectory, "temp.html"))
    if options.verbose:
        print '-- end of script --'

    return filenames


def main():
    if processCmdArgs() > 0:    # Will exit if usage requested or invalid argument found.
      return 2
      
    # Set report options.
    options = ReportOptions()
    options.appleId = appleId
    options.password = password
    options.outputDirectory = outputDirectory
    options.unzipFile = unzipFile
    options.verbose = verbose
    options.daysToDownload = daysToDownload
    options.dateToDownload = dateToDownload
    options.outputFormat = outputFormat
    options.debug = debug
    
    # Download the file.
    try:
        downloadFile(options)
    except ITCException, e:
        print e.value
        return 1


if __name__ == '__main__':
  sys.exit(main())
