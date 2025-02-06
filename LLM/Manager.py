import os 
from glob import glob
import warnings
import sys
import argparse


class Model_Path_Manager:
    def __init__(self, model_set_path:str='/home/am/DL/disk1/Models') -> None:
        self.model_set_path = model_set_path
        self.model_dict = self.get_model_dict()
    

    def get_model_dict(self, force_update=False):
        # get total sponsor-model_name dict
        if not force_update and hasattr(self, 'model_dict'):
            return self.model_dict

        path_list = glob(os.path.join(self.model_set_path, "*", "*"))
        self.model_dict = {}
        for path_i in path_list:
            path_parts = path_i.split(os.sep)
            model_name = path_parts[-1]
            model_sponsor = path_parts[-2]
            if self.model_dict.get(model_sponsor, "NONE_MODEL") == "NONE_MODEL":
                self.model_dict[model_sponsor] = []
            self.model_dict[model_sponsor].append((model_name, path_i))
        return self.model_dict
    

    def print_dict(self, print_path=False):
        # format print model_dict   
        for sponsor, model_list in self.model_dict.items():
            print(f"{sponsor}: ")
            for model_name_i, model_path_i in model_list:
                if print_path:
                    print(f"  - {model_name_i}: {model_path_i}")
                else:
                    print(f"  - {model_name_i}")
    

    def translate(self, relative_path:str, print_flag=False):
        # translate relative_path "sponsor/model_name" or model_name to absolute model_path
        # return None if not found, or return input if it's already an absolute path
        if os.path.isabs(relative_path):
            return relative_path
        
        if "/" in relative_path:
            sponsor, model_name = relative_path.split("/")
            model_list = self.model_dict.get(sponsor, None)
            if not model_list:
                warnings.warn(f'Model "{relative_path}" not found in model set.')
                return None
            else:
                for model_name_i, model_path_i in model_list:
                    if model_name_i == model_name:
                        if print_flag:
                            print(f'Model "{relative_path}" tranlated to "{model_path_i}".')
                        return model_path_i
        else:
            for sponsor, model_list in self.model_dict.items():
                for model_name_i, model_path_i in model_list:
                    if model_name_i == relative_path:
                        if print_flag:
                            print(f'Model "{relative_path}" tranlated to "{model_path_i}".')
                        return model_path_i
        warnings.warn(f'Model "{relative_path}" not found in model set.')
        return None


    def search(self, prompt:str, print_flag=True):
        # search model by prompt indicating model_name
        # return a list of matched model_name
        tar_model_dict = {}
        for sponsor, model_list in self.model_dict.items():
            for model_name_i, model_path_i in model_list:
                if prompt in model_name_i:
                    tar_model_dict[f'{sponsor}/{model_name_i}'] = model_path_i
        if print_flag:
            print(f'Models containing "{prompt}":')
            for key_i, value_i in tar_model_dict.items():
                print(f'  - {key_i}: {value_i}')
        return tar_model_dict
    

    def rm_empty_dir(self):
        # remove model_path if it's empty
        for sponsor, model_list in self.model_dict.items():
            for model_name_i, model_path_i in model_list:
                if not os.listdir(model_path_i):
                    os.rmdir(model_path_i)
                    print(f"Empty dir {sponsor}/{model_name_i} removed.")
        self.get_model_dict(force_update=True)
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Model Path Manager v1.0\n@Vaccummer   https://github.com/Vaccummer\nEnvironment Variable Name: Model_Set_Path",
                                 formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-l", "--list", help="Print Model lsit", action="store_true")
    parser.add_argument("-s", "--search", help="Search Model with Prompt", action="store_true")
    parser.add_argument("-t", "--translate", help="Translate Prompt to Model Path", action="store_true")
    parser.add_argument("prompt", nargs='*', help="One or more file or directory paths to operate on")
    args= parser.parse_args()

    default_model_set_path = "/home/am/DL/disk1/Models"
    model_set_path = os.environ.get('Model_Set_Path') 
    model_set_path = model_set_path if model_set_path else default_model_set_path
    model_path_manager = Model_Path_Manager(model_set_path)
    if args.list:
        model_path_manager.print_dict()
        sys.exit(0)
    for prompt_i in args.prompt:
        if args.search:
            model_path_manager.search(prompt_i)
        if args.translate:
            model_path_manager.translate(prompt_i, print_flag=True)
