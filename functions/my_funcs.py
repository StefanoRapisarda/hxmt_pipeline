import os
import sys
import sysconfig
import logging
import pathlib
import re

def create_dir(dir_name,path=os.getcwd()):
    '''
    Stefano Rapisarda, 09/05/2019, SHAO

    This routine checks if the folder dir_name exists.
    If so, it returns the same path, otherwise it creates the folder and
    return the full path.

    PARAMETERS
    ----------
    dir_name: string
              Name of the directory to create
    path: string, optional
              Path of the directory to create

    RETURN
    ------
    new_folder: string
              Full path of the newly created folder
    '''

    if not path:
        new_folder = os.path.join(dir_name)
    else:
        new_folder = os.path.join(path,dir_name)
    if os.path.isdir(new_folder):
        print('{} already exists.'.format(new_folder))
    else:
        print('{} does not exist, creating it'.format(dir_name))
        os.mkdir(new_folder)
    return new_folder

def list_items(path,itype = 'dir',ext = '',
                include_or=[],include_and=[],exclude_or=[],exclude_and=[],
                choose=False,show=False,sort=True,digits=False):
    '''
    DESCRIPTION
    -----------
    Depending on the specified option, it lists either all the files
    or the folders inside a specifide path. 
    If choose is True, returns an interactively chosen file/directory

    PARAMETERS
    ----------
    path: string or pathlib.Path
        target directory
    itype: string, optional 
        'dir' for directory, 'file' for files (default = 'dir')
    ext: string or list of strings, optional
        Only files with extension equal to .ext will be returned
    include_or: string or list, optional
        Only items including one of the specified string will be
        returned
    include_all: list, optional
        Only items including all the strings in the list
        will be included
    exclude_or: string or list, optional
        Only items excluding at least one of the elements in this 
        list will be returned
    exclude_and: string or list, optional
        Only items excluding all the elements in this list will be
        returned
    digits: boolean, string, or list, optional 
        If True only items whose names contain only digits will 
        be considered (default=False).
        If string or list, the item name will be split excluding 
        the characters in the list. If all the split elements include
        digits, the item will be returned
    sort: boolean, optional 
        If True the returned list of items will be sorted 
        (default=True)

    RETURNS
    -------
    list
        List of items

    HISTORY
    -------
    2019 07 11, Stefano Rapisarda (SHAO), creation date
    2019 07 16, Stefano Rapisarda (SHAO), Including ext and include options
    2019 07 19, Stefano Rapisarda (SHAO), Changed approach, from listing with next and os.walk to glob
    2019 07 23, Stefano Rapisarda (SHAO), Going back to os.walk and next to isolate folders and files
    2019 11 08, Stefano Rapisarda (SHAO), Introduced the option to specify a list of extension
    2019 11 21, Stefano Rapisarda (SHAO), Corrected some bugs and added the option include_all
    2019 11 23, Stefano Rapisarda (SHAO), Added the option all digits. Also added sort option.
    2021 05 05, Stefano Rapisarda (Uppsala)
        - The option to_removed was removed (you can sort files 
          according using other options);
        - include and exclude parameters have been extended with
          or and and;
        - The digit parameter now allows to exclude characters from
          the item name when checking if all the characters are digits;
        - Directories now are treated as pathlib.Path(s);
    '''

    if type(path) != type(pathlib.Path()):
        path = pathlib.Path(path)

    if ext != '': itype='file'

    # Listing items
    items = []
    for item in path.iterdir():
        if item.is_dir() and itype == 'dir':
            items += [item]
        elif item.is_file() and itype == 'file':
            items += [item]

    # Filtering files with a certain extension
    if itype == 'file' and ext != '':
        if type(ext) == str: ext = [ext]
        # Removing first dot
        new_ext = [ex[1:]  if ex[0]=='.' else ex for ex in ext]
        ext = new_ext

        new_items = []
        for item in items:
            # Finding the first occurrence of a dot
            #file_name = str(item.name)
            #target_index = file_name.find('.')
            # .suffix returns the extension with the point
            ext_to_test = item.suffix
            if ext_to_test[1:] in ext:
                new_items += [item]
        items = new_items

    # Filtering files according to include_or
    if include_or != []:
        if type(include_or) == str: include_or = [include_or]

        new_items = []
        for item in items:
            file_name = str(item.name)   
            flags = [True if inc in file_name else False for inc in include_or]
            if sum(flags) >= 1: new_items += [item]
        items = new_items

    # Filtering files according to include_and
    if include_and != []:
        if type(include_and) == str: include_and = [include_and]

        new_items = []
        for item in items:
            file_name = str(item.name)  
            flags = [True if inc in file_name else False for inc in include_and]
            if sum(flags) == len(include_and): new_items += [item]  
        items = new_items

    # Filtering files according to exclude_or
    if exclude_or != []:
        if type(exclude_or) == str: exclude_or = [exclude_or]

        new_items = []
        for item in items:
            file_name = str(item.name)   
            flags = [True if inc in file_name else False for inc in exclude_or]
            if sum(flags) == 0: new_items += [item]
        items = new_items

    # Filtering files according to exclude_and
    if exclude_and != []:
        if type(exclude_and) == str: exclude_and = [exclude_and]

        new_items = []
        for item in items:
            file_name = str(item.name)  
            flags = [True if inc in file_name else False for inc in exclude_and]
            if sum(flags) != len(exclude_and): new_items += [item]  
        items = new_items

    # Filtering according to digit
    if not digits is False:
        new_items = []
        if digits is True:
            new_items = [item for item in items if str(item.name).isdigit()]
        else:
            if type(digits) == str: digits = [digits]
            split_string = '['
            for dig in digits: 
                if str(dig) != '-':
                    split_string += str(dig)
                else:
                    split_string += '\-'
            split_string += ']'
            #print(split_string)

            for item in items:
                file_name = str(item.name)
                prediv = re.split(split_string,file_name) 
                div = [p  for p in prediv if p != '']
                flags = [True if d.isdigit() else False for d in div]
                if sum(flags) == len(div): new_items += [item]
        items = new_items


    if choose: show=True

    item_name = 'Folders'
    if itype == 'file': item_name = 'Files'
    if show: print('{} in {}:'.format(item_name,str(path)))
    happy = False
    while not happy:
        if show:
            for i, item in enumerate(items):
                print('{}) {}'.format(i+1,item.name))

        if choose:
            index = int(input('Choose a directory ====> '))-1
            target = items[index]
            ans=input('You chose "{}", are you happy?'.format(target.name))
            if not ('N' in ans.upper() or 'O' in ans.upper()):
                happy = True
        else:
            target = items
            happy = True

    if type(target) == list:
        if sort: target = sorted(target)
        if len(target) == 1: 
            target = target[0]
        elif len(target) == 0:
            target = False

    return target

def initialize_logger(log_name=False,level=logging.DEBUG):
    '''
    Initialize logging options to pring log messages on the screen
    and on a file (if log_name is specified)

    HISTORY
    -------
    unknown   , Stefano Rapisarda (SHAO), creation date
    2020 09 23, Stefano Rapisarda (Uppsala), efficiency improved
    '''

    # Creating an instance of the object logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Setting a format for the log
    formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')

    if log_name:
        logging.basicConfig(level=level,
                            format='%(levelname)s: %(asctime)s: %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            filename=log_name+'.log',
                            filemode='w')

    # Creating the log handler
    #handler = logging.StreamHandler(stream=sys.stderr)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter) 

    # Configuring the logger with the handler
    logger.addHandler(handler)   

    #if log_name:
        
    #    handler = logging.FileHandler(log_name,"w", encoding=None, delay="true")
    #    handler.setLevel(logging.DEBUG)
    #    handler.setFormatter(formatter)
    #    logger.addHandler(handler)

    return logger
