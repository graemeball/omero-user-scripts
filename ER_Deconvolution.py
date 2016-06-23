#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2016 Graeme Ball / Dundee Imaging Facility.
# All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
ER_deconvolution.py

OMERO script to run Priism ER deconvolution algorithm (remotely)

"""

import os
import shutil
import time
import json
import omero.scripts as script
from omero.gateway import BlitzGateway
from omero.rtypes import rstring, rlong
import omero.cli


# name of job definition file, and job parameters
jobs_filename = 'core2_decon.jobs'
results_filename = 'core2_decon.results'
job = {'command': 'core2_decon',
       'par.alpha': 5000,
       'par.lamf': 0.5,
       'par.niter': 25}

TEMP = '/ngom/'  # temp data folder (shared with processor/s)
KEEPALIVE_PULSE = 300
RESULTS_POLL_PULSE = 6  # FIXME -- change to 60 after testing!
TIMEOUT = 360  # FIXME -- increase afer testing!
HOST = 'localhost'  # BlitzGateway .host says 'null' :-[


def run():
    """
    Launch (remote) Priism ER deconvolution job on a list of images.
    Results imported back into dataset of origin for each image.
    """

    # Build GUI dialog for user to choose images & update parameters
    client = script.client(
        "ER_Deconvolution.py", "ER deconvolution",

        script.String(
            "Data_Type", optional=False,
            grouping="1", values=[rstring('Image')], default="Image"),

        script.List(
            "IDs", optional=False,
            description="image IDs (must have original .dv file!)",
            grouping='2').ofType(rlong(0)),

        script.Int(
            "alpha", optional=False,
            description='regularization parameter "alpha" - try 1000-10000',
            grouping='3', default=job['par.alpha'], min=0),

        script.Float(
            "lambda f", optional=False,
            description='smoothing parameter "lambda f" - try 0.1-1.0',
            grouping='4', default=job['par.lamf'], min=0.0, max=1.0),

        script.Int(
            "iterations", optional=False,
            description="number of iterations - try 10-100",
            grouping='5', default=job['par.niter'], min=0),

        version="0.99",
        authors=["Graeme Ball"],
        institutions=["Dundee Imaging Facility"],
        contact="g.ball@dundee.ac.uk"
    )

    try:
        tempdir = None
        input_image_ids = [int(n) for n in client.getInput("IDs", unwrap=True)]
        job['par.alpha'] = client.getInput("alpha", unwrap=True)
        job['par.lamf'] = client.getInput("lambda f", unwrap=True)
        job['par.niter'] = client.getInput("iterations", unwrap=True)

        conn = BlitzGateway(client_obj=client)
        user = str(conn.getUser().getName())
        group = str(conn.getGroupFromContext().getName())
        sid = client.getSessionId()

        # export images (must be .dv!) to shared / temp storage
        tempdir = mktempdir(user, TEMP)
        inputs = []
        for iid in input_image_ids:
            try:
                path = export_original_dvfile(conn, iid, tempdir)
                image = conn.getObject("Image", iid)
                fail(image is None, "No such image, ID=%d" % iid)
                did = image.getParent().getId()
                inputs.append({'imageID': iid, 'path': path, 'datasetID': did})
            except RuntimeError as e:
                print "Fail: " + str(e)

        jobs = []
        for inp in inputs:
            command = dict(job)  # copy
            command['inputs'] = [inp]  # only 1 input image for this job
            jobs.append(json.dumps([command]))  # only 1 command for this job
        # N.B. '.jobs' file format more flexible than needed here
        # write jobs definition file (1 line json string per job)
        jobs_filepath = os.path.join(tempdir, jobs_filename)
        with open(jobs_filepath, 'w') as f:
            f.writelines(["%s\n" % j for j in jobs])

        # poll filesystem, checking for results
        client.enableKeepAlive(KEEPALIVE_PULSE)
        results_filepath = os.path.join(tempdir, results_filename)
        result_count = 0  # results .json file grows as results appear
        import_count = 0  # ensure we only attempt to import each result once
        tstart = time.time()
        while result_count < len(inputs) and (time.time() - tstart) < TIMEOUT:
            time.sleep(RESULTS_POLL_PULSE)
            if os.path.exists(results_filepath):
                with open(results_filepath, 'r') as fr:
                    results = fr.readlines()  # 1 line json string per result
                    new_results = results[import_count:]
                    import_count += import_results(new_results, user, group,
                                                   sid, conn)
                    result_count = len(results)
        if result_count < len(inputs):
            print "Job timed out after %d seconds, %d results imported" % \
                (TIMEOUT, import_count)

    finally:
        if tempdir is not None and tempdir.startswith(TEMP):
            if os.path.exists(tempdir):
                shutil.rmtree(tempdir)  # we checked 'tempdir' is sane first!
        client.closeSession()


def mktempdir(user, temp):
    """Create a temporary dir based on user and time, and return path"""
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    tempdir = os.path.join(temp, user + "_" + timestamp)
    if not os.path.exists(tempdir):
        os.mkdir(tempdir)
    return tempdir


def export_original_dvfile(conn, imageID, tempdir):
    """Find .dv in original files of imageID, export and return path"""
    image = conn.getObject("Image", imageID)
    i = "Image ID=%d" % imageID  # just a str for error messages
    fail(image is None, i + " not found")
    im_files = list(image.getImportedImageFiles())
    fail(len(im_files) == 0, "%s has no original files" % i)
    dv = None
    for im_file in im_files:
        if im_file.getName()[-3:] == '.dv':
            dv = im_file
    fail(dv is None, "%s has no original .dv file" % i)
    export_dv_name = dv.getName()[:-3] + "_ID%d.dv" % imageID
    export_path = os.path.join(tempdir, export_dv_name)
    with open(export_path, "wb") as f:
        for chunk in dv.getFileInChunks():
            f.write(chunk)
    return export_path


def fail(when, why):
    if when:
        raise RuntimeError(why)


def import_results(results, user, group, sid, conn):
    """
    Import new results, print errors, return number of attempted imports

    'results' is a list of json strings representing dicts with keys:
        inputID: input Image ID
        fail: string with error message for failed processing job
        datasetID: dataset ID for this result (same as input image)
        results: 1st path uploaded as image file, all others attached
    """
    for result in results:
        try:
            r = json.loads(result)
            if 'fail' in r:
                print "ER decon failed for imageID=%s: %s" \
                    % (r['inputID'], r['fail'])
            else:
                cli = omero.cli.CLI()
                cli.loadplugins()
                import_args = ["import", "-s", HOST, "-k", "%s" % sid]
                import_args += ["-d", str(r['datasetID'])]
                result_dir = os.path.split(r['results'][0])[0]
                plog = os.path.join(result_dir, "imports.log")
                perr = os.path.join(result_dir, "imports.err")
                result_image = r['results'][0]
                import_args += ["---errs", perr, "---file", plog, result_image]
                cli.invoke(import_args, strict=True)
                with open(plog, 'r') as flog:
                    pix = int(flog.readlines()[0].rstrip())  # Pixels ID
                iid = conn.getQueryService().get("Pixels", pix).image.id.val
                img = conn.getObject("Image", oid=iid)
                descrip = "ER decon result from Image ID: %s" % r['inputID']
                img.setDescription(descrip)
                # attach remaining results
                if len(r['results']) > 1:
                    for attachment in r['results'][1:]:
                        fann = conn.createFileAnnfromLocalFile(str(attachment))
                        img.linkAnnotation(fann)
                img.save()

        except Exception as e:
            print str(e)

    return len(results)


if __name__ == "__main__":
    run()
