import os
import sys
from figuremark import figuremark

filename = "../../example/figuremark-example.md"
if len(sys.argv) > 1:
	# If there's an argument, assume it's a Markdown file path.
	filename = sys.argv[1]

try:
	# Open and read file.
	filename = os.path.abspath(filename)
	input_file = open(filename, 'r')
	file_contents = input_file.read()
	input_file.close()
	
	# Convert any FigureMark blocks.
	file_contents = figuremark.convert(file_contents)
	
	# Write out result to "-converted" file alongside original.
	basename, sep, ext = filename.partition(".")
	output_filename = f"{basename}-converted{sep}{ext}"
	output_file = open(output_filename, 'w')
	output_file.write(file_contents)
	output_file.close()
	print(f"Wrote output file: {output_filename}")
 
except IOError as e:
	print(f"Error: {e}")
	sys.exit(1)
