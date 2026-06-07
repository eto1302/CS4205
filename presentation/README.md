# TU Delft Style Dissertation template

Template for a PhD thesis following the [TU Delft corporate design](https://www.tudelft.nl/en/tu-delft-corporate-design), using the font family [Roboto Slab](https://fonts.google.com/specimen/Roboto+Slab) and [Arial](https://en.wikipedia.org/wiki/Arial) or alternatively using the LaTeX package '[Fourier](https://ctan.org/pkg/fourier)'.

The template extends and updates the dissertation template by [K.P. Hart](https://www.overleaf.com/latex/templates/tud-dissertation/tcddkjggskqx) and Wouter Bolsterlee.

The source files can be found on [Gitlab](https://gitlab.com/novanext/tudelft-dissertation). It is designed to work with LuaLaTeX and PdfLaTeX (faster but less features and less fancy font support).
On the Gitlab site more information can be found on using LaTeX and this template outside of Overleaf.

This version was created from Git commit e8542d3 on 2026-05-13.

## Fonts

The fonts can either be:

- Fourier; a more classic look:
  http://mirrors.ctan.org/fonts/fourier-GUT/doc/fourier-doc-en.pdf
- Arial (or Roboto) combined with RobotoSlab
  This combination fits the TUD corporate style:
  https://www.tudelft.nl/huisstijl/

This can be set by either adding or removing the class option `fourier'.
Fourier has a more classic look, while the moderner look of Roboto fits the TU Delft style guide.

If you use Roboto in LuaLaTeX, you can make use of advanced variable font features

- [Youtube: Amstelvar & Roboto Flex: Unprecedented Flexibility...](https://www.youtube.com/watch?v=K-ruvv6P8sk)
- [Roboto … But Make It Flex](https://m3.material.io/blog/roboto-flex)
- [Exploring typefaces with multiple weights or grades](https://fonts.google.com/knowledge/choosing_type/exploring_typefaces_with_multiple_weights_or_grades)


### Latexmk

`latexmk` is used by Overleaf to determine how the project is to be rendered.
Since we do not want to overrule the compiler set by the user, the line redefining
`pdflatex` is made a comment. An introduction to `latexmk`can be found here:
https://manpages.org/latexmk.

Two VS Code tasks run `latexkm`. 
- `latexmk (all files, once)`  
  builds everything of which `latexmk` can figure out how to do it
- `latexmk (current file, continuous)`  
  only build the pdf based on the file currently open in VS Code, but repeat
  process every time anything changes on which it depends according to `latexmk`.

For further inspiration and more features:
- https://www.overleaf.com/learn/how-to/How_does_Overleaf_compile_my_project%3F

One task runs `latexmk` once, creating `pdf`s from all `tex` files in the directory.
The other one continuously monitors the input file `disseration.tex` and updates `dissertation.pdf` whenever the input file is changed.
