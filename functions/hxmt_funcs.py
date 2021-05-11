import os
from os import path
import sys
import pathlib
from .my_funcs import list_items

import glob
import numpy as np
import logging
        
def check_exp_format(exp):
    '''
    Check the right formar of the proposal format

    ex. P010129900101-20170827-01-01
    '''

    if type(exp) == str: exp = pathlib.Path(exp)  
    exp = exp.name

    if exp[0] != 'P':
        logging.info('Exposure folder name does not begin with P')
        return False
    tmp = exp.split('-')
    if len(tmp[-1]) != 2:
        logging.info('The last two digits of the exposure folder are supposed to be two')
        return False
    if len(tmp[-2]) != 2:
        logging.info('The digits after the date are supposed to be two')
        return False    
    if len(tmp[-3]) != 8:
        logging.info('Date format is wrong')
        return False       
    if len(tmp[0]) != 13:
        logging.info('Exposure ID format is wrong')
        return False     
    return True

def he_cal(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs HXMT tool hepical creating a calibrated event file

    DESCRIPTION
    -----------
    The tool hepical remove spike events caused by electronic system and
    calculate PI columns values of HE event files.  
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory
    override: boolean, optional
        If True, existing files will be overwritten
                  
    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the calibrated eventfile. If some operation 
        is not successfull, it returns False.
        Output file is in the form:
        <full_path>/<exp_ID>_HE_evt_cal.fits

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inproved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        file is returned
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path
    '''

    logging.info('===>>> Running he_cal <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folder
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)
    
    # Initializing output file
    outfile = destination/'{}_HE_evt_cal.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('HE calibrated event file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing HE calibrated event file')

        # Initializing and checking existance of input files 
        # -------------------------------------------------------------
        evt = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-Evt',ext='.FITS')
        if type(evt) == list:
            if len(evt) > 1:
                logging.error('There is more than one HE-Evt file!')
                return
            if len(evt) == 0:
                logging.error('I did not find a HE-Evt file!')
                return
        # -------------------------------------------------------------

        # Running calibration
        glitch_file = destination/'{}_HE_spikes.fits'.format(exp_ID)
        cmd = f'hepical evtfile={evt} outfile={outfile} \
            minpulsewidth=54 maxpulsewidth=70 glitchfile={glitch_file} \
            clobber=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.warning('he_cal output file was NOT created')
            return         
    
    return outfile

def he_gti(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs HXMT tool hegtigen creating a gti file

    DESCRIPTION
    -----------
    hegtigen works similarly to NICER nimaketime, i.e. it generates a 
    fits file of good time intervals according to certain screening 
    criteria, without modifying the original event file. 
    It needs a high voltage file, temperature file,
    particle monitor file (HE folder), and a house keeping file 
    (AUX folder). These are do not need to be specified by the user,
    the routine automatically looks for them.

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.

    RETURN
    ------
    outfile: pathlib.Path or boolean
        The full path of the gti file. If some operation
        is not successfull, it returns False.

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if gti file
        already exists and override=False, the name of the gti
        file is returned
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path
    '''

    logging.info('===>>> Running he_gti <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    # Initializing outfile
    outfile=destination/'{}_HE_gti.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('HE GTI file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing HE GTI file')

        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # high voltage file
        hv = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-HV',ext='FITS')
        if type(hv) == list:
            if len(hv) > 1:
                logging.error('There is more than one HE-HV (high voltage) file!')
                return
            if len(hv) == 0:
                logging.error('I did not find a HE-HV (high voltage) file!')
                return

        # Temperature file
        temp = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-TH',ext='FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one HE-TH (temperature) file!')
                return
            if len(temp) == 0:
                logging.error('I did not find a HE-TH (temperature) file!')
                return

        # ehk file
        ehk = list_items(full_exp_dir/'AUX',itype='file',
            include_or='_EHK_',ext='FITS')
        if type(ehk) == list:
            if len(ehk) > 1:
                logging.error('There is more than one _EHK_ file!')
                return
            if len(ehk) == 0:
                logging.error('I did not find a _EHK_ file!')
                return        
        
        # pm file
        pm = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-PM',ext='FITS')
        if type(pm) == list:
            if len(pm) > 1:
                logging.error('There is more than one HE-PM file!')
                return
            if len(pm) == 0:
                logging.error('I did not find a HE-PM file!')
                return  
        # -------------------------------------------------------------

        # Running screening
        cmd = f'hegtigen hvfile={hv} tempfile={temp} pmfile={pm} \
        ehkfile={ehk} outfile={outfile} defaultexpr=NONE \
        expr="ELV>10&&COR>8&&SAA_FLAG==0&&TN_SAA>300&&T_SAA>300&&ANG_DIST<=0.04" \
        pmexpr="" clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.info('he_gti output file was not created')
            return

    return outfile


def he_screen(full_exp_dir,cal_evt_file=None,gti_file=None,
        out_dir = pathlib.Path.cwd(),minpi=0,maxpi=255,override=False):
    '''
    Runs HXMT tool he_screen creating a screened event file

    DESCRIPTION
    -----------
    hescreen uses the previously creted GTI file to remove photons from 
    the previously created calibrated event file. At this stage, events 
    can be also discriminated according to the pulse shape.

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    cal_evt_file: string or pathlib.Path or None, optional
        Calibrated event file (output of hepical) with its full path.
        If None (default), the script will look for it.
    gti_file: string or pathlib.Path or None, optional
        GTI file (output of hegtigen) with its full path.
        if None (default), the script will look for it.
    minpi: integer, optional
        Minimum energy channel, default is 0
    maxpi: integer, optiona
        Maximum energy channel, defaule is 255
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten

    RETURN
    ------
    outfile: pathlib.Path or boolean
        The full path of the screen event file. If some operation
        is not successfull, it returns False.

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        file is returned
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path
    '''

    logging.info('===>>> Running he_screen <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if cal_evt_file is None:
        cal_evt_file = list_items(destination,itype='file',
            include_or=['HE_evt_cal'])
        if cal_evt_file:
            if type(cal_evt_file) == list: 
                logging.error('There is more than one HE calibrated event file')
                return
        else:
            logging.error('I could not find a HE calibrated event file')
            return
    if type(cal_evt_file) == str: cal_evt_file = pathlib.Path(cal_evt_file)
    if not cal_evt_file.is_file():
        logging.error('{} does not exist'.format(cal_evt_file))
        return 

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['HE_gti'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one HE gti file')  
                return
        else:
            logging.error('I could not find a HE GTI file')
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return   
    # -----------------------------------------------------------------    

    # Initializing outfile
    outfile=destination/'{}_HE_evt_screen.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('HE screened event file already exists')
        compute = False  

    if compute or override:
        logging.info('Performing HE screening')    

        # Running hescreen
        cmd = f'hescreen evtfile={cal_evt_file} gtifile={gti_file} \
            outfile={outfile} userdetid="0-17" eventtype=1 \
            anticoincidence=yes starttime=0 stoptime=0 \
            minPI={minpi} maxPI={maxpi}  clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.warning('he_screen output file was not created')
            return

    return outfile

def he_spec(full_exp_dir,screen_evt_file=None,out_dir=pathlib.Path.cwd(),
    minpi=0,maxpi=255,user_det_id='0-15, 17',override=False):
    '''
    It computes an energy spectrum calling hespecgen
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path or None, optional
        Screaned and calibrated event file (output of hescreen).
        If None (default), the script will look for it.
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.
    minpi: integer, optional
        Low energy channel. Default value is 0
    maxpi: integer, optional
        High energy channel. Default value is 255
    user_det_id: string, optional
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves
                  
    RETURN
    ------
    outfile: pathlib.Path
        Energy spectrum with its full path

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if energy spectrum
        already exists and override=False, the name of the spectrum
        file is returned
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path.
        per_det parameter added.
    '''

    logging.info('===> Running he_genspec <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['HE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one HE screened event file')
                return
        else:
            logging.error('I could not find a HE screened event file')
            return
    if type(screen_evt_file) == str: screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return 
    # -----------------------------------------------------------------
    
    # Initializing outfile
    file_name_root='{}_HE_spec_ch{}-{}'.format(exp_ID,minpi,maxpi)
    outfile_root = destination/file_name_root

    spec_test = list_items(destination,itype='file',include_or=file_name_root,
        exclude_or=['rsp','bkg'],ext = 'pha')

    compute = True
    if spec_test:
        logging.info('Energy spectrum already exist')
        compute = False  

    if compute or override:
        logging.info('Computing HE energy spectrum')

        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Dead time file
        dead = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-DTime',ext='FITS')
        if type(dead) == list:
            if len(dead) > 1:
                logging.error('There is more than one HE-Dtime (deadtime) file, returning')
                return
            if len(dead) == 0:
                logging.error('I did not find a HE-Dtime (deadtime) file, returning')
                return   
        # -------------------------------------------------------------

        # Running hespecgen
        cmd = f'hespecgen evtfile={screen_evt_file} outfile={outfile_root} \
            deadfile={dead} userdetid="{user_det_id}" \
            eventtype=1 starttime=0 stoptime=0 \
            minPI={minpi} maxPI={maxpi} clobber=yes'
        os.system(cmd)
        
        spec_file = list_items(destination,itype='file',include_or=[file_name_root],
            exclude_or=['rsp','bkg'],ext='pha')

        # Verifing successful running
        if not spec_file:
            logging.warning('he_spec output file was not created')
            return   

        # Writing spectrum in a txt file
        with open(pathlib.Path(spec_file).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(spec_file)+'\n')

    return pathlib.Path(spec_file)

def he_rsp(full_exp_dir,energy_spectrum_file,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Generates a response file 
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    energy_spectrum_file: string or pathlib.Path, optional
        Energy spectrum (output of hespecgen).
        If None (default), the script will look for it.
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.
                  
    RETURNS
    -------    
    outfile: pathlib.Path
        Response file with its full path
        
    NOTES
    -----
    2021 01 26, Stefano Rapisarda (Uppsala)
        According to 2019 documentation, the current version cannot 
        produce response for the blind detector (DET 16).
        As later on files from each detector are merged to produce 
        the full spectrum, remember to remove spectrum and bkg of 
        detector 16.

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        file is returned
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path
    '''

    logging.info('===> Running he_genrsp <===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
    if type(energy_spectrum_file) == str: 
        energy_spectrum_file = pathlib.Path(energy_spectrum_file)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)

    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    outfile = energy_spectrum_file.with_suffix('.rsp')

    # Checking if responses already exist
    compute = True
    if outfile.is_file():
        logging.info('HE response file already exist')
        compute = False  
    # -----------------------------------------------------------------

    if compute or override:
        logging.info('Computing HE response file')
    
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Attitude file
        att = list_items(full_exp_dir/'ACS',itype='file',
            include_or='Att',ext='FITS')
        if type(att) == list:
            if len(att) > 1:
                logging.error('There is more than one attitude file, returning')
                return
            if len(att) == 0:
                logging.error('I did not find an attitude file, returning')
                return  
        # -------------------------------------------------------------  

        # Running herspgen
        cmd = f"herspgen phafile={energy_spectrum_file} outfile={outfile} \
            attfile={att} ra=-1 dec=-91 clobber=yes"
        os.system(cmd)

        # Checking existance of the just created files
        if not outfile.is_file():
            logging.warning('he_rsp output file was not created'.\
                format(outfile))     
        
    return outfile

def he_lc(full_exp_dir,screen_evt_file=None,
        binsize=1,minpi=8,maxpi=162,user_det_id='0-15, 17',
        out_dir = pathlib.Path.cwd(),override=False):
    '''
    It computes a binned lightcurve from screened evt file
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path, optional
        Screaned and calibrated event file (output of hescreen).
        If None (default), the script will look for it.
    binsize: float, optional
        Binsize of the lightcurve (time resolution). Default value is 1
    minpi: integer, optional
        Low energy channel. Default value is 8
    maxpi: integer, optional
        High energy channel. Default value is 162
    user_det_id: string, optional
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.
                  
    RETURNS
    -------
    outfile: pathlib.Path
        Lightcurve file with its full path

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        lightcurve is returned
    '''

    logging.info('===>>> Running he_lc <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['HE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one HE screened event file')
                return
        else:
            logging.error('I could not find a HE screened event file')
            return
    if type(screen_evt_file) == str: screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return 
    # -----------------------------------------------------------------
    
    # Initializing outfile
    file_name_root = '{}_HE_lc_ch{}-{}_{}s'.\
                         format(exp_ID,minpi,maxpi,binsize)
    outfile_root=destination/file_name_root

    lc_test = list_items(destination,itype='file',include_or=file_name_root,
        exclude_or='bkg',ext='lc')
    
    compute = True
    if lc_test:
        logging.info('Lightcurve already exists')
        compute = False  

    if compute or override:
        logging.info('Computing HE lightcurve')
    
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Dead time file
        dead = list_items(full_exp_dir/'HE',itype='file',
            include_or='HE-DTime',ext='FITS')
        if type(dead) == list:
            if len(dead) > 1:
                logging.error('There is more than one HE-Dtime (deadtime) file')
                return
            if len(dead) == 0:
                logging.error('I did not find a HE-Dtime (deadtime) file')
                return  
        # -------------------------------------------------------------

        # Running helcgen
        cmd = f'helcgen evtfile={screen_evt_file} outfile={outfile_root} \
            deadfile={dead} deadcorr=yes starttime=0 stoptime=0 \
            userdetid="{user_det_id}" eventtype=1 minPI={minpi} maxPI={maxpi} \
            binsize={binsize} clobber=yes'
        os.system(cmd)

        lc_file = list_items(destination,itype='file',include_or=[file_name_root],
            exclude_or='bkg',ext='lc')
    
        # Verifing successful running
        if not lc_file:
            logging.warning('he_le output file was not created')
            return

        # Writing lightcurve in a file
        with open(pathlib.Path(lc_file).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(lc_file)+'\n')
    
    return pathlib.Path(lc_file)

def he_bkg(full_exp_dir,ascii_file,screen_evt_file=None,gti_file=None,
    out_dir=pathlib.Path.cwd(),override=False):
    '''
    It computes background for either a HE lightcurve or an energy spectrum. 
    
    DESCRIPTION
    -----------
    The option (lightcurve or spectrum) it is automatically recognized 
    according to the extention of the first file in the provided ascii 
    text file. Also, the energy channels are automatically selected 
    according to the option. 
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder    
    ascii_file: string or pathlib.Path
        Full path of the text file either containing the energy spectra name or
        the lightcurve name.
        If the extension of the file is NOT .txt, the script will use file
        with the same name of the specified file, changing its extension to
        .txt
    screen_evt_file: string or pathlib.Path, optional
        Name of the calibrated and screened event file (output of hescreen)
        If None (default), the script will look for it
    gti_file: string or pathlib.Path, optional
        Name of the gti file (output of hegengti)
        If None (default), the script will look for it
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/HE).
        Default is current working directory.
    override: boolean, optional
        If True, existing output file are overwritten (default is False)

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        lightcurve is returned
    '''

    # hebkgmap needs spectrum or lightcurve, calibrated and screened 
    # event file, ehk file, gti file, and deadtime file.
    # It creates either a background file for each energy spectrum 
    # or a background lightcurve

    logging.info('===> Running he_bkg <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
    if type(ascii_file) == str: ascii_file = pathlib.Path(ascii_file)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)

    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'HE'
    if not destination.is_dir(): os.mkdir(destination)

    if ascii_file.suffix != '.txt': ascii_file = ascii_file.with_suffix('.txt')
    with open(ascii_file,'r') as infile:
        lines = infile.readlines()
    if len(lines) == 0:
        logging.error('HE ascii file is empty')
        return

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['HE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one HE screened event file')
                return
        else:
            logging.error('I could not find a HE screened event file')
            return
    if type(screen_evt_file) == str: screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return 

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['HE_gti'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one HE gti file')
                return
        else:
            logging.error('I could not find a HE gti file')
            return
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return    
    # -----------------------------------------------------------------
    
    # Automatically recognize channels and file type
    # -----------------------------------------------------------------
    file_name = pathlib.Path(lines[0]).stem
    ext = pathlib.Path(lines[0].strip()).suffix
    chunks = file_name.split('_')
    ch_chunk = [c for c in chunks if 'ch' in c][0].replace('ch','')
    minpi = int(ch_chunk.split('-')[0])
    maxpi = int(ch_chunk.split('-')[1]) 
    if ext == '.lc': 
        logging.info('Computing HE lightcurve background')
        opt = 'lc'
    elif ext == '.pha': 
        logging.info('Computing HE energy spectrum background')
        opt = 'spec'
    else:
        logging.info('File in the input list has not any recognizable format')
        return 
    output_root = destination/(file_name+'_bkg')
    output = destination/(file_name+'_bkg'+ext)
    # -----------------------------------------------------------------

    compute = True
    if output.is_file():
        logging.info('Background file already exists')
        compute = False  

        if compute or override:
            logging.info('Computing HE {} background'.format(opt))
            
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Dead time file
        dead = list_items(full_exp_dir/'HE',include_or='HE-DTime',ext='FITS')
        if not dead:
            logging.info('Dead Time file for HE missing')
            return

        # ehk file
        ehk = list_items(full_exp_dir/'AUX',include_or='_EHK_',ext='FITS')
        if not ehk:
            logging.info('Extend houskeeping data is missing')
            return 
        # -------------------------------------------------------------

        # Running hebkgmap  
        cmd = f'hebkgmap {opt} {screen_evt_file} {ehk} {gti_file} {dead} \
            {ascii_file} {minpi} {maxpi} {output_root}'
        os.system(cmd)

        if not output.is_file():
            logging.warning('he_bkg output file was not created')
            return

    return output


def me_cal(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs HXMT tool mepical

    DESCRITPTION
    ------------
    It checks the correct folder name, the existance of the event files, 
    and the output file.
    The tool mepical calculates PI columns values of ME event files.  
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, already existing files will be overwritten
                  
    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the calibrated file. If some of the operations
        is not successfull, it returns False.
        Output file is in the form:
        <destination>/<exp_ID>_ME_evt_cal.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running me_cal <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)
    
    # Initializing output file
    outfile = destination/'{}_ME_evt_cal.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('ME calibrated event file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing ME calibrated event file')

        # Initializing and checking existance of input files (event files) 
        # -------------------------------------------------------------
        evt = list_items(full_exp_dir/'ME',itype='file',include_or='ME-Evt',
            ext='.FITS')
        if type(evt) == list:
            if len(evt) > 1:
                logging.error('There is more than one ME-Evt file, returning')
                return
            if len(evt) == 0:
                logging.error('I did not find a ME-Evt file, returning')
                return

        # Temperature file
        temp = list_items(full_exp_dir/'ME',itype='file',include_or='ME-TH',
            ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one ME-TH file, returning')
                return
            if len(temp) == 0:
                logging.error('I did not find a ME-TH file, returning')
                return
        # -------------------------------------------------------------

        # Running calibration
        cmd = f'mepical evtfile={evt} tempfile={temp} outfile={outfile} \
            clobber=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('me_cal output file was NOT created')
            return         
    
    return outfile   


def me_grade(full_exp_dir,cal_evt_file=None,out_dir=pathlib.Path.cwd(),
    binsize=1,override=False):
    '''
    Run HXMT tool megrade.

    DESCRIPTIONS
    ------------
    It checks the correct folder name, the existance of the event files, 
    and the output file.
    The tool megrade calculates grade values of ME calibrated event and 
    calculate dead time of each FPGA
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    cal_evt_file: string or pathlib.Path, optional
        Full path of calibrated event file.
        If None (optional), the script will look for the file
    binsize: float, optional
        The binsize should be equal or less than the binned lightcurve
        binsize you want to compute
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True and a screened file already exists, this is removed
        Default is False
                  
    RETURNS
    -------
    outfile: tuple
        Tuple of pathlib.Paths or booleans.
        The full path of the graded event file and of the dead time file. 
        If some operation is not successfull, it returns False, False.
        Output file is in the form:
        <destination>/<exp_ID>_ME_evt_grade.fits,
        <destiantion>/<exp_ID>_ME_dtime_<timebin>s.fits.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running me_grade <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return False,False

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if cal_evt_file is None:
        cal_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_cal'])
        if cal_evt_file:
            if type(cal_evt_file) == list: 
                logging.error('There is more than one HE calibrated event file')
                return False,False
        else:
            logging.error('I could not find a HE calibrated event file')
            return False,False
    if type(cal_evt_file) == str: cal_evt_file = pathlib.Path(cal_evt_file)
    if not cal_evt_file.is_file():
        logging.error('{} does not exist'.format(cal_evt_file))
        return False,False
    # -----------------------------------------------------------------
    
    # Initializing output file
    evt_graded_file = destination/'{}_ME_evt_grade.fits'.format(exp_ID)
    dead_time_file = destination/'{}_ME_dtime_{}s.fits'.format(exp_ID,binsize)

    compute = True
    if evt_graded_file.is_file() and dead_time_file.is_file():
        logging.info('Grade file and/or dead time file already exist')
        compute = False  

    if compute or override:
        logging.info('Computing ME grade values and dead time')

        # Running megrade
        cmd = f'megrade evtfile={cal_evt_file} deadfile={dead_time_file} \
            outfile={evt_graded_file} binsize={binsize} clobber=yes'
        os.system(cmd)

        # Verifing successful running
        if not evt_graded_file.is_file() or not dead_time_file.is_file():
            logging.error('me_grade output file was NOT created')
            return False,False       
    
    return evt_graded_file,dead_time_file 

def me_gti(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Run HXMT tool megtigen

    DESCRIPTION
    -----------
    megtigen works similarly to NICER nimaketime, i.e. it generates a 
    fits file of good time intervals according to certain screening 
    criteria. 

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True and a screened file already exists, this is removed
        Default is False.

    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the calibrated file. If some operation is not 
        successfull, it returns False.
        Output file has format <destination>/<exp_id>_ME_gti_pre.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running me_gti <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Initializing outfile
    outfile=destination/'{}_ME_gti_pre.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('ME first gti file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing first ME GTI file')

        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # temperature file
        temp = list_items(full_exp_dir/'ME',itype='file',include_or='ME-TH',ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one ME-TH file, returning')
                return
            if len(temp) == 0:
                logging.error('I did not find a ME-TH file, returning')
                return

        # ehk file
        ehk = list_items(full_exp_dir/'AUX',itype='file',include_or='_EHK_',ext='FITS')
        if type(ehk) == list:
            if len(ehk) > 1:
                logging.error('There is more than one _EHK_ file, returning')
                return
            if len(ehk) == 0:
                logging.error('I did not find a _EHK_ file, returning')
                return        
        # -------------------------------------------------------------

        # Running screening
        cmd = f'megtigen tempfile={temp} ehkfile={ehk} outfile={outfile} \
            defaultexpr=NONE \
            expr="ELV>10&&COR>8&&SAA_FLAG==0&&TN_SAA>300&&T_SAA>300&&ANG_DIST<=0.04" \
            clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.info('me_gti output file was not created')
            return

    return outfile

def me_gticorr(full_exp_dir,grade_evt_file=None,gti_file=None,
    out_dir=pathlib.Path.cwd(),override=False):
    '''
    Run HXMT tool megticorr.

    DESCRIPTION
    -----------
    megticorr creates a second gti file according to some unknown creteria
    (they are not specified in the original guide). It also makes a file
    with information with good pixel
     
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    grade_evt_file: string or pathlib.Path or None, optional
        Full path of the graded event file (output of megrade).
        If None (default), the script will look for it
    gti_file: string or pathlib.Path or None, optional
        Full path of the first gti file (output of megtigen)
        If None (default), the script will look for it
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean (optional)
        If True, already existing files are overwritte (default is False)
                  
    RETURNS
    -------
    outfile: tuple
        (gti_file, bad_det_file)
        Output file is in the form:
        <exp_ID>_ME_gti.fits, <exp_ID>_ME_bad_det.fits or False,False

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running me_gticorr <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if grade_evt_file is None:
        grade_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_grade'])
        if grade_evt_file:
            if type(grade_evt_file) == list: 
                logging.error('There is more than one ME grade event file')
                return False,False
        else:
            logging.error('I could not find a ME grade event file')
            return False,False
    if type(grade_evt_file) == str: grade_evt_file = pathlib.Path(grade_evt_file)
    if not grade_evt_file.is_file():
        logging.error('{} does not exist'.format(grade_evt_file))
        return False,False

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['ME_gti_pre'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one first ME gti file')
                return False,False
        else:
            logging.error('I could not find a first ME gti file')
            return False,False
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return False,False   
    # -----------------------------------------------------------------
    
    # Initializing output file
    new_gti_file = destination/'{}_ME_gti.fits'.format(exp_ID)
    bad_det_file = destination/'{}_ME_bad_det.fits'.format(exp_ID)

    compute = True
    if new_gti_file.is_file() and bad_det_file.is_file():
        logging.info('Second ME gti file and bad det file already exist')
        compute = False  

    if compute or override:
        logging.info('Computing second ME gti file and bad det file')

        # Running calibration
        cmd = f'megticorr {grade_evt_file} {gti_file} {new_gti_file} \
            $HEADAS/refdata/medetectorstatus.fits {bad_det_file}'
        os.system(cmd)

        # Verifing successful running
        if not new_gti_file.is_file() or not bad_det_file.is_file():
            logging.error('me_gticorr output file was NOT created')
            return False,False   
    
    return new_gti_file,bad_det_file 

def me_screen(full_exp_dir,grade_evt_file=None,gti_file=None,bad_det_file=None,
            out_dir = pathlib.Path.cwd(),
            minpi=0,maxpi=1023,override=False):
    '''
    It runs HXMT tool me_screen

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    grade_evt_file: string or pathlib.Path or None, optional
        Full path of the graded event file (output of megrade).
        If None (default), the script will look for it
    gti_file: string or pathlib.Path or None, optional
        Full path of the second, corrected, gti file (output of megticorr)
        If None (default), the script will look for it
    bad_det_file: string or pathlib.Path or None, optional
        Full path of bad detector file (output of megticorr)
        If None (default), the script will look for it
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    minpi: integer, optional
        Minimum energy channel, default is 0
    maxpi: integer, optional
        Maximum energy channel, default is 1023
    override: boolean (optional)
        If True output files are overwritten (default is False)

    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the screened file. If some of the operations
        is not successfull, it returns False.
        The output file has format: <destination>/<exp_if>_ME_evt_screen.fits
    
    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala)
        Improved functionality and updated to pathlib.Path
    '''

    logging.info('===>>> Running me_screen <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if grade_evt_file is None:
        grade_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_grade'])
        if grade_evt_file:
            if type(grade_evt_file) == list: 
                logging.error('There is more than one ME grade event file')
                return False
        else:
            logging.error('I could not find a ME grade event file')
            return False
    if type(grade_evt_file) == str: grade_evt_file = pathlib.Path(grade_evt_file)
    if not grade_evt_file.is_file():
        logging.error('{} does not exist'.format(grade_evt_file))
        return False

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['ME_gti'],exclude_or=['pre','png'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one second ME gti file')
                return False
        else:
            logging.error('I could not find a second ME gti file')
            return False
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return False 

    if bad_det_file is None:
        bad_det_file = list_items(destination,itype='file',
            include_or=['ME_bad_det'])
        if bad_det_file:
            if type(bad_det_file) == list: 
                logging.error('There is more than one ME bad_det file')
                return False
        else:
            logging.error('I could not find a ME bad_det file')
            return False
    if type(bad_det_file) == str: bad_det_file = pathlib.Path(bad_det_file)
    if not bad_det_file.is_file():
        logging.error('{} does not exist'.format(bad_det_file))
        return False     
    # -----------------------------------------------------------------

    # Initializing outfile
    outfile=destination/'{}_ME_evt_screen.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('ME screened event file already exists')
        compute = False  

    if compute or override:
        logging.info('Performing ME screening')    

        # Running hescreen
        cmd = f'mescreen evtfile={grade_evt_file} gtifile={gti_file} \
            baddetfile={bad_det_file} outfile={outfile} userdetid="0-53" \
            starttime=0 stoptime=0 minPI={minpi} maxPI={maxpi} \
            clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('me_screen output file was not created')
            return

    return outfile


def me_spec(full_exp_dir,screen_evt_file=None,dead_time_file=None,
    user_det_ids='0-7,11-25,29-43,47-53',binsize=1,
    minpi=0,maxpi=1023,out_dir=pathlib.Path.cwd(),override=False):
    '''
    It computes ME energy spectrum colling megenspec
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path or None, optional
        Screaned and calibrated event file.
        If None (default), the script will look for it
    dead_time_file: string or pathlib.Path or None, optional
        Dead time file corresponding to the specified binsize
        If None (default), the script will look for it 
    user_det_ids: string (optional)
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves   
    binsize: float, optional
        Binsize of the lightcurve (time resolution). Default value is 1
    minpi: integer, optional
        Low energy channel. Default value is 119
    maxpi: integer, optional
        High energy channel. Default value is 546
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten
                  
    RETURN
    ------
    outfiles: pathlib.Path
        Energy spectrum with its full path. If some operation goes wrong,
        this will be False

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running me_spec <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one ME screen event file')
                return False
        else:
            logging.error('I could not find a ME screen event file')
            return False
    if type(screen_evt_file) == str: screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False

    if dead_time_file is None:
        dead_time_file = list_items(destination,itype='file',
            include_or=['ME_dtime_{}s'.format(binsize)])
        if dead_time_file:
            if type(dead_time_file) == list: 
                logging.error('There is more than one ME dead time file')
                return False
        else:
            logging.error('I could not find a ME dead time file')
            return False
    if type(dead_time_file) == str: dead_time_file = pathlib.Path(dead_time_file)
    if not dead_time_file.is_file():
        logging.error('{} does not exist'.format(dead_time_file))
        return False
    # -----------------------------------------------------------------
    
    # Initializing outfile
    file_name_root = '{}_ME_spec_ch{}-{}'.format(exp_ID,minpi,maxpi)
    outfile_root=destination/file_name_root

    test_spec = list_items(destination,itype='file',
        include_or=[file_name_root],exclude_or=['bkg','rsp'],ext='.pha')

    compute = True
    if test_spec:
        logging.info('ME energy spectrum already exist')
        compute = False  

    if compute or override:
        logging.info('Computing ME energy spectrum')
    
        # Running hespecgen
        cmd = f'mespecgen evtfile={screen_evt_file} outfile={outfile_root} \
            deadfile={dead_time_file} userdetid="{user_det_ids}" \
            starttime=0 stoptime=0 minPI={minpi} maxPI={maxpi} \
            clobber=yes'
        os.system(cmd)

        output = list_items(destination,itype='file',
            include_or=[file_name_root],exclude_or=['bkg','rsp'],ext='.pha')
    
        # Verifing successful running
        if not output.is_file():
            logging.warning('me_spec output file was not created')
            return

        # Writing lightcurve in a file
        with open(pathlib.Path(output).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(output)+'\n')

    return output

def me_lc(full_exp_dir,screen_evt_file=None,dead_time_file=None,
        user_det_ids='0-7,11-25,29-43,47-53',binsize=1,minpi=119,maxpi=546,
        out_dir = pathlib.Path.cwd(),override=False):
    '''
    It computes a lightcurve calling melcgen
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path or None, optional
        Screaned and calibrated event file.
        If None (default), the script will look for it
    dead_time_file: string or pathlib.Path or None, optional
        Dead time file corresponding to the specified binsize
        If None (default), the script will look for it 
    user_det_ids: string (optional)
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves   
    binsize: float, optional
        Binsize of the lightcurve (time resolution). Default value is 1
    minpi: integer, optional
        Low energy channel. Default value is 119
    maxpi: integer, optional
        High energy channel. Default value is 546
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten
             
    RETURNS
    -------
    outfile: pathlib.Path
        Lightcurve file with full path. If some operation goes wrong,
        this will be False

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running me_genlc <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one ME screen event file')
                return False
        else:
            logging.error('I could not find a ME screen event file')
            return False
    if type(screen_evt_file) == str: 
        screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False

    if dead_time_file is None:
        dead_time_file = list_items(destination,itype='file',
            include_or=['ME_dtime_{}s'.format(binsize)])
        if dead_time_file:
            if type(dead_time_file) == list: 
                logging.error('There is more than one ME dead time file')
                return False
        else:
            logging.error('I could not find a ME dead time file')
            return False
    if type(dead_time_file) == str: dead_time_file = pathlib.Path(dead_time_file)
    if not dead_time_file.is_file():
        logging.error('{} does not exist'.format(dead_time_file))
        return False
    # -----------------------------------------------------------------
 
    # Initializing outfile
    file_name_root = '{}_ME_lc_ch{}-{}_{}s'.format(exp_ID,minpi,maxpi,binsize)
    outfile_root=destination/file_name_root

    lc_test = list_items(destination,itype='file',
        include_or=[file_name_root],exclude_or=['bkg'],ext='.lc')
    compute = True
    if lc_test:
        logging.info('ME lightcurve already exists')
        compute = False  

    if compute or override:
        logging.info('Computing ME lightcurve')
    
        # Initializing and checking existance of input files
    
        # Running helcgen
        cmd = f'melcgen evtfile={screen_evt_file} outfile={outfile_root} \
            deadfile={dead_time_file} deadcorr=yes starttime=0 stoptime=0 \
            userdetid="{user_det_ids}" minPI={minpi} maxPI={maxpi} \
            binsize={binsize} clobber=yes'
        os.system(cmd)

        output = list_items(destination,itype='file',
            include_or=[file_name_root],ext='.lc')
    
        # Verifing successful running
        if not output.is_file():
            logging.warning('me_le output file was not created')
            return

        # Writing lightcurve in a file
        with open(pathlib.Path(output).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(output)+'\n')
    
    return pathlib.Path(output)

def me_rsp(full_exp_dir,energy_spectrum_file,
        out_dir=pathlib.Path.cwd(),override=False):
    '''
    Generates a response file for a ME spectrum running megenrsp
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    energy_spectrum_file: string or pathlib.Path, optional
        Energy spectrum (output of hespecgen).
        If None (default), the script will look for it.
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.
                  
    RETURNS
    -------    
    outfiles: list
        List of the response files with their full path
        
    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running me_genrsp <===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
    if type(energy_spectrum_file) == str: 
            energy_spectrum_file = pathlib.Path(energy_spectrum_file)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    # Checking if responses already exist
    # -----------------------------------------------------------------
    outfile = energy_spectrum_file.with_suffix('.rsp')

    compute = True
    if outfile.is_file():
        logging.info('ME response file already exists')
        compute = False

    if compute or override:
        logging.info('Computing ME response file')
    
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Attitude file
        att = list_items(full_exp_dir/'ACS',itype='file',
            include_or='Att',ext='FITS')
        if type(att) == list:
            if len(att) > 1:
                logging.error('There is more than one attitude file')
                return
            if len(att) == 0:
                logging.error('I did not find an attitude file')
                return  
        # -------------------------------------------------------------  

        # Running herspgen
        cmd = f"merspgen phafile={energy_spectrum_file} outfile={outfile} \
            attfile={att} ra=-1 dec=-91 clobber=yes"
        os.system(cmd)

        # Checking existance of the just created files
        if not outfile.is_file():
            logging.warning('me_rsp output file was not created'.\
                format(outfile))  
            return
        
    return outfile

def me_bkg(full_exp_dir,ascii_file,screen_evt_file=None,
    gti_file=None,dead_time_file=None,bad_det_file=None,
    binsize=1,
    out_dir=pathlib.Path.cwd(),override=False):
    '''
    It computes background for either a ME lightcurve or an energy spectrum
    calling mebkgmap
    
    DESCRIPTION
    -----------
    The option (lightcurve or spectrum) is automatically recognized 
    according to the extention of the first file in the provided ascii 
    text file. Also, the energy channels are automatically selected 
    according to the option. 
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder    
    ascii_file: string or pathlib.Path
        Full path of the text file either containing the energy spectra name or
        the lightcurve name.
        If the extension of the file is NOT .txt, the script will use file
        with the same name of the specified file, changing its extension to
        .txt
    screen_evt_file: string or pathlib.Path, optional
        Name of the calibrated and screened event file (output of mescreen)
        If None (default), the script will look for it
    gti_file: string or pathlib.Path, optional
        Name of the gti file (output of hegengti)
        If None (default), the script will look for it
    dead_time_file: string or pathlib.Path or None, optional
        Dead time file corresponding to the specified binsize
        If None (default), the script will look for it 
    bad_det_file: string or pathlib.Path or None, optional
        Full path of bad detector file (output of megticorr)
        If None (default), the script will look for it
    binsize: float, optional
        Binsize of the lightcurve, default is 1
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten (default is False)

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running me_bkg <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
    if type(ascii_file) == str: ascii_file = pathlib.Path(ascii_file)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)

    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'ME'
    if not destination.is_dir(): os.mkdir(destination)

    if ascii_file.suffix != '.txt': ascii_file = ascii_file.with_suffix('.txt')
    with open(ascii_file,'r') as infile:
        lines = infile.readlines()
    if len(lines) == 0:
        logging.error('ME ascii file is empty')
        return

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['ME_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one ME screen event file')
                return False
        else:
            logging.error('I could not find a ME screen event file')
            return False
    if type(screen_evt_file) == str: screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False

    if bad_det_file is None:
        bad_det_file = list_items(destination,itype='file',
            include_or=['ME_bad_det'])
        if bad_det_file:
            if type(bad_det_file) == list: 
                logging.error('There is more than one ME bad_det file')
                return False
        else:
            logging.error('I could not find a ME bad_det file')
            return False
    if type(bad_det_file) == str: bad_det_file = pathlib.Path(bad_det_file)
    if not bad_det_file.is_file():
        logging.error('{} does not exist'.format(bad_det_file))
        return False   

    if dead_time_file is None:
        dead_time_file = list_items(destination,itype='file',
            include_or=['ME_dtime_{}s'.format(binsize)])
        if dead_time_file:
            if type(dead_time_file) == list: 
                logging.error('There is more than one ME dead time file')
                return False
        else:
            logging.error('I could not find a ME dead time file')
            return False
    if type(dead_time_file) == str: dead_time_file = pathlib.Path(dead_time_file)
    if not dead_time_file.is_file():
        logging.error('{} does not exist'.format(dead_time_file))
        return False
    # -----------------------------------------------------------------
  
    # Automatically recognize channels and file type
    # -----------------------------------------------------------------
    file_name = pathlib.Path(lines[0]).stem
    ext = pathlib.Path(lines[0].strip()).suffix
    chunks = file_name.split('_')
    ch_chunk = [c for c in chunks if 'ch' in c][0].replace('ch','')
    minpi = int(ch_chunk.split('-')[0])
    maxpi = int(ch_chunk.split('-')[1]) 
    if ext == '.lc': 
        logging.info('Computing ME lightcurve background')
        opt = 'lc'
    elif ext == '.pha': 
        logging.info('Computing ME energy spectrum background')
        opt = 'spec'
    else:
        logging.info('File in the input list has not any recognizable format')
        return 
    output_root = destination/(file_name+'_bkg')
    outfile = destination/(file_name+'_bkg'+ext)
    # -----------------------------------------------------------------

    compute = True
    if not outfile.is_file():
        logging.info('{} already exists.'.format(outfile))
      
    if compute or override:
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # ehk file
        ehk = list_items(full_exp_dir/'AUX',include_or='_EHK_',ext='FITS')
        if not ehk:
            logging.info('Extend houskeeping data is missing')
            return 

        # Temperature file
        temp = list_items(full_exp_dir/'ME',itype='file',include_or='ME-TH',ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one ME-TH file, returning')
                return
            if len(temp) == 0:
                logging.error('I did not find a ME-TH file, returning')
                return
        # -------------------------------------------------------------

        # Running mebkgmap  
        cmd = f'mebkgmap {opt} {screen_evt_file} {ehk} {gti_file} \
            {dead_time_file} {temp} {ascii_file} {minpi} {maxpi} \
            {output_root}'
        os.system(cmd)

        if not outfile.is_file():
            logging.warning('ME background file was not created ({})'.format(outfile))
            return

    return outfile

def le_cal(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs HXMT tool lepical

    DESCRIPTION
    -----------
    It checks the correct folder name, the existance of the event files, 
    and the output file.
    The tool mepical calculates PI columns values of LE event files.  
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean, optional
        If True and a calibrated file already exists, this is removed
                  
    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the calibrated file. If some of the operations
        is not successfull, it returns False.
        Output file is in the form:
        <destination>/<exp_ID>_LE_evt_cal.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_cal <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)
    
    # Initializing output file
    outfile = destination/'{}_LE_evt_cal.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('LE calibrated event file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing LE calibrated event file')

        # Initializing and checking existance of input files (event files)
        # ------------------------------------------------------------- 
        evt = list_items(full_exp_dir/'LE',itype='file',include_or='LE-Evt',
            ext='.FITS')
        if type(evt) == list:
            if len(evt) > 1:
                logging.error('There is more than one LE-Evt file, returning')
                return
            if len(evt) == 0:
                logging.error('I did not find a LE-Evt file, returning')
                return

        # Temperature file
        temp = list_items(full_exp_dir/'LE',itype='file',include_or='LE-TH',
            ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one LE-TH file, returning')
                return
            if len(temp) == 0:
                logging.error('I did not find a LE-TH file, returning')
                return
        # -------------------------------------------------------------

        # Running calibration
        cmd = f'lepical evtfile={evt} tempfile={temp} outfile={outfile} \
            clobber=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('le_cal output file was NOT created')
            return         
    
    return outfile 

def le_recon(full_exp_dir,cal_evt_file=None,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs the HXMT tool lerecon.

    DESCRIPTION
    -----------
    It checks the correct folder name, the existance of the event files, 
    and the output file. 
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, already existing files will be overwritten
                  
    RETURN
    ------
    outfile: pathlib.Path or boolean
        The full path of the calibrated file. If some of the operations
        is not successfull, it returns False.
        Output file is in the form:
        <exp_ID>_LE_evt_recon.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_recon <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if cal_evt_file is None:
        cal_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_cal'])
        if cal_evt_file:
            if type(cal_evt_file) == list: 
                logging.error('There is more than one LE calibrated event file')
                return False
        else:
            logging.error('I could not find a LE calibrated event file')
            return False
    if type(cal_evt_file) == str: 
        cal_evt_file = pathlib.Path(cal_evt_file)
    if not cal_evt_file.is_file():
        logging.error('{} does not exist'.format(cal_evt_file))
        return False
    # -----------------------------------------------------------------
    
    # Initializing output file
    outfile = destination/'{}_LE_evt_recon.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('LE reconstructed event file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing LE reconstructed event file')

        # Initializing and checking existance of input files (event files) 
        # -------------------------------------------------------------
        status = list_items(full_exp_dir/'LE',itype='file',
            include_or='LE-InsStat',ext='.FITS')
        if type(status) == list:
            if len(status) > 1:
                logging.error('There is more than one LE-InsStat file, returning')
                return
            if len(status) == 0:
                logging.error('I did not find a LE-InsStat file, returning')
                return
            # -------------------------------------------------------------

        # Running calibration
        cmd = f'lerecon evtfile={cal_evt_file} outfile={outfile} \
            instatusfile={status} clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('le_recon output file was NOT created')
            return         
    
    return outfile 

def le_gti(full_exp_dir,out_dir=pathlib.Path.cwd(),override=False):
    '''
    Runs the HXMT tool legtigen

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean, optional
        If True and a screened file already exists, this is removed
        Default is False.

    RETURN
    ------
    outfile: pathlib.Path or boolean
        The full path of the gti file. If some operations is not 
        successfull, it returns False.
        Output file has format <destination>/<exp_id>_LE_gti_pre.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_gti <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Initializing outfile
    outfile=destination/'{}_LE_gti_pre.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('LE first gti file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing first LE GTI file')

        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        status = list_items(full_exp_dir/'LE',itype='file',
            include_or='LE-InsStat',ext='.FITS')
        if type(status) == list:
            if len(status) > 1:
                logging.error('There is more than one LE-InsStat file.')
                return
            if len(status) == 0:
                logging.error('I did not find a LE-InsStat file.')
                return

        # temperature file
        temp = list_items(full_exp_dir/'LE',itype='file',
            include_or='LE-TH',ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one LE-TH file.')
                return
            if len(temp) == 0:
                logging.error('I did not find a LE-TH file.')
                return

        # high voltage file
        ehk = list_items(full_exp_dir/'AUX',itype='file',
            include_or='_EHK_',ext='FITS')
        if type(ehk) == list:
            if len(ehk) > 1:
                logging.error('There is more than one _EHK_ file.')
                return
            if len(ehk) == 0:
                logging.error('I did not find a _EHK_ file.')
                return        
        # -------------------------------------------------------------

        # Running screening
        cmd = f'legtigen evtfile="NONE" instatusfile={status} tempfile={temp} \
            ehkfile={ehk} outfile={outfile} defaultexpr=NONE \
            expr="ELV>10&&DYE_ELV>30&&COR>8&&SAA_FLAG==0&&T_SAA>=300&&TN_SAA>=300&&ANG_DIST<=0.04" \
            clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.info('le_gti output file was not created')
            return

    return outfile

def le_gticorr(full_exp_dir,recon_evt_file=None,gti_file=None,
    out_dir=pathlib.Path.cwd(),override=False):
    '''
    Run HXMT tool legticorr.
     
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    recon_evt_file: string or pathlib.Path or None, optional
        Full path of the reconstructed event file (output of lerecon).
        If None (default), the script will look for it
    gti_file: string or pathlib.Path or None, optional
        Full path of the first gti file (output of legtigen)
        If None (default), the script will look for it
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean (optional)
        If True, already existing files are overwritte (default is False)
                  
    RETURN
    ------
    outfile: pathlib.Path or boolean
        Full path of the corrected gti file. If some operation goes 
        wrong, it returns False.

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_gticorr <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
       
    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if recon_evt_file is None:
        recon_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_recon'])
        if recon_evt_file:
            if type(recon_evt_file) == list: 
                logging.error('There is more than one LE recunstructed event file')
                return False,False
        else:
            logging.error('I could not find a LE recunstructed  event file')
            return False,False
    if type(recon_evt_file) == str: recon_evt_file = pathlib.Path(recon_evt_file)
    if not recon_evt_file.is_file():
        logging.error('{} does not exist'.format(recon_evt_file))
        return False,False

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['LE_gti_pre'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one first LE gti file')
                return False,False
        else:
            logging.error('I could not find a first LE gti file')
            return False,False
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return False,False   
    # -----------------------------------------------------------------
    
    # Initializing output file
    outfile = destination/'{}_LE_gti.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('LE gti file and bad det file already exist')
        compute = False  

    if compute or override:
        logging.info('Computing new gti file and bad det file')

        # Running calibration
        cmd = f'legticorr {recon_evt_file} {gti_file} {outfile}'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('le_gti output file was NOT created')
            return         
    
    return outfile

def le_screen(full_exp_dir,recon_evt_file=None,gti_file=None,
        user_det_ids='0-95',minpi=0,maxpi=1535,
        out_dir = pathlib.Path.cwd(),override=False):
    '''
    It runs HXMT tool le_screen

    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder
    recon_evt_file: string or pathlib.Path or None, optional
        Full path of the reconstructed event file (output of lerecon).
        If None (default), the script will look for it
    gti_file: string or pathlib.Path or None, optional
        Full path of the second, corrected, gti file (output of megticorr)
        If None (default), the script will look for it
    user_det_ids: string, optional
        String specifying selected detector ids
    minpi: integer, optional
        Minimum energy channel, default is 0
    maxpi: integer, optional
        Maximum energy channel, default is 1535
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean (optional)
        If True output files are overwritten (default is False)

    RETURNS
    -------
    outfile: pathlib.Path or boolean
        The full path of the screened file. If some of the operations
        is not successfull, it returns False.
        The output file has format: <destination>/<exp_if>_LE_evt_screen.fits

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_screen <<<===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)

    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if recon_evt_file is None:
        recon_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_recon'])
        if recon_evt_file:
            if type(recon_evt_file) == list: 
                logging.error('There is more than one LE recunstructed event file')
                return False,False
        else:
            logging.error('I could not find a LE recunstructed  event file')
            return False,False
    if type(recon_evt_file) == str: recon_evt_file = pathlib.Path(recon_evt_file)
    if not recon_evt_file.is_file():
        logging.error('{} does not exist'.format(recon_evt_file))
        return False,False

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['LE_gti'],exclude_or=['pre','png'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one second LE gti file')
                return False,False
        else:
            logging.error('I could not find a second LE gti file')
            return False,False
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return False,False   
    # -----------------------------------------------------------------

    # Initializing outfile
    outfile=destination/'{}_LE_evt_screen.fits'.format(exp_ID)

    compute = True
    if outfile.is_file():
        logging.info('Screened event file already exists')
        compute = False  

    if compute or override:
        logging.info('Performing screening')    

        # Running hescreen
        cmd = f'lescreen evtfile={recon_evt_file} gtifile={gti_file} \
            outfile={outfile} userdetid="{user_det_ids}" \
            eventtype=0 starttime=0 stoptime=0 \
            minPI={minpi} maxPI={maxpi} clobber=yes history=yes'
        os.system(cmd)

        # Verifing successful running
        if not outfile.is_file():
            logging.error('le_screen output file was not created')
            return

    return outfile

def le_lc(full_exp_dir,screen_evt_file=None,
        user_det_ids="0,2-4,6-10,12,14,20,22-26,28,30,32,34-36,38-42,44,46,52,54-58,60-62,64,66-68,70-74,76,78,84,86,88-90,92-94",
        binsize=1,minpi=106,maxpi=1169,
        out_dir = pathlib.Path.cwd(),override=False):
    '''
    It computes a lightcurve calling lelcgen
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path or None, optional
        Screaned and calibrated event file.
        If None (default), the script will look for it
    user_det_ids: string (optional)
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves   
    binsize: float, optional
        Binsize of the lightcurve (time resolution). Default value is 1
    minpi: integer, optional
        Low energy channel. Default value is 119
    maxpi: integer, optional
        High energy channel. Default value is 546
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten
                  
    RETURNS
    -------
    outfile: pathlib.Path or boolean
        Lightcurve file with full path. If some operation goes wrong,
        this will be False

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===>>> Running le_genlc <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one LE screen event file')
                return False
        else:
            logging.error('I could not find a LE screen event file')
            return False
    if type(screen_evt_file) == str: 
        screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False
    # -----------------------------------------------------------------
    
    # Initializing outfile
    file_name_root = '{}_LE_lc_ch{}-{}_{}s'.format(exp_ID,minpi,maxpi,binsize)
    outfile_root=destination/file_name_root

    lc_test = list_items(destination,itype='file',
        include_or=[file_name_root],exclude_or=['bkg'],ext='.lc')
    compute = True
    if lc_test:
        logging.info('LE lightcurve already exists')
        compute = False  

    if compute or override:
        logging.info('Computing lightcurve')
    
        # Initializing and checking existance of input files
    
        # Running helcgen
        cmd = f'lelcgen evtfile={screen_evt_file} outfile={outfile_root} \
            userdetid="{user_det_ids}" minPI={minpi} maxPI={maxpi} \
            eventtype=1 starttime=0 stoptime=0 binsize={binsize} \
            clobber=yes'
        os.system(cmd)

        output = list_items(destination,itype='file',
            include_or=[file_name_root],exclude_or=['bkg'],ext='.lc')
    
        # Verifing successful running
        if not output.is_file():
            logging.warning('le_le output file was not created')
            return

        # Writing lightcurve in a file
        with open(pathlib.Path(output).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(output)+'\n')
    
    return pathlib.Path(output)

def le_spec(full_exp_dir,screen_evt_file=None,
    user_det_ids="0,2-4,6-10,12,14,20,22-26,28,30,32,34-36,38-42,44,46,52,54-58,60-62,64,66-68,70-74,76,78,84,86,88-90,92-94",
    minpi=0,maxpi=1535,out_dir=pathlib.Path.cwd(),override=False):
    '''
    It computes an energy spectrum running lespecgen
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    screen_evt_file: string or pathlib.Path or None, optional
        Screaned and calibrated event file.
        If None (default), the script will look for it
    user_det_ids: string (optional)
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves   
    minpi: integer, optional
        Low energy channel. Default value is 0
    maxpi: integer, optional
        High energy channel. Default value is 1535
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten
                  
    RETURN
    ------
    outfiles: pathlib.Path or boolean
        Full path of the energy spectrum. If some operation goes wrong,
        this will be False

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running le_spec <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one LE screen event file')
                return False
        else:
            logging.error('I could not find a LE screen event file')
            return False
    if type(screen_evt_file) == str: 
        screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False
    # -----------------------------------------------------------------
    
    # Initializing outfile
    file_name_root = '{}_LE_spec_ch{}-{}'.format(exp_ID,minpi,maxpi)
    outfile_root=destination/file_name_root

    test_spec = list_items(destination,itype='file',
        include_or=[file_name_root],exclude_or=['bkg','rsp'],ext='.pha')

    compute = True
    if test_spec:
        logging.info('LE energy spectrum already exist')
        compute = False  

    if compute or override:
        logging.info('Computing ME energy spectrum')
    
        # Running hespecgen
        cmd = f'lespecgen evtfile={screen_evt_file} outfile={outfile_root} \
            userdetid="{user_det_ids}" starttime=0 stoptime=0 eventtype=1 \
            minPI={minpi} maxPI={maxpi} clobber=yes'
        os.system(cmd)

        output = list_items(destination,itype='file',
            include_or=[file_name_root],exclude_or=['bkg','rsp'],ext='.pha')
    
        # Verifing successful running
        if not output.is_file():
            logging.warning('le_spec output file was not created')
            return

        # Writing lightcurve in a file
        with open(pathlib.Path(output).with_suffix('.txt'),'w') as tmp:
            tmp.write(str(output)+'\n')

    return output

def le_bkg(full_exp_dir,ascii_file,screen_evt_file=None,
    gti_file=None,out_dir=pathlib.Path.cwd(),override=False):
    '''
    It computes background for either a lightcurve or an energy spectrum. 
    
    DESCRIPTION
    -----------
    The option (lightcurve or spectrum) is automatically recognized 
    according to the extention of the first file in the provided ascii 
    text file. Also, the energy channels are automatically selected 
    according to the option. 
    
    PARAMETERS
    ----------
    full_exp_dir: string or pathlib.Path
        Full path of the esposure folder    
    ascii_file: string or pathlib.Path
        Full path of the text file either containing the energy spectra name or
        the lightcurve name.
        If the extension of the file is NOT .txt, the script will use file
        with the same name of the specified file, changing its extension to
        .txt
    screen_evt_file: string or pathlib.Path, optional
        Name of the calibrated and screened event file (output of mescreen)
        If None (default), the script will look for it
    gti_file: string or pathlib.Path, optional
        Name of the gti file (output of hegengti)
        If None (default), the script will look for it
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/ME).
        Default is current working directory.
    override: boolean, optional
        If True, existing files will be overwritten (default is False)

    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running le_bkg <<<===')
    
    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir):
        print(full_exp_dir)
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)

    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    if ascii_file.suffix != '.txt': ascii_file = ascii_file.with_suffix('.txt')
    with open(ascii_file,'r') as infile:
        lines = infile.readlines()
    if len(lines) == 0:
        logging.error('LE ascii file is empty')

    # Verifying existance of input files
    # -----------------------------------------------------------------
    if screen_evt_file is None:
        screen_evt_file = list_items(destination,itype='file',
            include_or=['LE_evt_screen'])
        if screen_evt_file:
            if type(screen_evt_file) == list: 
                logging.error('There is more than one LE screen event file')
                return False
        else:
            logging.error('I could not find a LE screen event file')
            return False
    if type(screen_evt_file) == str: 
        screen_evt_file = pathlib.Path(screen_evt_file)
    if not screen_evt_file.is_file():
        logging.error('{} does not exist'.format(screen_evt_file))
        return False

    if gti_file is None:
        gti_file = list_items(destination,itype='file',
            include_or=['LE_gti'],exclude_or=['pre','png'])
        if gti_file:
            if type(gti_file) == list: 
                logging.error('There is more than one second LE gti file')
                return False,False
        else:
            logging.error('I could not find a second LE gti file')
            return False,False
    if type(gti_file) == str: gti_file = pathlib.Path(gti_file)
    if not gti_file.is_file():
        logging.error('{} does not exist'.format(gti_file))
        return False,False   
    # -----------------------------------------------------------------
    
    # Automatically recognize channels and file type
    # -----------------------------------------------------------------
    file_name = pathlib.Path(lines[0]).stem
    ext = pathlib.Path(lines[0].strip()).suffix
    chunks = file_name.split('_')
    ch_chunk = [c for c in chunks if 'ch' in c][0].replace('ch','')
    minpi = int(ch_chunk.split('-')[0])
    maxpi = int(ch_chunk.split('-')[1]) 
    if ext == '.lc': 
        logging.info('Computing LE lightcurve background')
        opt = 'lc'
    elif ext == '.pha': 
        logging.info('Computing LE energy spectrum background')
        opt = 'spec'
    else:
        logging.info('File in the input list has not any recognizable format')
        return 
    output_root = destination/(file_name+'_bkg')
    outfile = destination/(file_name+'_bkg'+ext)
    # -----------------------------------------------------------------

    compute = True
    if not outfile.is_file():
        logging.info('{} already exists.'.format(outfile))
      
    if compute or override:
        # Running lebkgmap  
        cmd = f'lebkgmap {opt} {screen_evt_file} {gti_file} {ascii_file} \
            {minpi} {maxpi} {destination/output_root}'
        os.system(cmd)

        if not outfile.is_file():
            logging.warning('LE background file was not created ({})'.\
                format(outfile))
            return

    return outfile

def le_rsp(full_exp_dir,energy_spectrum_file,
        out_dir=pathlib.Path.cwd(),override=False):
    '''
    Generates a response file for a LE spectrum running legenrsp
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    energy_spectrum_file: string or pathlib.Path, optional
        Energy spectrum (output of hespecgen).
        If None (default), the script will look for it.
    out_dir: string or pathlib.Path(), optional
        Name of the outoup products folder. If not existing, an analysis
        folder will be created inside this output folder and, inside it,
        a folder with the name of the exposure (proposal-obs_ID-exp_ID)
        and the instrument (proposal-obs_ID-exp_ID/LE).
        Default is current working directory.
    override: boolean, optional
        If True and a gti file already exists, this is overwritten.   
        Default is False.
                  
    RETURNS
    -------    
    outfiles: list
        List of the response files with their full path
        
    HISTORY
    -------
    2021 05 06, Stefano Rapisarda (Uppsala), creation date
    '''

    logging.info('===> Running le_rsp <===')

    if type(full_exp_dir) == str: full_exp_dir = pathlib.Path(full_exp_dir)
    if type(out_dir) == str: out_dir = pathlib.Path(out_dir)
    if type(energy_spectrum_file) == str: 
            energy_spectrum_file = pathlib.Path(energy_spectrum_file)

    # Checking exposure folder format
    if not check_exp_format(full_exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(full_exp_dir)
        return 

    # Defining obs_ID as proposal_ID-obs_ID-exp_ID
    exp_ID = str(full_exp_dir.name)
    
    # Creating destination folders
    an = out_dir/'analysis'
    if not an.is_dir(): os.mkdir(an)
    exp_dir = an/exp_ID
    if not exp_dir.is_dir(): os.mkdir(exp_dir)
    destination = exp_dir/'LE'
    if not destination.is_dir(): os.mkdir(destination)

    # Checking if responses already exist
    # -----------------------------------------------------------------
    outfile = energy_spectrum_file.with_suffix('.rsp')

    compute = True
    if outfile.is_file():
        logging.info('LE response file already exists')
        compute = False

    if compute or override:
        logging.info('Computing LE response file')
    
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Attitude file
        att = list_items(full_exp_dir/'ACS',itype='file',
            include_or='Att',ext='FITS')
        if type(att) == list:
            if len(att) > 1:
                logging.error('There is more than one attitude file')
                return
            if len(att) == 0:
                logging.error('I did not find an attitude file')
                return 

        # temperature file
        temp = list_items(full_exp_dir/'LE',itype='file',
            include_or='LE-TH',ext='.FITS')
        if type(temp) == list:
            if len(temp) > 1:
                logging.error('There is more than one LE-TH file')
                return
            if len(temp) == 0:
                logging.error('I did not find a LE-TH file')
                return 
        # -------------------------------------------------------------  

        # Running herspgen
        cmd = f"lerspgen phafile={energy_spectrum_file} outfile={outfile} \
            attfile={att} tempfile={temp} ra=-1 dec=-91 clobber=yes"
        os.system(cmd)

        # Checking existance of the just created files
        if not outfile.is_file():
            logging.warning('le_rsp output file was not created'.\
                format(outfile))  
            return
        
    return outfile

if __name__ == '__main__':
    args = sys.argv
    full_exp_dir = '/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/P0101315/P0101315002/P010131500201-20171031-01-01'
    out_dir='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1'
    obs_id='P010131500201-20171031-01-01'

    if 'me_cal' in args:
        me_cal_output = me_cal(full_exp_dir,out_dir=out_dir)
        print(me_cal_output)  
    if 'me_grade' in args:
        me_grade_output = me_grade(full_exp_dir,
            cal_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_evt_cal.fits',
            out_dir=out_dir) 
        print(me_grade_output) 
    if 'me_gti' in args:
        me_gti_output = me_gti(full_exp_dir,out_dir=out_dir)
        print(me_gti_output)
    if 'me_gticorr' in args:
        out1,out2 = me_gticorr(full_exp_dir,
        graded_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_evt_graded.fits',
        gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_gti_pre.fits',
        out_dir=out_dir)
        print(out1,out2)
    if 'me_screen' in args:
        out = me_screen(full_exp_dir,
            graded_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_evt_graded.fits',
            gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_gti.fits',
            bad_det_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_bad_det.fits',
            out_dir=out_dir)
        print(out)
    if 'me_spec' in args:
        out = me_spec(full_exp_dir,
            graded_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_evt_graded.fits',
            dead_time_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_dtime_1s.fits',
            out_dir=out_dir)
    if 'me_genlc' in args:
        out = me_lc(full_exp_dir,
            screened_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_evt_screen.fits',
            dead_time_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_ME_dtime_1s.fits',
            out_dir=out_dir
        )   
        print(out)
    if 'me_rspgen' in args:
        out = me_rsp(full_exp_dir,
            phafile=pathlib.Path(out_dir)/'analysis'/obs_id
            )

    if 'le_cal' in args:
        out = le_cal(full_exp_dir,out_dir=out_dir)
        print(out) 
    if 'le_recon' in args:
        out = le_recon(full_exp_dir,
        cal_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_cal.fits',
        out_dir=out_dir)
        print(out) 
    if 'le_gti' in args:
        out = le_gti(full_exp_dir,out_dir=out_dir)
        print(out)
    if 'le_gticorr' in args:
        out = le_gticorr(full_exp_dir,
        recon_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_recon.fits',
        gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_gti_pre.fits',
        out_dir=out_dir)
    if 'le_screen' in args:
        out = le_screen(full_exp_dir,
        recon_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_recon.fits',
        gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_gti_pre.fits',
        out_dir=out_dir)
        print(out)
    if 'le_lc' in args:
        out = le_lc(full_exp_dir,
        screen_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_screen.fits',
        out_dir=out_dir)
        print(out)
    if 'le_spec' in args:
        out = le_spec(full_exp_dir,
        screen_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_screen.fits',
        out_dir=out_dir)
    if 'le_bkg_lc' in args:
        out = le_bkg(full_exp_dir,
        screen_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_screen.fits',
        gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_gti.fits',
        ascii_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_lc_ch106-1169_1s_g0_0-94.txt',
        out_dir=out_dir)
        print(out)
    if 'le_bkg_spec' in args:
        out = le_bkg(full_exp_dir,
        screen_evt_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_evt_screen.fits',
        gti_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_gti.fits',
        ascii_file=pathlib.Path(out_dir)/'analysis'/obs_id/'P010131500201-20171031-01-01_LE_spec_g0_0-94.txt',
        out_dir=out_dir)
        print(out)

    if 'he_cal' in args:
        he_cal_output = he_cal(full_exp_dir,out_dir=out_dir)
        print(he_cal_output)
    if 'he_gti' in args:
        he_gti_output = he_gti(full_exp_dir,out_dir=out_dir)
        print(he_gti_output)
    if 'he_screen' in args :
        he_screen_output = he_screen(full_exp_dir,
        out_dir=out_dir,
        cal_evt = pathlib.Path('/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_evt_cal.fits'),
        gti = pathlib.Path('/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_gti.fits')
        )
        print(he_screen_output)
    if 'he_genspec' in args:
        he_gen_spec_output = he_spec(full_exp_dir,
        out_dir=out_dir,
        evt=pathlib.Path('/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_evt_cal_screen.fits')
        )
        print(he_gen_spec_output)
    if 'he_genrsp' in args:
        fold = pathlib.Path(out_dir)/'analysis/P010131500201-20171031-01-01'
        spectra = list_items(fold,itype='file',ext='pha',exclude_or=['rsp','bkg']) 
        he_genrsp_output = he_rsp(full_exp_dir,spectra,out_dir=out_dir)
        print(he_genrsp_output)
    if 'he_genlc' in args:
        fold = pathlib.Path(out_dir)/'analysis/P010131500201-20171031-01-01'
        he_genlc_output = he_lc(
            full_exp_dir=full_exp_dir,
            evt=fold/'P010131500201-20171031-01-01_HE_evt_cal_screen.fits',
            out_dir=out_dir
        )
        print(he_genlc_output)
    if 'he_bkgmap_spec' in args:
        he_bkg(full_exp_dir,
        ascii_file='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/HE_spectra_list.txt',
        evt='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_evt_cal_screen.fits',
        gti='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_gti.fits',
        out_dir=out_dir)
    if 'he_bkgmap_lc' in args:
        he_bkg(full_exp_dir,
        ascii_file='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_lc_ch8-162_1s_g0_0-17.txt',
        evt='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_evt_cal_screen.fits',
        gti='/Volumes/Samsung_T5/test_hxmt_pipeline/Cygnus_X1/analysis/P010131500201-20171031-01-01/P010131500201-20171031-01-01_HE_gti.fits',
        out_dir=out_dir)