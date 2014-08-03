# YonderGit

One of the great strengths of Git is the multiple and flexible ways of handling
remote repositories. Just like Subversion, they can be "served" out of a
location, but more generally, if you can reach it from your computer through
any number of ways (ssh, etc.), you can git it. YonderGit wraps up a number of
a common operations with remote repositories: creating, initializing, adding to
(associating with) the local repository, removing, etc. You can clone your own
copy of the YonderGit code repository using:

    git clone git://github.com/jeetsukumaran/YonderGit.git

Or you can download an archive directly here:

    http://github.com/jeetsukumaran/YonderGit/archives/master.

After downloading, enter "sudo python setup.py" in the YonderGit directory to
install. This will just copy the "ygit.py" script to your system path. After
that, enter "ygit.py commands?" for a summary of possible commands, or "ygit.py
--help" for help on options.

## Quick Summary of Commands

-   Create directory specified by "REPO-URL", using either the "ssh" or local
    filesystem transport protocol, initialize it as repository by running "git
    init", and add it as a remote called "NAME" of the local git repository. Will
    fail if directory already exists:

        $ ygit.py setup NAME REPO-URL

-   Create directory specified by "REPO-URL", using either the "ssh" or local
    filesystem transport protocol, and then initialize it as repository by
    running "git init". Will fail if directory already exists:

        $ ygit.py create REPO-URL

-   Initialize remote directory "REPO-URL" as a repository by running "git
    init" in the directory (will fail if directory does not already exist):

        $ ygit.py init REPO-URL

-   Add "REPO-URL" as a new remote called "NAME" of the local git repository.

        $ ygit.py add NAME REPO-URL

-   Recursively remove the directory "REPO-URL" and all subdirectories and
    files.

        $ ygit.py delete REPO-URL

## Valid Repository URL Syntax

### Secure Shell Transport Protocol

    ssh://user@host.xz:port/path/to/repo.git/
    ssh://user@host.xz/path/to/repo.git/
    ssh://host.xz:port/path/to/repo.git/
    ssh://host.xz/path/to/repo.git/
    ssh://user@host.xz/path/to/repo.git/
    ssh://host.xz/path/to/repo.git/
    ssh://user@host.xz/~user/path/to/repo.git/
    ssh://host.xz/~user/path/to/repo.git/
    ssh://user@host.xz/~/path/to/repo.git
    ssh://host.xz/~/path/to/repo.git
    user@host.xz:/path/to/repo.git/
    host.xz:/path/to/repo.git/
    user@host.xz:~user/path/to/repo.git/
    host.xz:~user/path/to/repo.git/
    user@host.xz:path/to/repo.git
    host.xz:path/to/repo.git
    rsync://host.xz/path/to/repo.git/

### Git Transport Protocol

    git://host.xz/path/to/repo.git/
    git://host.xz/~user/path/to/repo.git/
    HTTP/S Transport Protocol

    http://host.xz/path/to/repo.git/
    https://host.xz/path/to/repo.git/
    Local (Filesystem) Transport Protocol

    /path/to/repo.git/
    path/to/repo.git/
    ~/path/to/repo.git
    file:///path/to/repo.git/
    file://~/path/to/repo.git/

## Installation

To install, run::

    $ sudo python setup.py install

Alternatively, you can just copy all the scripts in the ``scripts``
subdirectory to some place on your system path.

## Copyright and License

(C) 2008 Jeet Sukumaran.

The code is free software; you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation; either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see http://www.gnu.org/licenses/.

