# FigureMark, by Matt Gemmell ~ https://mattgemmell.scot/figuremark
# Jekyll plugin. Install: _plugins/figuremark.rb

# Set figuremark: true in a post/page's YAML front-matter to enable processing.
# You can also set figuremark: true in your site's _config.yml file to enable it globally.

require 'set'

class FMAttributes
  # Directives
  FIG_NUM_FORMAT = "fig-num-format"
  EMPTY_CAPTIONS = "empty-captions"
  CAPTION_BEFORE = "caption-before"
  LINK_CAPTION = "link-caption"
  RETAIN_BLOCK = "retain-block"
  PROCESS_MODE = "process-mode"

  KNOWN_DIRECTIVES = Set[
    FIG_NUM_FORMAT,
    EMPTY_CAPTIONS,
    CAPTION_BEFORE,
    LINK_CAPTION,
    RETAIN_BLOCK,
    PROCESS_MODE
  ]

  # Magic
  SHARED_CLASS = "figuremark"
  ATTRIBUTED_CLASS = "attributed"
  IMPLICIT_CLASS = "implicit"
  DIRECTIVE_PREFIX = ":"
  REMOVE_TOKEN = "-#{DIRECTIVE_PREFIX}"

  attr_accessor :tag_id, :classes, :tag_attrs, :directives

  def initialize(raw_string = nil)
    @tag_id = nil
    @classes = [SHARED_CLASS]
    @tag_attrs = {}
    @directives = {}

    if raw_string
      pattern = /([.#][\w:-]+|[\w:-]+=(?:"[^"]*"|'[^']*'|[^\s]*)|[\w\-\.]+)/
      raw_string.scan(pattern).each do |match|
        item = match[0]
        if item.start_with?('.') && !@classes.include?(item[1..-1])
          @classes << item[1..-1]
        elsif item.start_with?('#')
          @tag_id = item[1..-1]
        elsif item.include?('=')
          key, val = item.split('=', 2)
          val = val || ""
          dest = @tag_attrs
          this_key = key
          if key.start_with?(DIRECTIVE_PREFIX)
            dest = @directives
            this_key = this_key[DIRECTIVE_PREFIX.size..-1]
            unless KNOWN_DIRECTIVES.include?(this_key)
              warn "Warning: Unknown directive '#{DIRECTIVE_PREFIX}#{this_key}'. Ignoring."
              next
            end
          end
          dest[this_key] = val.gsub(/\A['"]|['"]\z/, "")
        else
          item.split('.').each do |this_class|
            @classes << this_class unless @classes.include?(this_class)
          end
        end
      end
    end
  end

  def to_s
    attr_str = ""
    attr_str += %Q{ id="#{@tag_id}"} if @tag_id
    attr_str += %Q{ class="#{@classes.join(' ')}"} if @classes.length > 0
    @tag_attrs.each { |k, v| attr_str += %Q{ #{k}="#{v}"} }
    attr_str
  end

  def update(new_attrs)
    if new_attrs.tag_id && new_attrs.tag_id.start_with?(REMOVE_TOKEN)
      if @tag_id == new_attrs.tag_id[REMOVE_TOKEN.size..-1] || new_attrs.tag_id == REMOVE_TOKEN
        @tag_id = nil
      end
    elsif new_attrs.tag_id
      @tag_id = new_attrs.tag_id
    end

    new_attrs.classes.each do |new_class|
      if new_class == REMOVE_TOKEN
        @classes.clear
      elsif new_class.start_with?(REMOVE_TOKEN)
        target = new_class[REMOVE_TOKEN.size..-1]
        @classes.delete(target)
      elsif !@classes.include?(new_class)
        @classes << new_class
      end
    end

    new_attrs.tag_attrs.each do |k, v|
      if v == REMOVE_TOKEN
        @tag_attrs.delete(k)
      elsif k == REMOVE_TOKEN
        @tag_attrs.clear
      else
        @tag_attrs[k] = v
      end
    end

    new_attrs.directives.each do |k, v|
      if v == REMOVE_TOKEN
        @directives.delete(k)
      elsif k == REMOVE_TOKEN
        @directives.clear
      else
        @directives[k] = v
      end
    end
  end

  def incorporate(new_attrs)
    @tag_id ||= new_attrs.tag_id

    new_attrs.classes.each do |new_class|
      @classes << new_class unless @classes.include?(new_class)
    end

    temp = new_attrs.tag_attrs.dup
    temp.merge!(@tag_attrs)
    @tag_attrs = temp

    temp2 = new_attrs.directives.dup
    temp2.merge!(@directives)
    @directives = temp2
  end
end


Jekyll::Hooks.register [:documents, :pages], :pre_render do |doc|
  # Only process Markdown files.
  ext = doc.respond_to?(:extname) ? doc.extname : File.extname(doc.relative_path)
  next unless ext == '.md' || ext == '.markdown'
	
	proceed = true
	if doc.data.key?('figuremark')
		proceed = (doc.data['figuremark'] == true)
	else
		proceed = (doc.site.config['figuremark'] == true)
	end
	next unless proceed
	
		def convert(doc)
		text = doc.content
		
		fm_globals_pattern = /^(?:\{figure(?:mark)?\s*([^\}]*)\})\s*?$/mi
		figure_block_pattern = /(?<!<!--\n)^(`{3,}|~{3,})\s*figure(?:mark)?(\s+[^\{]+?)?\s*(?:\{([^\}]*?)\})?\s*$\n([\s\S\n]*?)\n\1\s*?$/mi
		figure_span_pattern = /(?<!\\)\[(.+?)(?<!\\)\]\{([^\}]+?)\}|\{([\d.-]+)\}|(\S+)\{([^\}]+)\}/
	
		marks_map = {
			"+" => "insert",
			"-" => "remove",
			"/" => "comment",
			">" => "result",
			"!" => "highlight"
		}
		figure_number = 0
		figs_processed = 0
		block_pattern_obj = figure_block_pattern
		span_pattern_obj = figure_span_pattern
		last_fig_end = 0
		global_attrs = FMAttributes.new
	
		text = text.dup
	
		block_match = block_pattern_obj.match(text, last_fig_end)
		while block_match
			block_title = block_match[2] ? block_match[2].strip : ""
			block_attributes = block_match[3]
			processed_block = block_match[4]
	
			other_figures = text[last_fig_end...block_match.begin(0)].to_s.scan(/<figure[^>]*>.+?<\/figure>/m)
			figure_number += other_figures.length
			figure_number += 1
	
			attrs = FMAttributes.new(block_attributes)
			attrs.tag_id ||= "figure-#{figure_number}"
			attrs.tag_attrs['data-fignum'] = figure_number.to_s
	
			pre_match_text = text[0...block_match.begin(0)]
			pre_match_orig_len = pre_match_text.length
			globals_matches = []
	
			pre_match_text.scan(fm_globals_pattern) do |gm|
				globals_matches << Regexp.last_match
				global_attrs.update(FMAttributes.new(gm[0]))
			end
	
			globals_matches.reverse.each do |gm|
				pre_match_text = pre_match_text[0...gm.begin(0)] + pre_match_text[gm.end(0)..-1]
			end
	
			pre_match_delta = pre_match_orig_len - pre_match_text.length
	
			attrs.incorporate(global_attrs)
	
			fig_num_format = (attrs.directives[FMAttributes::FIG_NUM_FORMAT] || "Fig. #").gsub("#", figure_number.to_s)
			empty_captions = (attrs.directives.fetch(FMAttributes::EMPTY_CAPTIONS, "true") == "true")
			caption_before = (attrs.directives.fetch(FMAttributes::CAPTION_BEFORE, "true") == "true")
			link_caption = attrs.directives[FMAttributes::LINK_CAPTION] || "num"
			retain_block = attrs.directives[FMAttributes::RETAIN_BLOCK] || "none"
			process_mode = attrs.directives[FMAttributes::PROCESS_MODE] || "transform"
	
			incept = (process_mode == "incept")
			incept_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} highlight">}
	
			last_span_end = 0
			span_match = span_pattern_obj.match(processed_block, last_span_end)
			while span_match
				processed_span = ""
				bracketed_text = span_match[1] || ""
				if span_match[3]
					ref_num = span_match[3]
					if incept
						processed_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} reference reference-#{ref_num}">{</span>#{ref_num}<span class="#{FMAttributes::SHARED_CLASS} reference reference-#{ref_num}">}</span>}
					else
						processed_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} reference reference-#{ref_num}">#{ref_num}</span>}
					end
				elsif span_match[2] && marks_map[span_match[2]]
					css_class = marks_map[span_match[2]]
					if incept
						processed_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} #{css_class}">[</span>#{bracketed_text}<span class="#{FMAttributes::SHARED_CLASS} #{css_class}">]{</span>#{span_match[2]}<span class="#{FMAttributes::SHARED_CLASS} #{css_class}">}</span>}
					else
						processed_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} #{css_class}">#{bracketed_text}</span>}
					end
				elsif span_match[2]
					span_attrs = FMAttributes.new(span_match[2])
					span_attrs.classes << FMAttributes::ATTRIBUTED_CLASS
					if incept
						processed_span = %Q{<span#{span_attrs}>[</span>#{bracketed_text}<span#{span_attrs}>]{</span>#{span_match[2]}<span#{span_attrs}>}</span>}
					else
						processed_span = %Q{<span#{span_attrs}>#{bracketed_text}</span>}
					end
				elsif span_match[5]
					# Implicit span.
					if marks_map[span_match[5]]
						# Known directive.
						css_class = marks_map[span_match[5]]
						if incept
							implicit_attrs = FMAttributes.new()
							implicit_attrs.classes << FMAttributes::IMPLICIT_CLASS
							processed_span = %Q{<span#{implicit_attrs}>#{span_match[4]}</span><span class="#{FMAttributes::SHARED_CLASS} #{css_class}">{</span>#{span_match[5]}<span class="#{FMAttributes::SHARED_CLASS} #{css_class}">}</span>}
						else
							processed_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} #{css_class} #{FMAttributes::IMPLICIT_CLASS}">#{span_match[4]}</span>}
						end
					else
						# Parse as an attribute list.
						span_attrs = FMAttributes.new(span_match[5])
						span_attrs.classes << FMAttributes::ATTRIBUTED_CLASS
						if incept
							implicit_attrs = FMAttributes.new()
							implicit_attrs.classes << FMAttributes::IMPLICIT_CLASS
							processed_span = %Q{<span#{implicit_attrs}>#{span_match[4]}</span><span#{span_attrs}>{</span>#{span_match[5]}<span#{span_attrs}>}</span>}
						else
							span_attrs.classes << FMAttributes::IMPLICIT_CLASS
							processed_span = %Q{<span#{span_attrs}>#{span_match[4]}</span>}
						end
					end
				end
				processed_block = processed_block[0...span_match.begin(0)] + processed_span + processed_block[span_match.end(0)..-1]
				last_span_end = span_match.begin(0) + processed_span.length
				span_match = span_pattern_obj.match(processed_block, last_span_end)
			end
	
			if incept
				attrs.classes << process_mode
				block_lines = block_match[0].lines
				block_start_line = block_lines[0] || ""
				block_end_line = block_lines[-1] || ""
				block_start_line.chomp!
				block_end_line.chomp!
	
				offset = block_match.begin(0)
				incept_start = ""
				if !block_title.empty? && block_attributes
					incept_start = "#{incept_span}#{block_start_line[0...block_match.begin(2)-offset]}</span>#{block_start_line[block_match.begin(2)-offset...block_match.begin(3)-offset-1]}#{incept_span}#{block_start_line[block_match.begin(3)-offset-1...block_match.end(3)-offset+1]}</span>#{block_start_line[block_match.end(3)-offset+1..-1]}"
				elsif !block_title.empty?
					incept_start = "#{incept_span}#{block_start_line[0...block_match.begin(2)-offset]}</span>#{block_start_line[block_match.begin(2)-offset..-1]}"
				elsif block_attributes
					start_stripped = block_start_line[0...block_match.begin(3)-offset-1].rstrip
					incept_start = "#{incept_span}#{start_stripped}</span>#{block_start_line[start_stripped.length...block_match.begin(3)-offset-1]}#{incept_span}#{block_start_line[block_match.begin(3)-offset-1...block_match.end(3)-offset+1]}</span>#{block_start_line[block_match.end(3)-offset+1..-1]}"
				else
					start_stripped = block_start_line.rstrip
					incept_start = "#{incept_span}#{start_stripped}</span>#{block_start_line[start_stripped.length..-1]}"
				end
				
				end_stripped = block_end_line.rstrip
				incept_end = "#{incept_span}#{end_stripped}</span>#{block_end_line[end_stripped.length..-1]}"
				no_html = "#{incept_start}\n#{processed_block}\n#{incept_end}".gsub(/<.*?>/, "")
				if block_match[0] != no_html
					warn "Warning: imperfect inception (delta #{no_html.length - block_match[0].length}). Please report this as a bug!"
					#warn "\n\n##### Original:\n#{block_match[0]}\n##### Processed:\n#{incept_start}\n#{processed_block}\n#{incept_end}\n##### Tag-stripped:\n#{no_html}\n#####"
					warn "\n\n##### Original:\n#{block_match[0]}\n##### Tag-stripped:\n#{no_html}\n#####"
				end
	
				directive_pattern = %Q{:#{FMAttributes::PROCESS_MODE}=['"]?#{process_mode}['"]?}
				trim_pattern = /(\s+#{directive_pattern}|#{directive_pattern}\s+|#{directive_pattern})/
				trimmed_incept_start = incept_start.gsub(trim_pattern, "")
				trimmed_incept_start = trimmed_incept_start.gsub(/\s*#{incept_span}{\s*}<\/span>\s*/, "")
				processed_block = "#{trimmed_incept_start}\n#{processed_block}\n#{incept_end}"
			end
	
			processed_lines = ""
			line_span = %Q{<span class="#{FMAttributes::SHARED_CLASS} line">}
			processed_block.each_line do |line|
				processed_lines += "#{line_span}#{line.chomp}</span>\n"
			end
			processed_block = processed_lines
	
			processed_block = processed_block.gsub(/(?<!\\)\\([\[\]\{\}\\])/, '\1')
			processed_block = %Q{<div class="figure-content">#{processed_block}</div>}
	
			if !block_title.empty? || empty_captions
				link_tag = %Q{<a href="##{attrs.tag_id}">}
				caption_string = %Q{<figcaption><span class="figure-number">#{link_tag}#{fig_num_format}</a></span><span class="figure-title">#{block_title}</span></figcaption>}
				if link_caption == "title"
					caption_string = %Q{<figcaption><span class="figure-number">#{fig_num_format}</span><span class="figure-title">#{link_tag}#{block_title}</a></span></figcaption>}
				elsif link_caption == "all"
					caption_string = %Q{<figcaption>#{link_tag}<span class="figure-number">#{fig_num_format}</span><span class="figure-title">#{block_title}</span></a></figcaption>}
				elsif link_caption == "none"
					caption_string = %Q{<figcaption><span class="figure-number">#{fig_num_format}</span><span class="figure-title">#{block_title}</span></figcaption>}
				end
	
				if caption_before
					processed_block = "#{caption_string}\n#{processed_block}"
				else
					processed_block = "#{processed_block}\n#{caption_string}"
				end
			end
	
			processed_block = %Q{<figure#{attrs}>#{processed_block}</figure>}
	
			if retain_block == "comment"
				processed_block = "<!--\n#{block_match[0]}\n-->\n\n#{processed_block}"
			elsif retain_block == "indent"
				processed_block = block_match[0].lstrip.lines.map { |l| "\t#{l}" }.join + "\n\n#{processed_block}"
			end
	
			last_fig_end = block_match.begin(0) + processed_block.length - pre_match_delta
			text = pre_match_text + processed_block + text[block_match.end(0)..-1]
			figs_processed += 1
			block_match = block_pattern_obj.match(text, last_fig_end)
		end
	
		if figs_processed > 0
			puts "Processed #{figs_processed} FigureMark blocks in \"#{doc.data['title']}\" (#{doc.path})."
		else
			#puts "No FigureMark blocks found in \"#{doc.data['title']}\" (#{doc.path})."
		end
	
		text
	end
	
	doc.content = convert(doc)
end
