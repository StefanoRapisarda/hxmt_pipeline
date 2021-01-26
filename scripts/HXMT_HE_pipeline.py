import sys
import os
current_dir = os.getcwd()
parent_dir = os.path.dirname(current_dir)
sys.path.append(os.path.join(parent_dir,'functions'))
print(parent_dir)

from hxmt_funcs import *
from my_funcs import *

import numpy as np
import datetime
import glob

from astropy.io import fits

import tkinter
from tkinter import filedialog

import logging

args = sys.argv
script_name = args[0]

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
parent_data_dir = '/media/QNAP_40T_HD/HXMTdata_version20200927'
folders = next(os.walk(parent_data_dir))[1]
happy = False
while not happy:
    for i,folder in enumerate(folders):
        print('{}) {}'.format(i+1,folder))
    index = int(input('Choose a directory ====> '))-1
    target = folders[index]
    ans=input('You chose {}, are you happy?'.format(target))
    if not ('N' in ans.upper() or 'O' in ans.upper()):
        happy = True
df = os.path.join(parent_data_dir,target)
# --------------------------------------------------------------------

# Destination and log folder
# --------------------------------------------------------------------
there = '/media/3HD/common_files'
rdf = create_dir(target,there) #raw data folder
logs = create_dir('logs',rdf)
# --------------------------------------------------------------------

# Initializing logger
# --------------------------------------------------------------------
now = datetime.datetime.now()
date = ('%d_%d_%d') % (now.day,now.month,now.year)
time = ('%d_%d') % (now.hour,now.minute)
logger_name = '{}/{}_D{}_T{}.log'.format(logs,script_name,date,time)
initialize_logger(logger_name)
# --------------------------------------------------------------------

# Reading parameters from calling sequence
# --------------------------------------------------------------------
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

logging.info('===>>> Running HXMT_HE_pipeline <<<===\n')
logging.info('Settings')
logging.info('-'*72)
logging.info('Data directory: {}'.format(df))
logging.info('Destination directory: {}'.format(rdf))
logging.info('Time resolution [s]: {}'.format(timeres))
logging.info('Energy channels {}-{}'.format(minch,maxch))
logging.info('-'*72+'\n')

if 'extract' in args:
    logging.info('Extracting (taz) files...')
    data_list = glob.glob('{}/*.taz'.format(df))
    for data in data_list:
        cmd = f'tar xvf {data} -C {rdf}'
        os.system(cmd)

if 'override' in args:
    override = True
else:
    override = False
# --------------------------------------------------------------------
    
    
# Running the script

# At this point data should be organized in proposal-observation-exposure folders inside rdf
proposals = sorted(next(os.walk(rdf))[1])
if 'logs' in proposals: proposals.remove('logs')

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

        # Checking ACS and AUX folders
        # --------------------------------------------------------------------
        flag_acs = True
        if 'ACS' in exposures: 
            exposures.remove('ACS')
        else:
            logging.info('ACS folder does not exists, response matrix cannot be computed.')
            logging.info('Energy spectrum will not be computed')
            flag_acs = False
        if 'AUX' in exposures: 
            exposures.remove('AUX')
        else:
            logging.info('AUX folder does not exists. Skipping obs.')
            logging.info('-'*80+'\n')
            continue
         # --------------------------------------------------------------------

        logging.info(f'There are {len(exposures)} exposures\n')
        for exposure in exposures:

            logging.info(f'Processing exposure {exposure}')
            logging.info('*'*80)
            wf = os.path.join(obs_folder,exposure)
            #print(wf)
            
            # I define the obs ID as the exposure
            obs_ID = exposure
            
            # Data reduction:
            # 1) Calibration
            cal = he_cal(wf, override=override)
            if cal:
                logging.info('1) Calibration successfully perfomed')
            else:
                logging.info('1) Calibration not perfomed. Skipping obs')
                logging.info('-'*80+'\n')
                continue

            # 2) GTI computation
            gti = he_gti(wf, override=override)
            if gti:
                logging.info('2) GTI successfully computed')
            else:
                logging.info('2) GTI not computed. Skipping obs')
                logging.info('-'*80+'\n')
                continue
                             
            # 3) Data screening
            screen = he_screen(wf,cal,gti, override=override)
            if screen:
                logging.info('3) Screening successfully performed')
            else:
                logging.info('3) Screening not perfomed. Skipping obs')
                logging.info('-'*80+'\n')
                continue                             

            # 4) Computing energy spectrum
            if flag_acs:
  
                # 4a) Energy spectrum
                spectra = he_genspec(wf,screen, override=override)
                if spectra:
                    logging.info('4) Energy spectrum successfully computed')

                    # Writing the energy spectra names into a text file 
                    # (this will be necessary for computing
                    # the background qwith hebkgmap)
                    dir_name = os.path.dirname(spectra[0])
                    with open(os.path.join(dir_name,'energy_spectra.txt'),'w') as txt:
                        for spectrum in spectra:
                          # Excluding blind detector spectrum
                          if not spectrum.split('_')[-1].replace('.pha','') == '16':
                            txt.write(spectrum+'\n')
                else:
                    spectra = False
                    logging.info('4) Energy spectrum not computed')

            # 4b) Computing energy spectra response
            if spectra:
                
                rsp = he_genrsp(wf,spectra, override=override)
                if rsp:
                    logging.info('4b) Response file sucessfully computed')
                    with open(os.path.join(dir_name,'energy_spectra_rsp.txt'),'w') as txt:
                        for f in rsp:
                          # Excluding blind detector spectrum
                          if not f.split('_')[-1].replace('.pha','') == '16':
                            txt.write(f+'\n')

                    # Updating energy spectra RESPFILE keyword
                    for i in range(len(spectra)):
                        logging.info('Updating {} response keyword with {}'.\
                            format(spectra[i],rsp[i]))
                        with fits.open(spectra[i]) as hdu_list:
                            header = hdu_list[0].header
                            header['RESPFILE']=rsp[i]
                else:
                    logging.info('4b) Response file not computed')

            # 4c) Computing energy spectra background
            if spectra and rsp:

                spec_bkg = he_bkgmap(wf,'energy_spectra.txt',screen,gti, override=override)
                if spec_bkg:
                    logging.info('7) Energy spectrum background successfully computed')
                
                    # Writing background files into a file (this will 
                    # be needed by hhe_spec2pi)
                    with open(os.path.join(dir_name,'energy_spectra_bkg.txt'),'w') as txt:
                        for bkg in spec_bkg:
                          # Excluding blind detector spectrum
                          if not bkg.split('_')[-1].replace('.pha','') == '16':
                            txt.write(bkg+'\n')

                    # Updating energy spectra BACKFILE keyword
                    for i in range(len(spectra)):
                        logging.info('Updating {} background keyword with {}'.\
                            format(spectra[i],spec_bkg[i]))
                        with fits.open(spectra[i]) as hdu_list:
                            header = hdu_list[0].header
                            header['BACKFILE']=spec_bkg[i]
                else:
                    logging.info('7) Energy spectrum background not computed')

            # 4d) Joining all the energy spectra from different detectors in a single file
            total_spec_flag = check_HE_spectra_files('energy_spectra.txt','energy_spectra_bkg.txt','energy_spectra_rsp.txt',dir_name)
            if total_spec_flag:
              cmd = 'hhe_spec2pi {} {} {} {} {} {}'.\
                format(dir_name+'/energy_spectra.txt',dir_name+'/energy_spectra_bkg.txt',dir_name+'/energy_spectra_rsp.txt',
                       dir_name+'/total_spectrum.pi',dir_name+'/total_spectrum_bkg.pi',dir_name+'/total_spectrum_rsp.pi')
              os.system(cmd)
              logging.info('Total energy spectrum successfully computed')
            else:
              logging.info('Could not compute total energy spectrum')  
                             
            # 5) Computing lightcurve
            lc = he_genle(wf,screen,binsize=timeres,minpi=minch,maxpi=maxch, override=override)
            if lc:
                logging.info('5) Lightcurve successfully computed')

                # Writing light curve name into a text file (this will be necessary 
                # for computing the background with hebkgmap)
                dir_name = os.path.dirname(lc)
                file_name = 'light_curve_ch{}-{}_{}s.txt'.\
                                format(minch,maxch,timeres)
                with open(os.path.join(dir_name,file_name),'w') as txt:
                    txt.write(lc+'\n')
            else:
                logging.info('5) Lightcurve not computed. Skipping obs')
                logging.info('-'*80+'\n')
                continue   
           
            # 5b) Computing lightcurve background
            if lc:
                lc_bkg = he_bkgmap(wf,file_name,screen,gti, override=override)
                if lc_bkg:
                    logging.info('8) Lightcurve background successfully computed')
                else:
                    logging.info('8) Lightcurve background not computed')

            logging.info('*'*80+'\n')
        logging.info('-'*80+'\n')
    logging.info('='*80+'\n')

