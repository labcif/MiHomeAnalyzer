# MiHomeAnalyzer - Detect Motion in Xiaomi's MJSXJ02HL security camera recordings

**MiHomeForensics** is an application that joins recordings from Xiaomi's MJSXJ02HL security camera and detect motion on them.

It uses one modified [MotionDetector](https://github.com/sgjava/motiondetector) to detect motion on the specified videos.

This application was built in **Python 3.9** (Windows 10 Pro) and **Python 3.10** (Ubuntu 22.04 LTS).

It supports Windows and Linux (Developed and tested in Windows 10 Pro and Ubuntu 22.04 LTS).


## Dependencies
### FFmpeg 
The only dependency required by this application is FFmpeg.
<details>
<summary>Click to see FFmpeg installation on Windows!</summary>

- Download the [.7z file](https://ffmpeg.org/download.html) <br>(Oficial Mirror, check it out [here](https://ffmpeg.org/download.html#build-windows)
- Extract the contents to on folder named "ffmpeg"
- Place the folder in "C:\Program Files"
- Run the following command to add the folder to system variables: <br>
```setx /m PATH "C:\Program Files\ffmpeg\bin;%PATH%```
</details>

<details>
<summary>Click to see FFmpeg installation on Linux!</summary>

### Run the commands: 
- **sudo apt update**
- ***sudo apt install ffmpeg***
</details>

<br>

## Compilation / Python execution
### In order to execute this application outside Autopsy you have to install the following libraries (tested on a Fresh Installation of both Operating Systems):
- **codeferm**, a self modified version of [MotionDetector's code](https://github.com/sgjava/motiondetector), can be found [here](./MotionDetector/)
- **pencv-python** (version 4.5.3.56, tested on **Windows**, or 4.5.5.64, tested on **Linux**)
- **ffmpeg-python**
- **psutil**
- **pyinstaller**, if you want to compile recompile the application

<br>

## Usage
### As Python Script / Executable application

This application can be used as a Python Script / Executable application. There are two versions:

* Python version: can be found [here](./MiHomeForensics)
* Executable versions: can be found [here](./MiHomeForensics/Pre-Compiled)

The executable versions does not need instalation.

They need arguments to work, use (-h) or (--help) argument to see a little usage example

Both the Executable application and the Python script need a [config file](./MotionDetector/config_example.ini) to execute.

### In Autopsy

In order to integrate **MiHomeAnalyzer** with [Autopsy](https://www.autopsy.com/), there are two modules:

 * [MiHomeAnalyzer](./AutopsyModules/MiHomeAnalyzer): uses the MiHomeForensics application in order to detect motion in joined videos
 * [MiHomeAnalyzer_Report](./AutopsyModules/MiHomeAnalyzer): exports a HTML report with the results of the ingest module

Place both folders ([MiHomeAnalyzer](./AutopsyModules/MiHomeAnalyzer)) and ([MiHomeAnalyzer_Report](./AutopsyModules/MiHomeAnalyzer)) in the python_modules folder of Autopsy

Then, in order to execute [MiHomeAnalyzer](./AutopsyModules/MiHomeAnalyzer), you have to place in the same folder the [Executable file](./MiHomeForensics/Pre-Compiled) for you Operating System
<br>

## Authors

 * ![](./Images/joao.jpg) <br> João Manuel Vieria Silva (Instituto Politécnico de Leiria - Portugal)

 * ![](./Images/pedro.jpg) <br> Pedro Pescadinha Viegas (Instituto Politécnico de Leiria - Portugal)

## Mentors

* Patrício Domingues (Instituto Politécnico de Leiria - Portugal)
* Miguel Frade (Instituto Politécnico de Leiria - Portugal)
* Miguel Negrão (Instituto Politécnico de Leiria - Portugal)