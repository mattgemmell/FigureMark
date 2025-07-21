
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
	incept_block = "incept-block"
	associative_spans = "associative-spans"
	numeric_ids = "numeric-ids"
	mark_types = "mark-types"
	encode_html = "encode-html"
	
	known_directives = {
		fig_num_format,
		empty_captions,
		caption_before,
		link_caption,
		retain_block,
		process_mode,
		incept_block,
		associative_spans,
		numeric_ids,
		mark_types,
		encode_html
	}
	
	# Magic
	shared_class = "figuremark"
	attributed_class = "attributed"
	implicit_class = "implicit"
	incepted_wrapper_class = "incepted-mark"
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
					val = val.strip('"\'')
					if dest == self.directives and this_key == FMAttributes.mark_types:
						if not FMAttributes.mark_types in self.directives:
							self.directives[FMAttributes.mark_types] = {}
						# Split value into marks with class-lists.
						these_marks = val.split(",")
						for this_mark in these_marks:
							if this_mark != FMAttributes.remove_token:
								the_mark, _, the_classes_str = this_mark.partition(FMAttributes.directive_prefix)
								if not the_mark in self.directives[FMAttributes.mark_types]:
									self.directives[FMAttributes.mark_types][the_mark] = []
								for the_class in the_classes_str.split("."):
									if not the_class in self.directives[FMAttributes.mark_types][the_mark]:
										self.directives[FMAttributes.mark_types][the_mark].append(the_class)
							else:
								if not this_mark in self.directives[FMAttributes.mark_types]:
									self.directives[FMAttributes.mark_types] = {}
					else:
						dest[this_key] = val
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


def display_encode(text):
	text = re.sub('(?<!{)>', '&gt;', text)
	return text.replace('<', '&lt;')


def display_decode(text):
	return text.replace('&lt;', '<').replace('&gt;', '>')


def string_to_slug(text):
		# Remove non-alphanumeric characters
    text = re.sub(r'\W+', ' ', text)
		
    # Replace whitespace runs with single hyphens
    text = re.sub(r'\s+', '-', text)
		
    # Remove leading and trailing hyphens
    text = text.strip('-')
		
    # Return in lowercase
    return text.lower()


def convert(text):
	fm_globals_pattern = r"(?mi)^(?:\{figure(?:mark)?\s*([^\}]*)\})\s*?$"
	figure_block_pattern = r"(?mi)(?<!<!--\n)^(`{3,}|~{3,})\s*figure(?:mark)?(\s+[^\{]+?)?\s*(?:\{([^\}]*?)\})?\s*$\n([\s\S\n]*?)\n\1\s*?$"
	figure_span_pattern = r"(?<!\\)\[(.+?)(?<!\\)\]\{([^\}<]+?)\}|\{(\d[\d.-]*)\}|([^\s\[\{]+)\{([^\d\}\]<]+)\}"
	associative_pattern = r"((&lt;.*?&gt;|\(.*?\)|‘.*?’|“.*?”|\\\[.*?\\\]|\{.*?\})|([^\w\s\]\}\\])(.*?)\8)\{([^\}<]+)\}" # must be |-appended to figure_span_pattern
	
	marks_map = {	"+": "insert",
								"-": "remove",
								"/": "comment",
								">": "result",
								"!": "highlight"}
	figure_number = 0
	figs_processed = 0
	block_pattern_obj = re.compile(figure_block_pattern)
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
		incept_block = attrs.directives.get(FMAttributes.incept_block, "content") # | all
		associative_spans = (attrs.directives.get(FMAttributes.associative_spans, "true") == "true")
		numeric_ids = (attrs.directives.get(FMAttributes.numeric_ids, "false") == "true")
		mark_types = attrs.directives.get(FMAttributes.mark_types, {})
		encode_html = (attrs.directives.get(FMAttributes.encode_html, "true") == "true")
		
		if not attrs.tag_id:
			# ID not specified either globally or as a local override. Use defaults.
			if not numeric_ids and block_title:
				attrs.tag_id = string_to_slug(block_title)
			else:
				attrs.tag_id = f"figure-{figure_number}"
		
		incept = (process_mode == "incept")
		incept_span = f'<span class="{FMAttributes.shared_class} highlight">'
		
		if incept or encode_html:
			processed_block = display_encode(processed_block)
		
		if associative_spans:
			figure_span_pattern += r'|' + associative_pattern
		span_pattern_obj = re.compile(figure_span_pattern)
		
		# Process any embedded figure-marking spans.
		last_span_end = 0
		span_match = span_pattern_obj.search(processed_block, last_span_end)
		implicit_attrs = FMAttributes()
		implicit_attrs.classes.append(FMAttributes.implicit_class)
		incepted_wrapper_attrs = FMAttributes()
		incepted_wrapper_attrs.classes.append(FMAttributes.incepted_wrapper_class)
		
		while span_match:
			processed_span = ""
			bracketed_text = span_match.group(1) if span_match.group(1) else ""
			if span_match.group(3):
				# Reference number without bracketed span.
				ref_num = span_match.group(3)
				if incept:
					processed_span = f'<span{incepted_wrapper_attrs}><span class="{FMAttributes.shared_class} reference reference-{ref_num}">{{{span_match.group(3)}}}</span></span>'
				else:
					processed_span = f'<span class="{FMAttributes.shared_class} reference reference-{ref_num}">{ref_num}</span>'
				
			elif span_match.group(2) and (span_match.group(2) in mark_types or span_match.group(2) in marks_map):
				# Known directive span.
				css_class = None
				if span_match.group(2) in mark_types:
					css_class = " ".join(mark_types[span_match.group(2)])
				else:
					css_class = marks_map[span_match.group(2)]
				
				if incept:
					processed_span = f'<span{incepted_wrapper_attrs}><span class="{FMAttributes.shared_class} {css_class}">[</span><span{implicit_attrs}>{bracketed_text}</span><span class="{FMAttributes.shared_class} {css_class}">]{{{span_match.group(2)}}}</span></span>'
				else:
					processed_span = f'<span class="{FMAttributes.shared_class} {css_class}">{bracketed_text}</span>'
				
			elif span_match.group(2):
				# Parse as an attribute list.
				span_attrs = FMAttributes(span_match.group(2))
				span_attrs.classes.append(FMAttributes.attributed_class)
				if incept:
					processed_span = f'<span{incepted_wrapper_attrs}><span{span_attrs}>[</span><lMspan{implicit_attrs}>{bracketed_text}</span><span{span_attrs}>]{{{span_match.group(2)}}}</span></span>'
				else:
					processed_span = f'<span{span_attrs}>{bracketed_text}</span>'
				
			elif span_match.group(5) or (associative_spans and span_match.group(10)):
				# Implicit or implicit-associative span.
				mark_type = span_match.group(5)
				mark_text = span_match.group(4)
				if associative_spans and span_match.group(10):
					mark_type = span_match.group(10)
					mark_text = span_match.group(6)
				
				if mark_type in mark_types or mark_type in marks_map:
					# Known directive.
					css_class = None
					if mark_type in mark_types:
						css_class = " ".join(mark_types[mark_type])
					else:
						css_class = marks_map[mark_type]
					
					if incept:
						processed_span = f'<span{incepted_wrapper_attrs}><span{implicit_attrs}>{mark_text}</span><span class="{FMAttributes.shared_class} {css_class}">{{{mark_type}}}</span></span>'
					else:
						processed_span = f'<span class="{FMAttributes.shared_class} {css_class} {FMAttributes.implicit_class}">{mark_text}</span>'
				else:
					# Parse as an attribute list.
					span_attrs = FMAttributes(mark_type)
					span_attrs.classes.append(FMAttributes.attributed_class)
					if incept:
						processed_span = f'<span{incepted_wrapper_attrs}><span{implicit_attrs}>{mark_text}</span><span{span_attrs}>{{{mark_type}}}</span></span>'
					else:
						span_attrs.classes.append(FMAttributes.implicit_class)
						processed_span = f'<span{span_attrs}>{mark_text}</span>'
			
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
			no_html = display_decode(no_html)
			if block_match[0] != no_html:
				print(f"Warning: imperfect inception (delta {len(no_html) - len(block_match[0])}). Please report this as a bug!")
				#print(f"\n\n##### Original:\n{block_match[0]}\n##### Processed:\n{incept_start}\n{processed_block}\n{incept_end}\n##### Tag-stripped:\n{no_html}\n#####")
				print(f"\n\n##### Original:\n{block_match[0]}\n##### Tag-stripped:\n{no_html}\n#####")
			
			# Trim out the incept directive for display purposes.
			directive_pattern = f":{FMAttributes.process_mode}=['\"]?{process_mode}['\"]?"
			trim_pattern = rf"\s+{directive_pattern}|{directive_pattern}\s+|{directive_pattern}"
			trimmed_incept_start = re.sub(trim_pattern, "", incept_start)
			directive_pattern = f":{FMAttributes.incept_block}=['\"]?\\w+['\"]?"
			trim_pattern = rf"\s+{directive_pattern}|{directive_pattern}\s+|{directive_pattern}"
			trimmed_incept_start = re.sub(trim_pattern, "", trimmed_incept_start)
			trimmed_incept_start = re.sub(rf"\s*{incept_span}{{\s*}}</span>\s*", "", trimmed_incept_start) # in case we've trimmed out all attributes.
			if incept_block == "all":
				processed_block = f"{trimmed_incept_start}\n{processed_block}\n{incept_end}"
		
		# Add line-spans.
		processed_lines = ""
		line_span = f'<span class="{FMAttributes.shared_class} line">'
		for line in processed_block.splitlines():
			processed_lines = f"{processed_lines}{line_span}{line}</span>\n"
		processed_block = processed_lines
		
		# Remove escaping backslashes from brackets and braces (and from literal backslashes).
		processed_block = re.sub(r"(?<!\\)\\([\[\]\{\}\\])", r"\1", processed_block)
		if not incept and not encode_html:
			processed_block = display_decode(processed_block)
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
