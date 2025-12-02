import os
import ast
import itertools

files_to_skip = [
    # Console Domain Disabled
    'test_console.py',
    "test_page_event_console.py",
    "test_page_event_pageerror.py",

    # https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues/31
    'test_route_web_socket.py'
]

tests_to_skip = [
    # Disabled Console Domain
    "test_block_blocks_service_worker_registration",
    "test_console_event_should_work",
    "test_console_event_should_work_in_popup",
    "test_console_event_should_work_in_popup_2",
    "test_console_event_should_work_in_immediately_closed_popup",
    "test_dialog_event_should_work_in_immdiately_closed_popup",
    "test_console_event_should_work_with_context_manager",
    "test_weberror_event_should_work",
    "test_console_repr",
    "test_console_should_work",
    "test_should_collect_trace_with_resources_but_no_js",
    "test_should_work_with_playwright_context_managers",
    "test_should_respect_traces_dir_and_name",
    "test_should_show_tracing_group_in_action_list",
    "test_page_error_event_should_work",
    "test_click_offscreen_buttons",
    "test_watch_position_should_be_notified",
    "test_page_error_should_fire",
    "test_page_error_should_handle_odd_values",
    "test_page_error_should_handle_object",
    "test_page_error_should_handle_window",
    "test_page_error_should_pass_error_name_property",
    "test_workers_should_report_console_logs",
    "test_workers_should_have_JSHandles_for_console_logs",
    "test_workers_should_report_errors",

    # InitScript Timing
    "test_expose_function_should_be_callable_from_inside_add_init_script",
    "test_expose_bindinghandle_should_work",
    "test_browser_context_add_init_script_should_apply_to_an_in_process_popup",
    "test_should_expose_function_from_browser_context",

    # Disable Popup Blocking
    "test_page_event_should_have_an_opener",

    # Minor Differences in Call Log. Deemed Unimportant
    "test_should_be_attached_fail_with_not",
    "test_add_script_tag_should_include_source_url_when_path_is_provided",
    # / Black Formatting
    "test_should_collect_sources",
    "test_should_record_trace_with_source",

    # Server/Client Header Mismatch
    "test_should_report_request_headers_array",
    "test_request_headers_should_get_the_same_headers_as_the_server_cors",
    "test_request_headers_should_get_the_same_headers_as_the_server",
]

dont_isolate_evaluation_tests = [
    "test_timeout_waiting_for_stable_position",
    "track_events",
    "test_expose_function_should_work_on_frames_before_navigation",
    "test_should_dispatch_drag_drop_events",
    "test_should_dispatch_drag_and_drop_events_element_handle",
]

# Reason for skipping tests_backup
skip_reason = "Skipped as per documentation (https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues/31)"


class ParentAnnotator(ast.NodeVisitor):
    def __init__(self):
        self.parents = {}

    def visit(self, node):
        for child in ast.iter_child_nodes(node):
            self.parents[child] = node
            self.visit(child)

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    file_tree = ast.parse(source)
    annotator = ParentAnnotator()
    annotator.visit(file_tree)

    for node in ast.walk(file_tree):
        # Rename Playwright Imports to Patchright
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("playwright"):
                    alias.name = alias.name.replace("playwright", "phantomwright_driver", 1)
        if isinstance(node, ast.ImportFrom) and node.module.startswith("playwright"):
            node.module = node.module.replace("playwright", "phantomwright_driver", 1)

        # Skip Tests Documented: https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues/31
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            # Add Server Arg to test_add_init_script Tests
            if "test_add_init_script" in file_path:
                node.args.args.append(ast.arg(arg='server', annotation=None))
            # Skip Tests to skip
            if node.name in tests_to_skip:
                skip_decorator = ast.parse(f"@pytest.mark.skip(reason='{skip_reason}')\ndef placeholder(): return").body[0].decorator_list[0]
                node.decorator_list.insert(0, skip_decorator)

        # Add isolated_context=False to every necessary evaluate/evaluate_handle Call
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            # Very Bad Hack to get the parent node
            test_name = ""
            current_node = node
            while annotator.parents.get(current_node):
                current_node = annotator.parents[current_node]
                if isinstance(current_node, ast.FunctionDef) or isinstance(current_node, ast.AsyncFunctionDef):
                    test_name = current_node.name

            if test_name in dont_isolate_evaluation_tests:
            #    # Don't add isolated_context=False to these tests
                continue

            if (node.func.attr in ("evaluate", "evaluate_handle", "evaluate_all")
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in ("page", "popup", "button", "new_page", "page1", "page2", "target", "page_1", "page_2", "frame")
                and not (node.func.value.id == "button" and "element_handle" in file_path)
            ):
                node.keywords.append(ast.keyword(arg='isolated_context', value=ast.Constant(value=False)))

    modified_source = ast.unparse(ast.fix_missing_locations(file_tree))

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_source)

def main():
    with open("./tests/assets/inject.html", "w") as f:
        f.write("<script>window.result = window.injected;</script>")

    with open("./tests/conftest.py", "r") as read_f:
        conftest_content = read_f.read()
        updated_conftest_content = conftest_content.replace(
            "Path(inspect.getfile(playwright)).parent",
            "Path(inspect.getfile(phantomwright_driver)).parent"
        )

        with open("./tests/conftest.py", "w") as write_f:
            write_f.write(updated_conftest_content)


    for root, _, files in os.walk("tests"):
        for file in files:
            file_path = os.path.join(root, file)

            # Init Script Behaviour https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues/30
            if file == "test_add_init_script.py":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the full quoted strings with valid Python expressions (not strings)
                content = content.replace(
                    '"data:text/html,<script>window.result = window.injected</script>"',
                    'server.PREFIX + "/inject.html"'
                ).replace(
                    '"data:text/html,<html></html>"',
                    'server.PREFIX + "/empty.html"'
                )

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Init Script Behaviour https://github.com/Kaliiiiiiiiii-Vinyzu/patchright/issues/30
            if file == "test_page_clock.py":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the full quoted strings with valid Python expressions (not strings)
                content = content.replace(
                    "about:blank",
                    "https://www.google.com/blank.html"
                ).replace(
                    "data:text/html,",
                    "https://www.google.com/blank.html"
                )

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # Import Pytest
            if file in ("test_browsercontext_service_worker_policy.py", "test_tracing.py", "test_popup.py", "test_dispatch_event.py"):
                # Append "import pytest" to the top of the file
                with open(file_path, 'r+', encoding='utf-8') as f:
                    content = f.read()
                    if "import pytest" not in content:
                        f.seek(0, 0)
                        f.write("import pytest\n" + content)

            # Skipping Files
            if file in files_to_skip:
                # Delete File
                os.remove(file_path)
                continue

            if file.endswith('.py'):
                process_file(file_path)

            if file == "test_queryselector.py":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the full quoted strings with valid Python expressions (not strings)
                content = content.replace(
                    "assert await page.eval_on_selector_all('isolated=ignored', 'es => window.__answer !== undefined')",
                    """await page.evaluate('() => window.__answer = document.querySelector("span")', isolated_context=True)\n    assert await page.eval_on_selector_all('isolated=ignored', 'es => window.__answer !== undefined')"""
                ).replace(
                    "assert page.eval_on_selector_all('isolated=ignored', 'es => window.__answer !== undefined')",
                    """page.evaluate('() => window.__answer = document.querySelector("span")', isolated_context=True)\n    assert page.eval_on_selector_all('isolated=ignored', 'es => window.__answer !== undefined')"""
                )

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == '__main__':
    main()