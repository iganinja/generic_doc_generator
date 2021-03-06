import os
import argparse
import shutil
import re
import glob

comment_ends = dict(h="*/", cpp="*/", lua="]]--")


class DocumentationBlock:
    def __init__(self, type, name, description, more):
        self.type = type
        self.name = name
        self.description = description
        self.more = more

    def just_name(self):
        if "." not in self.name:
            return self.name
        else:
            return self.name[self.name.rfind(".") + 1:]


class FunctionBlock(DocumentationBlock):
    def __init__(self, name, description, more, params_info, return_info):
        DocumentationBlock.__init__(self, "function", name, description, more)
        self.params_info = params_info
        self.return_info = return_info


def get_id_name(name):
    bare_bone_name = ""

    for i in range(len(name.split(" ")[0])):
        if name[i].isalnum() or name[i] == "_":
            bare_bone_name += name[i]
        else:
            break

    return bare_bone_name.lower()


def divide_text_in_paragraphs(text):
    description_parts = text.rstrip().splitlines()

    final_text = ""

    for part in description_parts:
        stripped = part.rstrip()
        if len(stripped) > 0:
            if "[code[" in stripped or "]code]" in stripped:
                final_text += stripped.strip()
            else:
                final_text += "<p>" + stripped + "</p>"

    return final_text


def add_links(html_text, container_names):
    processed_text = html_text
    regular_expression = re.compile("(\[\[.*?\|.*?\]\])")
    link_tags = regular_expression.findall(processed_text)

    if not link_tags:
        return processed_text

    link_html = """<a href='{URL}' style="text-decoration: none;"><code>{TEXT}</code></a>"""

    for link_tag in link_tags:
        link_info = link_tag.replace("[[", "").replace("]]", "")
        link_parts = [part.lower() for part in link_info.split("|")]

        url = ""

        if "." not in link_parts[1]:
            if link_parts[1] in container_names:
                url = "_" + link_parts[1] + "_.html"
            else:
                url = "index.html#" + link_parts[1]
        else:
            url_parts = link_parts[1].split(".")

            for i in range(len(url_parts) - 1):
                url += "_" + url_parts[i]

            if url_parts[-1] in container_names:
                url += "_" + url_parts[-1] + "_.html"
            else:
                url += "_.html#" + url_parts[-1]

        processed_text = processed_text.replace(link_tag, link_html.format(URL=url, TEXT=link_parts[0]))

    return processed_text


def add_code_parts(html_text):
    if "[code[" and "]code]" in html_text:
        return html_text.replace("[code[", "<pre><code>").replace("]code]", "</code></pre>")
    else:
        return html_text.rstrip()


def process_description_text(text, container_names):
    return add_code_parts(add_links(divide_text_in_paragraphs(text), container_names))


def get_tags_name_and_text(block_text):
    valid_lines = []

    for line in block_text.splitlines():
        if not line.startswith("   "):
            line_stripped = line.strip()
        else:
            line_stripped = line

        if len(line_stripped) > 0 and line_stripped[0] != "#":
            valid_lines.append(line_stripped)

    text = "\n".join(valid_lines)

    tags_and_texts = []

    while len(text) > 0:
        index_start = text.find("@")

        if index_start == -1:
            break

        index_end = text.find(" ", index_start)
        tag_name = text[index_start + 1:index_end].rstrip()

        index_start = index_end
        index_end = text.find("@", index_start)

        if index_end == -1:
            index_end = len(text)

        tag_text = text[index_start + 1:index_end].rstrip()

        tags_and_texts.append((tag_name, tag_text))

        text = text[index_end:]

    return tags_and_texts


def create_block(block_text):
    tags_info = dict()

    params_info = []

    for tag_text in get_tags_name_and_text(block_text):
        tag_name = tag_text[0]
        tag_text = tag_text[1]

        if tag_name == "param":
            params_info.append(tag_text)
        else:
            tags_info[tag_name] = tag_text

    description = ""
    if "description" in tags_info.keys():
        description = tags_info["description"]

    more = ""
    if "more" in tags_info.keys():
        more = tags_info["more"]

    if "function" in tags_info.keys():
        return_info = None

        if "return" in tags_info:
            return_info = tags_info["return"]

        return FunctionBlock(tags_info["function"], description, more, params_info, return_info)
    else:
        possible_names = ["container", "value"]

        key_name = None

        for name in possible_names:
            if name in tags_info:
                key_name = name
                break

        if not key_name:
            return None

        return DocumentationBlock(key_name,
                                  tags_info[key_name],
                                  description,
                                  more)


def get_next_block(file_content, comment_end_string):
    tag_index = file_content.find("@")

    if tag_index != -1:
        block_end_index = file_content.find(comment_end_string, tag_index)
        block_text = file_content[tag_index:block_end_index]
        return create_block(block_text), file_content[block_end_index:]
    else:
        return None, file_content


def get_file_documentation_blocks(file_path):
    with open(file_path, "r") as file_handler:
        file_content = file_handler.read()

    document_blocks = []

    comment_end_string = comment_ends[os.path.splitext(file_path)[1][1:]]

    new_doc_block, file_content = get_next_block(file_content, comment_end_string)

    while new_doc_block:
        document_blocks.append(new_doc_block)
        new_doc_block, file_content = get_next_block(file_content, comment_end_string)

    return document_blocks


def create_function_documentation(doc_block):
    function_template = """
        <div class="row alert alert-block alert-info text-justify">
            <div class="col-xs-12">
                <h4>
                    <span class="label label-success" id="{FUNCTION_ID}">
                        {NAME}
                    </span>
                </h4>
                <p>{DESCRIPTION}</p>
                <div>
                    {PARAMS_AND_RETURN}
                </div>
                <p>
                    <div>
                        {MORE}
                    </div>
                </p>
            </div>
        </div>
    """

    parameter_template = """
        <div>
            <span class="label label-default">{NAME}</span><span>{DESCRIPTION}</span>
        </div>
    """

    return_template = """
        <div>
            <span class="label label-primary">Return</span><span>{DESCRIPTION}</span>
        </div>
    """

    params_and_return = ""

    for param_info in doc_block.params_info:
        space_index = param_info.find(" ")
        name = param_info[0:space_index]
        description = param_info[space_index:]
        params_and_return += add_code_parts(divide_text_in_paragraphs(
                parameter_template.format(NAME=name,
                                          DESCRIPTION=description)))

    if doc_block.return_info:
        params_and_return += add_code_parts(
                divide_text_in_paragraphs(
                        return_template.format(DESCRIPTION=" " + doc_block.return_info)))

    return function_template.format(NAME=doc_block.just_name(),
                                    FUNCTION_ID=get_id_name(doc_block.just_name()),
                                    DESCRIPTION=doc_block.description,
                                    PARAMS_AND_RETURN=params_and_return,
                                    MORE=doc_block.more)


def create_value_documentation(doc_block):
    value_template = """
        <div class="row alert alert-block alert-warning">
            <div class="col-xs-12">
                <h4>
                    <span class="label label-success" id="{VALUE_ID}">
                        {NAME}
                    </span>
                </h4>
                <p class="text-justify">{DESCRIPTION}</p>
                <p class="text-justify">{MORE}</p>
            </div>
        </div>
    """

    return value_template.format(NAME=doc_block.just_name(),
                                 VALUE_ID=get_id_name(doc_block.just_name()),
                                 DESCRIPTION=doc_block.description,
                                 MORE=doc_block.more)


def create_container_elements_documentation(blocks):
    values_title_added = False
    functions_title_added = False

    content = ""

    for block in blocks:
        if block.type == "value":
            if not values_title_added:
                content += "<h2>Values</h2>"
                values_title_added = True

            content += create_value_documentation(block)
        elif block.type == "function":
            if not functions_title_added:
                content += "<h2>Functions</h2>"
                functions_title_added = True

            content += create_function_documentation(block)

    return content


def create_container_documentation(doc_block):
    container_template = """
        <div class="container">
            <div class="row" style="margin-top:10px">
                <div class="col-xs-12">
                    <button type="button" class="btn btn-md btn-info pull-right" onclick="window.location='index.html'">Back to index</button>
                </div>
            </div>
            <div class="row">
                <div class="col-xs-12">
                    <h1>
                        <span class="label label-default">{NAME}</span>
                    </h1>
                    <div class="alert alert-block alert-success text-justify">
                        <p>{DESCRIPTION}</p
                        <p>{MORE}</p>
                    </div>
                </div>
            </div>
            {CONTENT}
            <div class="row" style="margin-bottom:10px">
                <div class="col-xs-12">
                    <button type="button" class="btn btn-md btn-info pull-right" onclick="window.location='index.html'">Back to index</button>
                </div>
            </div>
        </div>
    """

    doc_block.child_blocks = sorted(doc_block.child_blocks, key=lambda b: b.type, reverse=True)

    return container_template.format(NAME=doc_block.name,
                                     DESCRIPTION=doc_block.description,
                                     MORE=doc_block.more,
                                     CONTENT=create_container_elements_documentation(doc_block.child_blocks))


def create_main_page(template_text, containers, container_names, container_free_blocks, title, description):
    description_template = """
        <div class="container">
            <div class="row">
                <div class="col-xs-12">
                    <div class="center-block">
                        <h1>
                            <span>{TITLE}</span>
                        </h1>
                        <div class="alert alert-block text-justify">
                            {DESCRIPTION}
                        <div>
                    </div>
                </div>
            </div>
        </div>
    """

    container_template = """
        <div class="row">
            <div class="col-xs-12" style="cursor: pointer;" onclick="window.location='{FILE_NAME}'">
                <h1>
                    <span class="label label-default">{NAME}</span>
                </h1>
                <div class="alert alert-block alert-success text-justify">
                    {DESCRIPTION}
                </div>
            </div>
        </div>
    """

    main_page_content = process_description_text(description_template.format(TITLE=title,
                                                                             DESCRIPTION=description),
                                                 container_names)

    main_page_content += create_container_elements_documentation(sorted(container_free_blocks,
                                                                        key=lambda b: b.type,
                                                                        reverse=True))

    for container in containers:
        doc_block = container[0]
        file_name = container[1]

        description = doc_block.description

        main_page_content += container_template.format(NAME=doc_block.name, DESCRIPTION=description,
                                                       FILE_NAME=file_name)

    return template_text.format(TITLE=title, BODY=main_page_content)


def copy_needed_files(file_src_dir, output_path):
    for file in glob.glob(file_src_dir + "files_to_copy/*.*"):
        shutil.copy(file, output_path)


def create_documentation(output_path, project_document_blocks, title, description):
    container_blocks = []
    container_free_blocks = []  # Blocks which are not container and are not in one

    for block in project_document_blocks:
        if block.type == "container":
            block.child_blocks = []
            container_blocks.append(block)
        elif "." not in block.name:  # It's possible that we have a free function or value (without a container)
            container_free_blocks.append(block)

    container_names = [b.just_name().lower() for b in container_blocks]

    for block in project_document_blocks:
        if len(block.description) > 0:
            block.description = process_description_text(block.description, container_names)
        if len(block.more) > 0:
            block.more = process_description_text(block.more, container_names)

        if block.type == "function":
            for i in range(len(block.params_info)):
                block.params_info[i] = add_links(block.params_info[i], container_names)

            if block.return_info:
                block.return_info = add_links(block.return_info, container_names)

        if block not in container_blocks and block not in container_free_blocks:
            block_container_name = block.name[:block.name.rfind(".")]
            for container in container_blocks:
                if block_container_name == container.name:
                    container.child_blocks.append(block)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_src_dir = os.path.dirname(os.path.realpath(__file__)) + "/"

    copy_needed_files(file_src_dir, output_path)

    with open(file_src_dir + "template.html", "r") as file:
        template_text = file.read()

    containers_info = []

    container_blocks = sorted(container_blocks, key=lambda c: c.name)

    for container in container_blocks:
        container_doc = create_container_documentation(container)

        file_name = "_" + container.name.replace(".", "_").lower() + "_.html"

        with open(output_path + file_name, "w") as file:
            file.write(template_text.format(TITLE=container.name, BODY=container_doc))

        containers_info.append((container, file_name))

    with open(output_path + "index.html", "w") as file:
        file.write(create_main_page(template_text, containers_info, container_names, container_free_blocks, title,
                                    description))


def main():
    parser = argparse.ArgumentParser(prog="Generic Document Generator")
    parser.add_argument("configuration_file",
                        help="Configuration file is a simple text file containing the different configuration options GDG needs to do its job.")

    arguments = parser.parse_args()

    with open(arguments.configuration_file, "r") as configuration_file:
        configuration_content = configuration_file.read()

    tags_texts = dict()

    for tag_text in get_tags_name_and_text(configuration_content):
        tag_name = tag_text[0]
        tag_text = tag_text[1]

        tags_texts[tag_name] = tag_text

    for mandatory_tag in ["extensions", "input_path", "output_path", "title"]:
        if mandatory_tag not in tags_texts.keys():
            print(
                    "Incorrect {0} configuration file: Missing {1} tag".format(arguments.configuration_file,
                                                                               mandatory_tag))

    extensions = [extension.strip() for extension in tags_texts["extensions"].split(",")]

    output_path = tags_texts["output_path"].replace("\\", "/")
    if output_path[-1] != "/":
        output_path += "/"

    input_path = tags_texts["input_path"].replace("\\", "/")
    if input_path[-1] != "/":
        input_path += "/"

    main_title = tags_texts["title"]

    description = ""

    if "description" in tags_texts.keys():
        description = tags_texts["description"]

    project_document_blocks = []

    for root, dirs, files in os.walk(input_path):
        root_normalized = root.replace("\\", "/")

        print("Entered {0} folder".format(root_normalized))
        for file in files:
            extension = os.path.splitext(file)[1]
            if extension[1:] in extensions:
                file_name = root_normalized + "/" + file
                file_document_blocks = get_file_documentation_blocks(file_name)
                if file_document_blocks:
                    project_document_blocks.extend(file_document_blocks)

                print("\tFile {0} processed: {1} document blocks".format(file_name, len(file_document_blocks)))

    print("Total document blocks: {0}".format(len(project_document_blocks)))

    create_documentation(output_path, project_document_blocks, main_title, description)


main()
