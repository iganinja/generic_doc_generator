# Generic Doc Generator
A very, very simple, generic documentation generator for APIs in just one Python script. It's job is to parse any text file, find some specific tags and generate documentation in html format. I use it in my C++/Lua projects.

For nice html presentation it uses [Bootstrap](http://getbootstrap.com/) and [highlightjs](https://highlightjs.org/)

Generator offers just the following tags:
- `@container`: indicates a class, table or anything which can be modeled as a container
- `@function`: a free function or a method
- `@value`: a constant or a special value maintaned by the infraestructure
- `@description`: an optional small description of the container, function or value
- `@more`: a bigger, optional extended description of the container, function or value
- `@param`: a parameter of a function (it's optional to define or not parameters)
- `@return`: the return value of the function (also optional)
- `[code[` and `]code]`: surround code portions in those tags to get sintax highlighting
- `[[text to show|url]]`: an internal link in the documentation. URL is the name of the container, function or value. For example if we want to point to `Simulation.Entity.collider()` function we write `[[check this link of collider()|Simulation.Entity.collider]]`

Container, function or values tags should be followed by their absolute name in the hierarchy. In the above example we have `Simulation.Entity.collider()`, which means we have the function `collider` inside container `Entity` which is contained in `Simulation`. Its tag would be for example:
```
@function Simulation.Entity.collider() 
@return Returns entity's collider
```
This hierarchy can represent agregation (like in Lua tables, for example) or inheritance like in a OO language.

The word following `@param` tag is assumed to be the parameter's name and it is marked.

Python script expect just the path of the configuration file as command line parameter. This file can have any name and extension, it just must include the following tags:

- `@extensions`: the file extensions which will be parsed, separated by commas
- `@input_path`: base path of the project directory tree to parse
- `@output_path`: path to the output directory: here will be created all the html files where documentation will be written
- `@title`: title of the documentation to be shown in the main page

Optionally it can include `@description` tag, which will be shown below documentation title in the main page

