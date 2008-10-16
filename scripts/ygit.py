#! /usr/bin/env python

############################################################################
##  ygit.py
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
Remote git repository creation and management.
"""

import sys
import os
import getpass
from optparse import OptionGroup
from optparse import OptionParser
import re
import subprocess

############################################################################
## Parsing Git repository URL's

EXAMPLE_URLS = [
    'rsync://host.xz/path/to/repo.git/',
    'http://host.xz/path/to/repo.git/',
    'https://host.xz/path/to/repo.git/',
    'git://host.xz/path/to/repo.git/',
    'git://host.xz/~user/path/to/repo.git/',
    'ssh://user@host.xz:port/path/to/repo.git/',
    'ssh://user@host.xz/path/to/repo.git/',
    'ssh://host.xz:port/path/to/repo.git/',
    'ssh://host.xz/path/to/repo.git/',
    'ssh://user@host.xz/path/to/repo.git/',
    'ssh://host.xz/path/to/repo.git/',
    'ssh://user@host.xz/~user/path/to/repo.git/',
    'ssh://host.xz/~user/path/to/repo.git/',
    'ssh://user@host.xz/~/path/to/repo.git',
    'ssh://host.xz/~/path/to/repo.git',
    'user@host.xz:/path/to/repo.git/',
    'host.xz:/path/to/repo.git/',
    'user@host.xz:~user/path/to/repo.git/',
    'host.xz:~user/path/to/repo.git/',
    'user@host.xz:path/to/repo.git',
    'host.xz:path/to/repo.git',
    '/path/to/repo.git/',
    'path/to/repo.git/',
    '~/path/to/repo.git',
    'file:///path/to/repo.git/',
    'file://~/path/to/repo.git/',
]

class RepositoryReference(object):
    """
    Wraps parsing of Git repository URL specifications.
    """

    def __init__(self, url=None):
        """
        Initializes variables to default values.
        """
        self.url = None
        self.protocol = None
        self.user = None
        self.host = None
        self.port = None
        self.repo_path = None
        self.dir_name = None
        self.repo_name = None
        self.repo_basename = None
        if url is not None:
            self.parse_from_url(url)

    def parse_repo_path(self, path):
        """
        Given a file or directory path, stores it as-is in
        self.repo_path, but then also tries to parse out the directory
        path component and the repository (directory) name component.
        """
        sep = os.path.sep
        if path.endswith(sep):
            path = path[:-1]
        self.dir_name = os.path.dirname(path)
        self.repo_name = os.path.basename(path)
        if not self.repo_name.endswith(".git"):
            self.repo_name += ".git"
        self.repo_basename = os.path.splitext(self.repo_name)[0]
        self.repo_path = os.path.join(self.dir_name, self.repo_name)

    def parse_from_url(self, url):
        """
        Does the bulk of the work of parsing out components of a repostiory URL
        specification.
        """
        self.__init__()
        self.url = url
        p_file = re.compile('file://(.*)')
        p_general = re.compile('(\w+://)(.+@)*([\w\d\.]+)(:[\d]+){0,1}/*(.*)')
        p_unspec = re.compile('(.+@)*([\w\d\.]+):(.*)')
        match = p_file.match(url)
        if match:
            self.protocol='file'
            self.parse_repo_path(match.group(1))
        else:
            match = p_general.match(url)
            if match:
                self.protocol = match.group(1).split(":")[0]
                if match.group(2):
                    self.user = match.group(2)[:-1]
                self.host = match.group(3)
                if match.group(4):
                    self.port = match.group(4)[1:]
                if match.group(5):
                    path = match.group(5)
                    if not path.startswith("~"):
                        path = "/" + path
                    self.parse_repo_path(path)
            else:
                match = p_unspec.match(url)
                if match:
                    if match.group(1):
                        self.user = match.group(1)[:-1]
                    self.host = match.group(2)
                    path = match.group(3)
                    self.parse_repo_path(path)
                    self.protocol='ssh'
                else:
                    # assume path
                    self.protocol='file'
                    self.parse_repo_path(url)

############################################################################
## Talking to the user

class Messenger(object):
    """
    Handles reporting of messages to user depending on settings and options.
    """

    def __init__(self,
                 ygit_quiet=False,
                 git_verbose=False,
                 all_quiet=False,
                 show_commands=False,
                 show_debug=False,
                 dry_run=False):
        self.ygit_quiet = ygit_quiet
        self.git_verbose = git_verbose
        self.all_quiet = all_quiet
        if self.all_quiet:
            self.ygit_quiet = True
            self.git_verbose = False
        self.show_commands = show_commands
        self.show_debug = show_debug
        self.dry_run = dry_run

    def newline_suffix(self, newline):
        if newline:
            suffix = "\n"
        else:
            suffix = ""
        return suffix

    def critical(self, msg, newline=True):
        sys.stdout.write(msg + self.newline_suffix(newline))

    def debug(self, msg, newline=True):
        if self.show_debug:
            sys.stdout.write(msg + self.newline_suffix(newline))

    def ygit_info(self, msg, newline=True):
        if not self.ygit_quiet:
            sys.stdout.write(msg + self.newline_suffix(newline))

    def info(self, msg, newline=True):
        sys.stdout.write(msg + self.newline_suffix(newline))

    def ygit_command(self, msg, newline=True):
        if self.show_commands or self.show_debug:
            if self.dry_run:
                prefix = "   DUMMY RUN: "
            else:
                prefix = "   EXECUTING: "
            sys.stdout.write("%s%s%s" % (prefix, msg, self.newline_suffix(newline)))

    def error(self, msg, newline=True):
        sys.stderr.write(msg + self.newline_suffix(newline))

    def compose_repo_ref(self, repo_ref):
        return repo_ref.url


############################################################################
## Core remote handlers

def remote_exists(repo_ref, messenger):
    """
    Checks if the directory at repo_ref exists. Returns True if it does, False
    otherwise.
    """
    #messenger.ygit_info("Checking if repository path exists: %s" % messenger.compose_repo_ref(repo_ref))
    if repo_ref.protocol == 'ssh':
        command = repo_ref.ssh_command + " 'if test -e %s; then echo 1; fi\'" % repo_ref.repo_path
        messenger.ygit_command(command)
        check = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check_stdout, check_stderr = check.communicate()
        if check_stderr:
            messenger.error(check_stderr, newline=False)
            error = True
        else:
            error = False
        if check_stdout:
            exists = True
        else:
            exists = False
    elif repo_ref.protocol == 'file':
        exists = os.path.exists(repo_ref.repo_path)
        error = False
    return exists, error

def check_remote(repo_ref, messenger, opts):
    """
    Inspect remote.
    """
    messenger.ygit_info("Checking: %s" % messenger.compose_repo_ref(repo_ref))
    exists, error = remote_exists(repo_ref=repo_ref, messenger=messenger)
    if error:
        messenger.error("Error connnecting to: %s" % messenger.compose_repo_ref(repo_ref))
        sys.exit(1)
    if exists:
        messenger.ygit_info("Repository path exists.")
        if repo_ref.protocol == 'ssh':
            command = repo_ref.ssh_command + " 'cd %s'" % repo_ref.repo_path
            messenger.ygit_command(command)
            check = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            check_stderr = check.communicate()[1]
            if check_stderr:
                isdir = False
            else:
                isdir = True
        elif repo_ref.protocol == 'file':
            isdir = os.path.isdir(repo_ref.repo_path)
        if isdir:
            messenger.ygit_info("Repository path is an accessible directory.")
        else:
            messenger.error("Failed to enter directory: %s." % messenger.compose_repo_ref(repo_ref))
            sys.exit(1)
#         messenger.ygit_info("Checking repository status ...")
#         if repo_ref.protocol == 'ssh':
#             command = repo_ref.ssh_command + " \"cd %s; git status\"" % repo_ref.repo_path
#         elif repo_ref.protocol == 'file':
#             command = "cd '%s'; git status" % repo_ref.repo_path
#         messenger.ygit_command(command)
#         gstatus = subprocess.Popen([command], shell=True, stdin=sys.stdin)
#         retcode = gstatus.wait()
#         if retcode:
#             messenger.error("Error checking repository status.")
#             sys.exit(1)
    else:
        messenger.error("Repository not found at: %s" % messenger.compose_repo_ref(repo_ref))
        sys.exit(1)

def remove_remote(repo_ref, messenger, opts):
    """
    Delete repository ... USE WITH CAUTION!
    """
    exists, error = remote_exists(repo_ref=repo_ref, messenger=messenger)
    if error:
        messenger.error("Error connnecting to: %s" % messenger.compose_repo_ref(repo_ref))
        sys.exit(1)
    if exists:
        messenger.ygit_info("Removing repository: %s" % messenger.compose_repo_ref(repo_ref))
        if repo_ref.protocol == 'ssh':
            command = repo_ref.ssh_command + " 'rm -r %s'" % repo_ref.repo_path
        elif repo_ref.protocol == 'file':
            command = "rm -r '%s'" % repo_ref.repo_path
        messenger.critical("About to execute:")
        messenger.critical("    %s" % command)
        messenger.critical("Continue (y/N)? ", newline=False)
        ok = raw_input()
        if not ok.lower().startswith("y"):
            messenger.critical("Cancelling.")
            sys.exit(1)
        messenger.ygit_command(command)
        if not opts.dry_run:
            rm = subprocess.Popen([command], shell=True, stdin=sys.stdin)
            retcode = rm.wait()
        else:
            retcode = 0
        if retcode:
            messenger.error("Error removing repository.")
            sys.exit(1)
        else:
            messenger.info("Repository removed, but may still be referenced in local.")
            messenger.info('Use "git remote rm <name>" to remove reference.')
    else:
        messenger.error("Repository not found: %s" % messenger.compose_repo_ref(repo_ref))

def create_remote(repo_ref, messenger, opts, init=True):
    """
    Create and (optionally) initialize a new repository directory.
    """
    exists, error = remote_exists(repo_ref=repo_ref, messenger=messenger)
    if error:
        messenger.error("Error connnecting to: %s" % messenger.compose_repo_ref(repo_ref))
        sys.exit(1)
    if exists:
        messenger.error("Repository already exists.")
        messenger.error("Please remove the repository before proceeding, or use another location.")
        sys.exit(1)
    if opts.all_quiet:
        git_stdout = subprocess.PIPE
    else:
        git_stdout = None
    messenger.ygit_info('Creating remote directory: "%s"' % repo_ref.repo_path)
    if repo_ref.protocol == 'ssh':
        command = repo_ref.ssh_command + " 'mkdir -p %s'" % repo_ref.repo_path
        messenger.ygit_command(command)
        if not opts.dry_run:
            create = subprocess.Popen([command], shell=True, stdin=sys.stdin, stdout=git_stdout)
            retcode = create.wait()
        else:
            retcode = 0
    elif repo_ref.protocol == 'file':
        if not opts.dry_run:

            # ignore directory creation errors,
            # but report error if directory does not exist
            # after all is said anddone mimics (sorta) "mkdir -p"
            try:
                os.makedirs(repo_ref.repo_path)
            except:
                pass
            if not os.path.exists(repo_ref.repo_path):
                retcode = 1
            else:
                retcode = 0
#             if not opts.dry_run:
#                 try:
#                     os.makedirs(repo_ref.repo_path)
#                     retcode = False
#                 except:
#                     retcode = True
#             else:
#                  retcode = False
    if retcode:
        messenger.error("Error creating directory.")
        sys.exit(1)
    if init:
        init_remote(repo_ref=repo_ref,
                    messenger=messenger,
                    opts=opts,
                    check=False)

def init_remote(repo_ref, messenger, opts, check=True):
    """
    Initialize a new remote repository
    """
    if check:
        check_remote(repo_ref=repo_ref, messenger=messenger, opts=opts)
    if opts.bare:
        bare = "--bare"
    else:
        bare = ""
    if opts.shared:
        shared = "--shared=" + opts.shared
    else:
        shared = ""
    init_command = "cd %s; git init %s %s; git update-server-info" % (repo_ref.repo_path, bare, shared)
    if repo_ref.protocol == 'ssh':
        command = repo_ref.ssh_command + ' "' + init_command + '"'
        host = str(repo_ref.host)
    elif repo_ref.protocol == 'file':
        command = init_command
        host = "localhost"
    messenger.ygit_command(command)
    if not opts.dry_run:
        init = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
        stdout = init.communicate()[0]
        if opts.all_quiet:
            pass
        else:
            messenger.info("[%s] %s" % (host, stdout), newline=False)
        if init.returncode:
            messenger.error("Error initializing repository.")
            sys.exit(1)

def add_remote(remote_name, repo_ref, messenger, opts):
    """
    Add a new remote repository to the local one.
    """
    if opts.all_quiet:
        git_stdout = subprocess.PIPE
    else:
        git_stdout = None
    if opts.mirror:
        mirror = "--mirror"
    else:
        mirror = ""
    messenger.ygit_info("Adding \"%s\": \"%s\"" % (remote_name, repo_ref.url))
    command = "cd \"%s\"; git remote add %s %s '%s' " % (opts.local_repo, mirror, remote_name, repo_ref.url)
    messenger.ygit_command(command)
    if not opts.dry_run:
        proc = subprocess.Popen([command], shell=True, stdout=git_stdout, stderr=subprocess.PIPE)
        retcode = proc.wait()
        if retcode:
            err = proc.stderr.read()
            messenger.error(err, newline=False)
            if err.lower().count("not a git repository"):
                hint = ' (have you run "git init" locally?)'
            elif err.lower().count("already exists"):
                hint = ' (maybe a remote called "%s" is already defined?)' % remote_name
            messenger.error('Error adding remote%s.' % hint)
            sys.exit(1)
    messenger.ygit_info('Configuring (master) branches for "%s"' % remote_name)
    command = "git config branch.master.remote '%s'" % remote_name
    messenger.ygit_command(command)
    if not opts.dry_run:
        proc = subprocess.Popen([command], shell=True, stdout=git_stdout)
        proc.wait()
    command = "git config branch.master.merge 'refs/heads/master'"
    messenger.ygit_command(command)
    if not opts.dry_run:
        proc = subprocess.Popen([command], shell=True, stdout=git_stdout)
        proc.wait()


def show_commands_help(stream=sys.stdout):
    stream.write("""\
    
Usage: ygit.py [options] <ACTION> <REPO-URL>
----------------+-----------------------------------------------------------
If ACTION is:   | YonderGit Will:
----------------+-----------------------------------------------------------
actions         | show this message and exit
setup REPO-URL  | create and initialize a new repository at REPO-URL,
                | and add it as a remote of the local one; equivalent
                | to "--create" and "--add"
create REPO-URL | create a new directory at REPO-URL and initialize it as a
                | new repository (including running "server-update-info")
init REPO-URL   | initialize existing directory at REPO-URL as a repository
add REPO-URL    | add REPO-URL as a remote reference to the local git
                | repository of the current directory
check REPO-URL  | check the existence of an accessible directory given
                | specified by REPO-URL
remove REPO-URL | recursively remove the directory specified by REPO-URL and
                | all subdirectories.
----------------+-----------------------------------------------------------
See "ygit.py --help" for help on options.
""")

############################################################################
## Main CLI

_prog_usage = '%prog [options] <ACTION> <REPO-URL>'
_prog_version = 'YonderGit Version 1.1'
_prog_description = """\
Remote Git repository manager: create, initialize and/or add a Git repository
at REPO-URL as a remote of the local repository. See "ygit.py actions" for
help on action commands."""
_prog_author = 'Jeet Sukumaran'
_prog_copyright = 'Copyright (C) 2008 Jeet Sukumaran.'
def main():
    """
    Main CLI handler.
    """

    parser = OptionParser(usage=_prog_usage,
                          add_help_option=True,
                          version=_prog_version,
                          description=_prog_description)

    parser.add_option('-?', '--actions',
        action='store_true',
        dest='actions',
        default=False,
        help='show list of possible action commands and exit')

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

    parser.add_option('-v', '--verbose',
        action='store_true',
        dest='git_verbose',
        default=False,
        help='run git subprocesses verbosely')

    parser.add_option('-x', '--show',
        action='store_true',
        dest='show_commands',
        default=False,
        help='show commands as they are executed')

    parser.add_option('--debug',
        action='store_true',
        dest='show_debug',
        default=False,
        help='show debugging messages (assumes "--show")')

    parser.add_option('--dry-run',
        action='store_true',
        dest='dry_run',
        default=False,
        help='do not actually do anything')

    act_opts = OptionGroup(parser, 'Actions')
    parser.add_option_group(act_opts)

    init_opts = OptionGroup(parser, 'Initialization Options')
    parser.add_option_group(init_opts)

    init_opts.add_option('--bare',
        action='store_true',
        dest='bare',
        default=True,
        help='make the remote bare (i.e., no working tree); this is the ' \
            + 'default (use "--working" to override)')

    init_opts.add_option('--working',
        action='store_false',
        dest='bare',
        help='create a working tree for the remote')

    init_opts.add_option('--shared',
        action='store',
        dest='shared',
        metavar="[={false|true|umask|group|all|world|everybody|0xxx}]",
        default="umask",
        help='Specify that the git repository is to be shared amongst several' \
            + ' users. This allows users belonging to the same group to push ' \
            + 'into that repository. When specified, the config variable ' \
            + '"core.sharedRepository" is set so that files and directories ' \
            + 'under REPO-URL are created with the requested permissions. ' \
            + 'When not specified, git will use permissions reported by ' \
            + 'umask(2). For more information, see "git help init".')

    add_opts = OptionGroup(parser, 'Adding Options')
    parser.add_option_group(add_opts)

    add_opts.add_option('-n', '--name',
        action='store',
        dest='name',
        default=None,
        help='name for repository at REPO-URL (default is server name if using ' \
            +' the ssh protocol or base repository parent directory name if '
            +' using file protocol)')

    add_opts.add_option('--mirror',
        action='store_true',
        dest='mirror',
        default=False,
        help='In mirror mode, enabled with --mirror, the refs will not be ' \
            + 'in the refs/remotes/ namespace, but in refs/heads. This option' \
            + ' only makes sense in bare repositories. If a remote uses ' \
            + 'mirror mode, furthermore, git push will always behave as if ' \
            + '--mirror was passed.')
    add_opts.add_option('-l', '--local-repo',
        action='store',
        dest='local_repo',
        default=os.path.abspath('.'),
        metavar="<LOCAL-REPO>",
        help='location of local repository to which REPO-URL will be added ' \
           + 'as a remote (default is the current directory); ' \
           + 'if this is not an initialized Git repository then ' \
           + 'the "add" operation will fail.')

    (opts, args) = parser.parse_args()

    messenger = Messenger(ygit_quiet=opts.ygit_quiet,
                          git_verbose=opts.git_verbose,
                          all_quiet=opts.all_quiet,
                          show_commands=opts.show_commands,
                          show_debug=opts.show_debug,
                          dry_run=opts.dry_run)

    if opts.actions:
        show_commands_help(sys.stdout)
        sys.exit(1)    
        
    # order actions will be executed if multiple specified:
    # check, remove, create (init), init, add
        
    if len(args) < 2 or args[0].lower().startswith("actions"):
        if len(args) == 0:
            messenger.error("Please specify an action and a remote repository:")
        elif len(args) == 1:
            messenger.error("Please specify a remote repository reference:")
        show_commands_help(sys.stderr)
        sys.exit(1)

    action_command = args[0].lower()
    action_check = False
    action_remove = False
    action_create = False
    action_init = False
    action_add = False
    if action_command == 'check':
        action_check = True
    if action_command == 'remove':
        action_remove = True
    if action_command == 'setup':
        action_create = True
        action_add = True
    if action_command == 'create':
        action_create = True
    if action_command == 'init':
        action_init = True
    if action_command == 'add':
        action_add = True

    if not action_check \
        and not action_create \
        and not action_init \
        and not action_add \
        and not action_remove:
        messenger.error('Need to specify an action: check, remove, setup, ' \
                        +'create, init, or add.')
        messenger.error('See "ygit.py actions" for more information.')
        sys.exit(1)

    remote_url = args[1]

    if remote_url.count(' ') or remote_url.count('\t'):
        messenger.error("Whitespace detected in URL path: refusing to continue with this insanity.")
        sys.exit(1)

    repo_ref = RepositoryReference(remote_url)

    if opts.name is None:
        if repo_ref.host is not None:
            remote_name = repo_ref.host
        elif repo_ref.dir_name is not None:
            remote_name = os.path.basename(os.path.expanduser(os.path.expandvars(repo_ref.repo_path)))
        else:
            remote_name = "origin"
    else:
        remote_name = opts.name

    #messenger.ygit_info("%s" % (_prog_version))

    messenger.debug('\n---')
    if remote_name:
        messenger.debug('    Remote: "%s"' % remote_name)
    if repo_ref.protocol:
        messenger.debug("  Protocol: %s" % repo_ref.protocol)
    if repo_ref.user:
        messenger.debug("      User: %s" % repo_ref.user)
    if repo_ref.host:
        messenger.debug("      Host: %s" % repo_ref.host)
    if repo_ref.port:
        messenger.debug("      Port: %s" % repo_ref.port)
    if repo_ref.dir_name:
        messenger.debug(" Directory: %s" % repo_ref.dir_name)
    if repo_ref.repo_name:
        messenger.debug("Repository: %s" % repo_ref.repo_name)
    messenger.debug('---\n')

    # setup support for actions
    if repo_ref.protocol == 'ssh':
        if repo_ref.user is None:
            repo_ref.user = getpass.getuser()
        repo_ref.ssh_command = "ssh " + repo_ref.user + "@" + repo_ref.host
    elif repo_ref.protocol == 'file':
        repo_ref.repo_path = os.path.expanduser(os.path.expandvars(repo_ref.repo_path))

    # check #
    if action_check:
        if repo_ref.protocol != 'ssh' and repo_ref.protocol != 'file':
            messenger.error('Currently only supporting "ssh" or "file" protocol for repository checking.')
            sys.exit(1)
        check_remote(repo_ref=repo_ref, messenger=messenger, opts=opts)

    # remove #
    if action_remove:
        if repo_ref.protocol != 'ssh' and repo_ref.protocol != 'file':
            messenger.error('Currently only supporting "ssh" or "file" protocol for repository removal.')
            sys.exit(1)
        remove_remote(repo_ref=repo_ref, messenger=messenger, opts=opts)

    # create and/or init #
    if action_create:
        if repo_ref.protocol != 'ssh' and repo_ref.protocol != 'file':
            messenger.error('Currently only supporting "ssh" or "file" protocol for repository creation.')
            sys.exit(1)
        create_remote(repo_ref=repo_ref, messenger=messenger, opts=opts, init=True)
    elif action_init:
        if repo_ref.protocol != 'ssh' and repo_ref.protocol != 'file':
            messenger.error('Currently only supporting "ssh" or "file" protocol for repository initialization.')
            sys.exit(1)
        init_remote(repo_ref=repo_ref,
                    messenger=messenger,
                    opts=opts,
                    check=True)

    # add #
    if action_add:
        add_remote(remote_name, repo_ref, messenger, opts)

if __name__ == '__main__':
    main()





