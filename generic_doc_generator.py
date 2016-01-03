import os
import argparse
import shutil

comment_ends = dict(h="*/", cpp="*/", lua="]]--")


class DocumentationBlock:
    def __init__(self, type, name, description):
        self.type = type
        self.name = name
        self.description = description

    def just_name(self):
        if "." not in self.name:
            return self.name
        else:
            return self.name[self.name.find(".") + 1:]


class FunctionBlock(DocumentationBlock):
    def __init__(self, name, description, params_info, return_info):
        DocumentationBlock.__init__(self, "function", name, description)
        self.params_info = params_info
        self.return_info = return_info


def get_tags_name_and_text(block_text):
    text = block_text.strip()

    tags_and_texts = []

    while len(text) > 0:
        index_start = text.find("@")

        if index_start == -1:
            break

        index_end = text.find(" ", index_start)
        tag_name = text[index_start + 1:index_end]

        index_start = index_end
        index_end = text.find("@", index_start)

        if index_end == -1:
            index_end = len(text)

        tag_text = text[index_start + 1:index_end].strip()

        tags_and_texts.append((tag_name, tag_text))

        text = text[index_end:]

    return tags_and_texts


def create_block(block_text):
    tags_info = dict()
    text = block_text.strip()

    params_info = []

    while len(text) > 0:
        index_start = text.find("@")

        if index_start == -1:
            break

        index_end = text.find(" ", index_start)
        tag_name = text[index_start + 1:index_end]

        index_start = index_end
        index_end = text.find("@", index_start)

        if index_end == -1:
            index_end = len(text)

        tag_text = text[index_start + 1:index_end].strip()

        if tag_name == "param":
            params_info.append(tag_text)
        else:
            tags_info[tag_name] = tag_text

        text = text[index_end:]

    if "function" in tags_info.keys():
        return_info = None

        if "return" in tags_info:
            return_info = tags_info["return"]

        return FunctionBlock(tags_info["function"], tags_info["description"], params_info, return_info)
    else:
        possible_names = ["container", "value"]

        key_name = None

        for name in possible_names:
            if name in tags_info:
                key_name = name
                break

        if not key_name:
            return None

        return DocumentationBlock(key_name, tags_info[key_name], tags_info["description"])


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
        <div class="container">
            <div class="row alert alert-block alert-info">
                <div class="col-xs-12">
                    <h4>
                        <span class="label label-success">
                            {NAME}
                        </span>
                    </h4>
                    <p><em>{DESCRIPTION}</em></p>
                    <div>
                        {CONTENT}
                    </div>
                </div>
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

    content = ""

    for param_info in doc_block.params_info:
        space_index = param_info.find(" ")
        name = param_info[0:space_index]
        description = param_info[space_index:]
        content += parameter_template.format(NAME=name, DESCRIPTION=description)

    if doc_block.return_info:
        content += return_template.format(DESCRIPTION=" " + doc_block.return_info)

    return function_template.format(NAME=doc_block.just_name(), DESCRIPTION=doc_block.description, CONTENT=content)


def create_value_documentation(doc_block):
    value_template = """
        <div class="container">
            <div class="row alert alert-block alert-warning">
                <div class="col-xs-12">
                    <h4>
                        <span class="label label-success">
                            {NAME}
                        </span>
                    </h4>
                    <p><em>{DESCRIPTION}</em></p>
                </div>
            </div>
        </div>
    """

    return value_template.format(NAME=doc_block.just_name(), DESCRIPTION=doc_block.description)


def divide_text_in_paragraphs(text):
    description_parts = text.splitlines()

    final_text = ""

    for part in description_parts:
        final_text += "<p>" + part.strip() + "</p>"

    return final_text


def create_container_documentation(doc_block):
    container_template = """
        <div class="container">
            <div class="row">
                <div class="col-xs-12">
                    <h1>
                        <span class="label label-default">{NAME}</span>
                    </h1>
                    <div class="alert alert-block alert-success">
                        {DESCRIPTION}
                    <div>
                </div>
            </div>
            <div>
                {CONTENT}
            </div>
        </div>
    """

    content = ""

    doc_block.child_blocks = sorted(doc_block.child_blocks, key=lambda b: b.type, reverse=True)

    values_title_added = False
    functions_title_added = False

    for block in doc_block.child_blocks:
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

    description = divide_text_in_paragraphs(doc_block.description)

    return container_template.format(NAME=doc_block.name, DESCRIPTION=description, CONTENT=content)


def create_main_page(template_text, containers):
    container_template = """
        <div class="container">
            <div class="row">
                <div class="col-xs-12" style="cursor: pointer;" onclick="window.location='{FILE_NAME}'">
                    <h1>
                        <span class="label label-default">{NAME}</span>
                    </h1>
                    <div class="alert alert-block alert-success">
                        {DESCRIPTION}
                    <div>
                </div>
            </div>
        </div>
    """

    main_page_content = ""

    container_number = len(containers)

    for i in range(container_number):
        doc_block = containers[i][0]
        file_name = containers[i][1]

        description = divide_text_in_paragraphs(doc_block.description)

        main_page_content += container_template.format(NAME=doc_block.name, DESCRIPTION=description,
                                                       FILE_NAME=file_name)

    return template_text.format(TITLE="JARE", BODY=main_page_content)


def create_documentation(output_path, project_document_blocks):
    container_blocks = []
    container_free_blocks = []  # Blocks which are not container and are not in one

    for block in project_document_blocks:
        if block.type == "container":
            block.child_blocks = []
            container_blocks.append(block)
        elif "." not in block.name:  # It's possible that we have a free function or value (without a container)
            container_free_blocks.append(block)

    for block in project_document_blocks:
        if block not in container_blocks and block not in container_free_blocks:
            block_container_name = block.name[:block.name.rfind(".")]
            for container in container_blocks:
                if block_container_name == container.name:
                    container.child_blocks.append(block)

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    file_src_dir = os.path.dirname(os.path.realpath(__file__)) + "/"

    shutil.copy(file_src_dir + "bootstrap.min.css", output_path)

    with open(file_src_dir + "template.html", "r") as file:
        template_text = file.read()

    containers = []

    for container in container_blocks:
        container_doc = create_container_documentation(container)

        file_name = container.name.replace(".", "_").lower() + ".html"

        with open(output_path + file_name, "w") as file:
            file.write(template_text.format(TITLE=container.name, BODY=container_doc))

        containers.append((container, file_name))

    with open(output_path + "index.html", "w") as file:
        file.write(create_main_page(template_text, containers))


def main():
    parser = argparse.ArgumentParser(prog="Generic Document Generator")
    parser.add_argument("extensions",
                        help="Extensions to be taken into account, separated by commas. For example for .lua and .cpp files: lua,cpp")
    parser.add_argument("output_path", help="Path where documentation files will be stored")
    parser.add_argument("--input_path",
                        help="Path where files to be parsed are in. If not provided current path (.) is used")
    arguments = parser.parse_args()

    file_names = []
    extensions = arguments.extensions.split(",")

    output_path = arguments.output_path.replace("\\", "/")

    if output_path[-1] != "/":
        output_path += "/"

    input_path = "."

    if arguments.input_path:
        input_path = arguments.input_path.replace("\\", "/")

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

    create_documentation(output_path, project_document_blocks)


main()
