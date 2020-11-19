import sys
import os
from ..functions.hxmt_funcs import *
from ..functions.my_funcs import *

import numpy as np
import datetime
import glob

import tkinter
from tkinter import filedialog

import logging

now = datetime.datetime.now()
date = ('%d_%d_%d') % (now.day,now.month,now.year)
time = ('%d_%d') % (now.hour,now.minute)

args = sys.argv
script = args[0]
logger_name = '{}_D{}_T{}.log'.format(script,date,time)

timeres = 1
minch = 26
maxch = 120
for arg in args:
    if 'minch' in arg:
        minch = float(arg.split('=')[1].strip())
    if 'maxch' in arg:
        maxch = float(arg.split('=')[1].strip())
    if 'timeres' in arg:
        timeres = eval(arg.split('=')[1].strip())
#mf.initialize_logger(logger_name)

root = tkinter.Tk()
root.withdraw()
# DF contains all the compressed data
# df = filedialog.askdirectory(initialdir='/media/QNAP_40T_HD/HXMTdata_version20200927',
                             #title='Select one of the sources')
# target = os.path.basename(df)
parent_data_dir = '/media/QNAP_40T_HD/HXMTdata_version20200927'
folders = next(os.walk(parent_data_dir))[1]
for i,folder in enumerate(folders):
    print('{}) {}'.format(i+1,folder))
index = int(input('Choose a directory ====> '))-1
target = folders[index]
df = os.path.join(parent_data_dir,target)

# This is the folder where I will store unzipped data and reduced products
there = '/media/3HD/common_files'
rdf = create_dir(target,there)
logs = create_dir('logs',rdf)

# Listing and extracting data
if 'extract' in args:
    print('Extracting files')
    data_list = glob.glob('{}/*.taz'.format(df))
    for data in data_list:
        cmd = f'tar xvf {data} -C {rdf}'
        os.system(cmd)

# At this point data should be organized in proposal-observation-exposure folders inside rdf
proposals = sorted(next(os.walk(rdf))[1])
if 'logs' proposals: proposals.remove('logs')

for proposal in proposals:
    
    logging.info(f'Processing proposal {proposal}')
    logging.info('='*80)
    
    prop_folder = os.path.join(rdf,proposal)
    observations = sorted(next(os.walk(prop_folder))[1])
    
    logging.info(f'There are {len(observations)} observations.\n')
    for observation in observations:

        logging.info(f'Processing observation {observation}')
        logging.info('-'*80)

        obs_folder = os.path.join(prop_folder,observation)
        exposures = sorted(next(os.walk(obs_folder))[1])
        if 'ACS' in exposures: exposures.remove('ACS')
        if 'AUX' in exposures: exposures.remove('AUX')

        logging.info(f'There are {len(exposures)} exposures\n')
        for exposure in exposures:

            logging.info(f'Processing exposure {exposure}')
            logging.info('*'*80)
            wf = os.path.join(obs_folder,exposure)
            print(wf)
            
            # Data reduction:
            # 1) Calibration
            cal = he_cal(wf)
            if cal:
                logging.info('1) Calibration successfully perfomed')
            else:
                logging.info('1) Calibration not perfomed')

            # 2) GTI computation
            gti = he_gti(wf)
            if gti:
                logging.info('2) GTI successfully computed')
            else:
                logging.info('2) GTI not computed')
                             
            # 3) Data screening
            screen = he_screen(wf,cal,gti)
            if screen:
                logging.info('3) Screening successfully performed')
            else:
                logging.info('3) Screening not perfomed')                             

            # 4) Computing energy spectrum
            spectra = sorted(he_genspec(wf,screen))
            if spectra:
                logging.info('4) Energy spectrum successfully computed')
            else:
                logging.info('4) Energy spectrum not computed')

            # 5) Generate response file
            rsp = sorted(he_genrsp(wf,spectra))
            if rsp:
                logging.info('5) Response file sucessfully computed')
            else:
                logging.info('5) Response file not computed')

            # 6) Updating energy spectra RESPFILE keyword
            for i in range(len(spectra)):
                print('Updating {} response keyword with {}'.format(spectra[i],rsp[i]))
                with fits.open(spectra[i]) as hdu_list:
                    header = hdu_list[0].header
                    header['RESPFILE']=rsp[i]
                             
            # 7) Computing lightcurve
            lc = he_genle(wf,screen,binsize=timeres,minpi=minch,maxpi=maxch)
            if lc:
                logging.info('6) Lightcurve successfully computed')
            else:
                logging.info('6) Lightcurve not computed')
                             
            # 8) Computing energy spectrum background
            spec_bkg = he_bkgmap(wf,'energy_spectra.txt',screen,gti)
            if spec_bkg:
                logging.info('7) Energy spectrum background successfully computed')
            else:
                logging.info('7) Energy spectrum background not computed')
                             
            # 9) Computing lightcurve background
            lc_bkg = he_bkgmap(wf,'light_curve.txt',screen,gti)
            if lc_bkg:
                logging.info('8) Lightcurve background successfully computed')
            else:
                logging.info('8) Lightcurve background not computed')

            # 10) Updating energy spectra BACKFILE keyword
            for i in range(len(spectra)):
                print('Updating {} background keyword with {}'.format(spectra[i],spec_bkg[i]))
                with fits.open(spectra[i]) as hdu_list:
                    header = hdu_list[0].header
                    header['RESPFILE']=spec_bkg[i]

            # TO DO
            # 11) Joining all the energy spectra from different detectors in a single file
            cmd = 'hhe_spec2pi srcphafile={} backfile={} respfile={}'

            logging.info('*'*80+'\n')
        logging.info('-'*80+'\n')
    logging.info('='*80+'\n')

