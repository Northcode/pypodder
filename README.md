# Pypodder
A scriptable podcatcher written in python 3!

### Installing

1. make sure you have python 3.3 atleast installed [python.org](https://www.python.org/downloads/)
2. git clone the repo or download the zip
3. use pip to install requirements
  * *Windows:* You should allready have pip installed in "%PYTHON%\Scripts"
  * *Mac:* run "sudo easy_install pip", and it should install
  * *Linux:* use your distros prefered method of installing pip, "sudo apt-get install python3-pip" on debian based distros
4. run "pip install -r requirements.txt" in the directory
5. Linux and mac users may need to add execute permission to "pypodder.py"

Run the program from pypodder.py
The first time is should exit and generate an empty feed.list file

### Configuring

The feed.list file contains the list podcast feeds to download.  
To add a podcast, find its rss feed (usually somewhere on their webpage), and paste it in the feed.list file followed by the name of the podcast  
When you start pypodder, it can be a good idea to add the "-v" option to give some output, or else it will remain quiet  

Configuring each podcast is done through the podcast.cfg file in the podcast directory.  
You can configure the output of each episode in the file:  
You can use:  
{{podcastname}} - podcast name/title  
{{episodename}} - episode name/title  
{{episodenum}}  - episode number  
{{episodesize}} - size of episode in bytes  
{{episodedate}} - uploaded date of episode  
Example format string:  
** {{podcastname}} - {{episodenum}} {{episodename}}.mp3 **  


Configuring each podcast is done through the podcast.cfg file in the podcast directory. 
You can configure the output of each episode in the file:
You can use:
{{podcastname}} - podcast name/title 
{{episodename}} - episode name/title 
{{episodenum}}  - episode number 
{{episodesize}} - size of episode in bytes 
{{episodedate}} - uploaded date of episode 
Example format string: 
** {{podcastname}} - {{episodenum}} {{episodename}}.mp3 ** 


### Issues, report them here!

Please report any issues to the issues page on the repository on [github](https://github.com/Northcode/pypodder/issues)
  
