import os
import glob
import logging

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


# Destination and log folder

there = '/media/3HD/common_files'
rdf = os.path.join(there,target)

limbo = '/media/3HD/stefano/climbo/Cygnus_X1'

# At this point data should be organized in proposal-observation-exposure folders inside rdf
proposals = sorted(next(os.walk(rdf))[1])
if 'logs' in proposals: proposals.remove('logs')

for proposal in proposals:

    prop_folder = os.path.join(rdf,proposal)
    observations = sorted(next(os.walk(prop_folder))[1])

    logging.info(f'There are {len(observations)} observations.\n')
    for observation in observations:

        logging.info(f'Processing observation {observation}')
        logging.info('-'*80)

        obs_folder = os.path.join(prop_folder,observation)
        exposures = sorted(next(os.walk(obs_folder))[1])

        # Checking ACS and AUX folders
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

        logging.info(f'There are {len(exposures)} exposures\n')
        for exposure in exposures:

            logging.info(f'Processing exposure {exposure}')
            logging.info('*'*80)
            wf = os.path.join(obs_folder,exposure)

            # Targeting destination folder
            target = os.path.join(wf,'HE/reduced_products')
            
            # Creating destination folder
            destination = os.path.join(limbo,exposure)
            os.system('mkdir {}'.format(destination))

            # Compying and zipping lc files
            lc_files = glob.glob('{}/*.lc'.format(target))
            for lc in lc_files:
                # Transfering lightcurves
                cmd = 'cp {} {}'.format(lc,destination)
                os.system(cmd)
                
                # Zipping the file
                cmd = 'gzip {}'.format(os.path.join(destination,lc))
                os.system(cmd)
                
            # Compying .pi files
            pi_files = glob.glob('{}/*.pi'.format(target))
            for pi in pi_files:
                cmd = 'cp {} {}'.format(pi,destination)
                os.system(cmd)
                
                
