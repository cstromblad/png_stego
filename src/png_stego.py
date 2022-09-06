#!/usr/bin/env python
import base64
import binascii
import struct
import sys

from collections import namedtuple
from typing import List

# https://en.wikipedia.org/wiki/Portable_Network_Graphics

# Basically this is what we do:
# 1. Unpack the PNG into a chain of chunks.
# 2. Generate a new chunk based on stdin-data.
# 3. Insert new chunk at selected position.
# 4. Reassemble PNG by packing chunks and adding them together.
# 5. Voila!


class PNGParser:

    MAGIC_LENGTH = 8
    IHDR_LENGTH = 13
    CHUNK_HEADER = 8
    CHUNK_CRC = 4

    Chunk = namedtuple('Chunk', ['length', 'type', 'data', 'crc'])

    def __init__(self, png_file: str):
        with open(png_file, 'rb') as f:
            self._png_file = f.read()
        
        self.is_parsed = False
        self.chunk_chain: List = []

    @property
    def png_file(self):
        return self._png_file
    
    def png_magic(self):

        (png_magic) = struct.unpack("8s", self.png_file[:self.MAGIC_LENGTH])  # Always returns a tuple

        return png_magic

    def get_chunk(self, offset):

        raw_file = self.png_file[offset:]

        if offset >= len(self.png_file):
            # End of file, no more chunks!
            return None

        (length, type_) = struct.unpack(">I4s", raw_file[:8])

        # SECURITY-NOTE: If length is unreasonably large, no checks are made.

        raw_file = raw_file[8:]
        (data, crc) = struct.unpack(f">{length}sI", raw_file[:length+4])

        chunk = self.Chunk(length, type_, data, crc)
        
        return chunk

    def populate_chunk_chain(self):

        if not self.is_parsed:
            offset = 0
            while True:

                chunk = self.get_chunk(parser.MAGIC_LENGTH + offset)
                if chunk.type == b'IEND':
                    self.chunk_chain.append(chunk)
                    break
                    
                self.chunk_chain.append(chunk)
                offset = offset + self.CHUNK_HEADER + chunk.length + self.CHUNK_CRC
            
            self.is_parsed = True


    def png_ihdr(self, chunk_data):

        ihdr = struct.unpack_from(">LLBBBBB", chunk_data)

        return ihdr

    def create_chunk(self,
                     data: bytes, 
                     type_: bytes = b'coRS'):

        # http://libpng.org/pub/png/spec/1.2/PNG-Structure.html#Chunk-layout

        length = len(data)

        type_and_data = b''.join([type_, data])
        crc = binascii.crc32(type_and_data)

        chunk = self.Chunk(length, type_, data, crc)
        #chunk = struct.pack(f'>L4s{length}sL', length, type_, data, crc)

        return chunk

    def append_chunk(self, chunk: Chunk):

        self.populate_chunk_chain()
        self.chunk_chain.append(chunk)

    def insert_chunk(self, chunk: Chunk, position):

        self.populate_chunk_chain()

        self.chunk_chain.insert(position, chunk)

    def create_png_from_chunk_chain(self, filename: str):

        self.populate_chunk_chain()

        (magic_intro) = struct.pack("8s", self.png_file[:self.MAGIC_LENGTH])

        new_file = b'' + magic_intro

        for index, chunk in enumerate(self.chunk_chain):
            data = struct.pack(f">L4s{chunk.length}sL", chunk.length, chunk.type, chunk.data, chunk.crc)
            
            new_file += data

        with open(filename, 'wb') as f:
            f.write(new_file)

if __name__ == "__main__":
    # Yes, I will clean this mess up and add a proper CLI.

    if len(sys.argv) < 2:
        print("Usage: ./png_stego.py file_to_be_encoded png_file_to_modify output_file_name")
        exit(-1)

    with open(sys.argv[1], 'rb') as fd:
        data = fd.read()

    b64_encoded_data = base64.b64encode(data)
    
    parser = PNGParser(sys.argv[2])

    chunk = parser.create_chunk(b64_encoded_data)
    parser.insert_chunk(chunk, len(parser.chunk_chain)-1)

    parser.create_png_from_chunk_chain(f'{sys.argv[3]}')

    parser = PNGParser(sys.argv[3]) 
    parser.populate_chunk_chain()
    
    for chunk in parser.chunk_chain:
        print(chunk.type)
        if chunk.type == b"coRS":
            with open('extracted_file', 'wb') as fd:
                fd.write(chunk.data)
