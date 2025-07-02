
# FigureMark, by Matt Gemmell ~ https://mattgemmell.scot/figuremark


import re


class FMAttributes:
	# Directives
	fig_num_format = "fig-num-format"
	empty_captions = "empty-captions"
	caption_before = "caption-before"
	link_caption = "link-caption"
	retain_block = "retain-block"
	process_mode = "process-mode"
	
	known_directives = {
		fig_num_format,
		empty_captions,
		caption_before,
		link_caption,
		retain_block,
		process_mode
	}
	
	# Magic
	shared_class = "figuremark"
	attributed_class = "attributed"
	implicit_class = "implicit"
	directive_prefix = ":"
	remove_token = f"-{directive_prefix}"
	
	def __init__(self, raw_string=None):
		self.tag_id = None
		self.classes = [FMAttributes.shared_class]
		self.tag_attrs = {}
		self.directives = {}
		
		if raw_string:
			# Parse attribute string like '.class #id key=val'.
			pattern = re.compile(r'([.#][\w:-]+|[\w:-]+=(?:"[^"]*"|\'[^\']*\'|[^\s]*)|[\w\-\.]+)')
			for match in pattern.findall(raw_string):
				item = match
				if item.startswith('.') and not item[1:] in self.classes:
					self.classes.append(item[1:])
				elif item.startswith('#'):
					self.tag_id = item[1:]
				elif "=" in item:
					key, _, val = item.partition('=')
					val = val or ""
					dest = self.tag_attrs
					this_key = key
					if key.startswith(FMAttributes.directive_prefix):
						dest = self.directives
						# Trim off the directive_prefix.
						this_key = this_key[len(FMAttributes.directive_prefix):]
						if not this_key in FMAttributes.known_directives:
							print(f"Warning: Unknown directive '{FMAttributes.directive_prefix}{this_key}'. Ignoring.")
							continue
					dest[this_key] = val.strip('"\'')
				else:
					split_classes = item.split(".")
					for this_class in split_classes:
						if not this_class in self.classes:
							self.classes.append(this_class)
	
	def __str__(self):
		attr_str = ""
		if self.tag_id:
			attr_str += f' id="{self.tag_id}"'
		if len(self.classes) > 0:
			attr_str += f' class="{" ".join(self.classes)}"'
		for k, v in self.tag_attrs.items():
			attr_str += f' {k}="{v}"'
		return attr_str
	
	def update(self, new_attrs):
		# Update self with values from new_attrs, OVERWRITING our own values if necessary.
		# This method also appropriately processes removals with the remove_token.
		
		if new_attrs.tag_id and new_attrs.tag_id.startswith(FMAttributes.remove_token):
			if self.tag_id == new_attrs.tag_id[len(FMAttributes.remove_token):] or new_attrs.tag_id == FMAttributes.remove_token:
				self.tag_id = None
		else:
			self.tag_id = new_attrs.tag_id
		
		for new_class in new_attrs.classes:
			if new_class == FMAttributes.remove_token:
				self.classes.clear()
			elif new_class.startswith(FMAttributes.remove_token):
				if new_class[len(FMAttributes.remove_token):] in self.classes:
					self.classes.remove(new_class[len(FMAttributes.remove_token):])
			elif not new_class in self.classes:
				self.classes.append(new_class)
		
		for k, v in new_attrs.tag_attrs.items():
			if v == FMAttributes.remove_token:
				if k in self.tag_attrs:
					del self.tag_attrs[k]
			elif k == FMAttributes.remove_token:
				self.tag_attrs.clear()
			else:
				self.tag_attrs[k] = v
		
		for k, v in new_attrs.directives.items():
			if v == FMAttributes.remove_token:
				if k in self.directives:
					del self.directives[k]
			elif k == FMAttributes.remove_token:
				self.directives.clear()
			else:
				self.directives[k] = v
	
	def incorporate(self, new_attrs):
		# Update self with values from new_attrs, letting our OWN values take precedence.
		# This method does NOT process removals.
		
		if not self.tag_id:
			self.tag_id = new_attrs.tag_id
		
		for new_class in new_attrs.classes:
			if not new_class in self.classes:
				self.classes.append(new_class)
		
		temp = dict(new_attrs.tag_attrs)
		temp.update(self.tag_attrs)
		self.tag_attrs = temp
		
		temp = dict(new_attrs.directives)
		temp.update(self.directives)
		self.directives = temp


def convert(text):
	fm_globals_pattern = r"(?mi)^(?:\{figure(?:mark)?\s*([^\}]*)\})\s*?$"
	figure_block_pattern = r"(?mi)(?<!<!--\n)^(`{3,}|~{3,})\s*figure(?:mark)?(\s+[^\{]+?)?\s*(?:\{([^\}]*?)\})?\s*$\n([\s\S\n]*?)\n\1\s*?$"
	figure_span_pattern = r"(?<!\\)\[(.+?)(?<!\\)\]\{([^\}]+?)\}|\{([\d.-]+)\}|([^\s\[\{]+)\{([^\d\}]+)\}"
	
	marks_map = {	"+": "insert",
								"-": "remove",
								"/": "comment",
								">": "result",
								"!": "highlight"}
	figure_number = 0
	figs_processed = 0
	block_pattern_obj = re.compile(figure_block_pattern)
	span_pattern_obj = re.compile(figure_span_pattern)
	last_fig_end = 0
	global_attrs = FMAttributes()
	
	# Find any FigureMark blocks needing rewritten.
	block_match = block_pattern_obj.search(text, last_fig_end)
	while block_match:
		block_title = block_match.group(2)
		if block_title:
			block_title = block_title.strip()
		block_attributes = block_match.group(3) 
		processed_block = block_match.group(4)
		
		# Sync figure number with any intervening non-FigureMark figures.
		other_figures = re.findall(r"(?sm)<figure[^>]*>.+?</figure>", text[last_fig_end:block_match.start()])
		if other_figures:
			figure_number += len(other_figures)
		figure_number += 1
		
		# Process attributes.
		attrs = FMAttributes(block_attributes)
		if not attrs.tag_id:
			attrs.tag_id = f"figure-{figure_number}"
		attrs.tag_attrs['data-fignum'] = f'{figure_number}'
		
		# Handle intervening globals blocks.
		pre_match_text = text[:block_match.start()]
		pre_match_orig_len = len(pre_match_text)
		globals_matches = []
		
		# Update global_attrs with each set of found globals, in order.
		for globals_match in re.finditer(fm_globals_pattern, pre_match_text):
			globals_matches.append(globals_match)
			global_attrs.update(FMAttributes(globals_match.group(1)))
				
		# Remove globals blocks in reverse, to preserve offsets as we go.
		for globals_match in reversed(globals_matches):
			pre_match_text = pre_match_text[:globals_match.start()] + pre_match_text[globals_match.end():]
		
		# Account for changed offsets in block_match due to removal of globals blocks.
		pre_match_delta = pre_match_orig_len - len(pre_match_text)
		
		# Incorporate global attributes, overriding with local values.
		attrs.incorporate(global_attrs)
		
		# Enact directives.
		fig_num_format = attrs.directives.get(FMAttributes.fig_num_format, "Fig. #").replace("#", str(figure_number))
		empty_captions = (attrs.directives.get(FMAttributes.empty_captions, "true") == "true")
		caption_before = (attrs.directives.get(FMAttributes.caption_before, "true") == "true")
		link_caption = attrs.directives.get(FMAttributes.link_caption, "num") # | title | all | none
		retain_block = attrs.directives.get(FMAttributes.retain_block, "none") # | comment | indent
		process_mode = attrs.directives.get(FMAttributes.process_mode, "transform") # | incept
		
		incept = (process_mode == "incept")
		incept_span = f'<span class="{FMAttributes.shared_class} highlight">'
		
		# Process any embedded figure-marking spans.
		last_span_end = 0
		span_match = span_pattern_obj.search(processed_block, last_span_end)
		while span_match:
			processed_span = ""
			bracketed_text = span_match.group(1) if span_match.group(1) else ""
			if span_match.group(3):
				# Reference number without bracketed span.
				ref_num = span_match.group(3)
				if incept:
					processed_span = f'<span class="{FMAttributes.shared_class} reference reference-{ref_num}">{{</span>{span_match.group(3)}<span class="{FMAttributes.shared_class} reference reference-{ref_num}">}}</span>'
				else:
					processed_span = f'<span class="{FMAttributes.shared_class} reference reference-{ref_num}">{ref_num}</span>'
				
			elif span_match.group(2) and span_match.group(2) in marks_map:
				# Known directive span.
				css_class = marks_map[span_match.group(2)]
				if incept:
					processed_span = f'<span class="{FMAttributes.shared_class} {css_class}">[</span>{bracketed_text}<span class="{FMAttributes.shared_class} {css_class}">]{{</span>{span_match.group(2)}<span class="{FMAttributes.shared_class} {css_class}">}}</span>'
				else:
					processed_span = f'<span class="{FMAttributes.shared_class} {css_class}">{bracketed_text}</span>'
				
			elif span_match.group(2):
				# Parse as an attribute list.
				span_attrs = FMAttributes(span_match.group(2))
				span_attrs.classes.append(FMAttributes.attributed_class)
				if incept:
					processed_span = f'<span{span_attrs}>[</span>{bracketed_text}<span{span_attrs}>]{{</span>{span_match.group(2)}<span{span_attrs}>}}</span>'
				else:
					processed_span = f'<span{span_attrs}>{bracketed_text}</span>'
				
			elif span_match.group(5):
				# Implicit span.
				if span_match.group(5) in marks_map:
					# Known directive.
					css_class = marks_map[span_match.group(5)]
					if incept:
						implicit_attrs = FMAttributes()
						implicit_attrs.classes.append(FMAttributes.implicit_class)
						processed_span = f'<span{implicit_attrs}>{span_match.group(4)}</span><span class="{FMAttributes.shared_class} {css_class}">{{</span>{span_match.group(5)}<span class="{FMAttributes.shared_class} {css_class}">}}</span>'
					else:
						processed_span = f'<span class="{FMAttributes.shared_class} {css_class} {FMAttributes.implicit_class}">{span_match.group(4)}</span>'
				else:
					# Parse as an attribute list.
					span_attrs = FMAttributes(span_match.group(5))
					span_attrs.classes.append(FMAttributes.attributed_class)
					if incept:
						implicit_attrs = FMAttributes()
						implicit_attrs.classes.append(FMAttributes.implicit_class)
						processed_span = f'<span{implicit_attrs}>{span_match.group(4)}</span><span{span_attrs}>{{</span>{span_match.group(5)}<span{span_attrs}>}}</span>'
					else:
						span_attrs.classes.append(FMAttributes.implicit_class)
						processed_span = f'<span{span_attrs}>{span_match.group(4)}</span>'
			
			last_span_end = span_match.start() + len(processed_span)
			processed_block = processed_block[:span_match.start()] + processed_span + processed_block[span_match.end():]
			span_match = span_pattern_obj.search(processed_block, last_span_end)
		
		# Handle incepted block delimiters.
		if incept:
			attrs.classes.append(process_mode)
			block_lines = block_match[0].splitlines()
			block_start_line = block_lines[0]
			block_end_line = block_lines[-1]
			
			# The group block_match[2] is the title, and [3] is the attributes. Both are optional.
			offset = block_match.start(0) # match indices are within the text as a whole.
			whitespace = " \t"
			incept_start = ""
			if block_title and block_attributes:
				incept_start = f"{incept_span}{block_start_line[:block_match.start(2)-offset]}</span>{block_start_line[block_match.start(2)-offset:block_match.start(3)-offset-1]}{incept_span}{block_start_line[block_match.start(3)-offset-1:block_match.end(3)-offset+1]}</span>{block_start_line[block_match.end(3)-offset+1:]}"
			elif block_title and not block_attributes:
				incept_start = f"{incept_span}{block_start_line[:block_match.start(2)-offset]}</span>{block_start_line[block_match.start(2)-offset:]}"
			elif not block_title and block_attributes:
				start_stripped = block_start_line[:block_match.start(3)-offset-1].rstrip(whitespace)
				incept_start = f"{incept_span}{start_stripped}</span>{block_start_line[len(start_stripped):block_match.start(3)-offset-1]}{incept_span}{block_start_line[block_match.start(3)-offset-1:block_match.end(3)-offset+1]}</span>{block_start_line[block_match.end(3)-offset+1:]}"
			else:
				start_stripped = block_start_line.rstrip(whitespace)
				incept_start = f"{incept_span}{start_stripped}</span>{block_start_line[len(start_stripped):]}"
			
			end_stripped = block_end_line.rstrip(whitespace)
			incept_end = f"{incept_span}{end_stripped}</span>{block_end_line[len(end_stripped):]}"
			no_html = re.sub(r"<.*?>", "", f"{incept_start}\n{processed_block}\n{incept_end}")
			if block_match[0] != no_html:
				print("Warning: imperfect inception (delta {len(no_html) - len(block_match[0])}). Please report this as a bug!")
				#print(f"\n\n##### Original:\n{block_match[0]}\n##### Processed:\n{incept_start}\n{processed_block}\n{incept_end}\n##### Tag-stripped:\n{no_html}\n#####")
				print(f"\n\n##### Original:\n{block_match[0]}\n##### Tag-stripped:\n{no_html}\n#####")
			
			# Trim out the incept directive for display purposes.
			directive_pattern = f":{FMAttributes.process_mode}=['\"]?{process_mode}['\"]?"
			trim_pattern = rf"\s+{directive_pattern}|{directive_pattern}\s+|{directive_pattern}"
			trimmed_incept_start = re.sub(trim_pattern, "", incept_start)
			trimmed_incept_start = re.sub(rf"\s*{incept_span}{{\s*}}</span>\s*", "", trimmed_incept_start) # in case we've trimmed out the only attribute.
			processed_block = f"{trimmed_incept_start}\n{processed_block}\n{incept_end}"
		
		# Add line-spans.
		processed_lines = ""
		line_span = f'<span class="{FMAttributes.shared_class} line">'
		for line in processed_block.splitlines():
			processed_lines = f"{processed_lines}{line_span}{line}</span>\n"
		processed_block = processed_lines
		
		# Remove escaping backslashes from brackets and braces (and from literal backslashes).
		processed_block = re.sub(r"(?<!\\)\\([\[\]\{\}\\])", r"\1", processed_block)
		processed_block = f"<div class=\"figure-content\">{processed_block}</div>"
		
		# Assemble a suitable pre-formatted figure block.
		if block_title != "" or empty_captions:
			link_tag = f"<a href=\"#{attrs.tag_id}\">"
			caption_string = f"<figcaption><span class=\"figure-number\">{link_tag}{fig_num_format}</a></span><span class=\"figure-title\">{block_title}</span></figcaption>"
			if link_caption == "title":
				caption_string = f"<figcaption><span class=\"figure-number\">{fig_num_format}</span><span class=\"figure-title\">{link_tag}{block_title}</a></span></figcaption>"
			elif link_caption == "all":
				caption_string = f"<figcaption>{link_tag}<span class=\"figure-number\">{fig_num_format}</span><span class=\"figure-title\">{block_title}</span></a></figcaption>"
			elif link_caption == "none":
				caption_string = f"<figcaption><span class=\"figure-number\">{fig_num_format}</span><span class=\"figure-title\">{block_title}</span></figcaption>"
			
			if caption_before:
				processed_block = f"{caption_string}\n{processed_block}"
			else:
				processed_block = f"{processed_block}\n{caption_string}"
				
		processed_block = f"<figure{attrs}>{processed_block}</figure>"
		
		if retain_block == "comment":
			processed_block = f"<!--\n{block_match[0]}\n-->\n\n{processed_block}"
		elif retain_block == "indent":
			processed_block = f"{'\t'.join(('\t'+block_match[0].lstrip()).splitlines(True))}\n\n{processed_block}"
		
		last_fig_end = block_match.start() + len(processed_block) - pre_match_delta
		text = pre_match_text + processed_block + text[block_match.end():]
		figs_processed += 1
		block_match = block_pattern_obj.search(text, last_fig_end)
	
	if figs_processed > 0:
		print(f"Processed {figs_processed} FigureMark blocks.")
	else:
		print(f"No FigureMark blocks found.")
	
	return text
