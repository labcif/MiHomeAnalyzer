from os import listdir, path, remove, mkdir, scandir, getpid, makedirs
from sys import stdout, exit, argv, exc_info
from getopt import getopt, GetoptError
from pathlib import Path
from codeferm import videoloop
from configparser import ConfigParser
from json import dumps
from psutil import Process
from subprocess import Popen, PIPE, STDOUT


#https://stackoverflow.com/questions/973473/getting-a-list-of-all-subdirectories-in-the-current-directory
#Função retirada do stackoverflow, que retorna todas as diretorias e subdiretorias da pasta selecionada
#A função é recursiva, em que vai sempre ser chamada até sejam listadas todas as subdiretorias de uma diretoria
#Todas estas diretorias são adicionadas à lista subfolders[]
def get_all_dirs(dirname):
    subfolders = [f.path for f in scandir(dirname) if f.is_dir()]
    for dirname in list(subfolders):
        subfolders.extend(get_all_dirs(dirname))
    return subfolders

#Função que retorna todos os ficheiros .mp4 encontrados nas diretorias e subdiretorias da pasta selecionada
def get_all_mp4_files_in_dirs(all_dirs):
    #Incialização da lista
    all_mp4_files = []

    #Percorrer todas as diretorias e subdiretorias retornadas pela função get_all_dirs()
    for i in all_dirs:

        #Lista os ficheiros contidos na diretoria que está a analizar
        files_in_dir=listdir(i)

        #Percorre cada ficheiro da diretoria
        for u in files_in_dir:

            #A camera cria todos os ficheiros para o determinado minuto
            #Caso seja desligada a meio, ficam ficheiros vazios na diretoria que iriam criar erros na junção de videos
            #Assim, todos os ficheiros com 0 Kb irão ser ignorados
            if path.getsize(i+"/"+u) == 0:
                continue

            #Verifica se a extenção do ficheiro é .mp4
            #Caso seja, adiciona à lista all_mp4_files[] com o caminho ("path") completo do ficheiro
            filename, file_extension = path.splitext(u)
            if file_extension.lower() == '.mp4' or file_extension.lower() == '.avi':
                all_mp4_files.append(Path(i+"//"+filename+file_extension))
    return all_mp4_files


def ffmpeg_joiner(videos_to_join, out_file_name, output_file_path):
    
    #Caso não exista a diretoria "joined_videos" vai ser criada
    if not path.exists(output_file_path+'/joined_videos'):
        makedirs(output_file_path+'/joined_videos')
    
    #Escreve no ficheiro temp_videos_paths os caminhos dos vídeos
    with open(output_file_path+"/joined_videos/temp_videos_paths.txt", "w", encoding="utf-8") as f:
        videos_to_join.sort()
        for video in videos_to_join:
            f.write("file '"+str(video)+"'\n")


    #https://stackoverflow.com/questions/17668996/python-how-to-join-multiple-video-files
    # set output filename
    outFile = Path(output_file_path+'/joined_videos/'+out_file_name+'.mp4')

    # create file object that will contain files for ffmpeg to concat
    input_files_path = Path(output_file_path+'/joined_videos/temp_videos_paths.txt')

    # this seems to be the proper concat input, with the path containing the list
    # of files for ffmpeg to concat, along with the format parameter, and safe, if i
    # read the docs correctly, is default/optional
    #ffInput = ffmpeg.input(input_files_path, format='concat', safe=0)

    # output parameters
    #params =    {
    #            'c:a': 'aac'
    #            }
    
    # input stream -> output stream with output filename and expanded params
    #ffOutput = ffInput.output(outFile.as_posix(), **params)

    # make ffmpeg quiet
    #ffOutput = ffOutput.global_args('-loglevel', 'error')
    #ffOutput = ffOutput.global_args('-stats')

    # something, something, run.
    #ffOutput.run(overwrite_output=True)
    process = Popen('ffmpeg -f concat -safe 0 -loglevel error -stats -i '+ input_files_path.as_posix() +' -y ' + outFile.as_posix(), stdout=PIPE, stderr=STDOUT, shell = True, bufsize = 1, encoding='utf-8', errors = 'replace')
    while True:
        realtime_output = process.stdout.readline()
        if realtime_output == '' and process.poll() is not None:
            break
        if realtime_output:
            print(realtime_output.strip(), flush=False, end='\r')
            stdout.flush()

    #Removing temp file of videos paths
    remove(input_files_path)

    #Devolver o caminho do ficheiro final
    return outFile.as_posix()


def run_motiondetector(joined_video, result_name, config_file_path, output_file_path, mp4_files):
    parser = ConfigParser()
    # Read configuration file
    parser.read(config_file_path)

    parser.set('camera', 'url', joined_video)
    parser.set('camera', 'name', result_name)
    parser.set('camera', 'recorddir', output_file_path+'\\results')
    # Writing our configuration file to 'example.ini'
    with open(config_file_path, 'w') as configfile:
        parser.write(configfile)
    
    
    videoLoop = videoloop.videoloop(config_file_path, mp4_files)
    motion_file_names = videoLoop.run()
    # Make sure read/write threads exit
    videoLoop.frameOk = False
    videoLoop.recording = False
    videoLoop.logger.info("Process exit")
    return motion_file_names


#Como funcionam as diretorias:
#Dentro do disco temos 2 pastas, apenas nos interessa a pasta "record"
#Dentro da pasta "record", temos os vídeos separados pelo dia que foram gravados
#Dentro de uma das pastas do dia da gravação, encontramos os vídeos separados pela hora da gravação


def join_all_videos(folder_path, output_file_path, config_file_path):
    #Executar as funções para obter todos os ficheiros .mp4
    all_folders = get_all_dirs(folder_path)
    all_files_in_folders = get_all_mp4_files_in_dirs(all_folders)

    #Executar a função para juntar os vídeos
    joined_video=ffmpeg_joiner(all_files_in_folders, "All_Videos", output_file_path)

    #Executar a função para detetar movimento no vídeo final
    return run_motiondetector(joined_video, "All_Videos", config_file_path, output_file_path, all_files_in_folders)


#Função que vai organizar e juntar os vídeos por dia
def join_videos_by_day(folder_path, output_file_path, config_file_path, day):
    day = day.split("-")

    if len(day[0]) != 2 or len(day[1]) != 2 or len(day[-1]) != 4:
        print("Wrong date format!\nExiting...")
        exit(2)

    day=day[-1]+day[1]+day[0]
    joined_videos=[]

    day_exists=False

    #Procura na pasta "record" pelas subpastas dos dias de gravação
    subfolders = [f.path for f in scandir(folder_path) if f.is_dir()]

    #Vai percorrer cada um desses dias
    for subfolder in subfolders:
        if subfolder.split("\\")[-1] == day:
            day_exists = True

            #Procura todas as subpastas
            all_folders = get_all_dirs(subfolder)

            #Procura todos os ficheiros .mp4 dessa pasta e das suas subpastas
            all_files_in_folders = get_all_mp4_files_in_dirs(all_folders)

            #Algoritmo para dar o nome ao vídeo final, neste caso vai ser "Vido_dia_DIA-MÊS-ANO"
            video_name = subfolder.split("\\")[-1]
            video_name = video_name[-2:] +"-"+ video_name[4:6] +"-"+ video_name[:-4]

            #Chamda da função que vai juntar os vídeos encontrados, recebe como parametros a lista de vídeos e o nome do vídeo final
            joined_videos.append(ffmpeg_joiner(all_files_in_folders, "Video_dia_"+video_name, output_file_path))
    
    if not day_exists:
        print("Day inserted not found!\nNothing done..")
        exit(3)
    
    motion_file_names={}
    for video in joined_videos:
        motion_file_names.update(run_motiondetector(video, video.split('/')[-1].replace('.mp4', ''), config_file_path, output_file_path, all_files_in_folders))
    return motion_file_names


def join_videos_by_hour(folder_path, output_file_path, config_file_path):
    joined_videos={}

    #Procura na pasta "record" pelas subpastas dos dias de gravação
    subfolders = [f.path for f in scandir(folder_path) if f.is_dir()]

    #Vai percorrer cada um desses dias
    for subfolder in subfolders:

        #Procura na pasta do dia pelas subpastas das horas de gravação
        hours=[f.path for f in scandir(subfolder) if f.is_dir()]

        #Percorre cada uma dessas horas
        for hour in hours:
                #Procura todas as subpastas
                all_folders = get_all_dirs(hour)

                #Procura todos os ficheiros .mp4 dessa pasta e das suas subpastas
                all_files_in_folders = get_all_mp4_files_in_dirs(all_folders)

                #Algoritmo para dar o nome ao vídeo final, neste caso vai ser "Vido_dia_DIA-MÊS-ANO_HORAH"
                video_day = hour.split("\\")[-2]
                video_day = video_day[-2:] +"-"+ video_day[4:6] +"-"+ video_day[:-4]
                video_name="Video_dia_"+video_day+"_"+hour.split("\\")[-1]+"H"

                #Chamda da função que vai juntar os vídeos encontrados, recebe como parametros a lista de vídeos e o nome do vídeo final
                joined_videos[ffmpeg_joiner(all_files_in_folders, video_name, output_file_path)]=all_files_in_folders
    
    motion_file_names={}
    for video, mp4_files in joined_videos.items():
        motion_file_names.update(run_motiondetector(video, video.split('/')[-1].replace('.mp4', ''), config_file_path, output_file_path, mp4_files))
    print(motion_file_names)
    return motion_file_names


def generate_json_with_motions(output_file_path, motion_file_names):
    motions=get_all_mp4_files_in_dirs(get_all_dirs(output_file_path+'/results'))
    json_path = output_file_path+"/results/motions.json"
    if path.exists(json_path):
        remove(json_path)
    with open(output_file_path+"/results/motions.json", "w", encoding="utf-8") as f:
        firstMotion=True
        f.write('{"motions":[\n')
        for motion in motions:
            motion_date = str(motion).split("\\")[-1].replace(".mp4", "").replace("motion ", "")
            try:
                original_path = motion_file_names[motion_date].as_posix()
            except KeyError:
                continue
            my_json = {
            "motion_path": str(motion.as_posix()),
            "motion_date": motion_date,
            "original_file_path": str(original_path)
            }
            if firstMotion:
                f.write(dumps(my_json, indent=6))
                firstMotion=False
            else:
                f.write(","+dumps(my_json, indent=6))
        f.write("]}")
    f.close()


def main(argv):
    #Definir quais os argumentos vão existir no Script
    try:
        opts, args = getopt(argv,"hp:c:o:d:t",["help","path=","day=","thour","config=", "output="])

    #Caso o argumento não seja nenhum dos argumentos possíveis
    except GetoptError:
        print('\nInvalid argument!\nUse -h to see the arguments accepted by the Script.\nShutting down...\n')
        exit(0)

    #Caso não sejam passados argumentos, apresenta mensagem de erro
    if not opts:
        print('\nNo argument(s) passed!\nUse -h to see the arguments accepted by the Script.\nShutting down...\n')
        exit(0)
    
    #Tratamento dos argumentos
    for opt, arg in opts:

        #Caso o argumento seja o -h(--help)
        if opt in ("-h", "--help"):
            print('\n-- MiHomeForensics --')
            print('Arguments accepted by the Script:\n')
            print('--help (-h): To see some help / information about the script.')
            print('--path (-p) <PATH>: To specify The path to search the videos.')
            print('--config (-c) <PATH>: To specify the config path.')
            print('--output (-o) <PATH>: To specif the output path.')
            print('--day (-d): To join videos by day.')
            print('--thour (-t): To join videos by hour.')
            print('The Script will join all videos in one if the arguments [-d] [-t] are not inserted.\n')
            print('Positional arguments: [-p] [-c] [-o].')
            print('Optional arguments: [-h] [-d] [-t].\n')
            print('Usage: MiHomeForensics.py(.exe) [-h] [-p PATH] [-c PATH] [-o PATH] [-d] [-t].\n')
            exit(0)

        #Caso o argumento seja o -p(--path)
        elif opt in ("-p", "--path"):
            folder_path = arg

        #Caso o argumento seja o -c(--config)
        elif opt in ("-c", "--config"):
            config_file_path = arg
        
        elif opt in ("-o", "--output"):
            if arg[-1] == '\\' or arg[-1] == '/':
                arg[-1]==''
            output_file_path = arg+'/MiHomeForensics'

        #Caso o argumento seja o -d(--day)
        elif opt in ("-d", "--day"):
            print("Day arg inserted, joining all videos in day "+arg+"!")
            day_result=join_videos_by_day(folder_path, output_file_path, config_file_path, arg)
            generate_json_with_motions(output_file_path, day_result)
            exit(0)

        #Caso o argumento seja o -t(--thour)
        elif opt in ("-t", "--thour"):
            print("Hour arg inserted, joining all videos by hour!")
            hour_result = join_videos_by_hour(folder_path, output_file_path, config_file_path)
            generate_json_with_motions(output_file_path, hour_result)
            exit(0)


    #Caso não seja inserido nenhum dos argumentos para juntar os vídeos ou
    #por hora ou por dia, o Script irá juntar todos os vídeos em apenas um 
    #vídeo só
    print("No arg inserted, joining all videos!")
    all_videos_result=join_all_videos(folder_path, output_file_path, config_file_path)
    generate_json_with_motions(output_file_path, all_videos_result)


def terminate_all_child_processes():
    current_process = Process(getpid())
    children = current_process.children(recursive=True)
    for child in children:
        if child.name()=='projInf.exe' or child.name()=='ffmpeg.exe':
            print(child)
            child.kill()

#Chamada da função main passando os argumentos
if __name__ == "__main__":
    try:
        main(argv[1:])
    except SystemExit as e:
        terminate_all_child_processes()
        exit(e.code)
    except:
        terminate_all_child_processes()
        print("Ocorreu um erro:", exc_info())