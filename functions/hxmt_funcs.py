import os
import sys
from my_funcs import create_dir

import glob
import numpy as np
import logging

def check_HE_spectra_files(spectra,bkgs,resps,folder=os.getcwd()):
    '''
    Checks if the .txt files spectra, bkgs, and resp exist,
    have the same number of files, and these files correspond
    to the same detectors
    
    PARAMETERS
    ----------
    spectra: string
        Text file containing energy spectra per HE detector
        
    bkgs: string
        Text file containing background spectra per HE detector
        
    resps: string
        Text file containing response spectra per HE detector
        
    RETURNS
    -------
    flag: boolean
        True if all the criteria are satisfied
        
    HISTORY
    -------
    2021 01 26, Stefano Rapisarda (Uppsala), creation date
    '''
    
    all_lines = []
    for f in [spectra,bkgs,resps]:
        if not os.path.isfile(os.path.join(folder,f)):
            logging.info('{} file does not exist in {}'.format(f,folder))
            return False
        else:
            with open(os.path.join(folder,f),'r') as infile:
                lines = infile.readlines()
            all_lines += [lines]
    
    if (len(all_lines[0]) != len(all_lines[1])) or (len(all_lines[0]) != len(all_lines[2])):
        logging.info('Number of files is not the same')
        return False
    
    for line1,line2,line3 in zip(all_lines[0],all_lines[1],all_lines[2]):
        if (line1.split('_')[-1] != line2.split('_')[-1]) or (line1.split('_')[-1] != line2.split('_')[-1]):
            logging.info('Channels do not correspond')
            return False
        
        
    return True
        
        
        
    
        

def check_exp_format(exp):
    '''
    Check the right formar of the proposal format

    ex. P010129900101-20170827-01-01
    '''
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

def check_and_choose(path=os.getcwd(),inc='',ext=''):
    '''
    List items according to specified criteria and returns the last one
    after sorting

    path: str, optional
        Folder containing the items to select. Default value is the 
        current working directory
    inc: str, optional
        Only files or directories including this string will be 
        selected. Default value is '' (whatever)
    ext: str, optional
        Only files with this extension will be selected
        If '' (default), only directories will be selected
        If '*', all possible extensions will be considered

    NOTES
    -----
    - if you include a path in the argument for glob, it will return
      items already including the full path (so you do not need to use
      os.path.join() on each of them)

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        This was depending on mf.list_items. I am rewriting it using 
        glob in order to make it independent from that.
        In list_items I had to specify a in variable to select folders
        (1) or files (2). Here I leave it to extension. If extension is
        '' (default), then the function will list folders.

    TODO: update list_items in kronos in this way
    '''

    if ext == '':
        items = glob.glob('{}/*{}*'.format(path,inc))
        items = sorted([item for item in items if os.path.isdir(item)])
    else:
        items = glob.glob('{}/*{}*.{}*'.format(path,inc,ext))
        items = sorted([item for item in items if os.path.isfile(item)])      

    #print(items)
    if len(items) > 1:
        logging.info('There is more than one file containing {} in {}'.format(inc,path))
        logging.info('Choosing {}'.format(items[-1]))
        return items[-1]
    elif len(items) == 0:
        logging.info('There are no files containing {} in {}'.format(inc,path))
        return
    else:
        return items[0]

def he_cal(full_exp_dir,out_dir = 'reduced_products',override=False):
    '''
    Run HXMT tool hepical.

    It checks the correct folder name, the existance of the event files, 
    and the output file.
    The tool hepical remove spike events caused by electronic system and
    calculate PI columns values of HE event files.  
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE
    override: boolean (optional)
        If True and a screened file already exists, this is removed
                  
    RETURN
    ------
    outfile: string
        The full path of the calibrated file. If some of the operations
        is not successfull, it returns False.
        Output file is in the form:
        HXMT_<exp_ID>_HE_evt_cal.fits

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        file is returned
    '''

    logging.info('===>>> Running he_cal <<<===')
    
    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('cal_he requires full path for exp_dir')
        return 
    exp_dir = tmp[-1] 
    
    # Checking exposure folder format
    if not check_exp_format(exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return 
    #exp_ID = exp_dir.split('-')[0]
    exp_ID = exp_dir
    
    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE'))
    
    # Initializing output file
    outfile = os.path.join(destination,'{}_HE_evt_cal.fits'.\
        format(exp_ID))

    compute = True
    if os.path.isfile(outfile):
        logging.info('Screened event file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing screened event file')

        # Initializing and checking existance of input files (event files) 
        evt = check_and_choose(os.path.join(full_exp_dir,'HE'),inc='HE-Evt',ext='FITS')
        if not evt:
            logging.info('There is not event file for HE')
            return 

        # Running calibration
        cmd = 'hepical evtfile={} outfile={} glitchfile={}/HE_spikes.fits '\
            'clobber=yes'.format(evt,outfile,destination)
        os.system(cmd)

        # Verifing successful running
        if not os.path.isfile(outfile):
            logging.info('he_cal output file was NOT created')
            return         
    
    return outfile

def he_gti(full_exp_dir,out_dir='reduced_products',override=False):
    '''
    Run HXMT tool hegtigen

    hegtigen works similarly to NICER nimaketime, i.e. it generates a 
    fits file of good time intervals according to certain screening 
    criteria. It needs a high voltave file, temperature file, and 
    particle monitor file (HE folder), and a house keeping file 
    (AUX folder)

    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE
    override: boolean (optional)
        If True and a screened file already exists, this is removed    

    RETURN
    ------
    outfile: string
        The full path of the calibrated file. If some of the operations
        is not successfull, it returns False.

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if gti file
        already exists and override=False, the name of the gti
        file is returned
    '''

    logging.info('===>>> Running he_gti <<<===')

    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_gti requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]

    # Checking exposure folder format
    if not check_exp_format(exp_dir):
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]

    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE'))

    # Initializing outfile
    outfile=os.path.join(destination,'{}_HE_gti.fits'.format(exp_ID))

    compute = True
    if os.path.isfile(outfile):
        logging.info('Gti file already exists')
        compute = False  

    if compute or override:
        logging.info('Computing GTI file')

        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # high voltage file
        hv = check_and_choose(os.path.join(full_exp_dir,'HE'),\
            inc='HE-HV',ext='FITS')
        if not hv:
            logging.info('High voltage file for HE missing')
            return

        # Temperature file
        temp = check_and_choose(os.path.join(full_exp_dir,'HE'),\
            inc='HE-TH',ext='FITS')
        if not temp:
            logging.info('Temperature file for HE is missing')
            return

        # ehk file
        ehk = check_and_choose(os.path.join(full_exp_dir,'AUX'),\
            inc='_EHK_',ext='FITS')
        if not ehk:
            logging.info('Extend houskeeping data is missing')
            return

        # pm file
        pm = check_and_choose(os.path.join(full_exp_dir,'HE'),\
            inc='HE-PM',ext='FITS')
        if not pm:
            logging.info('Particle monitoring file is missing')
            return
        # -------------------------------------------------------------

        # Running screening
        cmd = 'hegtigen hvfile={} tempfile={} pmfile={} ehkfile={} ' \
        'outfile={} defaultexpr=NONE '\
        'expr="ELV>10&&COR>8&&SAA_FLAG==0&&TN_SAA>300&&T_SAA>300&&ANG_DIST<=0.04"' \
        ' pmexpr="" clobber=yes history=yes'.format(hv,temp,pm,ehk,outfile)
        os.system(cmd)

        # Verifing successful running
        if not os.path.isfile(outfile):
            logging.info('he_gti output file was not created')
            return

    return outfile


def he_screen(full_exp_dir,cal_evt='',gti='',out_dir = 'reduced_products',
             minpi=0,maxpi=255,override=False):
    '''
    It runs HXMT tool he_screen

    hescreen uses the previously creted GTI file to remove photons from 
    the previously created calibrated event file. At this stage, events 
    can be also discriminated according to the pulse shape.
    As the input of hescreen are products created by other function, 
    we do not need to check if the input files exist. This is supposed 
    to be done by previous functions in the code.

    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    cal_evt: string
        Calibrated event file (output of hepical) with its full path
    gti: string
        GTI file (output of hegtigen) with its full path
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE
    minpi: integer (optional)
        Minimum energy channel, default is 0
    maxpi: integer (optiona)
        Maximum energy channel, defaule is 255
    override: boolean (optional)
        If True and a screened file already exists, this is removed

    RETURN
    ------
    outfile: string
        The full path of the screened file. If some of the operations
        is not successfull, it returns False.

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        file is returned

    '''

    logging.info('===>>> Running he_screen <<<===')

    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_screen requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]

    # Checking exposure folder format
    if not check_exp_format(exp_dir):
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]

    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE'))

    # Initializing outfile
    outfile=os.path.join(destination,'{}_HE_screen.fits'.format(exp_ID))

    compute = True
    if os.path.isfile(outfile):
        logging.info('Screened event file already exists')
        compute = False  

    if compute or override:
        logging.info('Performing second screening')    

        # Running hescreen
        cmd = 'hescreen evtfile={} gtifile={} outfile={} \
        userdetid="0-17" eventtype=1 anticoincidence=yes \
        starttime=0 stoptime=0 minPI={} maxPI={}  clobber=yes history=yes'.\
        format(cal_evt,gti,outfile,minpi,maxpi)
        os.system(cmd)

        # Verifing successful running
        if not os.path.isfile(outfile):
            logging.info('he_screen output file was not created')
            return

    return outfile

def he_genspec(full_exp_dir,evt,out_dir='reduced_products',override=False):
    '''
    It computes an energy spectrum for each detector

    # hespecgen computes an energy spectrum for each detector and has
    # as input the calibrated and screened event file. The task needs 
    # a Dead time file
    # This time, the output keyword does not need extension, it is 
    # just the prefix to the file
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    evt: string (optional)
        Screaned and calibrated event file
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE   
    override: boolean (optional)
        If True and a screened file already exists, this is removed
                  
    RETURN
    ------
    outfiles: list
        List of the energy spectra created with full path

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if energy spectrum
        already exists and override=False, the name of the spectrum
        file is returned
    '''

    logging.info('===> Running he_genspec <<<===')

    
    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_genspec requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]
    
    # Checking exposure folder format
    if not check_exp_format(exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return 
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]
    
    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE')) 
    
    # Initializing outfile
    outfile=os.path.join(destination,'{}_HE_spec'.format(exp_ID))

    outfiles = []
    for g in range(18):
        outfiles += [outfile+'_g{0}_{0}.pha'.format(g)]
    test = [os.path.isfile(f) for f in outfiles]

    compute = True
    if sum(test) == 18:
        logging.info('Energy specta already exist')
        compute = False  

    if compute or override:
        logging.info('Computing energy spectra')

        # Initializing and checking existance of input files
        # Dead time file
        dead = check_and_choose(os.path.join(full_exp_dir,'HE'),
            inc='HE-DTime',ext='FITS')
        if not dead:
            logging.info('Dead Time file for HE missing')
            return
    
        # Running hespecgen
        cmd = 'hespecgen evtfile={} outfile={} deadfile={} '\
        'userdetid="0;1;2;3;4;5;6;7;8;9;10;11;12;13;14;15;16;17" '\
        'eventtype=1 starttime=0 stoptime=0 minPI=0 maxPI=255 '\
        'clobber=yes'.format(evt,outfile,dead)
        os.system(cmd)
        
        # Verifing successful running
        for outfile in outfiles:
            if not os.path.isfile(outfile):
                logging.info('{} was not created'.format(outfile))
                return 

        outfiles = sorted(outfiles)
    
    return outfiles

def he_genrsp(full_exp_dir,spec_list,out_dir='reduced_products',override=False):
    '''
    Generates a response file for each HE detector
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    spec_list: list
        List of the energy spectra 
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE  
    override: boolean (optional)
        If True and a screened file already exists, this is removed 
                  
    RETURNS
    -------    
    outfiles: list
        List of the response files with their full path
        
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
    '''

    logging.info('===> Running he_genrsp <===')
    
    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_genrsp requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]
    
    # Checking exposure folder format
    if not check_exp_format(exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return 
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]
    
    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE')) 

    outfiles = []
    for spectrum in spec_list:
        outfiles += [spectrum.replace('spec','rsp')]
    test = [os.path.isfile(f) for f in outfiles]

    compute = True
    if sum(test) == 18:
        logging.info('Response files already exist')
        compute = False  

    if compute or override:
        logging.info('Computing response files')
    
        # Initializing and checking existance of input files
        # Attitude file
        att = check_and_choose(os.path.join(full_exp_dir,'ACS'),
            inc='Att',ext='FITS')
        if not att:
            logging.info('Attitude file for HE missing')
            return    

        # Running herspgen
        for spectrum in spec_list:
            outfile = spectrum.replace('spec','rsp')
            cmd = "herspgen phafile={} outfile={} attfile={} '\
                  'ra=-1 dec=-91 clobber=yes".format(spectrum,outfile,att)
            os.system(cmd)
            # Checking existance of the just created files
            if not os.path.isfile(outfile):
                logging.info('he_genrsp output file {} was not created'.\
                    format(outfile))
                return 

        outfiles=sorted(outfiles)       
        
    return outfiles  

def he_genle(full_exp_dir,evt,
             binsize=1,minpi=26,maxpi=120,det_ID='0-15, 17',
             out_dir='reduced_products',override=False):
    '''
    It computes a lightcurve
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder
    evt: string (optional)
        Screaned and calibrated event file
    binsize: float (optional)
        Binsize of the lightcurve (time resolution). Default value is 1
    minpi: integer (optional)
        Low energy channel. Default value is 26
    maxpi: integer (optional)
        High energy channel. Default value is 120
    det_ID: string (optional)
        String for selecting detectors. Single detectors or detector ranges
        (-) separated by come will be combined. When using semicolor, the
        script will generate different lightcurves
    out_dir: string (optional)
        Name of the outout products folder. This will be created inside
        full_exp_dir/HE  
    override: boolean (optional)
        If True and a screened file already exists, this is removed 
                  
    RETURNS
    -------
    outfile: string
        Lightcurve name

    HISTORY
    -------
    2019 12 01, Stefano Rapisarda (Shanghai), creation date
    2020 11 19, Stefano Rapisarda (Uppsala)
        Inprooved functionality and comments. Now, if a screened file
        already exists and override=False, the name of the screened 
        lightcurve is returned
    '''

    logging.info('===>>> Running he_genle <<<===')
    
    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_genle requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]
    
    # Checking exposure folder format
    if not check_exp_format(exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return 
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]
    
    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE')) 
    
    # Initializing outfile
    outfile=os.path.join(destination,'{}_HE_lc_ch{}-{}_{}s'.\
                         format(exp_ID,minpi,maxpi,binsize))

    lc_list = glob.glob('{}/*.lc'.format(destination))
    compute = True
    if outfile in lc_list:
        logging.info('Lightcurve already exists')
        compute = False  

    if compute or override:
        logging.info('Computing lightcurve')
    
        # Initializing and checking existance of input files
        # Dead time file
        dead = check_and_choose(os.path.join(full_exp_dir,'HE'),
            inc='HE-DTime',ext='FITS')
        if not dead:
            logging.info('Dead Time file for HE missing')
            return
    
        # Running helcgen
        cmd = 'helcgen evtfile={} outfile={} deadfile={} \
        userdetid="{}" eventtype=1 minPI={} maxPI={} binsize={} clobber=yes'.\
        format(evt,outfile,dead,det_ID,minpi,maxpi,binsize)
        os.system(cmd)

        lcs = glob.glob('{}*.lc'.format(outfile))
    
        # Verifing successful running
        if len(lcs)==0:
            logging.info('he_genle output file was not created')
            return
    
    return lcs[0]

def he_bkgmap(full_exp_dir,ascii_file,evt,gti,out_dir = 'reduced_products',
    override=False):
    '''
    It computes background for either a lightcurve or an energy spectrum. 
    
    The option (lightcurve or spectrum) it is automatically recognized 
    according to the extention of the first file in the provided ascii 
    text file. Also, the energy channels are automatically selected 
    according to the option. For Energy spectra, all the channels are used, 
    for lightcurve channels are read from the name of the lightcurve file
    
    PARAMETERS
    ----------
    full_exp_dir: string
        Full path of the esposure folder    
    ascii_file: string
        Name of the text file either containing the energy spectra name or
        the lightcurve name
    evt: string
        Name of the calibrated and screened event file
    gti string
        Name of the gti file
    out_dir: string (optional)
        Name of the output folder
    override: boolean (optional)
        If True and a screened file already exists, this is removed 

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
        
    # Checking that the input path corresponds to a full path
    if full_exp_dir[-1] == '/': full_exp_dir = full_exp_dir[0:-1]
    tmp = full_exp_dir.split('/')
    if len(tmp) == 1:
        logging.info('he_bkgmap requires full path for exp_dir')
        return ''
    exp_dir = tmp[-1]
    
    # Checking exposure folder format
    if not check_exp_format(exp_dir): 
        logging.info('Something is wrong in the exposure folder name, check:')
        logging.info(exp_dir)
        return 
    exp_ID = exp_dir
    #exp_ID = exp_dir.split('-')[0]
    
    # Creating destination folder
    destination = create_dir(out_dir,os.path.join(full_exp_dir,'HE'))  

    # Checking the format of the input file
    with open(os.path.join(destination,ascii_file),'r') as infile:
        lines = infile.readlines()
    # Automatically recognize channels

    if '.lc' in lines[0]: 
        opt = 'lc'
        lc_name = os.path.basename(lines[0]).strip()
        chunks = lc_name.split('_')
        ch_chunk = [c for c in chunks if 'ch' in c][0].replace('ch','')
        minPI = int(ch_chunk.split('-')[0])
        maxPI = int(ch_chunk.split('-')[1])
    elif '.pha' in lines[0]: 
        opt = 'spec'
        minPI = 0
        maxPI = 255
    else:
        logging.info('File in the input list has not any recognizable format')
        return 

    # Here I should put some lines to check if files already exists
    compute = True
    if opt == 'spec':
        outfile=os.path.join(destination,'HE_spec_bkg'.format(exp_ID))
        outfiles = []
        for g in range(18):
            outfiles += [outfile+'_{}.pha'.format(g)]
        test = [os.path.isfile(f) for f in outfiles]
        if sum(test) == 18:
            logging.info('Energy spectra background already exist')
            compute = False  
    elif opt == 'lc':
        outfile = lc_name.replace('_lc','_lc_bkg')
        outfile = outfile.replace('.lc','')
        lc_files = glob.glob('{}/*.lc'.format(destination))
        if  outfile in lc_files:
            logging.info('Lightcurve background already exists')
            compute = False

    if compute or override:  
    
        # Initializing and checking existance of input files
        # -------------------------------------------------------------
        # Dead time file
        dead = check_and_choose(os.path.join(full_exp_dir,'HE'),
            inc='HE-DTime',ext='FITS')
        if not dead:
            logging.info('Dead Time file for HE missing')
            return

        # ehk file
        ehk = check_and_choose(os.path.join(full_exp_dir,'AUX'),
            inc='_EHK_',ext='FITS')
        if not ehk:
            logging.info('Extend houskeeping data is missing')
            return 
        # -------------------------------------------------------------

        # Running hebkgmap  
        cmd = 'hebkgmap {} {} {} {} {} {} {} {} {}'.format(opt,evt,ehk,gti,dead,\
            os.path.join(destination,ascii_file),minPI,maxPI,os.path.join(destination,outfile))
        os.system(cmd)

    if opt == 'lc':
        return outfile
    elif opt == 'spec':
        return outfiles


