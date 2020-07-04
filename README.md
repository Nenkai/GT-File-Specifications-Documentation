# GT5-File-Specifications
File specifications for various Gran Turismo 5 file types.

This is an on-going effort to document file types used by Gran Turismo 5. 
Any help is welcome.

The provided files (templates) were created through 010 Editor, but should be fairly readable. (Aside from the names assigned to unknown variables and struct fields).
Simply loading your target file in 010 Editor, and run the template against your file and start reversing.

# General File Structure
Gran Turismo 5+ (and possibly lower) makes heavy use of trees & offsets within file formats, leading to maps of certain content types. This is a messy structure to generally reverse.

## File Formats 
* `MDL3` -> Model files, used for cars, wheels, sky. Contains model images, reflection & light data, original file names, mesh groups, textures.
  Usually extension less files (but can be found in car, wheel, .sky files in the crs folder).
  
* `TXS3` -> Texture files, originally DDS Images. Either found in .img files, or bundled inside files such as `MDL3`. Multiple can be present in a `MDL3`.
