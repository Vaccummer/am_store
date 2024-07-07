import os 
from glob import glob

class AM_Model_Store:
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
    
    def print_model_dict(self):
        # format print model_dict
        if not hasattr(self, 'model_dict'):
            self.model_dict = self.get_model_dict()
        
        for sponsor, model_list in self.model_dict.items():
            print(f"{sponsor}: ")
            for model_name_i, model_path_i in model_list:
                print(f"  - {model_name_i}")
    

    def find_model(self, prompt_f:str):
        # find model by prompt_f, return absolute path of model
        # prompt_f is a string, with the format of "sponsor_model_name"
        if not hasattr(self, 'model_dict'):
            self.model_dict = self.get_model_dict()
        
        sponsor, model_name = prompt_f.split("/")
        model_list = self.model_dict.get(sponsor, None)
        if not model_list:
            return None
        else:
            for model_name_i, model_path_i in model_list:
                if model_name_i == model_name:
                    return model_path_i
        return None


    