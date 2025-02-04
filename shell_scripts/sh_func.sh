#!/bin/bash
# cdm
# cdm 补全函数
_cdm_completion() {
    # 配置文件路径
    local config_file="/home/am/cdm/paths.conf"

    # 如果配置文件不存在，则不做任何补全
    if [[ ! -f "$config_file" ]]; then
        return
    fi

    # 从配置文件中提取出所有的名称
    local names=$(cut -d '=' -f 1 "$config_file")

    # 自动补全
    COMPREPLY=($(compgen -W "$names" -- "${COMP_WORDS[1]}"))
}

# 将补全函数与 cdm 命令关联
complete -F _cdm_completion cdm
# 在 ~/.bashrc 或 ~/.zshrc 中添加
cdm() {
    # 定义映射文件路径
    CONFIG_FILE="/home/am/cdm/paths.conf"
    
    # 如果没有提供参数，提示使用方法
    if [ -z "$1" ]; then
        echo "Usage: cdm <name>"
        return 1
    fi
    
    # 检查映射文件是否存在
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # 读取配置文件并查找对应的路径
    DEST_DIR=$(grep "^$1=" "$CONFIG_FILE" | cut -d '=' -f 2)
    
    # 如果未找到匹配项，输出错误信息
    if [ -z "$DEST_DIR" ]; then
        echo "No directory mapped for name: $1"
        return 1
    fi
    
    # 检查目标路径是否存在
    if [ -d "$DEST_DIR" ]; then
	cd "$DEST_DIR"
    elif [ -f "$DEST_DIR" ]; then
	echo "$DEST_DIR"
    else
        echo "Directory does not exist: $DEST_DIR"
        return 1
    fi
    
}
# cdmp 函数 - 打印 ~/.cdm_paths.conf 文件内容
cdmp() {
    # 配置文件路径
    CONFIG_FILE="/home/am/cdm/paths.conf"
    
    # 检查配置文件是否存在
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Config file not found: $CONFIG_FILE"
        return 1
    fi
    
    # 打印文件内容
    cat "$CONFIG_FILE"
}
# cmdp

# killm
amkill(){
    if [ -z "$1" ]; then
        echo "Usage: killm <process_keyword> | eg: killm java | kill all the process which name contains java"
        return 1
    fi
    pgrep "$1" | xargs kill -9
}
# killm

## amfind
amfind(){
    local absolute=0
    local args=()
    while [ "$#" -gt 0 ]; do
        local arg="$1"
        if [[ "$arg" == "-a" ]]; then
            absolute=1
            shift 
        elif [[ "$arg" == "-h" ]]; then
            echo "Usage: amfind [-a] <dir> <file_name> | -a for absolute path, dir use <.> for default"
            return 1
        else
            args+=("$arg")
            shift
        fi
    done
    if [ ${#args[@]} = 1 ]; then
        if [ $absolute = 1 ]; then
            find . -name "${args[0]}" -exec readlink -f {} +
        else
            find . -name "${args[0]}"
        fi
    else
        if [ $absolute = 1 ]; then
            find "${args[0]}" -name "${args[1]}" -exec readlink -f {} +
        else
            find "${args[0]}" -name "${args[1]}"
        fi
    fi
}
## amfind

## askm
askm() {
    local question=$(printf "%s" "$*")
    python3 "/disk_centremix/softwares/PyLib/am_store/shell_scripts/chat_shell.py" "$question"
}
## askm

## amget
amget() {
    if [ -e "$1" ]; then
        cp -r "$1" .
    else 
        echo "Usage: amget <file_path>"
    fi
}
## amget

## amcp
amcp(){
    # base on python
    local src dst
    local python_t=$AMPYTHON
    local force_s=0
    local script_path="/home/am/software/PyLib/am_store/shell_scripts/am_cp.py"
    if [ -z "$python_t" ]; then
        echo "Warning: \$AMPYTHON is not set, use python3 as default"
        python_t="python3"
    fi

    # 解析命令行参数
    while [ "$#" -gt 0 ]; do
        local arg="$1"
        if [[ "$arg" == "-f" ]]; then
            force_s=1
        elif [[ "$arg" == "-h" ]]; then
            echo "Usage: amcp [-f] <src> <dst>, -f for force copy and overwrite"
            return 1
        else
            if [ -z "$src" ]; then
                src="$arg"
            elif [ -z "$dst" ]; then
                dst="$arg"
            else
                echo "Usage: amcp [-j <process_num>] <src> <dst>"
                return 1
            fi
            shift
        fi
    done


    if [ -z "$src" ] || [ -z "$dst" ]; then
        echo "Error: src and dst are required."
        echo "Usage: amcp [-f] <src> <dst>"
        return 1
    fi

    src=$(realpath -m "$src")
    dst=$(realpath -m "$dst")

    if [ ! -d "$src" ]; then
        echo "Error: src is not a valid directory."
        return 1
    fi

    #find "$src" -mindepth 1 | parallel -j "$j" "cp -r {} '$dst'"
    $python_t $script_path "$src" "$dst" "$force_s"
}
## amcp

## amzip
_amzip_legacy(){
    # base on gzip, tar, pigz, unzip, unrar, rar, 7z, zip
    local filenames_show=1
    local ultra=0
    local params=()
    local arg
    local src=''
    local dst=''
    local zip_pattern=''
    local ext_name=''
    # 解析参数
    for arg in "$@"; do
        case $arg in
            -q)
            filenames_show=0
            ;;
            -u)
            ultra=1
            ;;
            -h)
            echo -e "amzip [-q] [-u] <path1> <path2> ... \nif path1 is zip file format, then unzip it, else zip it.Assign no path2 use path like path1\n-q for queit process, -u for multi thread process, -h for help"
            return 0
            ;;
            -*)
            echo "Unknowun Para: $arg, use -h for help"
            return 1
            ;;
            *)
            params+=("$arg")
            ;;
            esac
        done

    if [ ${#params[@]} -eq 0 ]; then
        echo "Usage: amzip [-p] [-u] <path1> <path2>"
        return 1
    elif [ ${#params[@]} -eq 1 ]; then
        local src=${params[0]}
        if ! [ -e "$src" ]; then
            echo "Error: $src is not a valid path"
            return 1
        else
            if [ -d "$src" ]; then
                dst="$src.tar.gz"
                zip_pattern='compress'
                ext_name='tar.gz'
            elif [ -f "$src" ]; then
                dst="${src%.*}"
                zip_pattern='decompress'
                ext_name="${src##*.}"
                if [[ "$dst" =~ \.tar$ ]]; then
                    dst="${dst%.*}"
                    ext_name="tar.$ext_name"
                fi
            else
                echo "Error: $src is not a valid path"
                return 1
            fi
        fi
    elif [ ${#params[@]} -eq 2 ]; then
        # local src=$(realpath ${params[0]})
        # local dst=$(realpath ${params[1]})
        local src=${params[0]}
        local dst=${params[1]}
        if ! [ -e "$src" ]; then
            echo "Error: $src is not a valid path, compressed file or file to be compressed"
            return 1
        else
            echo "Too many params recived, expect 1 or 2.Usage: amzip [-f] [-u] <path1> <path2>"
            return 1
        fi
    fi
    
    if [ -z "$zip_pattern" ] || [ -z "$ext_name" ]; then
        echo "Error: zip_pattern or ext_name is empty"
        return 1
    fi

    if [ "$ext_name" = 'tar.gz' ] || [ "$ext_name" = "gz" ]; then 
        if [ $ultra = 0 ];then
            echo "Detect format tar.gz, use -u for better performance"
            ultra=1
        fi
    else
        if [ $ultra = 1 ]; then
            echo "Error: -u only support tar.gz format"
            return 1
        fi
    fi

    if [ $ultra = 1 ]; then
        if [ -d "$src" ]; then
            if [ $filenames_show = 1 ]; then
                local file_f='v'
                tar "-cf$file_f" - "$src" | pigz -p 8 > "$dst"
                return 0
            else
                tar -cf - "$src" | pigz -p 8 > "$dst"
                return 0
            fi
        elif [ -f "$src" ]; then
            if ! [ -e "$dst" ]; then
                mkdir -p "$dst"
            fi
            if [[ "$src" =~ \.tar\.gz$ ]]; then
                pigz -p 8 -dc "$src" | tar -xvf - -C "$dst"
            elif [[ $src =~ \.gz$ ]]; then
                pigz -p 8 -c "$src" > "$dst"
            else
                echo "Error: -u only support tar.gz or gz format and has no progress bar"
                return 1
            fi
            return 0
        else
            echo "Error: $src is not a valid path"
            return 1
        fi
    fi

    if [ $zip_pattern = 'compress' ]; then
        case $ext_name in
            -zip)
            if [ $filenames_show = 1 ]; then
                zip -r "$dst" "$src"
            else
                zip -rq "$dst" "$src"
            fi
            ;;
            -tar.xz)
            if [ $filenames_show = 1 ]; then
                tar -Jcvf "$dst" "$src"
            else

                tar -Jcf "$dst" "$src"
            fi
            ;;
            -7z)
            7z a -mnt6 "$dst" "$src" -r
            ;;
            -rar)
            rar a -r -m5 -s -k "$dst" "$src"
            ;;
            *)
            echo "Error: $ext_name is not a valid compressed file"
            ;;
            esac

    elif [ $zip_pattern = 'decompress' ]; then
        if ! [ -e "$dst" ]; then
            mkdir -p "$dst"
        fi

        case $ext_name in
            -zip)
            if [ $filenames_show = 1 ]; then
                unzip "$dst" -d "$src"
            else
                unzip -q "$dst" -d "$src"
            fi
            ;;
            -tar.xz)
            if [ $filenames_show = 1 ]; then
                tar -Jxvf "$dst" -C "$src"
            else
                tar -Jxf "$dst" -C "$src"
            fi
            ;;
            -7z)
            if [ $filenames_show = 1 ]; then
                7z x -mmt6 "$dst" -o"$src"
            else
                7z x -mmt6 "$dst" -o"$src" 
            fi
            ;;
            -rar)
            if [ $filenames_show = 1 ]; then
                unrar x "$dst" "$src"
            else
                unrar -id=q x "$dst" "$src"
            fi
            ;;
            *)
            echo "Error: $ext_name is not a valid compressed file"
            ;;
            esac
    else
        echo "Error: zip_pattern is not valid"
        return 1
    fi
}

amzip(){
    local queit=0       # -q
    local options=''    
    local pigz_use=0    # -g
    local zip_file=''
    local folder=()
    local process_num=6 # -p
    local task=''       # -c or -d
    # read options
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h) echo "Usage: amzip [-q] [-g] [-p <value>] <output> <files...>"
                return 0 ;;
            -p) shift; process_num="$1" ;;
            -*) options+="$1" ;;
            *.rar|*.7z|*.zip|*.tar.gz|*.tar.xz|*.gz) 
            if [ -z "$zip_file" ]; then
                zip_file="$1" 
            else
                folder+=("$1")
            fi
            ;;
            *) folder+=("$1");;
        esac
        shift
    done
    # process options
    if [[ $options =~ 'q' ]]; then queit=1 
    fi

    if [[ $options =~ 'g' ]]; then pigz_use=1
    fi

    if [[ $options =~ 'c' ]]; then task='compress' 
    elif [[ $options =~ 'd' ]]; then task='decompress'
    fi
    
    if [ -z "$task" ]; then
        if [ -e "$zip_file" ]; then
            task='decompress'
        else
            task='compress'
        fi
    fi 
    
    if [ -z "$zip_file" ]; then
        zip_file="${folder[0]}.tar.gz"
    fi

    local ext_name="${zip_file##*.}"
    local temp_file="${zip_file%.*}"
    if [ "${temp_file##*.}" = "tar" ]; then
        ext_name="tar.$ext_name"
    fi

    if [ "$task" = "decompress" ];then
        if ! [ -e "$zip_file" ]; then
            echo "Error: $zip_file is not a valid path"
            return 1
        fi

        if [ ${#folder[@]} -eq 0 ]; then
            local dst='.'
        elif [ ${#folder[@]} -eq 1 ]; then
            local dst="${folder[0]}"
            if [ -e "$dst" ]; then
                mkdir -p "$dst"
            fi
        else
        echo "Error: Decompress mode recieve too many folders, only one is allowed"
        return 1
        fi
        if [ "$pigz_use" = 1 ]; then
            if  [ "$ext_name" != "gz" ] && [ "$ext_name" != "tar.gz" ]; then
                echo "Error: pigz only support gz or tar.gz format"
                return 1
            elif [ "$ext_name" = "tar.gz" ]; then
                if [ $queit = 1 ]; then
                    pigz -p "$process_num" -dc "$zip_file" | tar -xvf - -C "$dst"
                else
                    pigz -p "$process_num" -dcq "$zip_file" | tar -xf - -C "$dst"
                fi
            elif [ "$ext_name" = "gz" ]; then
                if [ $queit = 1 ]; then
                    pigz -p "$process_num" -dc "$zip_file" > "$dst"
                else
                    pigz -p "$process_num" -dcq "$zip_file" > "$dst"
                fi
            fi
        else
            local 7z_process="-mmt$process_num"
            7z x "$7z_process"  "$zip_file" -o"$dst"
        fi
    elif [ "$task" = "compress" ]; then
        if [ -e "$zip_file" ]; then
            echo "Error: $zip_file is already exist"
            return 1
        fi

        if [ ${#folder[@]} -eq 0 ]; then
            echo "Error: Compress mode recieve no folder"
            return 1
        else
            for i in "${folder[@]}"; do
                if ! [ -e "$i" ]; then
                    echo "Error: $i is not a valid path"
                    return 1
                fi
            done
        fi
        
        if [ "$pigz_use" = 1 ]; then
            if [ "$ext_name" != "tar.gz" ]; then
                echo "Error: pigz compress only support tar.gz format"
                return 1
            fi
            if [ "$queit" = 1 ]; then
                tar -cf - "${folder[@]}" | pigz -p "$process_num"  > "$zip_file"
            else
                tar -cvf - "${folder[@]}" | pigz -p "$process_num" > "$zip_file"
            fi
        else
            if [[ "$ext_name" =~ "tar" ]]; then
                if [ "$queit" = 1 ]; then
                    tar -cf - "${folder[@]}" | 7z a -mmt"$process_num" -si "$zip_file"
                else
                    tar -cvf - "${folder[@]}" | 7z a -mmt"$process_num" -si "$zip_file"
                fi
            else
                7z a -mmt"$process_num" "$zip_file" "${folder[@]}"
            fi

        fi
    fi
}
## amzip