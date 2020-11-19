import os

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

def list_items(wf=os.getcwd(),opt=1,ext='',include=[],include_all=[],exclude=[],to_remove=[],
               all_digits=False,sort=True):
    '''
    DESCRIPTION
    -----------
    Depending on the specified option, it lists either all the files
    or the folders in wf. It can also remove a list of names from 
    this list

    PARAMETERS
    ----------
    wf: string
        Working directory
    opt: integer, optional (default = 1)
        1 for folders, 2 for files
    ext: string or list of strings, optional
        Only items with extension equal to .ext will be returned
    include: string or list, optional
        Only items including this string will be returned
    include_all: list,optional
        Only itmes including all the strings in the list
        will be included
    exclude: string or list, opritonal
        Items containing this string/list will be excluded
    remove: list, optional
        List of names to remove from the files/folder list
    all_digits: boolean, optional (default=False)
        If True only items whose names contain only digits will 
        be considered.
    sort: boolean, optional (default=True)
        If True the returned list will be sorted

    RETURN
    ------
    item_list: list
        List of items

    HISTORY
    -------
    Stefano Rapisarda 11 07 2019, SHAO (creation date)
    Stefano Rapisarda 16 07 2019, SHAO
        Including ext and include options
    Stefano Rapisarda 19 07 2019, SHAO
        Changed approach, from listing with next and os.walk to glob
    Stefano Rapisarda 23 07 2019, SHAO
        Going back to os.walk and next to isolate folders and files
    Stefano Rapisarda 08 11 2019, SHAO
        Introduced the option to specify a list of extension
    Stefano Rapisarda 21 11 2019, SHAO
        Corrected some bugs and added the option include_all
    Stefano rapisarda 23 11 2019, SHAO
        Added the option all digits. Also added sort option.

    TO DO
    -----
    Stefano Rapisarda 21 11 2019
         I noticed only now that the different selecting operations
         are performed in a certain order. I may try to find a way
         to avoid this.
    '''

    if opt == 1:
        print('Listing items: folders')
    elif opt ==2:
        print('Listing items: files')
        
    if opt == 2 and ext:
        if type(ext) == str:
            if ext[0] != '.':
                ext = '.' + ext
        elif type(ext) == list:
            for e in range(len(ext)):
                if ext[e] != '.':
                    ext[e] = '.' + ext[e]

    item_list = next(os.walk(wf))[opt]

    tmp_item_list = []
    if all_digits:
        for item in item_list:
            if item.isdigit():
                tmp_item_list += [item]
        item_list = tmp_item_list
        del tmp_item_list
    
    sel_list1 = []
    if opt == 2:
        for i in item_list:
            if type(ext) == str:
                if ext in i:
                    sel_list1 += [i]
            elif type(ext) == list:
                flag = False
                for e in ext:
                    if e in i and  not flag:
                        flag = True
                        sel_list1 += [i]
    else:
        sel_list1 = item_list
                  

    # Including
    sel_list2 = []
    if include:
        for i in sel_list1:
            if type(include)==str:
                if include in i:
                    sel_list2 += [i]
            elif type(include)==list:
                flag = False
                for j in include:
                    if j in i and not flag:
                        flag = True
                        sel_list2 += [i]
            else:
                print('ERROR: wrong type in include')
                sys.exit()
    else:
        sel_list2 = sel_list1

    # Include all
    sel_list3 = []
    if include_all:
        for i in sel_list2:
            counter = 0
            for j in include_all:
                if j in i:
                    counter +=1
            if counter == len(include_all):
                sel_list3 += [i]
    else:
        sel_list3 = sel_list2
        
    # Excluding
    sel_list4 = []
    if exclude:
        if type(exclude) == str:
            for i in sel_list3:
                if not exclude in i:
                    sel_list4 += [i]
        elif type(exclude)==list:
            to_remove = []
            for j in exclude:
                for i in sel_list3:
                    if j in i: to_remove += [i]
            sel_list4 = sel_list3.copy()        
            for r in to_remove:
                sel_list4.remove(r)
    else:
        sel_list4 = sel_list3
        
    # Removing
    if type(to_remove) == str:
        if to_remove in sel_list4:
            sel_list4.remove(to_remove)
    elif type(to_remove) == list:
        for r in to_remove:
            if r in sel_list4:
                sel_list4.remove(r)
    else:
        print('ERROR: wrong object type for to_remove')

    if sort:
        sel_list4 = sorted(sel_list4)

    return sel_list4


def initialize_logger(log_name=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to info
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    if log_name:
        # create error file handler
        handler = logging.FileHandler(log_name,"w", encoding=None, delay="true")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
