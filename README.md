# FigureMark

This is [the repository for **FigureMark**](https://github.com/mattgemmell/FigureMark), a simple syntax for marking up _figures_ in Markdown documents (i.e. HTML `<figure>` blocks). Its purpose is to help with formatting explanatory content online and in digital and printed books. It was created by [Matt Gemmell](https://mattgemmell.scot), and is made available under the [GPL-3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).

Since github doesn't allow the use of custom CSS in hosted README files like this one, please **[read the FigureMark documentation here](https://mattgemmell.scot/figuremark)** for illustrated examples, syntax, etc.

Feature requests, bug reports, and general discussion are welcomed; you can [find my contact details here](https://mattgemmell.scot/contact/).


## Purpose

While working on my [pandoc-based Markdown publishing system](https://github.com/mattgemmell/pandoc-publish), it seemed to me that when writing non-fiction content, there was no accessible way to mark-up content for the purpose of explanation, examination, and education. It's often necessary to show something technical or detailed, and to annotate such material with clarifying or didactic decorations.

Syntax-highlighting systems are ubiquitous, but they apply only to code listings and certain related textual data, and they use the _mechanics_ of the language, rather than _explaining_ or _focusing_ on the content. Manual tagging with HTML and CSS is of course possible, but is tedious and lacks automation.

My aim was to provide an 80% solution, allowing the annotation of a document's figures in a semantic shorthand which is easily parsed and extended, with some functional conveniences included. The result is FigureMark.

FigureMark is intended to be useful in the creation of non-fiction works, particularly those on technical matters, such as learning a programming language, discussing complex concepts which benefit from detailed examples, and so on. Its focus is on simplicity, and meeting a set of common needs without complexity, at the expense of comprehensiveness.

Note in particular that while FigureMark is very useful for annotating code samples, it is equally intended for use in textual analysis of prose and poetry, discussing quotations, illustrating concepts, and much more. Its semantics are intentionally loose and extensible, and the user is encouraged to adapt it to their needs.

See [the documentation](https://mattgemmell.scot/figuremark) for more.
