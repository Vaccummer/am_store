import os 
from glob import glob
import warnings


class Model_Path_Manager:
    def __init__(self, model_set_path:str) -> None:
        self.model_set_path = model_set_path
        self.model_dict = self.get_model_dict()
    

    def get_model_dict(self):
        # get total sponsor-model_name dict
        if hasattr(self, 'model_dict'):
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
    

    def print_dict(self):
        # format print model_dict   
        for sponsor, model_list in self.model_dict.items():
            print(f"{sponsor}: ")
            for model_name_i, model_path_i in model_list:
                print(f"  - {model_name_i}")
    

    def translate_path(self, relative_path:str):
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
                        return model_path_i
        else:
            for sponsor, model_list in self.model_dict.items():
                for model_name_i, model_path_i in model_list:
                    if model_name_i == relative_path:
                        return model_path_i
        warnings.warn(f'Model "{relative_path}" not found in model set.')
        return None


    def search_model(self, prompt:str):
        # search model by prompt indicating model_name
        # return a list of matched model_name
        tar_model_list = []
        for sponsor, model_list in self.model_dict.items():
            for model_name_i, model_path_i in model_list:
                if prompt in model_name_i:
                    tar_model_list.append(model_name_i)
        return tar_model_list
    

    def rm_empty_dir(self):
        # remove model_path if it's empty
        for sponsor, model_list in self.model_dict.items():
            for model_name_i, model_path_i in model_list:
                if not os.listdir(model_path_i):
                    os.rmdir(model_path_i)
    
    
    