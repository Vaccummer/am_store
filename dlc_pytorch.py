import yaml
import os
from glob import glob
from typing import Literal
import shutil
import multiprocessing
from collections import defaultdict


def flatten_dict(dict_f):
    ## flatten dict
    sep_f = "$==>>$"
    def flatten_dict_core(d, parent_key='', sep=sep_f):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict_core(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    dict_ori = flatten_dict_core(dict_f)
    dict_out = {}
    for key, value in dict_ori.items():
        key_list = key.split(sep_f)
        dict_out[tuple(key_list)] = value
    return dict_out


def dict_format_print(dict_f, indent=0):
    ## dict format print
    for key, value in dict_f.items():
        print('\t' * indent + str(key))
        if isinstance(value, dict):
            dict_format_print(value, indent+1)
        else:
            print('\t' * (indent+1) + str(value))


def find_project(set_dir, time_f, mouse_f):
    ## get project path
    return os.path.join(set_dir, f'{time_f}-{mouse_f}')


def find_config(project_path_f:str, prompt_f:Literal['main', 'test', 'train']):
    ## get config path
    if os.path.isfile(project_path_f):
        project_path_f = os.path.dirname(project_path_f)
    main_path = os.path.join(project_path_f, 'config.yaml')
    test_paths = glob(os.path.join(project_path_f, 'dlc-models-pytorch', "**", "test", 'pose_cfg.yaml'), recursive=True)
    train_paths = glob(os.path.join(project_path_f, 'dlc-models-pytorch', "**", "train", 'pytorch_config.yaml'), recursive=True)
    test_path = None if not test_paths else test_paths[0]
    train_path = None if not train_paths else train_paths[0]

    total_dict = {
        'main':main_path,
        'test':test_path,
        'train':train_path
    }
    output_f = total_dict[prompt_f]
    if not output_f:
        Warning(f"config file not found for {prompt_f}")
    else:
        if not os.path.exists(output_f):
            Warning(f"config path is not valid: {output_f}")
    return total_dict[prompt_f]


def load_config(config_path):
    ## load config
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)


def edit_config_file(config_file_path:str, edit_info:dict, force=False):
    ## edit config files
    with open(config_file_path, 'r') as file:
        data_f = yaml.safe_load(file)
    edit_info_format = {}
    for key_i, value_i in edit_info.items():
        if isinstance(key_i, tuple):
            edit_info_format[key_i] = value_i
        else:
            edit_info_format.update(flatten_dict({key_i:value_i}))
    if not force:
        for key_tuple, value in edit_info_format.items():
            if len(key_tuple) == 1:
                if data_f.get(key_tuple[0]):
                    data_f[key_tuple[0]] = value
                continue
            sign_f = True
            for index_f, key in enumerate(key_tuple[:-1]):
                if index_f == 0:
                    if not data_f.get(key):
                        sign_f = False
                        break
                    else:
                        data_n = data_f[key]
                else:
                    if data_n.get(key):
                        data_n = data_n[key]
                    else:
                        sign_f = False
                        break
            if sign_f:
                data_n[key_tuple[-1]] = value    
    else:
        for key_tuple, value in edit_info_format.items():
            if len(key_tuple) == 1:
                data_f[key_tuple[0]] = value
                continue
            for index_f, key in enumerate(key_tuple[:-1]):
                if index_f == 0:
                    if not data_f.get(key):
                        data_f[key] = {}
                    data_n = data_f[key]
                else:
                    if not data_n.get(key):
                        data_n[key] = {}
                    data_n = data_n[key]
            data_n[key_tuple[-1]] = value
    with open(config_file_path, 'w') as file:
        yaml.dump(data_f, file, default_flow_style=False, sort_keys=False)
    return data_f


def print_config_info(project_path, type_f=Literal['main', 'test', 'train']):
    ## print config info
    config_path = find_config(project_path, type_f)
    config_dict = load_config(config_path)
    if type_f == 'main':
            dict_info_print = {}
            target_keys = ['project_path','numframes2pick','pcutoff', 'TrainingFraction', 'default_net_type', 
                        'default_augmenter','snapshotindex','batch_size']
            for target_key in target_keys:
                dict_info_print[target_key] = config_dict.get(target_key, 'No_Match')
            yaml_str = yaml.dump(dict_info_print, default_flow_style=False, sort_keys=False)
            print(yaml_str)
    elif type_f == 'train':
        dict_info_print = defaultdict(dict)
        dict_info_print['metadata'] = {'project_path':config_dict.get('metadata', dict()).get('project_path', 'No_Match'),
                                    }
        dict_info_print['model'] = {'backbone':config_dict.get('model', dict()).get('backbone', 'No_Match'),
                                    'backbone_output_channels':config_dict.get('model', dict()).get('backbone_output_channels', 'No_Match'),}
        dict_info_print['net_type'] = config_dict.get('net_type', 'No_Match')
        dict_info_print['runner'] = config_dict.get('runner', 'No_Match')
        dict_info_print['train_settings'] = config_dict.get('train_settings', 'No_Match')
        dict_info_print['mixed_precision'] = config_dict.get('mixed_precision', 'No_Match')
        yaml_str = yaml.dump(dict_info_print, default_flow_style=False, sort_keys=False)
        print(yaml_str)


def kill_tensorboard_process():
    # to kill tensorboard process which remains after the program is closed in vscode
    import subprocess
    command_f = "kill -9 $(ps -ef|grep tensorboard|grep -v grep|awk '{print $2}')"
    result = subprocess.run(command_f, shell=True, capture_output=True, text=True)
    return result


def cre_project(time_f:str, mouse_f:str, work_dir_f:str, avi_list_f:list=[]):
    # create dlc project
    ## if you want the dir name to be the format "{time_f}-{mouse_f}", go to create_new_project definition
    ## and modify this line "project_name = "{pn}-{exp}-{date}".format(pn=project, exp=experimenter, date=date)"
    import deeplabcut
    deeplabcut.create_new_project(project=time_f, 
                                  experimenter=mouse_f, 
                                  videos=avi_list_f, 
                                  working_directory=work_dir_f, 
                                  copy_videos=True, 
                                  multianimal=False)
    
    ## edit basic info
    project_path = os.path.join(work_dir_f, f"{time_f}-{mouse_f}")
    config_path = find_config(project_path, 'main')
    bodyparts = ['pupilM', 'pupilL', 'pupilU', 'pupilD', 'pupilLU', 'pupilRD', 'pupilRU', 'pupilLD', 'eyeM', 'eyeL', 'eyeU', 'eyeD', 'earD', 'earM', 'earU', 'earL', 'earR', 'noseU', 'noseD', 'noseMU', 'noseL', 'noseMD', 'mouthM', 'mouthR', 'mouthL', 'whisker1O', 'whisker1M', 'whisker1L', 'whisker1E', 'whisker2O', 'whisker2M', 'whisker2L', 'whisker2E', 'whisker3O', 'whisker3M', 'whisker3L', 'whisker3E']
    edit_info = {
        'Task':time_f,
        'scorer':mouse_f,
        'engine':"pytorch",
        'bodyparts': bodyparts,
        'numframes2pick': 30,
        'dotsize':8,
        'default_net_type':'hrnet',
        'default_augmenter':'albumentations',
        'batch_size': 4,
        'global_scale': 0.8,
        'freeze_bn_stats':False,
        'epochs': 1000,
        'max_snapshots_to_keep': 25,


    }
    edit_config_file(config_path, edit_info)


def extract_frames(config_path, video_list_f=None):
    # random choose frames to plot
    import deeplabcut
    deeplabcut.extract_frames(config_path, 
                            videos_list=video_list_f,
                            mode='automatic', 
                            algo='kmeans', 
                            userfeedback=False, 
                            crop=False)


def cre_train_dataset(config_path, 
                    net_type_f='hrnet_w48',
                    training_fraction=0.8,
                    sample_train_cfg_path='/home/am/dlc/Vgat/script_related_data/pytorch_train_config_sample.yaml'):
    # create training dataset
    ## augmenter_type for pytroch only supports albumentations
    edit_config_file(find_config(config_path, 'main'), {'TrainingFraction':[training_fraction]})
    import deeplabcut
    from deeplabcut.core.engine import Engine
    deeplabcut.create_training_dataset(config_path, 
                                       net_type=net_type_f, 
                                       augmenter_type='albumentations',
                                       engine=Engine.PYTORCH)
    
    ori_cfg_path = find_config(config_path, 'train')
    ori_cfg = load_config(ori_cfg_path)
    edit_info = {'metadata':{'project_path':ori_cfg['metadata']['project_path'],
                             'pose_config_path':ori_cfg['metadata']['pose_config_path'],}}
    os.remove(ori_cfg_path)
    shutil.copy(sample_train_cfg_path, ori_cfg_path)
    data_f = edit_config_file(ori_cfg_path, edit_info)


def find_weight(project_path_f:str, iters:int=-1):
    # find weights path
    paths_f = glob(os.path.join(project_path_f, 'dlc-models-pytorch', "**", "train", "snapshot-*.pt"), recursive=True)
    nums_f = [int(os.path.basename(path).split('-')[1].split('.')[0]) for path in paths_f]
    try:
        if iters == -1:
            return paths_f[nums_f.index(max(nums_f))]
        else:
            if iters not in nums_f:
                Warning(f"iter: {iters} not found in {project_path_f}")
                return None
            else:
                return paths_f[nums_f.index(iters)]
    except Exception:
        Warning('No Snapshot Has been Found!')
        return None
        

def tra_network(config_path, 
                snapshot_path=0,
                device='cuda:0',
                batch_size=2,
                epochs=1000,
                save_epochs=50,
                eval_interval=50,
                max_snapshots_to_keep=25,
                mixed_precision=False,
                metric_pcutoff:float=0.6):
    # train network
    project_path = os.path.dirname(config_path)
    # edit_config_file(find_config(project_path, 'train'), {'runner':{"eval_interval":eval_interval}, "model":{"heads":{"target_generator":{"device":device}}}})
    edit_config_file(find_config(project_path, 'train'), {("runner", "eval_interval"): eval_interval, ("model", "heads", "bodypart", "target_generator", "device"): device}, force=True)
    if os.path.exists(snapshot_path):
        snapshot_path = snapshot_path
    elif isinstance(snapshot_path, int):
        snapshot_path = find_weight(project_path, snapshot_path)
    else:
        snapshot_path = None
    import deeplabcut.pose_estimation_pytorch.apis
    deeplabcut.pose_estimation_pytorch.apis.train_network(config_path, 
                                                        device=device,
                                                        snapshot_path=snapshot_path,
                                                        batch_size=batch_size,
                                                        epochs=epochs,
                                                        save_epochs=save_epochs,
                                                        max_snapshots_to_keep=max_snapshots_to_keep,
                                                        mixed_precision = mixed_precision,
                                                        metric_pcutoff=metric_pcutoff)   


def eval_network(config_path, pcutoff=0.8):
    # evaluate network
    config_path = find_config(config_path, 'main')
    edit_config_file(config_path, {'pcutoff': pcutoff})
    import deeplabcut
    deeplabcut.evaluate_network(config_path)


def ana_video_func(device_f:str, queue_f):
    import deeplabcut
    while not queue_f.empty():
        para_f = queue_f.get()
        para_f['device'] = device_f
        deeplabcut.analyze_videos(**para_f)


def ana_videos(config_path:str, videos_f:list=[], muilti_process=True, cuda_available_list:list=[0,1,2,3]):
    # analyze videos
    if not videos_f:
        pro_path = os.path.dirname(config_path)
        videos_f = glob(os.path.join(pro_path, 'videos', '*.avi'))
    import deeplabcut
    if not muilti_process:
        deeplabcut.analyze_videos(
                                config=config_path, 
                                videos=videos_f, 
                                videotype='avi', 
                                shuffle=1, 
                                save_as_csv=True, )
        return
    def ana_video_f(device_f:str, queue_f):
        while not queue_f.empty():
            para_f = queue_f.get()
            para_f['device'] = device_f
            deeplabcut.analyze_videos(**para_f)
    queue_n = multiprocessing.Queue()
    videos_num = len(videos_f)
    for i in range(videos_num):
        para = {'config':config_path,
                'videos':[videos_f[i]],
                'save_as_csv':True,
                }
        queue_n.put(para)
    
    for device_i in cuda_available_list:
        p_i = multiprocessing.Process(target=ana_video_f, args=(f"cuda:{device_i}", queue_n))
        p_i.start()
    
    
def cre_label_videos(config_path:str, videos_f:list=[], dot_size=6, pcutoff=0.3):
    # create labeled video
    import deeplabcut
    if not videos_f:
        pro_path = os.path.dirname(config_path)
        videos_f = glob(os.path.join(pro_path, 'videos', '*.avi'))
    mp4_videos = glob(os.path.join(pro_path, 'videos', '*.mp4'))
    if mp4_videos:
        command = input(f"Delete all mp4 videos in {pro_path}/videos?(y/n):")
        if command == 'y':
            for video in mp4_videos:
                os.remove(video)
        else:
            return
    deeplabcut.create_labeled_video(config_path, 
                                    videos_f, 
                                    videotype='.avi',
                                    pcutoff=pcutoff,
                                    dotsize=dot_size)