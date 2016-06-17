OMERO User Scripts
==================

Installation
------------

1. Change into the scripts location of your OMERO installation

        cd OMERO_DIST/lib/scripts

2. Clone the repository with a unique name (e.g. "useful_scripts")

        git clone https://github.com/THISREPOSITORY/omero-user-scripts.git UNIQUE_NAME

3. Update your list of installed scripts by examining the list of scripts
   in OMERO.insight or OMERO.web, or by running the following command

        path/to/bin/omero script list

Upgrading
---------

1. Change into the repository location cloned into during installation

        cd OMERO_DIST/lib/scripts/UNIQUE_NAME

2. Update the repository to the latest version

        git pull --rebase

3. Update your list of installed scripts by examining the list of scripts
   in OMERO.insight or OMERO.web, or by running the following command

        path/to/bin/omero script list

Developer Installation
----------------------

1. Fork [omero-user-scripts](https://github.com/ome/omero-user-scripts/fork) in your own GitHub account

2. Change into the scripts location of your OMERO installation

        cd OMERO_DIST/lib/scripts

3. Clone the repository

        git clone git@github.com:YOURGITUSER/omero-user-scripts.git YOUR_SCRIPTS

Adding a script
---------------

1. Choose a naming scheme for your scripts. The name of the clone
   (e.g. "YOUR_SCRIPTS"), the script name, and all sub-directories will be shown
   to your users in the UI, so think about script organization upfront.

   a. If you don't plan to have many scripts, then you need not have any sub-directories
      and can place scripts directly under YOUR_SCRIPTS.

   b. Otherwise, create a suitable sub-directory. Examples of directories in use can be
      found in the [official scripts](https://github.com/ome/scripts) repository.

2. Place your script in the chosen directory:
  * If you have an existing script, simply save it.
  * Otherwise, copy [Example.txt](Example.txt) and edit it in place. (Don't use git mv)

3. Add the file to git, commit, and push.

Testing your script
-------------------

1. List the current scripts in the system

        path/to/bin/omero script list

2. List the parameters

        path/to/bin/omero script params SCRIPT_ID

3. Launch the script

        path/to/bin/omero script launch SCRIPT_ID

4. See the [developer documentation](https://www.openmicroscopy.org/site/support/omero4/developers/scripts/)
   for more information on testing and modifying your scripts.

Legal
-----

See [LICENSE](LICENSE)


# About #
This section provides machine-readable information about your scripts.
It will be used to help generate a landing page and links for your work.
Please modify **all** values on **each** branch to describe your scripts.

###### Repository name ######
NGOM Processing scripts

###### Minimum version ######
5.2

###### Maximum version ######
5.2

###### Owner(s) ######
Graeme Ball

###### Institution ######
University of Dundee

###### URL ######
https://github.com/graemeball/omero-user-scripts/blob/master/README.md

###### Email ######
g.ball@dundee.ac.uk

###### Description ######
Processing scripts for running slow, resource-intensive jobs remotely
(deconvolution, denoising etc.) via a shared filesystem. These OMERO
scripts write a .json "job definition" file and import results, as they
appear, to the same dataset as the input images. The actual processing
is carried out separately by a daemon that watches the shared FS.

In Dundee, the hardware used to run these remote processing jobs has
been funded by an MRC Next Generation Optical Microscopy (NGOM) award
-- hence the repository name.
