import os
import sys
from figuremark import figuremark

file_path = "../../example/figuremark-example.md"
this_script_path = os.path.abspath(os.path.expanduser(sys.argv[0]))
file_path = os.path.join(os.path.dirname(this_script_path), file_path)

if len(sys.argv) > 1:
	# If there's an argument, assume it's a Markdown file path.
	file_path = sys.argv[1]

try:
	# Open and read file.
	input_file = open(os.path.abspath(file_path), 'r')
	file_contents = input_file.read()
	input_file.close()
	
	# Convert any FigureMark blocks.
	file_contents = figuremark.convert(file_contents)
	sys.exit(0)
	# Write out result to "-converted" file alongside original.
	basename, sep, ext = file_path.partition(".")
	output_filename = f"{basename}-converted{sep}{ext}"
	output_file = open(output_filename, 'w')
	output_file.write(file_contents)
	output_file.close()
	print(f"Wrote output file: {output_filename}")
 
except IOError as e:
	print(f"Error: {e}")
	sys.exit(1)
