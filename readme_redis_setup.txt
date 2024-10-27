u have to be running redis-server

if windows, just click start, type "powershell" run it

type "wsl" to launch linux subsystem for windows. select Ubuntu image

now when u in ubuntu do these commands type each hit enter: 

sudo apt update && upgrade 
sudo service redis-server restart
redis-cli
monitor

Now after all those commands ^^^^ u can minimize this window or leave it in a corner of your screen , its in monitor mode so u can watch data come in and out of redis.

