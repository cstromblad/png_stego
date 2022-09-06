This is a very simple proof of concept program to add some data into an already existing PNG-file by creating a ancillary chunk.

The process is rather simple.
1. Unpack the PNG file into a list of chunks.
2. Create a new chunk with an ancillary chunk type.
3. Add the chunk at the end, but before the IEND
4. Reassemble by packing it all up and adding it to a file.
5. Voila!

It's not pretty, but the code should be possible to use and modify at least.