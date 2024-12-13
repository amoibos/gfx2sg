For creating tile and palette files which are compatible to sverx/devkitSMS/tree/master/SGlib.
It supports background tiles and sprites which requires transparent argument. 

The code is simple but do not have:
  * resizing
  * color reduction
  * Dithering
  * Avoiding tile duplicate by using a tilemap

Known Bugs:
  * preview function show transparency in the image

Usage:
python gfx2sg.py FILENAME

  

