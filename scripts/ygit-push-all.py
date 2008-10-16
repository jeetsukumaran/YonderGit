#! /usr/bin/env python

############################################################################
##  ygit-push-all.py
##
##  Copyright 2008 Jeet Sukumaran.
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this programm. If not, see <http://www.gnu.org/licenses/>.
##
############################################################################

"""
Simultaneously push to all remote repositories.
"""

import sys
import os
import subprocess
from optparse import OptionGroup
from optparse import OptionParser

_prog_usage = '%prog [options] <ACTION> <REPO-URL>'
_prog_version = 'ygit-push-all Version 1.0'
_prog_description = """\
Push out to all remote repositories"""
_prog_author = 'Jeet Sukumaran'
_prog_copyright = 'Copyright (C) 2008 Jeet Sukumaran.'

def show_command(command, opts):
    if opts.show_commands:
        sys.stdout.write("[" + command + "]\n")        

def main():
    """
    Main CLI handler.
    """

    parser = OptionParser(usage=_prog_usage,
                          add_help_option=True,
                          version=_prog_version,
                          description=_prog_description)
                                                                          
    parser.add_option('-q', '--quiet',
        action='store_true',
        dest='ygit_quiet',
        default=False,
        help='suppress all ygit wrapper messages')
        
    parser.add_option('-Q', '--all-quiet',
        action='store_true',
        dest='all_quiet',
        default=False,
        help='suppress all messages from both ygit and git subprocesses')
        
    parser.add_option('-x', '--show',
        action='store_true',
        dest='show_commands',
        default=False,
        help='show commands as they are executed')
        
    parser.add_option('--dry-run',
        action='store_true',
        dest='dry_run',
        default=False,
        help='do not actually do anything')   
        
    parser.add_option('-f', '--force',
        action='store_true',
        dest='force',
        default=False,
        help='force push')          
        
        
    (opts, args) = parser.parse_args()    
    
    if opts.all_quiet:
        ygit_stdout = open(os.devnull)
        git_stdout = subprocess.PIPE
    elif opts.ygit_quiet:
        ygit_stdout = open(os.devnull)
        git_stdout = None
    else:
        ygit_stdout = sys.stdout
        git_stdout = None    
        
    # get remote repositories
    command = "git remote"
    show_command(command, opts)

    proc = subprocess.Popen(command,
        shell=True,
        stdout=subprocess.PIPE)
    retcode = proc.wait()
    if retcode:
        sys.exit(1)
    else:
        remotes = []
        for remote in proc.stdout:
            remotes.append(remote.replace("\n",""))
    
    if opts.force:
        force = "-f "
    else:
        force = ""
    for remote in remotes:
        command = "git push %s%s" % (force, remote)
        show_command(command, opts)
        push = subprocess.Popen(command,
            shell=True,
            stdout=git_stdout)
        retcode = push.wait()

if __name__ == '__main__':
    main()





