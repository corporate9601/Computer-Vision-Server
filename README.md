# Computer-Vision-Server
An API server for Molmo 7B - Describe web pages or computer screenshots and point to elements using Molmo 7B - a multimodal vision model which can describe real and virtual images and point at objects

Using this tool, you can describe web pages, and turn them into a JSON list of elements and actions that should be taken

You can then split that list up as it's a list of JSON objects, 

for each object, you can use Molmo in "point mode" to show the location of the described object on the image

if doing web vision, or computer vision, this is helpful, as you can prompt the model with the "goal" it should achieve, the screenshot, and it will describe a list of actions you should take in order to achieve this goal, in a format ready to use. 

To get JSON just ask the model. tell it "reply with JSON" and keep tokens low like 200-600 new tokens

How to force the model to point:

when prompting, start the prompt with "point_wa:" and then the rest of your prompt

using "point_wa:" at the start of the prompt will always force the model to reply with an X and Y location of the objects

So yea enjoy ! if anything isn't clear just make an Issue this is the worst ReadMe ever I know it is rushed I'm about to put this on a server lol OK byeee

PS: u can use this to make a tool just like "Computer" from anthropic but WAAAY BETTER! use this with an automation browser to do web automation! 
ALSO:: if u want to do COMPUTER AUTOMATION with this -- search for "XVFB" and "XVFB-wrapper" to use it in python. virtual monitors. 
and u can tell pyautogui to use the specific X11 monitor you just created in XVFB so you can have a virtual mouse and virtual keyboard for your virtual monitor. 
so u can get insane automation of your PC but without restrictions

just code the systems yourself for using the user prompt to make an "action list" and revise it every action to keep the agent as PLASTIC as possible, adapting as it acts. we so close to AGI fam.

COMING SOON:
- API connector. already coded it and made an awesome web automation program with it.. I'm just really busy using it lol so HOLDUP! -- to the 1 person that wont find this ;D

  
