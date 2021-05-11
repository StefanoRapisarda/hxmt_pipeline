import sys

args = sys.argv
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

for key,item in arg_dict.items():
    print(key,item)