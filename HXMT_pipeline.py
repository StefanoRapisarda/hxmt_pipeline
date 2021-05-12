import sys
import os
import pathlib
import numpy as np
import glob
import logging

import tkinter
from tkinter import filedialog

from astropy.io import fits

from functions.hxmt_funcs import *
from functions.my_funcs import *
from functions.my_logging import *

args = sys.argv

# Getting arguments into a dictionary
arg_dict = {}
for i,arg in enumerate(args):
    if i == 0:
        div = ['name',arg]
    else:
        if ':' in arg:
            div = arg.split(':')
        elif '=' in arg:
            div = arg.split('=')
        else:
            div = [arg.strip(),True]
    if type(div[0]) == str: div[0]=div[0].strip()
    if type(div[1]) == str: div[1]=div[1].strip()
    arg_dict[div[0]] = div[1] 

# Choosing data directory

# This opens a dialogue window to choose the input folder, but it is
# slow from remote
#root = tkinter.Tk()
#root.withdraw()
# DF contains all the compressed data
# df = filedialog.askdirectory(initialdir='/media/QNAP_40T_HD/HXMTdata_version20200927',
                             #title='Select one of the sources')
# target = os.path.basename(df)

# Choosing raw data folder
# --------------------------------------------------------------------
# data_dir contains the unzipped files organised per download date and object
# ex. /media/QNAP_40T_HD/20200101/Cygnus_x1
if 'data_dir' in arg_dict.keys():
    data_dir = arg_dict['data_dir']
else:
    data_dir = pathlib.Path('/media/QNAP_40T_HD/')
df1 = list_items(data_dir,choose=True)
df = list_items(df1,choose=True)
# target name is supposed to be the name of the object
target_name = str(df.name)
# --------------------------------------------------------------------

# Creating destination and log folder
# --------------------------------------------------------------------
if 'destination' in arg_dict.keys():
    there = pathlib.Path(arg_dict['destination'])
else:
    there = pathlib.Path('/media/3HD/stefano/hxmt_reduced_data')
rdf = there/target_name
if not rdf.is_dir():
    os.mkdir(rdf)
# --------------------------------------------------------------------

# Initializing logger
# --------------------------------------------------------------------
log_name = get_logger_name('HXMT_pipeline')
make_logger(log_name,outdir=rdf)
# --------------------------------------------------------------------

# Reading parameters from calling sequence
# --------------------------------------------------------------------
hetimeres = 1
if 'hetimeres' in arg_dict.keys():
    hetimeres = eval(arg_dict['hetimeres'])

heminch = 8
hemaxch = 162
if 'heminch' in arg_dict.keys():
    heminch = float(arg_dict['heminch'])
if 'hemaxch' in arg_dict.keys():
    hemaxch = float(arg_dict['hemaxch'])

metimeres = 1
if 'metimeres' in arg_dict.keys():
    metimeres = eval(arg_dict['metimeres'])

meminch = 119
memaxch = 546
if 'meminch' in arg_dict.keys():
    meminch = float(arg_dict['meminch'])
if 'memaxch' in arg_dict.keys():
    memaxch = float(arg_dict['memaxch'])

letimeres = 1
if 'letimeres' in arg_dict.keys():
    letimeres = eval(arg_dict['letimeres'])

leminch = 106
lemaxch = 1169
if 'leminch' in arg_dict.keys():
    leminch = float(arg_dict['leminch'])
if 'lemaxch' in arg_dict.keys():
    lemaxch = float(arg_dict['lemaxch'])

if 'override' in arg_dict.keys():
    override = True
else:
    override = False

comp_lc = True
comp_spec = True
if 'onlyspec' in arg_dict.keys(): comp_lc = False
if 'onlylc' in arg_dict.keys(): comp_spec = False
# --------------------------------------------------------------------

# Printing settings
# --------------------------------------------------------------------
logging.info('===>>> Running HXMT_pipeline <<<===\n')
logging.info('Settings')
logging.info('-'*72)
logging.info('Data directory: {}'.format(df))
logging.info('Destination directory: {}'.format(rdf))
if 'HE' in arg_dict.keys():
    logging.info('HE Time resolution [s]: {}'.format(hetimeres))
    logging.info('HE energy channels {}-{}'.format(heminch,hemaxch))
if 'ME' in arg_dict.keys():    
    logging.info('ME Time resolution [s]: {}'.format(metimeres))
    logging.info('ME energy channels {}-{}'.format(meminch,memaxch))
if 'LE' in arg_dict.keys():  
    logging.info('LE Time resolution [s]: {}'.format(letimeres))  
    logging.info('LE energy channels {}-{}'.format(leminch,lemaxch))
logging.info('-'*72+'\n')
# --------------------------------------------------------------------

# Extracting data from zip archives
# --------------------------------------------------------------------
if 'extract' in arg_dict.keys():
    logging.info('Extracting (taz) files...')
    data_list = glob.glob('{}/*.taz'.format(df))
    for data in data_list:
        cmd = f'tar xvf {data} -C {rdf}'
        os.system(cmd)   
# --------------------------------------------------------------------
    
    
# Running the script
# =====================================================================

# At this point data should be organized in proposal-observation-exposure folders inside rdf
# Listing proposal folders (Level1)
proposals = list_items(rdf,exclude_or=['logs','analysis'])
if type(proposals) != list: proposals = [proposals]

# Start Proposal LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOP
for i,proposal in enumerate(proposals):
    
    proposal_name = str(proposal.name)
    logging.info(f'Processing proposal {proposal_name} ({i+1}/{len(proposals)})')
    logging.info('='*80)
    
    # Listing observation folders (Level2)
    observations = list_items(proposal)
    if type(observations) != list: observations = [observations]
    
    logging.info(f'There are {len(observations)} observations.\n')
    
    # Start Observation LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOP
    for j,observation in enumerate(observations):

        observation_name = observation.name
        logging.info(f'Processing observation {observation_name} ({j+1}/{len(observations)})')
        logging.info('-'*80)

        # Listing exposure folders (Level3)
        exposures = list_items(observation,exclude_or='ACS')
        if type(exposures) != list: exposures = [exposures]

        # Checking ACS and AUX folders
        # --------------------------------------------------------------------
        flag_acs = True
        if not (observation/'ACS').is_dir(): 
            logging.info('ACS folder does not exists, response matrix cannot be computed.')
            logging.info('Energy spectrum will not be computed')
            flag_acs = False
        if not (observation/'AUX').is_dir():
            logging.info('AUX folder does not exists. Skipping obs.')
            logging.info('-'*80+'\n')
            continue
         # --------------------------------------------------------------------

        logging.info(f'There are {len(exposures)} exposures\n')

        # Start Exposure LOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOP
        for exposure in exposures:

            # The Exposure folder name is in the format 
            # proposal-obs-exposure
            # I define this as the obs ID as the exposure, as each 
            # exposure can be univocally identified by this 
            obs_ID = exposure.name

            logging.info(f'Processing exposure {obs_ID}')
            logging.info('*'*80)
            # Definition of the working folder
            wf = exposure
            
            # HE data reduction
            # ---------------------------------------------------------
            if 'HE' in arg_dict.keys():
                
                logging.info('HE data reduction...')
                
                # Data reduction:
                # 1) Calibration
                hecal = he_cal(wf, override=override, out_dir=rdf)
                if hecal:
                    logging.info('1) HE calibration successfully perfomed')
                else:
                    logging.info('1) HE calibration not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                # 2) GTI computation
                hegti = he_gti(wf, override=override, out_dir=rdf)
                if hegti:
                    logging.info('2) HE GTI successfully computed')
                else:
                    logging.info('2) HE GTI not computed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue
                             
                # 3) Data screening
                hescreen = he_screen(wf,override=override, out_dir=rdf)
                if hescreen:
                    logging.info('3) HE Screening successfully performed')
                else:
                    logging.info('3) HE Screening not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue  

                # 4) Computing lightcurve
                if comp_lc:
                    helc = he_lc(wf,binsize=hetimeres,minpi=heminch,maxpi=hemaxch, 
                        override=override, out_dir=rdf)
                    if helc:
                        logging.info('4) Lightcurve successfully computed')
                    else:
                        logging.info('4) Lightcurve not computed. Skipping obs')

                    # 4b) Computing lightcurve background
                    if helc:
                        helc_bkg = he_bkg(wf,helc,override=override, out_dir=rdf)
                        if helc_bkg:
                            logging.info('4b) Lightcurve background successfully computed')
                        else:
                            logging.info('4b) Lightcurve background not computed')                           

                # 5) Computing energy spectrum
                if comp_spec and flag_acs:

                    hespectrum = he_spec(wf, override=override, out_dir=rdf)
                    if hespectrum:
                        logging.info('5) Energy spectrum successfully computed')

                    else:
                        logging.info('5) Energy spectrum not computed')

                    # 5b) Computing energy spectra response
                    if hespectrum:

                        hersp = he_rsp(wf,hespectrum, override=override, out_dir=rdf)
                        if hersp:
                            logging.info('5b) Response file sucessfully computed')
                        
                            # Updating energy spectra RESPFILE keyword
                            with fits.open(hespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['RESPFILE']=str(hersp.name)
                        else:
                            logging.info('5b) Response file not computed')

                    # 5c) Computing energy spectra background
                    if hespectrum:

                        hespec_bkg = he_bkg(wf,hespectrum,override=override, out_dir=rdf)
                        if hespec_bkg:
                            logging.info('5c) Energy spectrum background successfully computed')

                            # Updating energy spectra BACKFILE keyword
                            with fits.open(hespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['BACKFILE']=str(hespec_bkg.name)
                    else:
                        logging.info('5c) Energy spectrum background not computed')
            # ---------------------------------------------------------
                             

            # ME data reduction
            # ---------------------------------------------------------
            if 'ME' in arg_dict.keys():
                
                logging.info('ME data reduction...')
                
                # Data reduction:
                # 1) Calibration
                mecal = me_cal(wf, override=override, out_dir=rdf)
                if mecal:
                    logging.info('1) ME calibration successfully perfomed')
                else:
                    logging.info('1) ME calibration not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                # 2) Grading events
                megrade,medead = me_grade(wf, binsize=metimeres, 
                    override=override, out_dir=rdf)
                if megrade and medead:
                    logging.info('2) ME grading successfully perfomed')
                else:
                    logging.info('2) ME grading not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                if metimeres != 1:
                # 2b) Creating deadtime for energy spectrum
                    megrade1,medead1 = me_grade(wf, override=override, out_dir=rdf)
                    if megrade and medead:
                        logging.info('2b) ME second grading successfully perfomed')
                    else:
                        logging.info('2b) ME second grading not perfomed. Skipping obs')
                        logging.info('-'*80+'\n')
                        continue

                # 3) GTI computation
                megti_pre = me_gti(wf, override=override, out_dir=rdf)
                if megti_pre:
                    logging.info('3) ME first GTI successfully computed')
                else:
                    logging.info('3) ME first GTI not computed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                # 4) GTI correction
                megti,mebad_det = me_gticorr(wf, override=override, out_dir=rdf)
                if megti and mebad_det:
                    logging.info('4) ME GTI successfully computed')
                else:
                    logging.info('4) ME GTI not computed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue
                             
                # 5) Data screening
                mescreen = me_screen(wf,override=override, out_dir=rdf)
                if mescreen:
                    logging.info('5) ME screening successfully performed')
                else:
                    logging.info('5) ME screening not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue  

                # 6) Computing lightcurve
                if comp_lc:
                    melc = me_lc(wf,binsize=metimeres,minpi=meminch,maxpi=memaxch, 
                        override=override, out_dir=rdf)
                    if melc:
                        logging.info('6) Lightcurve successfully computed')
                    else:
                        logging.info('6) Lightcurve not computed. Skipping obs')

                    # 6b) Computing lightcurve background
                    if melc:
                        melc_bkg = me_bkg(wf,melc,override=override, out_dir=rdf)
                        if melc_bkg:
                            logging.info('6b) Lightcurve background successfully computed')
                        else:
                            logging.info('6b) Lightcurve background not computed')                           

                # 7) Computing energy spectrum
                if comp_spec and flag_acs:

                    mespectrum = me_spec(wf, binsize=1, override=override, out_dir=rdf)
                    if mespectrum:
                        logging.info('7) Energy spectrum successfully computed')
                    else:
                        logging.info('7) Energy spectrum not computed')

                    # 7b) Computing energy spectra response
                    if mespectrum:

                        mersp = me_rsp(wf,mespectrum, override=override, out_dir=rdf)
                        if mersp:
                            logging.info('7b) Response file sucessfully computed')
                        
                            # Updating energy spectra RESPFILE keyword
                            with fits.open(mespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['RESPFILE']=str(mersp.name)
                        else:
                            logging.info('7b) Response file not computed')

                    # 7c) Computing energy spectra background
                    if mespectrum:

                        mespec_bkg = me_bkg(wf,mespectrum,override=override, out_dir=rdf)
                        if mespec_bkg:
                            logging.info('7c) Energy spectrum background successfully computed')

                            # Updating energy spectra BACKFILE keyword
                            with fits.open(mespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['BACKFILE']=str(mespec_bkg.name)
                    else:
                        logging.info('7c) Energy spectrum background not computed')
            # ---------------------------------------------------------

            # LE data reduction
            # ---------------------------------------------------------
            if 'LE' in arg_dict.keys():
                
                logging.info('LE data reduction...')
                
                # Data reduction:
                # 1) Calibration
                lecal = le_cal(wf, override=override, out_dir=rdf)
                if lecal:
                    logging.info('1) LE calibration successfully perfomed')
                else:
                    logging.info('1) LE calibration not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                lerecon = le_recon(wf, override=override, out_dir=rdf)
                if lerecon:
                    logging.info('2) LE reconstruction successfully perfomed')
                else:
                    logging.info('2) LE recontruction not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue                

                # 3) GTI computation
                legti_pre = le_gti(wf, override=override, out_dir=rdf)
                if legti_pre:
                    logging.info('3) LE first GTI successfully computed')
                else:
                    logging.info('3) LE first GTI not computed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue

                # 4) GTI correction
                legti = le_gticorr(wf, override=override, out_dir=rdf)
                if legti:
                    logging.info('4) LE GTI successfully computed')
                else:
                    logging.info('4) LE GTI not computed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue
                             
                # 5) Data screening
                lescreen = le_screen(wf,override=override, out_dir=rdf)
                if lescreen:
                    logging.info('5) LE screening successfully performed')
                else:
                    logging.info('5) LE screening not perfomed. Skipping obs')
                    logging.info('-'*80+'\n')
                    continue  

                # 6) Computing lightcurve
                if comp_lc:
                    lelc = le_lc(wf,binsize=letimeres,minpi=meminch,maxpi=memaxch, 
                        override=override, out_dir=rdf)
                    if lelc:
                        logging.info('6) Lightcurve successfully computed')
                    else:
                        logging.info('6) Lightcurve not computed. Skipping obs')

                    # 6b) Computing lightcurve background
                    if lelc:
                        lelc_bkg = le_bkg(wf,lelc,override=override, out_dir=rdf)
                        if lelc_bkg:
                            logging.info('6b) Lightcurve background successfully computed')
                        else:
                            logging.info('6b) Lightcurve background not computed')                           

                # 7) Computing energy spectrum
                if comp_spec and flag_acs:

                    lespectrum = le_spec(wf, override=override, out_dir=rdf)
                    if lespectrum:
                        logging.info('7) Energy spectrum successfully computed')

                    else:
                        logging.info('7) Energy spectrum not computed')

                    # 7b) Computing energy spectra response
                    if lespectrum:

                        lersp = le_rsp(wf,lespectrum, override=override, out_dir=rdf)
                        if lersp:
                            logging.info('7b) Response file sucessfully computed')
                        
                            # Updating energy spectra RESPFILE keyword
                            with fits.open(lespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['RESPFILE']=str(lersp.name)
                        else:
                            logging.info('7b) Response file not computed')

                    # 7c) Computing energy spectra background
                    if lespectrum:

                        lespec_bkg = le_bkg(wf,lespectrum,override=override, out_dir=rdf)
                        if lespec_bkg:
                            logging.info('7c) Energy spectrum background successfully computed')

                            # Updating energy spectra BACKFILE keyword
                            with fits.open(lespectrum,'update') as hdu_list:
                                for hdu in hdu_list:
                                    hdu.header['BACKFILE']=str(lespec_bkg.name)
                    else:
                        logging.info('7c) Energy spectrum background not computed')
            # ---------------------------------------------------------

            logging.info('*'*80+'\n')
        logging.info('-'*80+'\n')
    logging.info('='*80+'\n')

